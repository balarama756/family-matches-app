from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import re
import os
import subprocess
from datetime import datetime
from werkzeug.utils import secure_filename
import hashlib
from PIL import Image
import time
from threading import Thread
import uuid
import fitz  # PyMuPDF - works on any hosting
import easyocr  # Free OCR - works on any hosting
import io

def get_image_hash(image_path):
    """Generate hash of image for duplicate detection"""
    with open(image_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Create directories
os.makedirs('uploads', exist_ok=True)
os.makedirs('static/pages', exist_ok=True)

# Load page data
try:
    with open('page_data.json', 'r', encoding='utf-8') as f:
        page_data = json.load(f)
except FileNotFoundError:
    page_data = {}

# Poppler path
POPPLER_PATH = r'C:\poppler-25.07.0\Library\bin'

# Store upload progress
upload_progress = {}

# Initialize EasyOCR once globally (faster)
reader = None

def get_ocr_reader():
    global reader
    if reader is None:
        reader = easyocr.Reader(['en'], gpu=False)  # CPU only for compatibility
    return reader

def extract_text_hybrid(image_path):
    """Use Tesseract locally, EasyOCR for deployment"""
    try:
        # Try Tesseract first (faster locally)
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        img = Image.open(image_path)
        img = img.convert('L')
        config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/-: '
        text = pytesseract.image_to_string(img, config=config)
        return ' '.join(text.split())
    except:
        # Fallback to EasyOCR (for deployment)
        reader = get_ocr_reader()
        ocr_results = reader.readtext(image_path, 
                                    width_ths=0.7,
                                    height_ths=0.7,
                                    paragraph=False)
        text = ' '.join([result[1] for result in ocr_results if result[2] > 0.5])
        return ' '.join(text.split())

def extract_date_of_birth(text):
    """Extract date of birth from text with enhanced patterns"""
    patterns = [
        r'date\s*of\s*birth[:\s]*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{4})',
        r'dob[:\s]*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{4})',
        r'birth[:\s]*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{4})',
        r'born[:\s]*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{4})',
        r'([0-9]{1,2}[-/.][0-9]{1,2}[-/.]19[0-9]{2})',
        r'([0-9]{1,2}[-/.][0-9]{1,2}[-/.]20[0-9]{2})',
        r'([0-9]{1,2}\s*[-/.]\s*[0-9]{1,2}\s*[-/.]\s*[0-9]{4})',
        r'([0-9]{1,2}[th|st|nd|rd]*\s*[a-zA-Z]+\s*[0-9]{4})'
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Normalize date format
            date_str = re.sub(r'[^0-9/\-.]', '', match)
            if len(date_str.split('/')) == 3 or len(date_str.split('-')) == 3 or len(date_str.split('.')) == 3:
                return date_str
    return None

def extract_occupation_place(text):
    """Extract place of work/occupation from text with enhanced patterns"""
    patterns = [
        r'working\s+(?:at|in|for)\s+([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'company[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'organization[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'employer[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'occupation[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'job[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'profession[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'place\s*of\s*work[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'current\s*location[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'(?:hyderabad|bangalore|chennai|mumbai|delhi|pune|kolkata|ahmedabad|surat|jaipur|lucknow|kanpur|nagpur|visakhapatnam|indore|thane|bhopal|patna|vadodara|ghaziabad|ludhiana|agra|nashik|faridabad|meerut|rajkot|kalyan|vasai|varanasi|srinagar|aurangabad|dhanbad|amritsar|navi mumbai|allahabad|ranchi|howrah|coimbatore|jabalpur|gwalior|vijayawada|jodhpur|madurai|raipur|kota|guwahati|chandigarh|solapur|hubli|tiruchirappalli|bareilly|mysore|tiruppur|gurgaon|aligarh|jalandhar|bhubaneswar|salem|warangal|guntur|bhiwandi|saharanpur|gorakhpur|bikaner|amravati|noida|jamshedpur|bhilai|cuttack|firozabad|kochi|nellore|bhavnagar|dehradun|durgapur|asansol|rourkela|nanded|kolhapur|ajmer|akola|gulbarga|jamnagar|ujjain|loni|siliguri|jhansi|ulhasnagar|jammu|sangli|miraj|kupwad|belgaum|mangalore|ambattur|tirunelveli|malegaon|gaya|jalgaon|udaipur|maheshtala)(?:\s|,|\.|$)'
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and len(match.strip()) > 2:
                return match.strip().title()
    return None

def extract_native_address(text):
    """Extract native place/address from text with enhanced patterns"""
    patterns = [
        r'native[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'native\s*place[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'home\s*town[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'birth\s*place[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'place\s*of\s*birth[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'residential\s*address[:\s]*([a-zA-Z0-9\s,.-]+?)(?:\n|contact|phone|mobile)',
        r'permanent\s*address[:\s]*([a-zA-Z0-9\s,.-]+?)(?:\n|contact|phone|mobile)',
        r'address[:\s]*([a-zA-Z0-9\s,.-]+?)(?:\n|contact|phone|mobile)',
        r'settled\s*(?:in|at)[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)'
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and len(match.strip()) > 2:
                return match.strip().title()
    return None

def extract_salary(text):
    """Extract salary information from text with enhanced patterns"""
    patterns = [
        r'salary[:\s]*(\d+(?:\.\d+)?)\s*(?:lakhs?|lpa|k|crores?|thousands?)',
        r'income[:\s]*(\d+(?:\.\d+)?)\s*(?:lakhs?|lpa|k|crores?|thousands?)',
        r'package[:\s]*(\d+(?:\.\d+)?)\s*(?:lakhs?|lpa|k|crores?|thousands?)',
        r'annual\s*(?:income|salary|package)[:\s]*(\d+(?:\.\d+)?)\s*(?:lakhs?|lpa|k|crores?|thousands?)',
        r'ctc[:\s]*(\d+(?:\.\d+)?)\s*(?:lakhs?|lpa|k|crores?|thousands?)',
        r'(\d+(?:\.\d+)?)\s*(?:lakhs?|lpa|k|crores?)\s*(?:per\s*annum|pa|annually)',
        r'earning[:\s]*(\d+(?:\.\d+)?)\s*(?:lakhs?|lpa|k|crores?|thousands?)',
        r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:k|thousand|per\s*year|annually)?',
        r'(\d+(?:\.\d+)?)\s*(?:thousand|k)\s*(?:usd|dollars?|per\s*month)'
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and match.strip():
                return match.strip()
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    dob_filter = request.args.get('dob', '')
    place_filter = request.args.get('place', '').lower()
    salary_filter = request.args.get('salary', '')
    
    results = []
    
    for page_id, data in page_data.items():
        text = data['text'].lower()
        
        # Text search
        if query and query not in text:
            continue
            
        # DOB filter
        if dob_filter:
            page_dob = extract_date_of_birth(text)
            if not page_dob or dob_filter not in page_dob:
                continue
                
        # Place filter (search in both occupation place and native address)
        if place_filter:
            occ_place = extract_occupation_place(text) or ''
            native_addr = extract_native_address(text) or ''
            if place_filter not in occ_place.lower() and place_filter not in native_addr.lower():
                continue
                
        # Salary filter
        if salary_filter:
            page_salary = extract_salary(text)
            if not page_salary or salary_filter not in page_salary:
                continue
        
        results.append({
            'page_id': page_id,
            'image_path': f'static/pages/page_{page_id}.png',
            'dob': extract_date_of_birth(text),
            'occupation_place': extract_occupation_place(text),
            'native_address': extract_native_address(text)
        })
    
    return jsonify(results)

@app.route('/page/<page_id>')
def view_page(page_id):
    if page_id in page_data:
        data = page_data[page_id]
        return render_template('page_detail.html', 
                             page_id=page_id, 
                             data=data,
                             image_path=f'static/pages/page_{page_id}.png')
    return "Page not found", 404

@app.route('/upload', methods=['POST'])
def upload_pdf():
    try:
        if 'pdf' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
    except:
        return jsonify({'error': 'File too large. Maximum size is 100MB'}), 413
    
    file = request.files['pdf']
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Please select a PDF file'}), 400
    
    # Save file first
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Generate unique upload ID
    upload_id = str(uuid.uuid4())
    upload_progress[upload_id] = {
        'status': 'starting',
        'progress': 0,
        'total_pages': 0,
        'processed_pages': 0,
        'start_time': time.time(),
        'cancelled': False,
        'filepath': filepath,
        'filename': filename
    }
    
    # Start processing in background
    thread = Thread(target=process_pdf_background, args=(upload_id,))
    thread.start()
    
    return jsonify({'upload_id': upload_id})

def process_pdf_background(upload_id):
    global page_data, upload_progress
    
    try:
        progress = upload_progress[upload_id]
        progress['status'] = 'converting'
        
        filepath = progress['filepath']
        filename = progress['filename']
        
        # Use PyMuPDF - works on any hosting (no system dependencies)
        doc = fitz.open(filepath)
        progress['total_pages'] = len(doc)
        progress['status'] = 'processing'
        
        # Use global OCR reader (faster)
        reader = get_ocr_reader()
        
        image_files = []
        for page_num in range(len(doc)):
            if progress['cancelled']:
                break
                
            page = doc[page_num]
            
            # Convert page to high-quality image (300 DPI)
            mat = fitz.Matrix(3.0, 3.0)  # 3x zoom = 300 DPI
            pix = page.get_pixmap(matrix=mat)
            
            # Save as PNG
            temp_filename = f'page-{page_num + 1:03d}.png'
            temp_path = os.path.join('static/pages', temp_filename)
            pix.save(temp_path)
            
            image_files.append(temp_filename)
            
            progress['processed_pages'] = page_num + 1
            progress['progress'] = int((page_num + 1) / len(doc) * 100)
        
        doc.close()
        progress['total_pages'] = len(image_files)
        progress['status'] = 'processing'
        
        new_pages = 0
        for i, img_file in enumerate(image_files):
            if progress['cancelled']:
                break
                
            page_num = img_file.split('-')[1].split('.')[0]
            new_page_id = str(len(page_data) + new_pages + 1)
            
            while os.path.exists(f'static/pages/page_{new_page_id}.png'):
                new_page_id = str(int(new_page_id) + 1)
            
            old_path = os.path.join('static/pages', img_file)
            new_path = f'static/pages/page_{new_page_id}.png'
            
            # Process image
            image_hash = get_image_hash(old_path)
            
            try:
                # Use hybrid OCR (Tesseract locally, EasyOCR for deployment)
                text = extract_text_hybrid(old_path)
            except:
                text = f"Page from {filename} - {page_num}"
            
            # Strong duplicate detection
            is_duplicate = False
            duplicate_reason = ""
            duplicate_page_id = ""
            
            for existing_id, existing_data in page_data.items():
                existing_path = f'static/pages/page_{existing_id}.png'
                if os.path.exists(existing_path):
                    existing_hash = get_image_hash(existing_path)
                    text_similarity = len(set(text.lower().split()) & set(existing_data['text'].lower().split())) / max(len(text.split()), len(existing_data['text'].split()), 1)
                    
                    if existing_hash == image_hash:
                        is_duplicate = True
                        duplicate_reason = "IDENTICAL IMAGE"
                        duplicate_page_id = existing_id
                        break
                    elif text_similarity > 0.9:
                        is_duplicate = True
                        duplicate_reason = f"SAME TEXT ({int(text_similarity*100)}% match)"
                        duplicate_page_id = existing_id
                        break
            
            if is_duplicate:
                os.remove(old_path)
                print(f"🚫 DUPLICATE FOUND: Page {page_num} from {filename}")
                print(f"   Reason: {duplicate_reason}")
                print(f"   Already exists as: page_{duplicate_page_id}.png")
                print(f"   ✅ Skipped and removed duplicate image")
                progress['duplicates_skipped'] = progress.get('duplicates_skipped', 0) + 1
            else:
                os.rename(old_path, new_path)
                page_data[new_page_id] = {
                    'text': text,
                    'original_text': text,
                    'source_pdf': filename,
                    'local_page': int(page_num),
                    'image_hash': image_hash
                }
                new_pages += 1
            
            progress['processed_pages'] = i + 1
            progress['progress'] = int((i + 1) / len(image_files) * 100)
            
            # Add preview data for current page
            if not is_duplicate:
                dob = extract_date_of_birth(text)
                occ_place = extract_occupation_place(text)
                native_addr = extract_native_address(text)
                progress['current_preview'] = {
                    'page_id': new_page_id,
                    'dob': dob,
                    'occupation_place': occ_place,
                    'native_address': native_addr
                }
        
        if not progress['cancelled']:
            # Save data
            with open('page_data.json', 'w', encoding='utf-8') as f:
                json.dump(page_data, f, ensure_ascii=False, indent=2)
            page_data = json.load(open('page_data.json', 'r', encoding='utf-8'))
            
            progress['status'] = 'completed'
            progress['pages_added'] = new_pages
            progress['duplicates_skipped'] = progress.get('duplicates_skipped', 0)
            progress['end_time'] = time.time()
            print(f"\n✅ UPLOAD COMPLETED: {new_pages} new pages added, {progress['duplicates_skipped']} duplicates skipped")
        else:
            progress['status'] = 'cancelled'
        
        os.remove(filepath)
        
    except Exception as e:
        progress['status'] = 'error'
        progress['error'] = str(e)

@app.route('/upload/progress/<upload_id>')
def get_upload_progress(upload_id):
    if upload_id in upload_progress:
        progress = upload_progress[upload_id].copy()
        if 'start_time' in progress:
            elapsed = time.time() - progress['start_time']
            progress['elapsed_time'] = round(elapsed, 1)
            
            if progress['processed_pages'] > 0 and progress['total_pages'] > 0:
                avg_time_per_page = elapsed / progress['processed_pages']
                remaining_pages = progress['total_pages'] - progress['processed_pages']
                estimated_remaining = avg_time_per_page * remaining_pages
                progress['estimated_remaining'] = round(estimated_remaining, 1)
        
        # Remove filepath from response
        if 'filepath' in progress:
            del progress['filepath']
        
        return jsonify(progress)
    return jsonify({'error': 'Upload not found'}), 404

@app.route('/upload/cancel/<upload_id>', methods=['POST'])
def cancel_upload(upload_id):
    if upload_id in upload_progress:
        upload_progress[upload_id]['cancelled'] = True
        return jsonify({'success': True})
    return jsonify({'error': 'Upload not found'}), 404

@app.route('/delete/<page_id>', methods=['DELETE'])
def delete_page(page_id):
    global page_data
    if page_id in page_data:
        # Remove image file
        image_path = f'static/pages/page_{page_id}.png'
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # Remove from data
        del page_data[page_id]
        
        # Save updated data
        with open('page_data.json', 'w', encoding='utf-8') as f:
            json.dump(page_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True})
    return jsonify({'error': 'Page not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)