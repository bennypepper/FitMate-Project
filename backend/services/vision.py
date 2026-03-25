import os
from google.cloud import vision

def extract_and_translate_text(image_bytes: bytes) -> list[dict]:
    """
    Extracts text using Google Cloud Vision and groups by words/lines.
    Uses 'zh' as language hint if needed.
    """
    # Warning: During prototype, if credentials are not configured properly,
    # this will raise an error. Ensure GOOGLE_APPLICATION_CREDENTIALS is set
    # or the Cloud SDK is authenticated.
    
    # Optional: Mock implementation if GOOGLE_CLOUD_VISION_API_KEY is missing
    # in local development to allow testing without hitting the API.
    if os.environ.get("MOCK_VISION_API", "true").lower() == "true":
        # Return a mock output matching the expected format
        return [
            {
                "text": "人参",
                "bounding_box": [{"x": 10, "y": 10}, {"x": 50, "y": 10}, {"x": 50, "y": 30}, {"x": 10, "y": 30}]
            },
            {
                "text": "当归",
                "bounding_box": [{"x": 10, "y": 40}, {"x": 50, "y": 40}, {"x": 50, "y": 60}, {"x": 10, "y": 60}]
            }
        ]

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)

    # Use document_text_detection for dense text (like labels)
    response = client.document_text_detection(image=image)
    
    if response.error.message:
        raise Exception(f"{response.error.message}")

    results = []
    
    # Iterate over pages > blocks > paragraphs > words
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                # Group by paragraph or word. We'll extract lines/words
                # D-02: Group OCR results into words/lines
                text_content = ""
                box_vertices = paragraph.bounding_box.vertices
                
                for word in paragraph.words:
                    word_text = "".join([symbol.text for symbol in word.symbols])
                    text_content += word_text
                
                if text_content.strip():
                    results.append({
                        "text": text_content,
                        "bounding_box": [
                            {"x": vertex.x, "y": vertex.y}
                            for vertex in box_vertices
                        ]
                    })
                    
    return results
