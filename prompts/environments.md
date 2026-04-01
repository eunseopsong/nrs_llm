# Environments

This document defines the coordinate conventions, unit standards, and default motion-control interpretation rules used when the AI agent converts natural-language instructions into safe robot actions.

## 1. Coordinate Frames (REP-103 Style)

- **base**: Global reference frame  
  - +X: Forward toward workspace  
  - +Y: Left  
  - +Z: Up  
- **tool0**: UR10 flange mounting plane  
- **tcp**: Tool Center Point (contact center of the polishing tool).  
  All motion commands are expressed in the `base` frame with respect to the `tcp`.  
- **camera_link**: Mounted RGB-D sensor (e.g., RealSense L515).  
  Even when perception uses `camera_link`, final motion commands are executed in the `base` frame.

## 2. Units and Conventions

- Length: **meters (m)**  
- Angles: **radians (rad)** (degrees automatically converted to rad)  
- Orientation: **quaternion {x, y, z, w}** (RPY converted internally)  
- Time: **seconds (s)**  

## 3. Default Interpretation of Verbal Inputs

When the user omits numeric values, default interpretations apply:

| Expression | Axis Direction (base) | Magnitude (m) |
|-------------|----------------------|---------------|
| forward | +X | — |
| backward | −X | — |
| left | −Y | — |
| right | +Y | — |
| up | +Z | — |
| down | −Z | — |

**Distance keywords:**
- “slightly”: 0.05  
- “a little”: 0.10  
- “a lot”: 0.20  

**Speed keywords (vel_scale 0–1):**
- “slowly”: 0.10  
- “normally”: 0.20  
- “quickly”: 0.50  

**Rotation keywords (rad):**
- “slightly”: 5° (≈0.0873)  
- “a little”: 10° (≈0.1745)  
- “a lot”: 30° (≈0.5236)  

## 4. Motion Interface

Absolute TCP motion in the base frame is executed via the `/go_to_pose` service (type `nrs_mcp2/srv/GoToPose`).

```yaml
target_frame: 'base'
pose:
  position: {x: ..., y: ..., z: ...}
  orientation: {x: ..., y: ..., z: ..., w: ...}
vel_scale: 0.20
acc_scale: 0.20
allowed_planning_time: 2.0
cartesian: true|false
eef_step: 0.005
jump_threshold: 0.0
plan_only: false
```
- cartesian=true: Cartesian linear motion

- cartesian=false: Joint-space motion

Default parameters remain unchanged unless explicitly modified.

## 5. Relative Motion (Nudge)
For “move a little left/right/up/down” type commands, the system computes an absolute target based on the current TCP pose.

Algorithm:

1. Obtain current TCP pose from /get_tcp_pose (type `nrs_mcp2/srv/GetTcpPose`)

2. Parse language into axis and distance

3. Apply workspace bounds

4. Add delta to position, keep orientation unchanged

5. Call /go_to_pose with cartesian=true

Example: “move left a little” → −Y, 0.10 m

## 6. Relative Rotation
For rotational commands around TCP axes (roll=X, pitch=Y, yaw=Z):

1. Identify intended axis and magnitude

2. Convert degrees → radians

3. Compose new quaternion from current orientation + delta rotation

4. Maintain position, change only orientation

5. Send to /go_to_pose

Example: “yaw 10 degrees left” → +Z 10°

## 7. Absolute Targets (Numeric Inputs)
When the user provides absolute coordinates or quaternion, use them directly but clamp within workspace limits.
If given in RPY, convert to quaternion via:

qx = sin(r/2)*cos(p/2)*cos(y/2) - cos(r/2)*sin(p/2)*sin(y/2)
qy = cos(r/2)*sin(p/2)*cos(y/2) + sin(r/2)*cos(p/2)*sin(y/2)
qz = cos(r/2)*cos(p/2)*sin(y/2) - sin(r/2)*sin(p/2)*cos(y/2)
qw = cos(r/2)*cos(p/2)*cos(y/2) + sin(r/2)*sin(p/2)*sin(y/2)

## 8. Tool and Contact Alignment
- The polishing tool is mounted on tool0, with TCP at the contact center.

- When approaching a surface, align the TCP −Z axis with the surface normal.

## 9. Safety and Workspace Limits
- Targets are restricted to a predefined workspace volume.

- Maximum per-command step: 0.25 m translation or 45° rotation.

- For short straight motions, use cartesian=true.

- Collision checking in MoveIt must remain enabled.

## 10. Example Commands
Natural Command	Interpreted Motion
“Move forward a little”	-> +X 0.10 m (cartesian)
“Go up 20 cm”	-> +Z 0.20 m
“Move right slightly”	-> +Y 0.05 m
“Back 5 cm slowly”	-> −X 0.05 m, vel_scale 0.10
“Rotate yaw 10° left”	-> +Z 10°

## 11. Summary for Agent Reasoning
- Control input: TCP target pose in base frame

- Perception input: Objects detected in camera frame → transformed to base frame via TF

- Ambiguous commands: Apply default values, confirm the computed goal, then call /go_to_pose

