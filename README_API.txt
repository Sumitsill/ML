╔════════════════════════════════════════════════════════════════════════════╗
║                    AI EXERCISE TRAINER - FASTAPI DEPLOYMENT                ║
╚════════════════════════════════════════════════════════════════════════════╝

QUICK START
═══════════════════════════════════════════════════════════════════════════════

1. Install Dependencies:
   pip install -r requirements.txt

2. Start the API Server:
   python app.py

   Server will start at: http://localhost:8000

3. Test the API:
   python test_api.py


API ENDPOINTS
═══════════════════════════════════════════════════════════════════════════════

1. GET /
   Description: Root endpoint with API information
   Example: http://localhost:8000/

2. GET /health
   Description: Check if API is running
   Example: http://localhost:8000/health

3. GET /exercises
   Description: List all available exercises
   Example: http://localhost:8000/exercises

4. POST /analyze
   Description: Analyze exercise video
   Parameters:
     - video (file): Video file to analyze
     - exercise_type (string): pushup, squat, situp, sitnreach, skipping, 
                               jumpingjacks, vjump, bjump
     - save_output (boolean): true/false (optional, default: false)
   
   Example using curl:
   curl -X POST "http://localhost:8000/analyze" \
        -F "video=@push-up.mp4" \
        -F "exercise_type=pushup" \
        -F "save_output=true"

5. GET /download/{filename}
   Description: Download processed video
   Example: http://localhost:8000/download/pushup_processed.avi


USING THE API
═══════════════════════════════════════════════════════════════════════════════

Option 1: Using Python requests
─────────────────────────────────────────────────────────────────────────────
import requests

url = "http://localhost:8000/analyze"
files = {'video': open('push-up.mp4', 'rb')}
data = {'exercise_type': 'pushup', 'save_output': 'true'}

response = requests.post(url, files=files, data=data)
result = response.json()

# View logs (terminal output simulation)
for log in result['metrics']['logs']:
    print(log)


Option 2: Using cURL
─────────────────────────────────────────────────────────────────────────────
curl -X POST "http://localhost:8000/analyze" \
     -F "video=@push-up.mp4" \
     -F "exercise_type=pushup" \
     -F "save_output=true"


Option 3: Using Postman
─────────────────────────────────────────────────────────────────────────────
1. Create new POST request to: http://localhost:8000/analyze
2. Go to Body tab
3. Select "form-data"
4. Add fields:
   - video: [File] - Select your video file
   - exercise_type: [Text] - Enter exercise type
   - save_output: [Text] - Enter true or false


RESPONSE FORMAT
═══════════════════════════════════════════════════════════════════════════════

{
  "success": true,
  "exercise": "pushup",
  "metrics": {
    "exercise": "pushup",
    "overall_score": 85,
    "rating": "⭐⭐⭐⭐ VERY GOOD",
    "repetitions": {
      "total": 10,
      "good": 8,
      "bad": 2
    },
    "scores": {
      "form": 80,
      "rom": 90,
      "alignment": 85,
      "symmetry": 88,
      "tempo": 82
    },
    "feedback": [
      "✓ FORM: Excellent form maintained!",
      "✓ ROM: Great depth!",
      "✓ ALIGNMENT: Excellent spine stability!",
      "✓ SYMMETRY: Good left/right balance"
    ],
    "logs": [
      "Starting PUSHUP analysis...",
      "Pushup Count: 1",
      "Pushup Count: 2",
      ...
    ],
    "timestamp": "2025-11-30 14:30:45"
  },
  "output_video_available": true,
  "output_video_path": "pushup_processed.avi"
}


TERMINAL OUTPUT SIMULATION
═══════════════════════════════════════════════════════════════════════════════

The API response includes a 'logs' array that captures all print statements
from the original test.py, exactly replicating the terminal behavior:

- Rep counts
- Form feedback
- Analysis progress
- Final metrics report

Access logs via: response['metrics']['logs']


SUPPORTED EXERCISES
═══════════════════════════════════════════════════════════════════════════════

1. pushup       - Push-ups
2. squat        - Squats
3. situp        - Sit-ups
4. sitnreach    - Sit-and-Reach (Flexibility)
5. skipping     - Skipping (Jump Rope)
6. jumpingjacks - Jumping Jacks
7. vjump        - Vertical Jump
8. bjump        - Broad Jump (Horizontal)


FILES REQUIRED FOR DEPLOYMENT
═══════════════════════════════════════════════════════════════════════════════

✓ app.py              - FastAPI application
✓ utils.py            - Pose calibration utilities
✓ metrics.py          - Performance metrics calculation
✓ yolov8n-pose.pt     - YOLOv8 pose detection model
✓ requirements.txt    - Python dependencies


DEPLOYMENT OPTIONS
═══════════════════════════════════════════════════════════════════════════════

Local Development:
  python app.py

Production (using Gunicorn):
  pip install gunicorn
  gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

Docker:
  Create Dockerfile and deploy to container

Cloud Platforms:
  - AWS (EC2, Lambda, ECS)
  - Google Cloud (Cloud Run, App Engine)
  - Azure (App Service, Container Instances)
  - Heroku
  - Railway
  - Render


TESTING
═══════════════════════════════════════════════════════════════════════════════

Run the test script:
  python test_api.py

This will:
1. Check API health
2. List available exercises
3. Analyze a sample video
4. Display logs and metrics


TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════

Issue: "Could not connect to API"
Solution: Make sure the server is running with: python app.py

Issue: "Video file not found"
Solution: Use absolute path to video file or place video in same directory

Issue: "Model not found"
Solution: Ensure yolov8n-pose.pt is in the same directory as app.py

Issue: "Memory error during processing"
Solution: Process shorter videos or increase available RAM


INTERACTIVE API DOCUMENTATION
═══════════════════════════════════════════════════════════════════════════════

FastAPI provides automatic interactive documentation:

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

You can test all endpoints directly from the browser!


NOTES
═══════════════════════════════════════════════════════════════════════════════

- The API maintains the exact same logic as test.py
- All print statements are captured in the 'logs' array
- Metrics calculation is identical to local execution
- Video processing happens synchronously (may take time for long videos)
- Processed videos are temporarily stored and can be downloaded

═══════════════════════════════════════════════════════════════════════════════
