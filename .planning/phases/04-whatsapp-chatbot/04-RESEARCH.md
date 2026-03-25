# Phase 04: WhatsApp Chatbot - Research

## Objective
Identify how to implement the hybrid WhatsApp chatbot (FastAPI webhook, Meta API configuration, Gemini Flash integration, and strict rule enforcement) for the backend.

## Architecture

1.  **WhatsApp Cloud API Webhook Flow:**
    *   **Endpoint:** A FastAPI route (`POST /whatsapp/webhook`) needs to be exposed and verified by Meta's WhatsApp Cloud API endpoint (with `GET /whatsapp/webhook` for hub token verification).
    *   **Message Reception:** The webhook receives a JSON payload containing the sender's phone number and the text of the message sent.

2.  **Hybrid LLM + Rule-Based Engine Pipeline:**
    *   **Intent Parsing (Gemini Flash):** Send the incoming message to Gemini API. Use a strict system prompt outputting JSON. E.g., `{"intent": "ingredient_inquiry", "ingredient_name": "Ginseng"}`. We solely use Gemini for entity extraction and intent understanding out of messy natural language.
    *   **Database Lookup (MongoDB):** Query the MongoDB toxicity database (using fuzzy matching from Phase 2) for `ingredient_name`.
    *   **Response Construction (Rules):**
        *   If ingredient exists: Format the safe/toxic warning, contraindications, and mandatory medical disclaimer from Phase 2 logic.
        *   If ingredient not found or intent not `ingredient_inquiry`: Fallback directly to the required "Not in database / I don't know" response.
    *   **Send Message (Meta API):** Dispatch the constructed response payload via the WhatsApp Cloud API send message endpoint (`POST https://graph.facebook.com/.../messages`).

3.  **Security & Rate Limiting:**
    *   **Request Validation:** Ensure Meta signatures are validated.
    *   **Rate Limiting:** Implement per-phone-number rate limits (using an in-memory or generic database rate limiter bucket depending on what's available) to prevent Gemini API budget exhaustion. 

## Best Practices & Patterns

*   **Idempotency & Retry Handling:** WhatsApp sends retries if the webhook doesn't respond quickly (e.g., 200 OK within limited time). A best practice is to offload message processing to `fastapi.BackgroundTasks` so the webhook returns `200 OK` immediately, but this breaks stateless easily. Since we use Gemini Flash API, it should return fast enough (1-2s). If not, we might need a background queue or fast failure.
*   **System Prompts:** Keep the Gemini system prompt strict. Ex: "You are an entity extractor. Return ONLY JSON. Extract the TCM ingredient the user is asking about."
*   **Decoupled Services:** Extract Meta API client wrapper (for sends/verifications) from the webhook router.

## Dependencies

*   `google-generativeai`: For invoking Gemini Flash.
*   `httpx`: Standard for async HTTP calls in FastAPI (to send Meta API requests).
*   `slowapi` or custom middleware for FastAPI rate limiting.

## Validation Architecture

*   **Unit Tests:** Mock Gemini Flash responses to ensure predictable intent parsing; Unit test Meta webhook verification token logic.
*   **Integration Tests:** Send a simulated webhook POST to the FastAPI endpoint to verify the correct response payload structure is built and rate limits are respected.
*   **Environment checks:** Verify `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `GEMINI_API_KEY` are read properly from defaults/`.env`.

## RESEARCH COMPLETE
