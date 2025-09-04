import requests
import base64
from PIL import Image
import io

def convert_pdf_to_images_cloud(pdf_file):
    """Convert PDF to images using CloudConvert API (free tier)"""
    # CloudConvert free: 25 conversions/day
    api_key = "YOUR_CLOUDCONVERT_API_KEY"
    
    # Upload PDF
    files = {'file': pdf_file}
    response = requests.post(
        f"https://api.cloudconvert.com/v2/convert/pdf/png",
        headers={'Authorization': f'Bearer {api_key}'},
        files=files
    )
    return response.json()

def extract_text_from_image_cloud(image_data):
    """Extract text using Google Vision API (free tier: 1000 requests/month)"""
    api_key = "YOUR_GOOGLE_VISION_API_KEY"
    
    # Convert image to base64
    image_base64 = base64.b64encode(image_data).decode()
    
    payload = {
        "requests": [{
            "image": {"content": image_base64},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }
    
    response = requests.post(
        f"https://vision.googleapis.com/v1/images:annotate?key={api_key}",
        json=payload
    )
    
    result = response.json()
    if 'responses' in result and result['responses']:
        return result['responses'][0].get('fullTextAnnotation', {}).get('text', '')
    return ""