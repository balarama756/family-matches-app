# API Configuration
GOOGLE_VISION_API_KEY = "YOUR_GOOGLE_VISION_API_KEY_HERE"
CLOUDCONVERT_API_KEY = "YOUR_CLOUDCONVERT_API_KEY_HERE"

# For production, use environment variables:
import os
GOOGLE_VISION_API_KEY = os.getenv('GOOGLE_VISION_API_KEY', 'your-key-here')
CLOUDCONVERT_API_KEY = os.getenv('CLOUDCONVERT_API_KEY', 'your-key-here')