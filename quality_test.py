import requests
import base64

def test_google_vision_quality(image_path):
    """Test Google Vision API quality"""
    api_key = "YOUR_API_KEY"
    
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    image_base64 = base64.b64encode(image_data).decode()
    
    payload = {
        "requests": [{
            "image": {"content": image_base64},
            "features": [
                {"type": "TEXT_DETECTION"},
                {"type": "DOCUMENT_TEXT_DETECTION"}  # Even better for documents
            ]
        }]
    }
    
    response = requests.post(
        f"https://vision.googleapis.com/v1/images:annotate?key={api_key}",
        json=payload
    )
    
    result = response.json()
    
    # Get confidence scores
    if 'responses' in result:
        text_annotations = result['responses'][0].get('textAnnotations', [])
        for annotation in text_annotations[:5]:  # First 5 words
            print(f"Text: '{annotation['description']}' - Confidence: {annotation.get('confidence', 'N/A')}")
    
    return result

# Test with your existing image
# test_google_vision_quality('static/pages/page_1.png')