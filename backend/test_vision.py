"""
Quick smoke test for Google Cloud Vision credentials.
Run from the backend/ directory with the venv activated:
  python test_vision.py
"""
import os
import sys

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials/google-vision-key.json"

try:
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()
    print("✅ Vision client created successfully")
    print("   Credentials loaded from:", os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
except Exception as e:
    print("❌ Failed to create Vision client:", e)
    sys.exit(1)

# Minimal API call: annotate a 1x1 white pixel PNG (smallest valid image)
# This confirms the API is enabled and the key has permission.
import base64

# 1x1 white pixel PNG, base64
WHITE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)

try:
    image = vision.Image(content=WHITE_PIXEL_PNG)
    response = client.text_detection(image=image)
    if response.error.message:
        print("❌ API returned error:", response.error.message)
        sys.exit(1)
    print("✅ API call succeeded — Vision API is enabled and credentials are valid")
    print("   Texts detected:", [t.description for t in response.text_annotations] or "(none — expected for blank image)")
except Exception as e:
    print("❌ API call failed:", e)
    sys.exit(1)
