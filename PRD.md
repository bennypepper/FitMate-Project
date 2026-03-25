Product Requirements Document (PRD): FitMate

Project: FitMate (TCM Safety Scanner & Consultant)
Document Version: 2.0 (Updated with Data Pipeline & Brand Guidelines)
Role: Product Manager & System Architect

1. Overview

The widespread practice of unsupervised self-medication using Traditional Chinese Medicine (TCM) presents a significant public health risk. Most consumers cannot read Mandarin labels and are unaware of potential nephrotoxic or cardiotoxic side effects. FitMate provides a vital safety net by combining a Web-Based OCR Scanner (for visual detection) and a WhatsApp Chatbot Consultant (for follow-up text consultation). By allowing users to scan TCM labels, the application instantly translates the ingredients and cross-references them against a strictly validated, rule-based medical database to flag dangerous compounds. The main objective is to empower regular users with accessible, zero-hallucination medical information to prevent health emergencies, while providing a structured data pipeline for pharmacists to safely update the TCM toxicity knowledge base.

2. Requirements

Platform/Responsiveness: Web-Based Progressive Web App (PWA) optimized for mobile camera usage, ensuring a native-like experience without requiring app store downloads.

Role-based Access Constraints:

Guest/User: Can access the camera scanner, view translation results, receive warnings, and interact with the WhatsApp Chatbot statelessly (no login or account creation required).

Admin/Pharmacist: Requires secure login to access the dashboard, manage the TCM database, and upload validated datasets.

Data/System Behavior: * Real-time OCR extraction and translation of Mandarin characters via Google Cloud Vision API.

Strict Rule-Based validation ensuring "Zero Hallucination" (no AI guessing in medical advice).

Stateless Synchronization using dynamic pre-filled URLs (wa.me) to bridge the Web App and WhatsApp Bot without session overhead.

UI/UX Expectations: * User-friendly interface with high accessibility.

Strict adherence to the 60-25-10-5 color ratio rule, utilizing Imperial Red exclusively for critical toxicity warnings to grab immediate attention.

3. Core Features

Landing Page / Main Interface (Web Scanner)

Camera Access Integration via HTML5.

Real-time processing loader with visual bounding boxes for Hanzi text.

Dynamic URL generation for the "Consult via WhatsApp" CTA based on detected ingredients.

ASCII Wireframe Reference:

+---------------------------------------+
| [ FitMate ]                  [ Menu ] |
+---------------------------------------+
|                                       |
|  Scan Your TCM Composition Label      |
|  to check for hidden health risks.    |
|                                       |
|    +-----------------------------+    |
|    |                             |    |
|    |      [ Camera Feed ]        |    |
|    |    [  Focus on Hanzi  ]     |    |
|    |                             |    |
|    +-----------------------------+    |
|                                       |
|          ( CAPTURE IMAGE )            |
|                                       |
+---------------------------------------+
|  Results:                             |
|  [!] TOXICITY WARNING DETECTED        |
|  Ingredient: Diterpenoid Alkaloids    |
|  Risk: Cardiotoxic (Heart Risk)       |
|                                       |
|       [ Consult via WhatsApp ]        |
+---------------------------------------+


User Core System (Validation & Consultation)

OCR Translation Engine (Mandarin to Indonesian).

Toxicity Warning System (Red Flag pop-ups).

Stateless Deep Link Generator (wa.me/628...?text=...).

WhatsApp NLP Chatbot configured strictly for text-based rule-based lifestyle and dosage consultations (does not process images to avoid timeout complexity).

Admin Dashboard & Data Pipeline

Automated Data Scraping triggers (fetching raw data from TCMID/SymMap).

Knowledge Base Management (Excel/CSV upload feature for pharmacist-validated data).

Rule Management (Setting If-Then-Else logic parameters).

Authentication System

JWT-based secure login for the Admin panel.

Role-based middleware to protect database mutation routes.

4. User Flow

Alur Pengguna (User):

User opens the FitMate PWA via their mobile browser.

User grants camera permissions and captures the TCM packaging label.

The system processes the image (OCR) and cross-references the translated text against the MongoDB Knowledge Base.

User views the extracted ingredients. If toxic, a warning appears in Imperial Red.

User clicks the "Consult via WhatsApp" button.

The React frontend dynamically generates a wa.me URL containing the detected ingredient and user context.

User is redirected to their WhatsApp app with a pre-filled message (e.g., "Hello FitMate, I just scanned Diterpenoid Alkaloids...").

User hits send, and the NLP Chatbot instantly replies with rule-based medical advice.

Alur Pengelola (Admin/Pharmacist) - Data Pipeline Flow:

IT Admin runs the Python scraping script (using BeautifulSoup4/Selenium) targeting TCMID/BPOM databases.

IT Admin exports the raw scraped data to an Excel (.xlsx) file.

Pharmacist (Admin) manually reviews the Excel file, adds is_toxic = TRUE/FALSE flags, and writes medical advice.

Pharmacist logs into the FitMate Admin Dashboard.

Pharmacist uploads the validated Excel file.

The system updates the MongoDB database, instantly applying the new rules to the live scanner.

System Flow Diagram:

graph TD
    %% Data Pipeline Flow (Admin)
    subgraph Data Pipeline & Backend
        Z1[Scrape TCMID/BPOM] --> Z2[Export Raw Excel]
        Z2 --> Z3[Manual Pharmacy Validation]
        Z3 --> Z4[Import to MongoDB]
        Z4 --> DB[(Knowledge Base DB)]
    end

    %% User Interaction Flow
    subgraph Frontend Client (PWA)
        A[Open FitMate Web App] --> B[Capture TCM Label Image]
        B --> C[Send to Backend via API]
    end
    
    C -->|Google Vision API| D[Extract & Translate Hanzi]
    D --> E{Cross-reference DB}
    DB -.-> E
    E -->|Toxic Match| F[Display Imperial Red Warning]
    E -->|Safe Match| G[Display Safe Ingredients]
    
    F --> H[Generate Stateless wa.me Deep Link]
    G --> H
    
    subgraph WhatsApp Environment
        H --> I[User Clicks Send on Pre-filled WA Message]
        I --> J[WhatsApp Bot Replies via Rule-Based Logic]
    end


5. Architecture

FitMate utilizes a Modern Client-Server Architecture with Separation of Concerns.
The Frontend (React PWA) is strictly responsible for heavy UI tasks: accessing the camera, displaying loading states, and showing colored alerts.
The Backend (Python/FastAPI) acts as the central processor, handling asynchronous calls to the Google Cloud Vision API for OCR and querying the MongoDB NoSQL database.
To ensure maximum speed and minimal server load, the integration between the Web App and the WhatsApp Bot uses a Stateless Pre-filled URL strategy. Instead of saving temporary session IDs in the database, the Frontend directly generates a WhatsApp deep link containing the context of the scanned ingredient. The WhatsApp Bot serves purely as a text-based consultant, eliminating the risk of image processing timeouts on the Meta API.

6. Database Schema

USERS_ADMIN

UUID id (PK)

VARCHAR username

VARCHAR password_hash

VARCHAR role

TIMESTAMP created_at

TCM_INGREDIENTS

UUID id (PK)

VARCHAR mandarin_name

VARCHAR indonesian_name

BOOLEAN is_toxic

VARCHAR target_organ

TEXT description

SAFETY_RULES

UUID id (PK)

UUID ingredient_id (FK)

VARCHAR condition_logic

TEXT warning_message

TEXT medical_advice

SCAN_LOGS

UUID id (PK)

TEXT ocr_raw_text

VARCHAR detected_ingredients

BOOLEAN warning_triggered

TIMESTAMP scanned_at

7. Tech Stack

Frontend: React.js (Next.js) + Tailwind CSS (configured as a PWA).

Backend: Python 3 (FastAPI) for high-performance API routing.

Data Pipeline/Scraping: BeautifulSoup4, Selenium, Pandas.

Database: MongoDB (for flexible Knowledge Base/Rules) and PostgreSQL (for Admin Users/Logs).

Authentication: JWT (JSON Web Tokens) for secure admin sessions.

External APIs: Google Cloud Vision API (OCR) & WhatsApp Cloud API.

Deployment: Vercel (Frontend) and AWS EC2 / VPS Hostinger (Backend).

8. Design Guidelines

Palet Warna (Color Palette):

Warna Primer: Imperial Red (#930014) - Used for crucial warnings, main headings, and indicating contraindications or toxicity to grab the user's immediate attention. Deep Burgundy (#5B000B) is used for primary body text and footers.

Warna Sekunder: Coral Red (#DB4B3A) - Used for sub-headings, icons, highlights, and secondary buttons. Warm Peach (#E68757) is utilized for section backgrounds and hover states.

Warna Netral: Soft Beige (#E7BD8A) & White (#FFFFFF) - Soft beige acts as the main background and divider, while White is used for cards and text on dark backgrounds to ensure maximum readability and a clean UI space.

Accent Color: Imperial Gold (#D4AF37) - Strictly restricted to Call-To-Action (CTA) buttons, important badges (e.g., BPOM certification), and crucial icons to maintain a premium feel.

Typography: Playfair Display / Merriweather for Headings; Inter / Poppins for Body; Noto Sans SC for Chinese characters.

9. Development Process Flow

Planning → Designing → Frontend Dev → Backend Dev → Integration → Testing

Planning: Month 1 phase. Define business needs, write Python scripts to scrape raw data from TCMID/SymMap, export to Excel, and conduct manual medical validation by the Pharmacy team to ensure Zero Hallucination.

Designing: Create high-fidelity UI/UX wireframes applying the 60-25-10-5 color ratio rule, design the database schema, and map out the NLP conversation flowchart for the WhatsApp Chatbot.

Frontend Dev: Build the responsive Web App interface using React and Tailwind CSS, configure PWA settings, implement the camera access module, and program the stateless wa.me deep link generation logic.

Backend Dev: Set up the Python FastAPI server and MongoDB. Develop the rule-based decision engine and integrate the Google Cloud Vision API for Hanzi OCR translation.

Integration: Connect the React Client and WhatsApp Webhook to the Python Server. Ensure the stateless data handoff from Web Scanner to WhatsApp Bot works flawlessly in real-time.

Testing: Conduct Black-box testing for system bugs, UAT (User Acceptance Testing) with 15-20 layperson respondents, and rigorous medical validation with advising professors before the final deployment to AWS/Hostinger for the PIMNAS presentation.