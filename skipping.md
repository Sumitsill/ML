SKIPPING (JUMP ROPE) PERFORMANCE ANALYSIS USING YOLOv8 POSE
(Rule-Based, No ML, No LLM)

SYSTEM OVERVIEW

This system evaluates skipping / jump-rope performance using YOLOv8 Pose.
Body keypoints are extracted from video frames, and biomechanical rules are
used to count jumps, check posture, timing, and consistency.

Pipeline:
Video Input
→ YOLOv8 Pose (17 body keypoints)
→ Jump detection using ankle motion
→ Rule-based metric calculation
→ Skipping count, accuracy, and performance score

YOLOv8 POSE INPUT

Each frame outputs 17 body keypoints in the form:

(x, y, confidence)

Keypoints used for skipping analysis:

Left & Right Ankle (jump detection)

Left & Right Knee

Left & Right Hip

Left & Right Shoulder

Left & Right Wrist (optional rope-hand motion)

Low-confidence frames are ignored.

WHAT DEFINES ONE SKIPPING JUMP

A single skip (jump) is defined as:

Both feet leave the ground

Ankles reach a vertical peak

Feet return to ground level

Mathematically:
A jump occurs when ankle Y-position rises above a threshold
and then returns below it.

CORE MOTION METRICS

4.1 Vertical Ankle Movement

For each frame:

Ankle_Y = average(Left_Ankle_Y, Right_Ankle_Y)

Ground reference is calculated as:

Ground_Y = median(Ankle_Y during standing frames)

JUMP DETECTION LOGIC

Jump UP condition:
Ankle_Y < Ground_Y − Jump_Threshold

Jump DOWN condition:
Ankle_Y ≥ Ground_Y

A jump is counted when:
UP → DOWN transition occurs.

METRICS AND HOW THEY ARE CALCULATED

JUMP COUNT

Each valid UP → DOWN cycle counts as 1 skip.

Total Skips = Number of detected jumps

JUMP HEIGHT (OPTIONAL QUALITY METRIC)

Jump height approximation:

Jump_Height = Ground_Y − minimum(Ankle_Y during jump)

Higher value → better clearance

TEMPO / SKIPPING SPEED

Time for one skip:

Jump_Duration = Jump_End_Time − Jump_Start_Time

Skipping frequency:

Skips_per_second = Total_Skips / Total_Time

TEMPO CONSISTENCY

Compute variance of jump durations:

Tempo_Variance = variance(Jump_Duration for all jumps)

Low variance indicates rhythmic skipping.

POSTURE / UPPER BODY STABILITY

Back angle:

Back_Angle = Shoulder – Hip – Knee

Deviation:

Back_Error = |Back_Angle − 180 degrees|

Large deviation indicates bending or fatigue.

KNEE BEND CONTROL

Knee angle:

Knee_Angle = Hip – Knee – Ankle

Excessive knee bend during skipping
indicates poor skipping efficiency.

ARM MOVEMENT (OPTIONAL)

Using wrist circular motion:

Wrist_Path_Length = total movement of wrists per jump

Helps detect rope rotation coordination.

SKIPPING ACCURACY (PHYSICAL ACCURACY)

A jump is considered correct if:

Both feet leave the ground

Jump height ≥ minimum threshold

No double bounce

Controlled landing

Accuracy calculation:

Accuracy = Correct_Jumps / Total_Jumps

Range:
0.0 → Poor skipping
1.0 → Perfect skipping

FINAL SKIPPING PERFORMANCE SCORE

All components are normalized between 0 and 1.

Final Score Formula:

Final_Score =
0.35 × Accuracy

0.20 × Tempo_Consistency_Score

0.20 × Jump_Height_Score

0.15 × Posture_Score

0.10 × Knee_Control_Score

Score Interpretation:
0.8 – 1.0 → Excellent skipping
0.6 – 0.8 → Good
0.4 – 0.6 → Average
< 0.4 → Poor

HOW YOLOv8 SOLVES SKIPPING EFFECTIVELY

Tracks ankle vertical movement precisely

Detects peak and landing events

Enables real-time jump counting

Provides stable posture & joint angle estimation

Works without rope detection

WHY THIS METHOD WORKS

No ML training required

Robust to lighting and backgrounds

Works from side or front views

Real-time and explainable

Sports-science aligned