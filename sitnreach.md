SYSTEM OVERVIEW

This system evaluates flexibility using the Sit-and-Reach fitness test.
It uses YOLOv8 Pose to extract body keypoints and applies deterministic
biomechanical formulas to compute flexibility and posture metrics.

Pipeline:
Video Input
→ YOLOv8 Pose (17 keypoints)
→ Angle and distance calculation
→ Rule-based metric evaluation
→ Final flexibility score

YOLOv8 POSE INPUT

Each video frame provides 17 body keypoints.
Each keypoint is represented as:

(x, y, confidence)

Keypoints required for Sit-and-Reach:

Left and Right Shoulder

Left and Right Hip

Left and Right Knee

Left and Right Ankle

Left and Right Wrist

Frames with low-confidence keypoints are ignored.

SIT-AND-REACH TEST DEFINITION

The participant:

Sits on the floor

Keeps legs fully extended

Keeps feet fixed against a reference plane

Reaches forward with both hands simultaneously

The maximum forward reach achieved during the test
is used for evaluation.

CORE MATHEMATICS

ANGLE COMPUTATION (3-POINT METHOD)

For three points A, B, C, the angle at B is:

θ = arccos( (BA · BC) / (|BA| × |BC|) )

This formula is used to compute hip, knee, and back angles.

METRICS AND THEIR CALCULATION

FORWARD REACH DISTANCE (PRIMARY METRIC)

Horizontal reach distance is computed as:

Reach_Distance = Wrist_x − Ankle_x

The maximum value across all frames is taken:

Max_Reach = max(Reach_Distance)

NORMALIZED REACH SCORE

To remove body-size dependency, reach is normalized using arm length.

Arm length:

Arm_Length = distance(Shoulder, Wrist)

Normalized reach score:

Reach_Score = Max_Reach / Arm_Length

Range: 0.0 to 1.0

HIP FLEXION ANGLE (TRUNK FLEXIBILITY)

Hip angle:

Hip_Angle = Shoulder – Hip – Knee

Minimum value during the reach:

Min_Hip_Angle = minimum(Hip_Angle over frames)

Interpretation:
Min_Hip_Angle < 60 degrees → Excellent flexibility
60–80 degrees → Average flexibility

90 degrees → Poor flexibility

BACK ALIGNMENT (SPINE CONTROL)

Back angle:

Back_Angle = Shoulder – Hip – Knee

Deviation from ideal straight posture:

Back_Error = |Back_Angle − 180 degrees|

Lower deviation indicates better spine control.

KNEE EXTENSION VALIDITY (TEST VALIDITY CHECK)

Knee angle:

Knee_Angle = Hip – Knee – Ankle

Validity condition:

If Knee_Angle ≥ 165 degrees → Legs straight (valid test)
If Knee_Angle < 165 degrees → Legs bent (invalid test)

REACH SYMMETRY (LEFT VS RIGHT)

Symmetry error is calculated as:

Symmetry_Error =
|Left_Wrist_X − Right_Wrist_X|

Lower value indicates balanced bilateral flexibility.

HIP STABILITY (NO BOUNCING)

Vertical hip stability is measured using variance:

Hip_Variance = variance(Hip_Y positions over frames)

High variance indicates bouncing or jerky reaching,
which reduces test validity.

SIT-AND-REACH ACCURACY (PHYSICAL ACCURACY)

A sit-and-reach attempt is considered valid if:

Legs remain straight

Reach motion is continuous

No excessive bouncing

Accuracy calculation:

Accuracy = Valid_Attempts / Total_Attempts

Range:
0.0 → Completely invalid test
1.0 → Perfect execution

FINAL SIT-AND-REACH PERFORMANCE SCORE

All component scores are normalized between 0 and 1.

Final Score Formula:

Final_Score =
0.40 × Reach_Score

0.25 × Trunk_Flexibility_Score

0.15 × Back_Alignment_Score

0.10 × Symmetry_Score

0.10 × Knee_Validity_Score

Score Interpretation:
0.8 – 1.0 → Excellent flexibility
0.6 – 0.8 → Good flexibility
0.4 – 0.6 → Average flexibility
< 0.4 → Poor flexibility

WHY THIS METHOD WORKS

Deterministic and explainable

Sports-science compliant

No training data required

Real-time capable

Suitable for fitness assessment and grading