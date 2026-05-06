# FitMate 🌿

FitMate is a Traditional Chinese Medicine (TCM) Safety Scanner and Consultant built as a Progressive Web App (PWA) with a WhatsApp chatbot companion. It enables consumers to scan TCM product labels using their phone camera, instantly translates the Mandarin ingredient text, and cross-references ingredients against a validated toxicity database to flag dangerous compounds and contraindications.

When warnings are detected, users are seamlessly bridged to a WhatsApp chatbot for rule-based medical guidance - with zero AI hallucination in medical recommendations.

## Features

- 📸 **Web-Based OCR Scanner:** Real-time extraction and translation of Mandarin characters via an LLM-based multimodal pipeline.
- 🚦 **Toxicity Warning System:** Strict rule-based validation ensures medical information is accurate and non-hallucinated.
- 💬 **WhatsApp Chatbot Consultant:** Stateless synchronization generates pre-filled `wa.me` links to bridge the Web App and WhatsApp Bot without session overhead. The bot provides conversational yet strictly rule-based medical guidance.
- 📱 **Progressive Web App (PWA):** Native-like experience on mobile devices without requiring app store downloads.
- 🛠️ **Admin Dashboard:** Secure login for pharmacists to manage the TCM database and upload validated datasets.

## Architecture

FitMate utilizes a modern Client-Server Architecture:
- **Frontend (React/Next.js + Tailwind CSS):** A PWA that handles UI tasks, camera access, and stateless deep link generation to WhatsApp.
- **Backend (Python/FastAPI):** Central processor that orchestrates OCR processing (via Google Cloud Vision / Gemini Multimodal) and queries the MongoDB database.
- **WhatsApp Integration (Twilio):** Serves as a text-based consultant. The stateless pre-filled URL strategy eliminates the risk of image processing timeouts on the Meta API.

## Tech Stack

- **Frontend:** React.js (Next.js 14), Tailwind CSS, PWA
- **Backend:** Python 3.11, FastAPI
- **Database:** MongoDB (Knowledge Base/Rules), PostgreSQL (Admin Users/Logs)
- **Authentication:** JWT (JSON Web Tokens)
- **External APIs:** Gemini 2.5 Flash Lite (OCR/NLU via OpenRouter), Twilio (WhatsApp Cloud API)
- **Deployment:** Vercel (Frontend), AWS EC2 / VPS Hostinger (Backend)

## Getting Started

### Prerequisites

- Node.js (v18+)
- Python (v3.11+)
- MongoDB (running locally or via Atlas)
- Accounts/API keys for Twilio and OpenRouter

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/FitMate-Project.git
   cd FitMate-Project
   ```

2. **Backend Setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
   Create a `.env` file in the `backend` directory with your database and API credentials (see `backend/.env.example`).
   Run the development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

3. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   ```
   Create a `.env.local` file with the required environment variables (e.g., `NEXT_PUBLIC_API_URL=http://localhost:8000`).
   Run the development server:
   ```bash
   npm run dev
   ```

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
