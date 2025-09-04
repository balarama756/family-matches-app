import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary_config import CLOUDINARY_CONFIG
import requests
import tempfile
import os

# Configure Cloudinary
cloudinary.config(**CLOUDINARY_CONFIG)

def process_pdf_with_cloudinary(pdf_file_path, progress_callback=None):
    """Process PDF using Cloudinary - converts to images automatically"""
    try:
        # Check file size (Cloudinary free tier: 10MB limit)
        file_size = os.path.getsize(pdf_file_path)
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise Exception(f"PDF too large ({file_size/1024/1024:.1f}MB). Use local processing.")
        
        # Upload PDF to Cloudinary
        upload_result = cloudinary.uploader.upload(
            pdf_file_path,
            resource_type="raw",
            format="pdf"
        )
        
        # Get all page URLs
        public_id = upload_result['public_id']
        pages = upload_result.get('pages', 1)
        
        image_urls = []
        for page in range(1, pages + 1):
            # Generate URL for each page
            page_url = cloudinary.CloudinaryImage(public_id).build_url(
                page=page,
                format="png",
                quality="auto:best",
                fetch_format="auto"
            )
            image_urls.append(page_url)
            
            if progress_callback:
                progress_callback(page, pages)
        
        return image_urls
        
    except Exception as e:
        print(f"Cloudinary processing error: {e}")
        return []

def download_image_from_url(url, local_path):
    """Download image from Cloudinary URL to local storage"""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Download error: {e}")
    return False