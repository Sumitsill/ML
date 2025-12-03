from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import cv2
import numpy as np
import tempfile
import os
import shutil
from pathlib import Path
import json
import asyncio
from io import StringIO
import sys

from utils import PoseCalibrator
from metrics import PerformanceMetrics

# Global instance
evaluator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global evaluator
    evaluator = ExerciseEvaluator()
    print("✓ AI Exercise Trainer API Started")
    print("✓ Model loaded: yolov8n-pose.pt")
    yield
    # Shutdown
    print("✓ API Shutting down")

app = FastAPI(title="AI Exercise Trainer API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExerciseEvaluator:
    def __init__(self):
        self.calibrator = PoseCalibrator(model_path='yolov8n-pose.pt')
        self.metrics = PerformanceMetrics()
        
        # Exercise State Variables
        self.current_exercise = None
        self.counter = 0
        self.stage = None
        self.feedback = "Setup"
        self.start_time = None
        
        # Thresholds (Degrees)
        self.thresholds = {
            'pushup': {'down': 90, 'up': 160, 'form_hip_min': 150},
            'squat': {'down': 100, 'up': 160, 'deep': 80},
            'situp': {'up': 70, 'down': 20, 'good_crunch': 50},
            'sitnreach': {'excellent_hip': 60, 'average_hip': 80, 'knee_valid': 165},
            'skipping': {'jump_threshold': 30, 'min_height': 20},
            'jumpingjacks': {'arm_open': 150, 'leg_open': 150},
            'vjump': {'min_height': 30, 'good_countermovement': 110},
            'bjump': {'min_distance': 50, 'good_countermovement': 110}
        }
        
        # Output buffer for logs
        self.logs = []

    def log(self, message):
        """Capture log messages"""
        self.logs.append(message)
        print(message)  # Also print to console

    def _draw_dashboard(self, frame, exercise_name):
        """Draws the exercise statistics overlay."""
        if exercise_name == 'sitnreach':
            cv2.rectangle(frame, (0, 0), (240, 90), (16, 117, 245), -1)
            cv2.putText(frame, 'MAX REACH (px)', (10, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
            max_distance = int(self.metrics.max_reach_distance) if self.metrics.max_reach_distance > 0 else 0
            cv2.putText(frame, str(max_distance), (20, 75), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3, cv2.LINE_AA)
            
            cv2.rectangle(frame, (250, 0), (490, 90), (245, 117, 16), -1)
            cv2.putText(frame, 'CURRENT (px)', (260, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
            current_distance = int(self.metrics.reach_distances[-1]) if self.metrics.reach_distances else 0
            cv2.putText(frame, str(current_distance), (270, 75), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3, cv2.LINE_AA)
            
            color = (0, 255, 0) if self.stage == "VALID" else (0, 165, 255)
            cv2.rectangle(frame, (0, 95), (490, 130), (255, 255, 255), -1)
            cv2.putText(frame, self.feedback, (10, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)
        elif exercise_name == 'skipping':
            cv2.rectangle(frame, (0, 0), (180, 90), (117, 245, 16), -1)
            cv2.putText(frame, 'JUMPS', (15, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, str(self.metrics.jump_count), (20, 75), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3, cv2.LINE_AA)
            
            cv2.rectangle(frame, (190, 0), (380, 90), (245, 200, 16), -1)
            cv2.putText(frame, 'SKIPS/SEC', (200, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            frequency = self.metrics._get_skipping_frequency() if hasattr(self.metrics, '_get_skipping_frequency') else 0
            cv2.putText(frame, f"{frequency:.1f}", (210, 75), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3, cv2.LINE_AA)
            
            color = (0, 255, 0) if self.stage == "AIR" else (200, 200, 200)
            cv2.rectangle(frame, (0, 95), (380, 130), (255, 255, 255), -1)
            cv2.putText(frame, self.feedback, (10, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)
        elif exercise_name == 'jumpingjacks':
            cv2.rectangle(frame, (0, 0), (180, 90), (200, 117, 245), -1)
            cv2.putText(frame, 'REPS', (15, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, str(self.metrics.jj_rep_count), (20, 75), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3, cv2.LINE_AA)
            
            cv2.rectangle(frame, (190, 0), (380, 90), (117, 200, 245), -1)
            cv2.putText(frame, 'STATE', (200, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            state_text = self.metrics.jj_state.upper()
            cv2.putText(frame, state_text, (200, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
            
            color = (0, 255, 0) if self.metrics.jj_state == 'open' else (200, 200, 200)
            cv2.rectangle(frame, (0, 95), (380, 130), (255, 255, 255), -1)
            cv2.putText(frame, self.feedback, (10, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)
        elif exercise_name == 'vjump':
            cv2.rectangle(frame, (0, 0), (180, 90), (16, 245, 117), -1)
            cv2.putText(frame, 'JUMPS', (15, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, str(self.metrics.vjump_jump_count), (20, 75), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3, cv2.LINE_AA)
            
            cv2.rectangle(frame, (190, 0), (400, 90), (245, 117, 245), -1)
            cv2.putText(frame, 'MAX (px)', (200, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            max_height = int(max(self.metrics.vjump_jump_heights)) if self.metrics.vjump_jump_heights else 0
            cv2.putText(frame, str(max_height), (210, 75), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3, cv2.LINE_AA)
            
            state_colors = {'standing': (200, 200, 200), 'airborne': (0, 255, 0), 'landing': (255, 165, 0)}
            color = state_colors.get(self.metrics.vjump_state, (200, 200, 200))
            cv2.rectangle(frame, (0, 95), (400, 130), (255, 255, 255), -1)
            cv2.putText(frame, self.feedback, (10, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)
        elif exercise_name == 'bjump':
            cv2.rectangle(frame, (0, 0), (180, 90), (245, 117, 16), -1)
            cv2.putText(frame, 'JUMPS', (15, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, str(self.metrics.bjump_jump_count), (20, 75), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3, cv2.LINE_AA)
            
            cv2.rectangle(frame, (190, 0), (400, 90), (16, 200, 245), -1)
            cv2.putText(frame, 'MAX DIST (px)', (200, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            max_dist = int(self.metrics.bjump_max_distance)
            cv2.putText(frame, str(max_dist), (210, 75), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3, cv2.LINE_AA)
            
            state_colors_bjump = {'standing': (200, 200, 200), 'airborne': (0, 255, 0), 'landing': (255, 165, 0)}
            color = state_colors_bjump.get(self.metrics.bjump_state, (200, 200, 200))
            cv2.rectangle(frame, (0, 95), (400, 130), (255, 255, 255), -1)
            cv2.putText(frame, self.feedback, (10, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)
        else:
            cv2.rectangle(frame, (0, 0), (225, 73), (245, 117, 16), -1)
            
            cv2.putText(frame, 'REPS', (15, 12), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, str(self.counter), (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)
            
            cv2.putText(frame, 'STAGE', (65, 12), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, str(self.stage if self.stage else '-'), (60, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

            color = (0, 255, 0) if self.feedback == "Good Form" else (0, 0, 255)
            cv2.rectangle(frame, (0, 73), (225, 103), (255, 255, 255), -1)
            cv2.putText(frame, self.feedback, (15, 95), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)
        
        return frame

    def process_pushup(self, angles, keypoints):
        """Logic for Pushups"""
        if keypoints is None or len(keypoints) < 17:
            self.feedback = "Body not detected"
            return
        
        left_conf = keypoints[7][2]
        right_conf = keypoints[8][2]
        
        if left_conf > right_conf:
            elbow = angles['left_elbow']
            hip = angles['left_hip']
        else:
            elbow = angles['right_elbow']
            hip = angles['right_hip']

        if elbow is None or hip is None:
            self.feedback = "Body not visible"
            return

        self.metrics.update_angle_data(
            angles.get('left_elbow'), angles.get('right_elbow'),
            angles.get('left_hip'), angles.get('right_hip'),
            None, None, None, None, None, None, None, None
        )

        if hip < self.thresholds['pushup']['form_hip_min']:
            self.feedback = "Fix Back!"
            self.metrics.bad_form_count += 1
        else:
            self.feedback = "Good Form"

        if elbow > self.thresholds['pushup']['up']:
            self.stage = "UP"
        
        if elbow < self.thresholds['pushup']['down'] and self.stage == 'UP':
            self.stage = "DOWN"
            self.counter += 1
            
            is_good = (self.feedback == "Good Form")
            self.metrics.record_rep(
                rep_max=self.thresholds['pushup']['up'],
                rep_min=elbow,
                duration_seconds=1.0,
                is_good_form=is_good
            )
            
            self.log(f"Pushup Count: {self.counter}")

    def process_squat(self, angles, keypoints):
        """Logic for Squats"""
        if keypoints is None or len(keypoints) < 17:
            self.feedback = "Body not detected"
            return
        
        import time
        left_conf = keypoints[13][2]
        right_conf = keypoints[14][2]
        
        if left_conf > right_conf:
            knee = angles['left_knee']
        else:
            knee = angles['right_knee']

        if knee is None:
            self.feedback = "Legs not visible"
            return
        
        current_time = time.time()
        torso_angle = angles.get('torso_angle')
        shin_angle_left = angles.get('shin_angle_left')
        shin_angle_right = angles.get('shin_angle_right')
        
        left_knee_conf = keypoints[13][2]
        right_knee_conf = keypoints[14][2]
        if left_knee_conf > right_knee_conf:
            shin_angle = shin_angle_left
        else:
            shin_angle = shin_angle_right
        
        self.metrics.update_squat_data(keypoints, angles, torso_angle, shin_angle, current_time)
        
        if knee > self.thresholds['squat']['up']:
            if self.stage == "DOWN":
                if self.metrics.rep_bottom_time is not None:
                    concentric_time = current_time - self.metrics.rep_bottom_time
                    self.metrics.concentric_times.append(concentric_time)
                    
                    if self.metrics.min_velocity_angle is not None:
                        self.metrics.sticking_points.append(self.metrics.min_velocity_angle)
                    
                    self.metrics.min_velocity = float('inf')
                    self.metrics.min_velocity_angle = None
                    self.metrics.rep_bottom_time = None
            
            self.stage = "UP"
            self.metrics.current_phase = 'standing'
            
            if self.metrics.rep_start_time is None:
                self.metrics.rep_start_time = current_time
        
        elif knee < self.thresholds['squat']['down']:
            self.metrics.current_phase = 'descending'
            
            if self.stage == 'UP':
                self.stage = "DOWN"
                self.counter += 1
                self.metrics.current_phase = 'bottom'
                
                if self.metrics.rep_start_time is not None:
                    eccentric_time = current_time - self.metrics.rep_start_time
                    self.metrics.eccentric_times.append(eccentric_time)
                
                self.metrics.rep_bottom_time = current_time
                self.metrics.rep_start_time = None
                self.metrics.squat_depths.append(knee)
                
                if knee < self.thresholds['squat']['deep']:
                    self.feedback = "Great Depth!"
                    self.metrics.good_reps += 1
                    is_good_form = True
                else:
                    self.feedback = "Go Lower"
                    self.metrics.bad_reps += 1
                    is_good_form = False
                
                if torso_angle and torso_angle > 45:
                    self.feedback = "Too Much Lean!"
                    is_good_form = False
                
                self.metrics.record_rep(
                    rep_max=self.thresholds['squat']['up'],
                    rep_min=knee,
                    duration_seconds=1.0,
                    is_good_form=is_good_form
                )
                
                self.log(f"Squat Count: {self.counter}")
        
        else:
            if self.stage == 'UP':
                self.metrics.current_phase = 'descending'
            elif self.stage == 'DOWN':
                self.metrics.current_phase = 'ascending'
            
            if self.stage != "DOWN":
                self.feedback = "Squat"

    def process_situp(self, angles, keypoints):
        """Logic for Sit-ups"""
        if keypoints is None or len(keypoints) < 17:
            self.feedback = "Body not detected"
            return
        
        import time
        current_time = time.time()
        
        torso_inclination = angles.get('torso_inclination_horizontal')
        hip_flexion = angles.get('hip_flexion_angle')
        
        if torso_inclination is None:
            self.feedback = "Body not visible"
            return
        
        self.metrics.update_situp_data(keypoints, angles, torso_inclination, hip_flexion, current_time)
        foot_lifted = self.metrics._detect_foot_lift(keypoints)
        neck_distance = self.metrics._detect_neck_strain(keypoints)
        if neck_distance:
            self.metrics.situp_neck_strains.append(neck_distance)
        
        if torso_inclination <= self.thresholds['situp']['down']:
            if self.metrics.situp_state == 'descending':
                if self.metrics.situp_peak_time is not None:
                    eccentric_time = current_time - self.metrics.situp_peak_time
                    self.metrics.situp_eccentric_times.append(eccentric_time)
                    self.metrics.situp_peak_time = None
                
                momentum_score = self.metrics._calculate_momentum_score()
                self.metrics.situp_momentum_scores.append(momentum_score)
                self.metrics.shoulder_positions.clear()
                self.metrics.max_torso_inclination = 0
                self.metrics.min_hip_flexion = 180
                
            self.metrics.situp_state = 'rest'
            self.stage = "DOWN"
            
            if self.metrics.situp_rep_start_time is None:
                self.metrics.situp_rep_start_time = current_time
        
        elif torso_inclination >= self.thresholds['situp']['up'] or \
             (hip_flexion is not None and hip_flexion <= self.thresholds['situp']['good_crunch']):
            if self.metrics.situp_state in ['rest', 'ascending']:
                self.counter += 1
                self.metrics.situp_state = 'peak'
                self.stage = "UP"
                
                if self.metrics.situp_rep_start_time is not None:
                    concentric_time = current_time - self.metrics.situp_rep_start_time
                    self.metrics.situp_concentric_times.append(concentric_time)
                    self.metrics.situp_rep_start_time = None
                
                self.metrics.situp_peak_time = current_time
                self.metrics.situp_torso_inclinations.append(self.metrics.max_torso_inclination)
                self.metrics.situp_hip_flexions.append(self.metrics.min_hip_flexion if hip_flexion else 180)
                self.metrics.situp_foot_lifts.append(1 if foot_lifted else 0)
                
                good_rom = torso_inclination >= self.thresholds['situp']['up']
                good_crunch = hip_flexion is not None and hip_flexion <= self.thresholds['situp']['good_crunch']
                
                if good_rom and good_crunch:
                    self.feedback = "Perfect Rep!"
                    self.metrics.good_reps += 1
                    self.metrics.situp_valid_reps += 1
                    is_good_form = True
                elif good_rom:
                    self.feedback = "Good - Crunch Tighter"
                    self.metrics.good_reps += 1
                    self.metrics.situp_valid_reps += 1
                    is_good_form = True
                else:
                    self.feedback = "Go Higher!"
                    self.metrics.bad_reps += 1
                    self.metrics.situp_short_rom_count += 1
                    is_good_form = False
                
                if foot_lifted:
                    self.feedback += " - Feet Lifted!"
                    is_good_form = False
                
                self.metrics.record_rep(
                    rep_max=torso_inclination,
                    rep_min=0,
                    duration_seconds=1.0,
                    is_good_form=is_good_form
                )
                
                self.log(f"Sit-up Count: {self.counter}")
            
            if torso_inclination < self.thresholds['situp']['up'] - 10:
                self.metrics.situp_state = 'descending'
        
        else:
            if self.metrics.situp_state == 'rest':
                self.metrics.situp_state = 'ascending'
                self.feedback = "Keep Going Up"
            elif self.metrics.situp_state == 'peak':
                self.metrics.situp_state = 'descending'
                self.feedback = "Controlled Down"

    def process_sitnreach(self, angles, keypoints):
        """Logic for Sit-and-Reach"""
        if keypoints is None or len(keypoints) < 17:
            self.feedback = "Body not detected"
            return
        
        import time
        current_time = time.time()
        
        if self.metrics.sitnreach_start_time is None:
            self.metrics.sitnreach_start_time = current_time
        
        self.metrics.sitnreach_test_duration = current_time - self.metrics.sitnreach_start_time
        
        reach_distance = angles.get('reach_distance')
        arm_length = angles.get('arm_length')
        hip_angle = angles.get('sitnreach_hip_angle')
        back_angle = angles.get('sitnreach_back_angle')
        knee_angle = angles.get('sitnreach_knee_angle')
        symmetry_error = angles.get('reach_symmetry')
        
        if reach_distance is None:
            self.feedback = "Position not visible"
            return
        
        self.metrics.update_sitnreach_data(
            keypoints, angles, reach_distance, arm_length,
            hip_angle, back_angle, knee_angle, symmetry_error, current_time
        )
        
        feedback_parts = []
        
        if reach_distance > self.metrics.max_reach_distance * 0.95:
            feedback_parts.append("MAX REACH!")
        elif reach_distance > self.metrics.max_reach_distance * 0.85:
            feedback_parts.append("Keep Reaching")
        else:
            feedback_parts.append("Stretch Forward")
        
        if knee_angle and knee_angle < self.thresholds['sitnreach']['knee_valid']:
            feedback_parts.append("Straighten Legs!")
        
        if symmetry_error and symmetry_error > 50:
            feedback_parts.append("Balance Both Sides")
        
        if hip_angle:
            if hip_angle < self.thresholds['sitnreach']['excellent_hip']:
                feedback_parts.append("Excellent Flex!")
            elif hip_angle < self.thresholds['sitnreach']['average_hip']:
                feedback_parts.append("Good Flex")
            else:
                feedback_parts.append("Bend More")
        
        self.feedback = " | ".join(feedback_parts)
        
        if arm_length and arm_length > 0:
            normalized_reach = (self.metrics.max_reach_distance / arm_length) * 100
            self.counter = int(normalized_reach)
        
        if knee_angle and knee_angle >= self.thresholds['sitnreach']['knee_valid']:
            self.stage = "VALID"
        else:
            self.stage = "INVALID"

    def process_skipping(self, angles, keypoints):
        """Logic for Skipping"""
        if keypoints is None or len(keypoints) < 17:
            self.feedback = "Body not detected"
            return
        
        import time
        current_time = time.time()
        
        if self.metrics.skip_start_time is None:
            self.metrics.skip_start_time = current_time
        
        self.metrics.update_skipping_data(keypoints, angles, current_time)
        
        feedback_parts = []
        
        if self.metrics.jump_state == 'air':
            self.stage = "AIR"
            feedback_parts.append("IN AIR")
        else:
            self.stage = "GROUND"
            feedback_parts.append("Ready")
        
        back_angle = angles.get('skip_back_angle')
        if back_angle and abs(back_angle - 180) > 30:
            feedback_parts.append("Stand Upright!")
        
        knee_angle = angles.get('skip_knee_angle')
        if knee_angle and knee_angle < 120:
            feedback_parts.append("Less Knee Bend")
        
        if self.metrics.jump_count > 10:
            frequency = self.metrics._get_skipping_frequency()
            if frequency > 3:
                feedback_parts.append("Excellent Speed!")
            elif frequency < 1.5:
                feedback_parts.append("Speed Up")
        
        self.feedback = " | ".join(feedback_parts)

    def process_jumpingjacks(self, angles, keypoints):
        """Logic for Jumping Jacks"""
        if keypoints is None or len(keypoints) < 17:
            self.feedback = "Body not detected"
            return
        
        import time
        current_time = time.time()
        
        if self.metrics.jj_start_time is None:
            self.metrics.jj_start_time = current_time
        
        self.metrics.update_jumpingjacks_data(keypoints, angles, current_time)
        
        feedback_parts = []
        
        arm_spread = list(self.metrics.jj_arm_spreads)[-1] if self.metrics.jj_arm_spreads else 0
        leg_spread = list(self.metrics.jj_leg_spreads)[-1] if self.metrics.jj_leg_spreads else 0
        arm_angle = list(self.metrics.jj_arm_angles)[-1] if self.metrics.jj_arm_angles else 0
        
        state_text = f"STATE: {self.metrics.jj_state.upper()}"
        feedback_parts.append(state_text)
        
        arm_status = "✓" if arm_angle >= 135 else ("✗" if arm_angle <= 45 else "~")
        leg_status = "✓" if leg_spread >= 120 else ("✗" if leg_spread <= 100 else "~")
        spread_status = "✓" if arm_spread >= 180 else ("✗" if arm_spread <= 120 else "~")
        
        feedback_parts.append(f"Angle:{int(arm_angle)}°{arm_status}")
        feedback_parts.append(f"ArmSpread:{int(arm_spread)}px{spread_status}")
        feedback_parts.append(f"LegSpread:{int(leg_spread)}px{leg_status}")
        
        if self.metrics.jj_state == 'open':
            if arm_angle < 120:
                feedback_parts.append("↑ RAISE ARMS!")
        else:
            if arm_angle > 60:
                feedback_parts.append("↓ LOWER ARMS!")
            if leg_spread > 120:
                feedback_parts.append("→← FEET TOGETHER!")
        
        self.feedback = " | ".join(feedback_parts)

    def process_vjump(self, angles, keypoints):
        """Logic for Vertical Jump"""
        if keypoints is None or len(keypoints) < 17:
            self.feedback = "Body not detected"
            return
        
        import time
        current_time = time.time()
        
        if self.metrics.vjump_start_time is None:
            self.metrics.vjump_start_time = current_time
        
        self.metrics.update_vjump_data(keypoints, angles, current_time)
        
        feedback_parts = []
        
        state_text = f"STATE: {self.metrics.vjump_state.upper()}"
        feedback_parts.append(state_text)
        
        if self.metrics.vjump_state == 'standing':
            feedback_parts.append("Ready to jump")
        elif self.metrics.vjump_state == 'preparing':
            knee_angle = angles.get('vjump_countermovement_angle')
            if knee_angle:
                feedback_parts.append(f"Knee bend: {knee_angle}°")
                if knee_angle < 100:
                    feedback_parts.append("Good depth!")
            feedback_parts.append("Swing arms up!")
        elif self.metrics.vjump_state == 'airborne':
            feedback_parts.append("In the air!")
            if self.metrics.vjump_min_ankle_y:
                current_height = self.metrics.vjump_ground_y - self.metrics.vjump_min_ankle_y
                feedback_parts.append(f"Height: {int(current_height)}px")
        elif self.metrics.vjump_state == 'landing':
            feedback_parts.append("Prepare for landing")
            landing_knee = angles.get('vjump_landing_knee_angle')
            if landing_knee:
                if landing_knee < 100:
                    feedback_parts.append("Too much bend!")
                elif landing_knee > 160:
                    feedback_parts.append("Land softer!")
                else:
                    feedback_parts.append("Good landing!")
        
        if self.metrics.vjump_jump_count > 0:
            max_jump = int(max(self.metrics.vjump_jump_heights))
            feedback_parts.append(f"Best: {max_jump}px")
        
        self.feedback = " | ".join(feedback_parts)

    def process_bjump(self, angles, keypoints):
        """Logic for Broad Jump"""
        if keypoints is None or len(keypoints) < 17:
            self.feedback = "Body not detected"
            return
        
        import time
        current_time = time.time()
        
        if self.metrics.bjump_start_time is None:
            self.metrics.bjump_start_time = current_time
        
        self.metrics.update_bjump_data(keypoints, angles, current_time)
        
        feedback_parts = []
        
        state_text = f"STATE: {self.metrics.bjump_state.upper()}"
        feedback_parts.append(state_text)
        
        if self.metrics.bjump_state == 'standing':
            feedback_parts.append("Ready to jump")
        elif self.metrics.bjump_state == 'airborne':
            feedback_parts.append("In the air!")
            if self.metrics.bjump_landing_x and self.metrics.bjump_start_x:
                current_dist = abs(self.metrics.bjump_landing_x - self.metrics.bjump_start_x)
                feedback_parts.append(f"Distance: {int(current_dist)}px")
        elif self.metrics.bjump_state == 'landing':
            feedback_parts.append("Landing...")
        
        if self.metrics.bjump_jump_count > 0:
            max_dist = int(self.metrics.bjump_max_distance)
            feedback_parts.append(f"Best: {max_dist}px")
        
        self.feedback = " | ".join(feedback_parts)

    def process_video(self, video_path, exercise_type, save_output=False):
        """Process video file and return results"""
        import time
        from datetime import datetime
        
        self.logs = []
        self.current_exercise = exercise_type
        self.metrics.exercise = exercise_type
        self.start_time = time.time()
        
        self.log(f"\n{'='*50}")
        self.log(f"Starting {exercise_type.upper()} analysis...")
        self.log(f"{'='*50}\n")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not open video file")
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        output_path = None
        writer = None
        
        if save_output:
            output_path = video_path.replace('.mp4', '_processed.avi')
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame, keypoints, angles = self.calibrator.process_frame(frame, show_angles_panel=False)
            
            if keypoints is not None:
                if exercise_type == 'pushup':
                    self.process_pushup(angles, keypoints)
                elif exercise_type == 'squat':
                    self.process_squat(angles, keypoints)
                elif exercise_type == 'situp':
                    self.process_situp(angles, keypoints)
                elif exercise_type == 'sitnreach':
                    self.process_sitnreach(angles, keypoints)
                elif exercise_type == 'skipping':
                    self.process_skipping(angles, keypoints)
                elif exercise_type == 'jumpingjacks':
                    self.process_jumpingjacks(angles, keypoints)
                elif exercise_type == 'vjump':
                    self.process_vjump(angles, keypoints)
                elif exercise_type == 'bjump':
                    self.process_bjump(angles, keypoints)
            
            frame = self._draw_dashboard(frame, exercise_type)
            
            if writer:
                writer.write(frame)
            
            frame_count += 1
        
        cap.release()
        if writer:
            writer.release()
        
        self.log("\n" + "="*50)
        self.log("Analysis Complete!")
        self.log("="*50)
        
        # Get metrics
        result = None
        if exercise_type == 'pushup':
            result = self.metrics.pushup_metrics()
        elif exercise_type == 'squat':
            result = self.metrics.squat_metrics()
        elif exercise_type == 'situp':
            result = self.metrics.situp_metrics()
        elif exercise_type == 'sitnreach':
            result = self.metrics.sitnreach_metrics()
        elif exercise_type == 'skipping':
            result = self.metrics.skipping_metrics()
        elif exercise_type == 'jumpingjacks':
            result = self.metrics.jumpingjacks_metrics()
        elif exercise_type == 'vjump':
            result = self.metrics.vjump_metrics()
        elif exercise_type == 'bjump':
            result = self.metrics.bjump_metrics()
        
        if result:
            result['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result['logs'] = self.logs
        
        return result, output_path


@app.get("/")
async def root():
    return {
        "message": "AI Exercise Trainer API",
        "version": "1.0.0",
        "endpoints": {
            "/analyze": "POST - Analyze exercise video",
            "/exercises": "GET - List available exercises",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": evaluator is not None}


@app.get("/exercises")
async def list_exercises():
    return {
        "exercises": [
            {"id": "pushup", "name": "Push-ups"},
            {"id": "squat", "name": "Squats"},
            {"id": "situp", "name": "Sit-ups"},
            {"id": "sitnreach", "name": "Sit-and-Reach"},
            {"id": "skipping", "name": "Skipping (Jump Rope)"},
            {"id": "jumpingjacks", "name": "Jumping Jacks"},
            {"id": "vjump", "name": "Vertical Jump"},
            {"id": "bjump", "name": "Broad Jump"}
        ]
    }


@app.post("/analyze")
async def analyze_exercise(
    video: UploadFile = File(...),
    exercise_type: str = Form(...),
    save_output: bool = Form(False)
):
    """
    Analyze exercise video
    
    - **video**: Video file to analyze
    - **exercise_type**: Type of exercise (pushup, squat, situp, sitnreach, skipping, jumpingjacks, vjump, bjump)
    - **save_output**: Whether to save processed video
    """
    
    if exercise_type not in ['pushup', 'squat', 'situp', 'sitnreach', 'skipping', 'jumpingjacks', 'vjump', 'bjump']:
        raise HTTPException(status_code=400, detail="Invalid exercise type")
    
    # Save uploaded video temporarily
    temp_dir = tempfile.mkdtemp()
    video_path = os.path.join(temp_dir, video.filename)
    
    try:
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        
        # Process video
        result, output_path = evaluator.process_video(video_path, exercise_type, save_output)
        
        response = {
            "success": True,
            "exercise": exercise_type,
            "metrics": result,
            "output_video_available": output_path is not None
        }
        
        # If output video was generated, include download link
        if output_path and os.path.exists(output_path):
            # Copy to temp location for download
            output_filename = f"{exercise_type}_processed.avi"
            final_output_path = os.path.join(temp_dir, output_filename)
            shutil.copy(output_path, final_output_path)
            response["output_video_path"] = output_filename
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{filename}")
async def download_processed_video(filename: str):
    """Download processed video"""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, media_type="video/x-msvideo", filename=filename)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
