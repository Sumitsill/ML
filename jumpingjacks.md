SYSTEM OVERVIEW

This system evaluates jumping jacks exercise performance using YOLOv8 Pose.
Body keypoints are extracted from video frames, and deterministic rules are
applied to count repetitions, assess coordination, posture, and rhythm.

Pipeline:
Video Input
→ YOLOv8 Pose (17 body keypoints)
→ Distance, angle, and motion computation
→ Rule-based rep detection and evaluation
→ Count, accuracy, and performance score

YOLOv8 POSE INPUT

Each frame provides 17 keypoints in the format:

(x, y, confidence)

Key keypoints used for jumping jacks:

Left & Right Wrist (arm spread)

Left & Right Shoulder

Left & Right Ankle (leg spread + jump)

Left & Right Hip

Left & Right Knee

Low-confidence frames are ignored for stability.

WHAT DEFINES ONE JUMPING JACK REP

One complete jumping jack consists of two positions:

OPEN POSITION

Arms raised overhead and spread

Legs spread apart

CLOSED POSITION

Arms down at sides

Legs together

A rep is counted when the sequence occurs:

CLOSED → OPEN → CLOSED

CORE DISTANCES & ANGLES

4.1 ARM SPREAD DISTANCE

Horizontal distance between wrists:

Arm_Spread =
|Left_Wrist_X − Right_Wrist_X|

4.2 LEG SPREAD DISTANCE

Horizontal distance between ankles:

Leg_Spread =
|Left_Ankle_X − Right_Ankle_X|

4.3 ARM ELEVATION ANGLE

Arm raise angle (each side):

Arm_Angle = Shoulder – Elbow – Wrist

Higher angle → arms raised overhead.

POSITION DETECTION RULES

OPEN POSITION CONDITIONS

Arm_Spread ≥ Arm_Open_Threshold

Leg_Spread ≥ Leg_Open_Threshold

Arm_Angle ≥ 150 degrees

CLOSED POSITION CONDITIONS

Arm_Spread ≤ Arm_Close_Threshold

Leg_Spread ≤ Leg_Close_Threshold

Arm_Angle ≤ 40 degrees

REP COUNTING LOGIC

Maintain a state variable:

Initial State: CLOSED

If state == CLOSED and OPEN conditions satisfied:
state = OPEN

If state == OPEN and CLOSED conditions satisfied:
state = CLOSED
rep_count += 1

METRICS AND THEIR CALCULATION

REP COUNT

Total jumping jacks performed:

Total_Reps = rep_count

ARM-LEG COORDINATION

Time difference between:

arms reaching OPEN

legs reaching OPEN

Coordination_Error =
|t_arm_open − t_leg_open|

Lower value → better coordination.

RANGE OF MOTION (ARMS & LEGS)

Arm ROM:
Arm_ROM = max(Arm_Angle) − min(Arm_Angle)

Leg ROM:
Leg_ROM = max(Leg_Spread) − min(Leg_Spread)

TEMPO / SPEED

Rep duration:

Rep_Duration = Rep_End_Time − Rep_Start_Time

TEMPO CONSISTENCY

Tempo consistency measured by variance:

Tempo_Variance = variance(Rep_Duration over all reps)

POSTURE CONTROL

Back angle:

Back_Angle = Shoulder – Hip – Knee

Deviation:

Back_Error = |Back_Angle − 180 degrees|

Large deviation indicates bending or fatigue.

JUMPING JACKS ACCURACY (PHYSICAL ACCURACY)

A jumping jack repetition is considered correct if:

Arms fully open and close

Legs fully spread and return

Arm and leg movement are synchronized

No skipped or half movement

Accuracy calculation:

Accuracy = Correct_Reps / Total_Reps

Range:
0.0 → Poor performance
1.0 → Perfect performance

FINAL JUMPING JACKS PERFORMANCE SCORE

All components are normalized between 0 and 1.

Final Score Formula:

Final_Score =
0.35 × Accuracy

0.20 × Coordination_Score

0.15 × Arm_ROM_Score

0.15 × Leg_ROM_Score

0.15 × Tempo_Consistency_Score

Score Interpretation:
0.8 – 1.0 → Excellent
0.6 – 0.8 → Good
0.4 – 0.6 → Average
< 0.4 → Poor

WHY YOLOv8 WORKS WELL FOR JUMPING JACKS

Clear detection of arm and leg spread

Easy state-based rep counting

Robust to lighting and background changes

Works in real-time

No object detection needed