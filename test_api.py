"""
Test script for FastAPI Exercise Trainer
"""
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing Health Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_exercises():
    """Test exercises list endpoint"""
    print("\n" + "="*60)
    print("Testing Exercises List Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/exercises")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_analyze(video_path, exercise_type, save_output=False):
    """Test analyze endpoint"""
    print("\n" + "="*60)
    print(f"Testing Analyze Endpoint - {exercise_type.upper()}")
    print("="*60)
    
    with open(video_path, 'rb') as video_file:
        files = {'video': video_file}
        data = {
            'exercise_type': exercise_type,
            'save_output': str(save_output).lower()
        }
        
        print(f"Uploading video: {video_path}")
        print(f"Exercise type: {exercise_type}")
        print(f"Save output: {save_output}")
        print("\nProcessing... (this may take a moment)")
        
        response = requests.post(f"{BASE_URL}/analyze", files=files, data=data)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Print logs (simulating terminal output)
            if 'metrics' in result and 'logs' in result['metrics']:
                print("\n" + "="*60)
                print("EXERCISE ANALYSIS LOGS (Terminal Output)")
                print("="*60)
                for log in result['metrics']['logs']:
                    print(log)
            
            # Print summary
            print("\n" + "="*60)
            print("API RESPONSE SUMMARY")
            print("="*60)
            print(f"Success: {result.get('success')}")
            print(f"Exercise: {result.get('exercise')}")
            print(f"Output video available: {result.get('output_video_available')}")
            
            if 'metrics' in result:
                metrics = result['metrics']
                # Remove logs from display to keep it clean
                if 'logs' in metrics:
                    del metrics['logs']
                print(f"\nMetrics Summary:")
                print(json.dumps(metrics, indent=2))
        else:
            print(f"Error: {response.text}")


def main():
    print("="*60)
    print("AI EXERCISE TRAINER API - TEST SUITE")
    print("="*60)
    
    # Test 1: Health check
    test_health()
    
    # Test 2: List exercises
    test_exercises()
    
    # Test 3: Analyze video
    # Replace with your video path
    video_path = "push-up.mp4"  # Change this to test different videos
    exercise_type = "pushup"     # Change this to test different exercises
    
    print(f"\n\nNote: Make sure '{video_path}' exists in the current directory")
    print("Available exercises: pushup, squat, situp, sitnreach, skipping, jumpingjacks, vjump, bjump")
    
    try:
        test_analyze(video_path, exercise_type, save_output=True)
    except FileNotFoundError:
        print(f"\n❌ Error: Video file '{video_path}' not found!")
        print("Please update the video_path variable in this script.")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API!")
        print("Make sure the FastAPI server is running:")
        print("  python app.py")


if __name__ == "__main__":
    main()
