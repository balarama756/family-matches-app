from app import app

if __name__ == '__main__':
    print("Starting Family Matches Web Application...")
    print("Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    try:
        app.run(debug=True, host='127.0.0.1', port=5000)
    except Exception as e:
        print(f"Error starting server: {e}")
        input("Press Enter to exit...")