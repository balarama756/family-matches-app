import fitz  # PyMuPDF - completely free
from PIL import Image
import easyocr  # Free OCR alternative to Tesseract
import io

def extract_pdf_free(pdf_path):
    """Extract images and text using completely free libraries"""
    
    # Open PDF with PyMuPDF (free)
    doc = fitz.open(pdf_path)
    
    # Initialize EasyOCR (free, no API keys)
    reader = easyocr.Reader(['en'])
    
    results = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Convert page to high-quality image
        mat = fitz.Matrix(3.0, 3.0)  # 3x zoom = 300 DPI
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        
        # Save image
        image_path = f'static/pages/page_{page_num + 1}.png'
        image.save(image_path)
        
        # Extract text with EasyOCR (better than Tesseract)
        ocr_results = reader.readtext(img_data)
        text = ' '.join([result[1] for result in ocr_results])
        
        results.append({
            'page': page_num + 1,
            'image_path': image_path,
            'text': text
        })
        
        print(f"Processed page {page_num + 1}/{len(doc)}")
    
    doc.close()
    return results

# Install required packages:
# pip install PyMuPDF easyocr