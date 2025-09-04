import os

# Use actual credentials with environment variable fallback
CLOUDINARY_CONFIG = {
    'cloud_name': os.getenv('CLOUDINARY_CLOUD_NAME', 'dfqdojq1t'),
    'api_key': os.getenv('CLOUDINARY_API_KEY', '595981693986421'),
    'api_secret': os.getenv('CLOUDINARY_API_SECRET', 'QqEQHMf5fVDsICijL_xUHXtG5U4')
}