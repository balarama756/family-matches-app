# Family Matches Project

A web application for viewing and searching through extracted PDF images with OCR text processing and filtering capabilities.

## Features

- **Image Display**: View all extracted PDF pages as images in a responsive grid layout
- **Text Search**: Search through OCR-extracted text content
- **Smart Filtering**: 
  - Filter by Date of Birth (DOB)
  - Filter by Place/Location
  - Filter by Salary information
- **Detailed View**: Click on any result to see the full page image and complete text
- **Git Optimization**: Large image files are excluded from Git tracking for better performance

## Project Structure

```
family_matches_project2/
├── static/
│   └── pages/           # 1745+ extracted PNG images (excluded from Git)
├── templates/
│   ├── index.html       # Main search interface
│   └── page_detail.html # Individual page view
├── app.py              # Flask web application
├── run.py              # Application runner
├── page_data.json      # OCR text data from PDFs
├── requirements.txt    # Python dependencies
├── .gitignore         # Git exclusions for performance
└── README.md          # This file
```

## Installation & Setup

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python run.py
   ```

3. **Open in Browser**:
   Navigate to `http://localhost:5000`

## Usage

### Search and Filter
- **Text Search**: Enter any text to search through OCR content
- **Date Filter**: Enter date in DD/MM/YYYY or DD-MM-YYYY format
- **Place Filter**: Enter city, state, or location name
- **Salary Filter**: Enter salary amount or range

### View Details
- Click on any search result card to view the full page image and complete text
- Use the back button to return to search results

## Git Performance Optimization

The `.gitignore` file excludes the `static/pages/` directory containing 1745+ PNG images to improve Git performance:

- **Before**: Git operations were slow due to large binary files
- **After**: Only code and JSON data are tracked, making Git fast and efficient
- **Images**: Store images locally or use a separate storage solution for production

## Technical Details

### OCR Text Processing
- Extracts dates using multiple regex patterns
- Identifies location information from various text formats
- Parses salary information in different formats (lakhs, LPA, etc.)

### Web Framework
- **Flask**: Lightweight Python web framework
- **Responsive Design**: Works on desktop and mobile devices
- **AJAX Search**: Real-time search without page reloads

### Data Format
The `page_data.json` contains:
```json
{
  "page_id": {
    "text": "processed_ocr_text",
    "original_text": "raw_ocr_text", 
    "source_pdf": "source_file.pdf",
    "local_page": page_number
  }
}
```

## Development

To add new features or modify the application:

1. **Backend**: Edit `app.py` for new routes or search logic
2. **Frontend**: Modify templates in `templates/` directory
3. **Styling**: Update CSS in the HTML templates
4. **Data Processing**: Enhance regex patterns for better text extraction

## Troubleshooting

### Images Not Loading
- Ensure PNG files exist in `static/pages/` directory
- Check file naming convention: `page_X.png` where X is the page ID

### Search Not Working
- Verify `page_data.json` is properly formatted
- Check Flask server logs for errors

### Performance Issues
- Consider implementing pagination for large result sets
- Use database storage for production deployments
- Implement caching for frequently accessed data

## Production Deployment

For production use:
1. Use a production WSGI server (gunicorn, uWSGI)
2. Store images in cloud storage (AWS S3, Google Cloud Storage)
3. Use a proper database (PostgreSQL, MongoDB)
4. Implement user authentication if needed
5. Add error logging and monitoring