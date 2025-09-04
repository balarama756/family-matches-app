import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# Configure Cloudinary
cloudinary.config(
    cloud_name="your_cloud_name",
    api_key="your_api_key", 
    api_secret="your_api_secret"
)

def upload_and_process_pdf(pdf_file):
    """Upload PDF to Cloudinary and convert to images"""
    
    # Upload PDF
    upload_result = cloudinary.uploader.upload(
        pdf_file,
        resource_type="raw",
        format="pdf"
    )
    
    # Convert to images (Cloudinary does this automatically)
    image_urls = []
    pdf_url = upload_result['secure_url']
    
    # Generate image URLs for each page
    for page in range(1, 11):  # Assuming max 10 pages
        image_url, _ = cloudinary_url(
            upload_result['public_id'],
            format="png",
            page=page,
            resource_type="image"
        )
        image_urls.append(image_url)
    
    return image_urls