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

# Store upload progress
upload_progress = {}

def extract_text_simple(image_path):
    """Simple OCR using Tesseract (available in Docker)"""
    try:
        import pytesseract
        img = Image.open(image_path)
        img = img.convert('L')
        text = pytesseract.image_to_string(img)
        return ' '.join(text.split())
    except:
        return f"Text from {os.path.basename(image_path)}"

def extract_date_of_birth(text):
    """Extract date of birth from text with enhanced patterns"""
    patterns = [
        r'date\s*of\s*birth[:\s]*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{4})',
        r'dob[:\s]*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{4})',
        r'birth[:\s]*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{4})',
        r'born[:\s]*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{4})',
        r'([0-9]{1,2}[-/.][0-9]{1,2}[-/.]19[0-9]{2})',
        r'([0-9]{1,2}[-/.][0-9]{1,2}[-/.]20[0-9]{2})'
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            date_str = re.sub(r'[^0-9/\-.]', '', match)
            if len(date_str.split('/')) == 3 or len(date_str.split('-')) == 3 or len(date_str.split('.')) == 3:
                return date_str
    return None

def extract_occupation_place(text):
    """Extract place of work/occupation from text"""
    patterns = [
        r'working\s+(?:at|in|for)\s+([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'company[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'occupation[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'(?:hyderabad|bangalore|chennai|mumbai|delhi|pune|kolkata)(?:\s|,|\.|$)'
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and len(match.strip()) > 2:
                return match.strip().title()
    return None

def extract_native_address(text):
    """Extract native place/address from text"""
    patterns = [
        r'native[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'native\s*place[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'home\s*town[:\s]*([a-zA-Z0-9\s,.-]+?)(?:[,.]|\n|$)',
        r'address[:\s]*([a-zA-Z0-9\s,.-]+?)(?:\n|contact|phone|mobile)'
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and len(match.strip()) > 2:
                return match.strip().title()
    return None

def extract_salary(text):
    """Extract salary information from text"""
    patterns = [
        r'salary[:\s]*(\d+(?:\.\d+)?)\s*(?:lakhs?|lpa|k|crores?)',
        r'income[:\s]*(\d+(?:\.\d+)?)\s*(?:lakhs?|lpa|k|crores?)',
        r'(\d+(?:\.\d+)?)\s*(?:lakhs?|lpa|k|crores?)\s*(?:per\s*annum|pa|annually)'
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
        
        if query and query not in text:
            continue
        if dob_filter:
            page_dob = extract_date_of_birth(text)
            if not page_dob or dob_filter not in page_dob:
                continue
        if place_filter:
            occ_place = extract_occupation_place(text) or ''
            native_addr = extract_native_address(text) or ''
            if place_filter not in occ_place.lower() and place_filter not in native_addr.lower():
                continue
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
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
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
        
        # Use PyMuPDF for PDF processing
        doc = fitz.open(filepath)
        progress['total_pages'] = len(doc)
        progress['status'] = 'processing'
        
        image_files = []
        for page_num in range(len(doc)):
            if progress['cancelled']:
                break
                
            page = doc[page_num]
            mat = fitz.Matrix(2.0, 2.0)  # Reduced from 3.0 to save memory
            pix = page.get_pixmap(matrix=mat)
            
            temp_filename = f'page-{page_num + 1:03d}.png'
            temp_path = os.path.join('static/pages', temp_filename)
            pix.save(temp_path)
            
            image_files.append(temp_filename)
            progress['processed_pages'] = page_num + 1
            progress['progress'] = int((page_num + 1) / len(doc) * 100)
        
        doc.close()
        
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
            
            image_hash = get_image_hash(old_path)
            text = extract_text_simple(old_path)
            
            # Duplicate detection
            is_duplicate = False
            for existing_id, existing_data in page_data.items():
                existing_path = f'static/pages/page_{existing_id}.png'
                if os.path.exists(existing_path):
                    existing_hash = get_image_hash(existing_path)
                    if existing_hash == image_hash:
                        is_duplicate = True
                        break
            
            if is_duplicate:
                os.remove(old_path)
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
        
        if not progress['cancelled']:
            with open('page_data.json', 'w', encoding='utf-8') as f:
                json.dump(page_data, f, ensure_ascii=False, indent=2)
            
            progress['status'] = 'completed'
            progress['pages_added'] = new_pages
            progress['duplicates_skipped'] = progress.get('duplicates_skipped', 0)
            progress['end_time'] = time.time()
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
        image_path = f'static/pages/page_{page_id}.png'
        if os.path.exists(image_path):
            os.remove(image_path)
        del page_data[page_id]
        with open('page_data.json', 'w', encoding='utf-8') as f:
            json.dump(page_data, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True})
    return jsonify({'error': 'Page not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)