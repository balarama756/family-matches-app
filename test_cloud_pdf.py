from cloudinary_processor import process_pdf_with_cloudinary
import os

def test_pdf_processing():
    """Test PDF processing with Cloudinary"""
    
    # Find a PDF file in uploads folder
    pdf_files = [f for f in os.listdir('uploads') if f.endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF files found in uploads folder")
        print("Upload a PDF first using the web interface")
        return
    
    pdf_path = os.path.join('uploads', pdf_files[0])
    print(f"Testing with: {pdf_files[0]}")
    
    def progress_callback(current, total):
        print(f"Processing page {current}/{total}")
    
    # Test cloud processing
    image_urls = process_pdf_with_cloudinary(pdf_path, progress_callback)
    
    if image_urls:
        print(f"✅ Success! Generated {len(image_urls)} images")
        print("Sample URLs:")
        for i, url in enumerate(image_urls[:3], 1):
            print(f"  Page {i}: {url}")
    else:
        print("❌ Failed to process PDF")

if __name__ == "__main__":
    test_pdf_processing()