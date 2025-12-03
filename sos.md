CAMERA-ONLY SOS (SAFETY OVERRIDE SYSTEM)
FOR ATHLETIC TESTS USING YOLOv8 POSE

FILE NAME: camera_only_SOS_logic.txt

PURPOSE OF SOS SYSTEM

The SOS (Safety Override System) continuously monitors an athlete during
a physical fitness test using camera-only pose estimation.

The system immediately halts the test and raises a visible and audible
alert if unsafe or emergency conditions are detected.

This system is preventive, conservative, and explainable.

INPUT AVAILABLE TO THE SYSTEM

Camera-based data ONLY (no sensors):

YOLOv8 pose keypoints (17 body keypoints)

Body posture and angles

Joint movement over time

Center of mass motion

Frame-to-frame displacement

Time duration of postures

CORE SAFETY PRINCIPLE

IF THE ATHLETE LOSES SAFE BODY CONTROL OR CANNOT RECOVER VOLUNTARILY
→ IMMEDIATELY STOP THE TEST

SOS TRIGGER CONDITIONS (IMMEDIATE STOP)

If ANY ONE of the following conditions is true, SOS is triggered.

4.1 FALL OR COLLAPSE DETECTION

Logic:

Sudden vertical drop of hip

Rapid torso angle change

Athlete ends up on ground

No recovery within 2 seconds

Condition:

IF
hip_vertical_drop is sudden AND
torso_angle_change > 60 degrees AND
no standing recovery for > 2 seconds
THEN
SOS = TRUE (Reason: FALL OR COLLAPSE)

4.2 LOSS OF VOLUNTARY MOVEMENT

Logic:

Athlete visible but not moving

No joint angle change

No postural correction

Condition:

IF
body_visible == TRUE AND
joint_movement < minimal_threshold AND
duration > 3 seconds
THEN
SOS = TRUE (Reason: UNRESPONSIVE)

4.3 FAILURE TO RECOVER TO SAFE POSTURE

Logic:

Athlete cannot return to upright standing position

Condition:

IF
posture != upright AND
time_in_low_or_hunched_posture > 4 seconds
THEN
SOS = TRUE (Reason: FAILED RECOVERY)

4.4 SEVERE LOSS OF BALANCE

Logic:

Uncontrolled sway

Large, rapid center-of-mass shifts

Multiple corrective steps

Condition:

IF
center_of_mass_displacement > balance_threshold AND
oscillations > predefined_count
THEN
SOS = TRUE (Reason: BALANCE LOSS)

4.5 PROLONGED DISTRESS POSTURE

Logic:

Protective fatigue or distress posture

Detected Patterns:

Hands on knees

Excessive forward trunk bend

Head down

No attempt to resume test

Condition:

IF
trunk_flexion_angle > distress_angle AND
posture_duration > distress_time_limit
THEN
SOS = TRUE (Reason: DISTRESS POSTURE)

SECONDARY WARNING ESCALATION

Non-critical warning signs:

Erratic movement

Asymmetrical motion

Extremely slow execution

Repeated failed reps

Escalation rule:

IF
warning_events >= 2 within short duration
THEN
SOS = TRUE (Reason: ESCALATED WARNING)

MASTER SOS DECISION RULE

SOS is triggered if ANY ONE primary condition OR
secondary escalation condition is satisfied.

SYSTEM ACTIONS WHEN SOS IS TRIGGERED

IMMEDIATELY PERFORM ALL ACTIONS BELOW:

Stop rep counting and test logic

Freeze further motion analysis

Display full-screen RED SOS ALERT

Play continuous warning sound

Log timestamp and reason

Require manual supervisor reset

ON-SCREEN SOS ALERT SPECIFICATION

Visual Output:

Full screen overlay

RED background

Large white text:

"🚨 SOS ALERT 🚨"
"TEST HALTED FOR SAFETY"
"PLEASE ASSIST THE ATHLETE IMMEDIATELY"

Flashing effect (recommended)

AUDIO ALERT SPECIFICATION

Audio behavior:

Loud, repetitive alarm / beep sound

Volume at maximum safe level

Continues until manually stopped

Condition:

IF
SOS == TRUE
THEN
play_alert_sound(loop = TRUE)

PSEUDOCODE FOR ALERT DISPLAY AND SOUND

if SOS == True:
    display_fullscreen(color="RED")
    display_text("SOS ALERT - TEST HALTED")
    play_sound("alarm.wav", loop=True)
    lock_system_until_manual_reset()


SYSTEM RESET CONDITIONS

The system can ONLY resume when:

Supervisor manually confirms safety

SOS flag is cleared

Athlete is verified stable

LIMITATION DISCLAIMER (IMPORTANT)

This SOS system is based solely on visual observation.
It does NOT replace medical supervision or physiological monitoring.

ONE-LINE TECHNICAL SUMMARY

A camera-only SOS system halts athletic testing by detecting fall,
unresponsiveness, inability to recover, balance loss, or prolonged
distress posture using pose-based spatiotemporal rules.