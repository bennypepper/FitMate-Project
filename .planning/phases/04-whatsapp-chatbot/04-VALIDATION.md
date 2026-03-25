---
phase: 04-whatsapp-chatbot
date: 2026-03-25
---

# Phase 04 Validation Strategy

This document outlines the testing dimensions required to validate Phase 04 completely. Plans MUST include specific tasks to build these validations.

## 1. Unit Testing
- Test the Meta Webhook token verification endpoint.
- Test Gemini Prompt Builder/Parser with mocked GenerativeModel responses to ensure correct intent extraction and JSON parsing.

## 2. Integration Testing
- Create a test client simulating an incoming `POST` Webhook event from Meta containing a message string.
- Mock the Meta `send_message` API endpoint.
- Assert the backend queries MongoDB (via fake/real mongo instance) and formats a reply containing rule-based answers and the medical disclaimer.
- Assert that rate limit headers and 429 status codes trigger correctly for rapid repeated messages from the same phone number.

## 3. Boundary / Edge Case Testing
- Ensure an unrecognized ingredient forces the exact default "Not in database / I don't know" textual response with no hallucinations or guesses.
- Test missing properties in Meta's JSON payload.

## 4. End-to-End Testing (Manual)
- Manually configure a Meta developer test phone number. Send a message to the deployed or Ngrok-tunneled webhook and receive a successfully generated response.

## 5. Environment & Infrastructure
- Ensure `slowapi` decorators (or equivalent route-level middleware) correctly interpret `req.client.host` for standard rate limiting, and the Meta webhook correctly parses the WhatsApp sender ID for bot rate limiting. 
- Must read `WHATSAPP_TOKEN`, `VERIFY_TOKEN`, and `GEMINI_API_KEY` from environment variables safely.
