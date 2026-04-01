# Predefined Waypoints for Scanning

This file lists the target TCP poses for scanning supported objects.
Gemini must use these values to construct the `pose` field (`geometry_msgs/msg/Pose`) in the `/go_to_pose` service request (Type: `nrs_mcp2/srv/GoToPose`).

**Format Reference:**
The values below map directly to the JSON structure:

```json
"pose": {
  "position": {"x": ..., "y": ..., "z": ...},
  "orientation": {"x": ..., "y": ..., "z": ..., "w": ...}
}

```

---

## Fender (7 waypoints):

position: {x: 0.386, y: -0.207, z: 0.656}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.471, y: -0.059, z: 0.656}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.557, y: 0.046, z: 0.656}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.628, y: 0.175, z: 0.656}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.496, y: 0.239, z: 0.656}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.476, y: 0.309, z: 0.656}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.369, y: 0.383, z: 0.656}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

## Lid (3 waypoints):

position: {x: 0.429, y: -0.044, z: 0.609}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.511, y: 0.064, z: 0.609}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.444, y: 0.260, z: 0.609}, orientation: {x: -0.167, y: 0.986, z: 0.017, w: -0.006}

## Propeller (3 waypoints):

position: {x: 0.429, y: -0.044, z: 0.609}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.511, y: 0.064, z: 0.609}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.444, y: 0.260, z: 0.609}, orientation: {x: -0.167, y: 0.986, z: 0.017, w: -0.006}

## Bonnet (3 waypoints):

position: {x: 0.429, y: -0.044, z: 0.609}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.511, y: 0.064, z: 0.609}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.444, y: 0.260, z: 0.609}, orientation: {x: -0.167, y: 0.986, z: 0.017, w: -0.006}

## Side Panel (3 waypoints):

position: {x: 0.429, y: -0.044, z: 0.609}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.511, y: 0.064, z: 0.609}, orientation: {x: -0.407, y: 0.913, z: -0.003, w: -0.001}

position: {x: 0.444, y: 0.260, z: 0.609}, orientation: {x: -0.167, y: 0.986, z: 0.017, w: -0.006}
