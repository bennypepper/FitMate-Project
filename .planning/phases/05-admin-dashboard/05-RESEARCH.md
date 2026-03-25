# Phase 5: Admin Dashboard — Research

## Executive Summary
- **JWT Authentication**: Use **PyJWT** + **passlib[recommended]** (bcrypt). Store hashed password in `.env` — never plaintext. Use `HTTPBearer` FastAPI security dependency for protected routes.
- **Admin UI Guard**: Client-side `AuthGuard` component in Next.js using `useEffect` to check `localStorage` after mount — avoids hydration mismatch. Route group `(admin)` keeps URL as `/admin/*`.
- **Data Pipeline**: `openpyxl` for .xlsx + built-in `csv` module for .csv — avoids heavy `pandas` dependency. In-memory via `io.BytesIO`. Two-phase: validate endpoint → import endpoint.
- **MongoDB Upsert**: `update_one` with `upsert=True` using `mandarin_name` as natural key. Build `$set` dynamically to avoid overwriting fields with empty cells.

---

## 1. FastAPI JWT Authentication

### Library Decision
**PyJWT** over `python-jose` — python-jose is less actively maintained in 2024-2025. PyJWT is the current community standard and has cleaner APIs.

**passlib[recommended]** for bcrypt hashing — provides `CryptContext` with bcrypt scheme.

### Admin Credential Storage
```env
# .env
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...  # pre-calculated bcrypt hash, never store plaintext
JWT_SECRET_KEY=your-256-bit-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8
```

Generate hash one-time: `python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('yourpassword'))"`

### Login Flow
```python
# routers/admin.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/login")
@limiter.limit("5/minute")  # brute-force protection
async def login(request: Request, credentials: LoginRequest):
    if credentials.username != settings.ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not pwd_context.verify(credentials.password, settings.ADMIN_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    payload = {
        "sub": credentials.username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}
```

### Protected Route Dependency
```python
def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Usage on protected routes:
@router.get("/ingredients")
async def list_ingredients(admin: str = Depends(get_current_admin)):
    ...
```

### Rate Limiting Login
Apply `slowapi` `@limiter.limit("5/minute")` to the login endpoint — the limiter is already configured on `app.state.limiter` in `main.py`.

---

## 2. Next.js Auth Guard Pattern

### Route Group
Use `app/(admin)/admin/` structure. The `(admin)` folder is a route group (parentheses = excluded from URL), so URLs stay clean as `/admin`, `/admin/login`, `/admin/ingredients`, `/admin/upload`.

Actually, simpler for this prototype: just use `app/admin/` directly — no route group needed since there's no URL conflict. The route group `(admin)` is useful when you need a shared layout that doesn't affect the path, but `app/admin/layout.tsx` already achieves this.

**Final structure:**
```
frontend/src/app/
  admin/
    layout.tsx           ← wraps all /admin/* with AuthGuard
    login/page.tsx       ← public (no AuthGuard needed — excluded from layout check)
    page.tsx             ← redirect to /admin/ingredients or overview
    ingredients/page.tsx ← ingredient list table
    upload/page.tsx      ← Excel upload
```

### AuthGuard Component
```tsx
// components/admin/AuthGuard.tsx
'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const [authorized, setAuthorized] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (!token || isTokenExpired(token)) {
      localStorage.removeItem('admin_token');
      router.replace('/admin/login');
    } else {
      setAuthorized(true);
    }
  }, [router]);

  if (!authorized) return <div className="min-h-screen bg-surface flex items-center justify-center">
    <span className="text-on-surface-variant font-sans text-sm">Memuat...</span>
  </div>;
  
  return <>{children}</>;
}
```

### Admin Layout
```tsx
// app/admin/layout.tsx
import { AuthGuard } from '@/components/admin/AuthGuard';
import { AdminSidebar } from '@/components/admin/AdminSidebar';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen">
        <AdminSidebar />
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </AuthGuard>
  );
}
```

**Hydration note:** `authorized` starts as `false`, rendering a loading state on first paint (both server and client agree). `useEffect` only runs client-side — sets `authorized: true` if valid, or redirects. This avoids the hydration mismatch that occurs when you access `localStorage` during render.

### Login Page (excluded from AuthGuard)
The `/admin/login` page must NOT be wrapped by AuthGuard. Since `admin/layout.tsx` applies to ALL `/admin/*` routes, the login check in AuthGuard should skip redirect if already on `/admin/login` — or use a separate layout for login only.

**Simplest approach:** check `usePathname()` in AuthGuard and skip redirect on `/admin/login`.

### API Call Pattern
```ts
// lib/adminApi.ts
export function getAdminHeaders() {
  const token = localStorage.getItem('admin_token');
  return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
}
```

---

## 3. Excel/CSV Parsing in FastAPI

### Library Decision
- **openpyxl** for .xlsx — lightweight, no numpy dependency, purpose-built for Excel
- **built-in `csv` module** for .csv — zero additional dependencies
- Avoid pandas for this use case — adds ~30MB of dependencies for simple row iteration

### In-Memory File Processing
```python
import openpyxl
import csv
import io
from fastapi import UploadFile, File

async def parse_excel_file(file: UploadFile) -> list[dict]:
    content = await file.read()
    filename = file.filename.lower()
    
    if filename.endswith('.xlsx'):
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        sheet = wb.active
        headers = [cell.value for cell in sheet[1]]  # first row = headers
        rows = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            rows.append(dict(zip(headers, row)))
        return rows
        
    elif filename.endswith('.csv'):
        stream = io.StringIO(content.decode('utf-8-sig'))  # utf-8-sig handles BOM from Excel CSV export
        reader = csv.DictReader(stream)
        return list(reader)
    
    else:
        raise ValueError("Unsupported file format")
```

### Validation with Row-Level Errors
```python
def validate_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Returns (valid_rows, errors) where errors have row number."""
    valid, errors = [], []
    for i, row in enumerate(rows, start=2):  # row 2 = first data row (row 1 = headers)
        row_errors = []
        
        # Required fields
        if not row.get('mandarin_name'):
            row_errors.append({'field': 'mandarin_name', 'message': 'Nama Mandarin wajib diisi'})
        if not row.get('indonesian_name'):
            row_errors.append({'field': 'indonesian_name', 'message': 'Nama Indonesia wajib diisi'})
        if row.get('is_toxic') not in (True, False, 'true', 'false', 'TRUE', 'FALSE', '1', '0'):
            row_errors.append({'field': 'is_toxic', 'message': 'Status toksisitas harus true/false'})
        if not row.get('source_reference') or str(row.get('source_reference', '')).lower() in ('', 'unknown', 'none'):
            row_errors.append({'field': 'source_reference', 'message': 'Referensi sumber wajib diisi'})
        
        if row_errors:
            errors.append({'row': i, 'errors': row_errors})
        else:
            valid.append(row)
    
    return valid, errors
```

### Async Consideration
openpyxl is synchronous. For prototype, calling sync code directly in an async FastAPI handler is acceptable (no significant blocking for files under 10MB). For production, wrap in `asyncio.get_event_loop().run_in_executor(None, sync_func)`.

---

## 4. MongoDB Upsert Pattern

### Natural Key
`mandarin_name` is the unique identifier for TCM ingredients. Use it as the upsert filter.

### Dynamic Update (avoid overwriting with None)
```python
async def upsert_ingredient(db, row: dict) -> str:
    """Returns 'inserted' or 'updated'."""
    # Convert is_toxic to bool
    is_toxic_raw = str(row.get('is_toxic', 'false')).lower()
    is_toxic = is_toxic_raw in ('true', '1', 'yes')
    
    # Build update object — exclude None values to avoid overwriting existing data
    update_data = {
        'indonesian_name': row.get('indonesian_name'),
        'is_toxic': is_toxic,
        'source_reference': row.get('source_reference'),
    }
    # Optional fields — only include if present in Excel
    for field in ['pinyin_name', 'latin_name', 'english_name', 'target_organ', 'toxicity_level', 'description']:
        if row.get(field):
            update_data[field] = row[field]
    
    result = await db.tcm_ingredients.update_one(
        {'mandarin_name': row['mandarin_name']},
        {'$set': update_data},
        upsert=True
    )
    return 'inserted' if result.upserted_id else 'updated'
```

### Collection Name
From `database/schemas.py` context, collection is `tcm_ingredients`.

---

## 5. Drag-and-Drop File Upload

### Library Decision
**react-dropzone** — 14KB gzipped, well-maintained, handles all edge cases (drag states, MIME type filtering, size limits, accessibility). Native HTML5 drag-and-drop requires significant boilerplate to handle all browser quirks.

```tsx
import { useDropzone } from 'react-dropzone';

const { getRootProps, getInputProps, isDragActive } = useDropzone({
  accept: {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'text/csv': ['.csv'],
  },
  maxSize: 10 * 1024 * 1024, // 10MB
  maxFiles: 1,
  onDrop: async (acceptedFiles) => {
    const file = acceptedFiles[0];
    const formData = new FormData();
    formData.append('file', file);
    
    const token = localStorage.getItem('admin_token');
    const response = await fetch('/api/v1/admin/upload/validate', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData,  // No Content-Type header — browser sets multipart boundary automatically
    });
    const result = await response.json();
    setValidationResult(result);
  }
});
```

### Upload Validation Response Shape
```ts
interface ValidationResult {
  valid_count: number;
  error_count: number;
  errors: Array<{
    row: number;
    errors: Array<{ field: string; message: string; }>;
  }>;
}
```

---

## 6. Dependencies to Add

### Backend (add to requirements.txt)
```
PyJWT>=2.8.0
passlib[bcrypt]>=1.7.4
openpyxl>=3.1.2
python-multipart>=0.0.9   # for FastAPI file uploads — check if already present
```

### Frontend (add to package.json)
```
react-dropzone    # ^14.x
jwt-decode        # ^4.x — OR use manual base64 decode (already shown in AuthGuard above)
```

Note: `jwt-decode` is optional since the manual `atob(token.split('.')[1])` approach is already implemented in the AuthGuard above. Only add if you want a more robust decode.

---

## Validation Architecture

### JWT Authentication
```bash
# Test login — should return { "access_token": "...", "token_type": "bearer" }
curl -X POST http://localhost:8000/api/v1/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}'

# Test protected route without token — should return 403
curl http://localhost:8000/api/v1/admin/ingredients

# Test protected route with valid token — should return ingredient list
curl http://localhost:8000/api/v1/admin/ingredients \
  -H "Authorization: Bearer <token_from_login>"

# Test brute force protection — 6th request within 1 min should return 429
for i in {1..6}; do curl -X POST http://localhost:8000/api/v1/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "wrongpassword"}'; done
```

### Auth Guard (Frontend)
```
1. Open /admin/ingredients in browser while logged out → verify redirect to /admin/login
2. Log in → verify token stored in localStorage
3. Navigate to /admin/ingredients → verify page loads (no redirect)
4. Manually delete token from localStorage → refresh → verify redirect to /admin/login
5. Set token expiry to 1 second in test → wait → refresh → verify redirect
```

### Excel Upload Validate Endpoint
```bash
# Create a test file with valid rows — should return { valid_count: N, error_count: 0, errors: [] }
curl -X POST http://localhost:8000/api/v1/admin/upload/validate \
  -H "Authorization: Bearer <token>" \
  -F "file=@test_valid.xlsx"

# Create a test file with row missing mandarin_name — should return error for that row
curl -X POST http://localhost:8000/api/v1/admin/upload/validate \
  -H "Authorization: Bearer <token>" \
  -F "file=@test_invalid.xlsx"
# Expected: { valid_count: N-1, error_count: 1, errors: [{ row: X, errors: [...] }] }
```

### MongoDB Upsert After Import
```bash
# Get ingredient count before import
curl http://localhost:8000/api/v1/analyze/ingredients/count

# Import validated file
curl -X POST http://localhost:8000/api/v1/admin/upload/import \
  -H "Authorization: Bearer <token>" \
  -F "file=@test_valid.xlsx"
# Expected: { imported: N, updated: M }

# Get count after — should be initial_count + (N - M)
curl http://localhost:8000/api/v1/analyze/ingredients/count
```

### Dashboard Data Display
```
1. Navigate to /admin → verify stat cards show ingredient count, toxic count
2. Navigate to /admin/ingredients → verify table shows ingredient rows with Mandarin char avatar, toxicity badges
3. Navigate to /admin/upload → verify drag-and-drop zone renders
```
