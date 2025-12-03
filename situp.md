# Sit-Up Analysis AI: Performance Metrics & Data Requirements

This project utilizes YOLOv8 Pose Estimation to analyze sit-up/crunch mechanics. This document outlines the specific biomechanical metrics calculated, the raw data required from the model, and the mathematical derivation for each output.

## 1. Data Source: YOLOv8 Keypoint Mapping
The system relies on the COCO Pose keypoint format. The primary view should be **Sagittal (Side Profile)** for the most accurate analysis.

| Joint Name | Keypoint Index (Left) | Keypoint Index (Right) |
| :--- | :---: | :---: |
| **Ear** (Head Position) | 3 | 4 |
| **Shoulder** | 5 | 6 |
| **Hip** (Pivot Point) | 11 | 12 |
| **Knee** | 13 | 14 |
| **Ankle** (Anchor) | 15 | 16 |

*Note: The system generally tracks the side of the body visible to the camera.*

---

## 2. Performance Metrics & Input Requirements

### Category A: Biomechanical Form (Technique)

#### 1. Torso Inclination (Rep Completion)
* **Description:** Measures the angle of the torso relative to the floor to determine if the athlete has risen high enough.
* **Required Data:**
    * Shoulder Coordinates $(x_{shoulder}, y_{shoulder})$
    * Hip Coordinates $(x_{hip}, y_{hip})$
    * Horizontal Vector reference (1, 0)
* **Calculation:** Angle between Vector $\vec{Hip-Shoulder}$ and the horizontal X-axis.
* **Target Output:**
    * **Value:** Degrees ($^\circ$)
    * **Pass Criteria (Up):** Angle $\ge 70^\circ$ (High position).
    * **Pass Criteria (Reset):** Angle $\le 20^\circ$ (Shoulders touched floor/mat).

#### 2. Hip Flexion Angle (Crunch Factor)
* **Description:** Measures how tightly the body folds. This is the primary metric for "closing the gap."
* **Required Data:**
    * Shoulder Coordinates $(x_{shoulder}, y_{shoulder})$
    * Hip Coordinates $(x_{hip}, y_{hip})$
    * Knee Coordinates $(x_{knee}, y_{knee})$
* **Calculation:** Internal angle at the Hip vertex connected to Shoulder and Knee.
* **Target Output:**
    * **Value:** Degrees ($^\circ$).
    * **Logic:** The smaller the angle, the better the crunch. Typically $< 50^\circ$ at peak contraction.

#### 3. Foot Lift / Anchoring (Cheating Detection)
* **Description:** Detects if the feet or knees lift off the ground/anchor point to generate leverage (momentum cheating).
* **Required Data:**
    * Knee Coordinates $(x_{knee}, y_{knee})$
    * Ankle Coordinates $(x_{ankle}, y_{ankle})$
* **Calculation:** Monitor the variance in the $Y$ (height) coordinate of the Knee and Ankle.
* **Target Output:**
    * **Value:** Vertical Displacement (Pixels).
    * **Alert:** If `Delta_Y > Threshold`, flag as "Feet Lifting."

#### 4. Neck Strain (Chin Tuck)
* **Description:** Checks if the user is pulling on their neck rather than using abs.
* **Required Data:**
    * Ear Coordinates $(x_{ear}, y_{ear})$
    * Shoulder Coordinates $(x_{shoulder}, y_{shoulder})$
* **Calculation:** Distance between Ear and Shoulder.
* **Target Output:**
    * **Logic:** If distance decreases significantly during the ascent, the user is hunching/pulling the neck.

---

### Category B: Physics & Power

#### 5. Repetition Tempo (Cadence)
* **Description:** Time taken for the concentric (up) vs. eccentric (down) phase.
* **Required Data:**
    * Timestamps at State Change (Floor -> Up -> Floor).
* **Target Output:**
    * **Value:** "Up: 1.0s, Down: 2.0s"
    * **Rating:** "Explosive" (Fast Up) vs. "Controlled" (Slow Down).

#### 6. Momentum Usage (Jerk Detection)
* **Description:** Detects if the user is throwing their body weight to start the rep rather than engaging the core.
* **Required Data:**
    * Shoulder Acceleration (2nd derivative of position).
* **Calculation:** If Acceleration peaks abruptly in the first 10% of movement, momentum is being used.
* **Target Output:**
    * **Value:** Jerk Score (0-100).
    * **Feedback:** "Don't swing your arms."

---

### Category C: Logic & Scoring

#### 7. Valid Rep Counter
* **Description:** Counts only strict repetitions.
* **Logic:**
    1.  **State 0 (Rest):** Torso Inclination $< 20^\circ$.
    2.  **State 1 (Ascent):** Torso Angle increasing.
    3.  **State 2 (Peak):** Torso Inclination $> 70^\circ$ OR Hip Flexion $< 50^\circ$.
    4.  **State 3 (Descent):** Torso Angle decreasing back to State 0.
* **Target Output:** Integer (Total Valid Reps).

#### 8. Form Score (0-100)
* **Description:** A composite score for the set.
* **Calculation:**
    * Start with 100.
    * Subtract 5 points for every rep where feet lifted.
    * Subtract 2 points for every rep with "Short Range of Motion" (didn't go all the way up or down).
* **Target Output:** Percentage.

---

## 3. Implementation Logic (Python Snippet Guide)

**Defining the Ground:**
Unlike squats, sit-ups happen horizontally.
```python
# Calculate angle relative to horizontal ground
def get_torso_inclination(shoulder, hip):
    dy = shoulder[1] - hip[1]
    dx = shoulder[0] - hip[0]
    angle = math.degrees(math.atan2(-dy, dx)) # Negative dy because image Y is inverted
    return abs(angle)