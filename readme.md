# Push-Up Performance Evaluation Using YOLOv8 Pose

This document describes how to compute **push-up performance metrics** using
**YOLOv8 pose models**, starting from **model calibration** to **final scoring**.
The approach is based on **17 pose keypoints**, **angle detection**, and
**biomechanical rules**.

---

## 1. System Assumptions and Setup

- Pose model: YOLOv8-Pose  
- Input: Video of a subject performing push-ups  
- Output per frame:
  - 17 body keypoints `(x, y, confidence)`
- Camera view:
  - Preferably side view or slight oblique angle
- Coordinate system:
  - Pixel coordinates (optionally normalized)

Only frames where keypoint confidence ≥ 0.5 are considered for analysis.

---

## 2. Keypoint Extraction (YOLOv8 Pose)

For each frame:

1. Run YOLOv8-Pose inference
2. Extract required keypoints:
   - Shoulders (Left, Right)
   - Elbows (Left, Right)
   - Wrists (Left, Right)
   - Hips (Left, Right)
   - Knees (Left, Right)
   - Ankles (Left, Right)

These keypoints are used to calculate joint angles and posture metrics.

---

## 3. Angle Calculation (Core Formula)

All joint angles are computed using **three points**:

Angle at point `B` formed by points `A – B – C`:

θ = cos⁻¹ [ ((A − B) · (C − B)) / (|A − B| × |C − B|) ]

This angle formula is used for:
- Elbow angle
- Back (spine) angle
- Hip and knee alignment

---

## 4. Elbow Angle (Push-Up Depth Detection)

**Keypoints used:**
- Shoulder, Elbow, Wrist (both arms)

**Computation:**
- Left elbow angle = angle(Left Shoulder, Left Elbow, Left Wrist)
- Right elbow angle = angle(Right Shoulder, Right Elbow, Right Wrist)

**Usage:**
- Detect UP position: elbow angle > 150°
- Detect DOWN position: elbow angle < 90°
- A valid push-up repetition is detected when motion transitions from DOWN → UP

---

## 5. Back Straightness (Spine Angle)

**Keypoints used:**
- Shoulder, Hip, Knee (both sides)

**Computation:**
- Left back angle = angle(Left Shoulder, Left Hip, Left Knee)
- Right back angle = angle(Right Shoulder, Right Hip, Right Knee)
- Average back angle = (Left + Right) / 2

**Interpretation:**
- Ideal back angle ≈ 180°
- Lower values indicate sagging or excessive curvature

---

## 6. Hip Sag Measurement

**Keypoints used:**
- Shoulders, Hips, Ankles (y-coordinates)

**Computation:**
- Hip Y = average(Left Hip Y, Right Hip Y)
- Shoulder Y = average(Left Shoulder Y, Right Shoulder Y)
- Ankle Y = average(Left Ankle Y, Right Ankle Y)

Hip Sag Error =  
| Hip Y − (Shoulder Y + Ankle Y) / 2 |

**Interpretation:**
- Smaller error means better body alignment
- Larger error indicates hips dropping or lifting excessively

---

## 7. Range of Motion (ROM)

**Data extracted:**
- Maximum elbow angle (UP position)
- Minimum elbow angle (DOWN position)

**Computation:**
- ROM = Angle_up − Angle_down
- Ideal ROM ≈ 90°

ROM Score = ROM / 90 (clipped between 0 and 1)

**Interpretation:**
- Higher score means deeper and fuller push-ups

---

## 8. Alignment Score (Spine Straightness Score)

**Data extracted:**
- Average back angle

**Computation:**
- Alignment Error = | Back Angle − 180° |
- Maximum acceptable deviation = 45°

Alignment Score = 1 − (Alignment Error / 45)

**Interpretation:**
- Score close to 1 indicates good alignment
- Lower score indicates posture issues

---

## 9. Arm Symmetry

**Data extracted:**
- Left and Right elbow angles

**Computation:**
- Symmetry Error = | Left Elbow Angle − Right Elbow Angle |
- Maximum allowed asymmetry = 30°

Symmetry Score = 1 − (Symmetry Error / 30)

**Interpretation:**
- Higher score indicates balanced arm movement

---

## 10. Tempo Consistency

**Data extracted:**
- Time taken for each repetition

Let:
- t₁, t₂, …, tₙ be durations of push-ups

**Computation:**
- Mean time = μ
- Standard deviation = σ

Tempo Variation = σ / μ  
Tempo Score = 1 − Tempo Variation

**Interpretation:**
- Consistent pace gives higher score

---

## 11. Repetition Count Accuracy

**Data extracted:**
- Predicted repetition count (P)
- Ground truth repetition count (G)

**Computation:**
Accuracy_rep = 1 − |P − G| / G

**Interpretation:**
- Measures numerical correctness of counting

---

## 12. Machine Learning Metrics (Optional)

Used when a classifier is trained to label push-ups as **correct** or **incorrect**.

**Extract:**
- TP (True Positives)
- TN (True Negatives)
- FP (False Positives)
- FN (False Negatives)

**Formulas:**
- Accuracy = (TP + TN) / (TP + TN + FP + FN)
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1 Score = 2 × (Precision × Recall) / (Precision + Recall)
- Mean Squared Error (MSE) = (1 / n) × Σ (Actual − Predicted)²

---

## 13. Overall System Flow

1. Input push-up test video  
2. Extract 17 keypoints per frame using YOLOv8 Pose  
3. Compute joint angles using cosine rule  
4. Detect UP and DOWN positions  
5. Count repetitions and record time per rep  
6. Calculate ROM, alignment, symmetry, hip sag, and tempo  
7. Compute accuracy and ML metrics (if ground truth is available)  
8. Produce final push-up performance scores

---
