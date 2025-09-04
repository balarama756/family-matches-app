import requests
import base64
import json
from config import GOOGLE_VISION_API_KEY, CLOUDCONVERT_API_KEY

def convert_pdf_to_images(pdf_file_path):
    """Convert PDF to images using CloudConvert API"""
    url = "https://api.cloudconvert.com/v2/convert/pdf/png"
    
    headers = {
        'Authorization': f'Bearer {CLOUDCONVERT_API_KEY}'
    }
    
    with open(pdf_file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, headers=headers, files=files)
    
    if response.status_code == 200:
        result = response.json()
        # Download converted images
        download_urls = result.get('data', {}).get('url', [])
        return download_urls
    else:
        raise Exception(f"PDF conversion failed: {response.text}")

def extract_text_from_image(image_path):
    """Extract text using Google Vision API"""
    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_VISION_API_KEY}"
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    image_base64 = base64.b64encode(image_data).decode()
    
    payload = {
        "requests": [{
            "image": {"content": image_base64},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if 'responses' in result and result['responses']:
            text_annotation = result['responses'][0].get('fullTextAnnotation')
            if text_annotation:
                return text_annotation.get('text', '')
    
    return ""