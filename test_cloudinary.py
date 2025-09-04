import cloudinary
import cloudinary.uploader
from cloudinary_config import CLOUDINARY_CONFIG

# Configure Cloudinary
cloudinary.config(**CLOUDINARY_CONFIG)

def test_upload():
    """Test if Cloudinary is working"""
    try:
        # Test upload (use any small image file)
        result = cloudinary.uploader.upload("static/pages/page_1.png")
        print("✅ Cloudinary working!")
        print(f"Image URL: {result['secure_url']}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_upload()