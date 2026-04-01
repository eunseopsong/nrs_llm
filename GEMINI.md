# Gemini Project Profile for ROS-MCP Polishing Pipeline

You are working on a local robotics polishing pipeline on this laptop.

## 1. Source of truth
The real executable behavior is defined by the MCP tools exposed from `server.py`.

Treat `server.py` as the primary execution layer.
This file (`GEMINI.md`) is only a project instruction layer that helps choose the correct tools and interpret project-specific data correctly.

Do not prioritize older generic ROS workflows over the MCP tools if both are available.

---

## 2. Current local environment
Active practical environment:

- ROS 2 workspace: `~/ros2_ws`
- MCP project directory: `~/ros-mcp-server`
- Main robot execution node:
  - `ros2 run ur_custom_ik txt_ik_executor_force_patched`
- Logger:
  - `~/ros2_ws/data/ep/auto_logger.py`
- Filtering:
  - `~/ros2_ws/data/ep/filter_logs_txt.py`
- Analysis / regeneration:
  - `~/ros2_ws/data/ep/polish_pipeline.py`

Assume this environment by default unless the user explicitly says otherwise.

---

## 3. Primary MCP tools to prefer
When available from the connected MCP server, prefer these tools:

- `execute_polishing_path(txt_path, log_dir, timeout)`
  - Executes a polishing path and logs telemetry.

- `run_filtering_pipeline(...)`
  - Filters raw logs such as `xyz.txt`, `vxyz.txt`, `fxyz.txt`, `rpy.txt`.

- `run_analysis_pipeline(...)`
  - Runs polishing removal analysis and creates:
    - `summary.txt`
    - plots
    - `removal_map.npz`

- `run_regen_path(...)`
  - Regenerates a path from analysis results.

Default execution order for a full closed loop:
1. execute path
2. filter logs
3. analyze
4. regenerate path
5. report results

---

## 4. Important telemetry semantics
This project uses `/polish/sample` telemetry from the executor node.

Current data layout:

- `[0]` = time [s]
- `[1]` = line number
- `[2..4]` = `Xd` (target position)
- `[5..7]` = `Xcmd` (commanded position after admittance)
- `[8..10]` = `tcp_pos` (actual TCP position)
- `[11..13]` = tool z-axis in base frame
- `[14]` = `Fd_z`
- `[15]` = `Fn`
- `[16..18]` = `F_base`

Important interpretation rules:
- `Xd` is not the same as actual TCP position.
- For executed-path logging and spatial analysis, actual TCP position (`tcp_pos`) is the correct quantity.
- Do not confuse target path and executed path.
- `F_base` is already force expressed in base-related coordinates.

---

## 5. Unit convention
Downstream analysis expects the following conventions:

- `xyz.txt`: mm
- `vxyz.txt`: mm/s
- `fxyz.txt`: N
- `rpy.txt`: rad

Simulator/internal values may originate as:
- position: m
- velocity: m/s

Before reasoning about removal results, always verify:
- executed path is logged using actual TCP position
- m was converted to mm
- m/s was converted to mm/s

If `Fn` looks correct but removal is zero, suspect speed-unit mismatch first.

---

## 6. Current analysis policy
Default analysis preference for this project:

- `xyz`: raw/original
- `vxyz`: filtered
- `fxyz`: filtered
- `rpy`: raw/original

Reasoning:
- `xyz` should preserve spatial geometry as much as possible
- `vxyz` and `fxyz` are noise-sensitive and benefit from filtering
- `rpy_filtered` may degrade quality in this project, so raw `rpy` is currently preferred unless the user says otherwise

Do not automatically switch to fully filtered inputs unless the user asks for it.

---

## 7. Troubleshooting order
When the pipeline behaves incorrectly, use this order:

1. confirm the execution node actually ran successfully
2. confirm raw logs were newly generated
3. confirm logger saved actual TCP position, not target position
4. confirm unit consistency
5. run filtering
6. run analysis
7. inspect `summary.txt` and plots
8. run regeneration only after analysis results are meaningful

Do not jump to threshold tuning first if units or logging semantics are not confirmed.

---

## 8. Guidance style for this project
When helping with this project:

- prioritize concrete local behavior over generic ROS advice
- distinguish clearly between:
  - confirmed facts from code/logs
  - hypotheses
- prefer minimal and reversible code edits
- do not assume older project notes are still valid
- preserve the user’s current validated workflow when possible

---

## 9. Legacy note
Older project instructions may mention:

- `~/dev_ws`
- `/run_command`
- `/go_to_pose`
- `terminator`
- `nrs_mcp2`
- `test_ik_control`

Treat those as legacy unless the user explicitly says that environment is currently active.
