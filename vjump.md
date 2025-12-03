STANDING VERTICAL JUMP ANALYSIS USING YOLOv8 POSE
(Rule-Based, No ML, No LLM)

SYSTEM OVERVIEW

This system evaluates explosive lower-body strength using the
Standing Vertical Jump test. YOLOv8 Pose is used to track body keypoints
and deterministic biomechanical rules are applied to compute jump height,
technique, and performance scores.

Pipeline:
Video Input
→ YOLOv8 Pose (17 body keypoints)
→ Vertical motion & angle computation
→ Jump event detection
→ Jump height, accuracy, and performance score

YOLOv8 POSE INPUT

Each frame outputs 17 body keypoints in the format:

(x, y, confidence)

Keypoints used:

Left & Right Ankle (jump height detection)

Left & Right Knee

Left & Right Hip

Left & Right Shoulder

Left & Right Wrist (arm swing)

Low-confidence frames are ignored.

WHAT DEFINES ONE VERTICAL JUMP

A single vertical jump consists of three phases:

PREPARATION (COUNTERMOVEMENT)

Slight knee and hip flexion

TAKE-OFF

Feet leave the ground

LANDING

Feet return to ground level

One jump is counted when TAKE-OFF → LANDING occurs.

GROUND REFERENCE ESTIMATION

Ground level is estimated using ankle positions:

Ground_Y = median(Ankle_Y during standing frames)

Ankle Y-position decreases during upward movement
(image coordinate system assumption).

JUMP HEIGHT CALCULATION

Ankle vertical movement:

Ankle_Y = average(Left_Ankle_Y, Right_Ankle_Y)

Jump height (relative measure):

Jump_Height = Ground_Y − min(Ankle_Y during jump)

This value is proportional to actual vertical jump height.

METRICS AND THEIR CALCULATION

JUMP HEIGHT (PRIMARY METRIC)

Relative jump height:

Jump_Height = Ground_Y − min(Ankle_Y)

Higher value → better explosive strength.

COUNTERMOVEMENT DEPTH

Minimum knee angle before take-off:

Min_Knee_Angle = minimum(Knee_Angle before jump)

Indicates effective power generation.

ARM SWING UTILIZATION

Arm swing angle:

Arm_Angle = Shoulder – Elbow – Wrist

Effective arm swing:
Arm_Angle ≥ threshold before take-off.

TAKE-OFF SYMMETRY

Difference in ankle take-off timing:

Symmetry_Error =
|Left_Ankle_Takeoff − Right_Ankle_Takeoff|

Lower value → better balance.

LANDING CONTROL

Landing knee angle:

Landing_Knee_Angle = Knee_Angle at first ground contact

Excessive flexion or stiffness indicates poor control.

JUMP ACCURACY (PHYSICAL ACCURACY)

A vertical jump is considered valid if:

Both feet leave the ground

Jump height exceeds minimum threshold

No stepping or running start

Accuracy calculation:

Accuracy = Valid_Jumps / Total_Attempts

Range:
0.0 → Invalid attempts
1.0 → Perfect execution

FINAL VERTICAL JUMP PERFORMANCE SCORE

All scores normalized between 0 and 1.

Final Score Formula:

Final_Score =
0.40 × Jump_Height_Score

0.20 × Countermovement_Score

0.15 × Arm_Swing_Score

0.15 × Symmetry_Score

0.10 × Landing_Control_Score

Score Interpretation:
0.8 – 1.0 → Excellent explosive power
0.6 – 0.8 → Good
0.4 – 0.6 → Average
< 0.4 → Poor

HOW YOLOv8 SOLVES VERTICAL JUMP EFFECTIVELY

Tracks precise ankle vertical movement

Reliable detection of take-off and landing

Joint angle estimation for technique analysis

Works without force plates or markers

Real-time capable

WHY THIS METHOD WORKS

Deterministic and explainable

No datasets or training required

Sports-science aligned

Robust and efficient

Easy to implement