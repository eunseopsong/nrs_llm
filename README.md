# nrs_llm

`nrs_llm` is an MCP server for ROS 2 environments. It connects to ROS through **rosbridge WebSocket** and exposes tools for:

- ROS 2 topic / service introspection
- topic publish / subscribe workflows
- service calls
- robot connectivity checks
- polishing log filtering and analysis
- polishing path regeneration
- TXT-based polishing path execution and logging

This repository is designed around the following environment assumptions:

- **Ubuntu 22.04**
- **ROS 2 Humble**
- **Python 3.10+**
- a separate ROS 2 workspace at `~/ros2_ws`
- **rosbridge_server** running on `127.0.0.1:9090`

This README is written so that a user can set up and run `nrs_llm` from scratch.

---

## 1. Recommended directory layout

The current codebase is easiest to run when you keep the following layout:

```bash
~/nrs_llm
~/ros2_ws
├── src
│   └── ... your ROS 2 packages
├── build
├── install
├── log
└── data
    └── ep
        ├── xyz.txt
        ├── vxyz.txt
        ├── fxyz.txt
        ├── rpy.txt
        ├── real_flat_filtered.txt
        ├── auto_logger.py
        ├── filter_logs_txt.py
        ├── polish_pipeline.py
        └── ...
```

If you move these paths, some parts of the polishing pipeline may fail unless you also update the corresponding paths in the code.

---

## 2. System requirements

Install the base system tools first.

### 2.1 Ubuntu packages

```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-colcon-common-extensions \
    git
```

### 2.2 ROS 2 Humble

This README assumes that **ROS 2 Humble is already installed** at:

```bash
/opt/ros/humble
```

Check it with:

```bash
test -f /opt/ros/humble/setup.bash && echo "ROS 2 Humble found" || echo "ROS 2 Humble missing"
```

If this prints `ROS 2 Humble missing`, install ROS 2 Humble first before continuing.

---

## 3. Clone the repository

Clone this repository into your home directory:

```bash
cd ~
git clone <YOUR_REPOSITORY_URL> nrs_llm
cd ~/nrs_llm
```

If the repository is already cloned, just move into it:

```bash
cd ~/nrs_llm
```

---

## 4. Create and activate the Python virtual environment

This project should be run inside a dedicated virtual environment.

Create the environment:

```bash
cd ~/nrs_llm
python3 -m venv env_llm
```

Activate it:

```bash
source ~/nrs_llm/env_llm/bin/activate
```

After activation, your terminal prompt should show something like:

```bash
(env_llm) user@host:~/nrs_llm$
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

To deactivate later:

```bash
deactivate
```

To activate again in a new terminal:

```bash
cd ~/nrs_llm
source env_llm/bin/activate
```

---

## 5. Install Python dependencies

Install the required Python packages inside `env_llm`.

### 5.1 Core packages

```bash
cd ~/nrs_llm
source env_llm/bin/activate

pip install \
    fastmcp \
    pillow \
    numpy \
    scipy \
    matplotlib \
    pandas \
    opencv-python \
    websocket-client
```

### 5.2 Why these packages are needed

- `fastmcp`: MCP server framework
- `pillow`: image handling
- `numpy`, `scipy`, `matplotlib`, `pandas`: filtering / analysis utilities
- `opencv-python`: required because `utils/websocket_manager.py` imports `cv2`
- `websocket-client`: required because `utils/websocket_manager.py` imports `websocket`

### 5.3 Verify imports

Run this check after installation:

```bash
cd ~/nrs_llm
source env_llm/bin/activate
python - <<'PY'
import cv2
import websocket
import numpy
import pandas
import scipy
import matplotlib
from PIL import Image
print("All required Python imports succeeded.")
PY
```

If this command succeeds, the Python environment is ready.

---

## 6. Prepare the ROS 2 workspace

This project assumes a ROS 2 workspace at `~/ros2_ws`.

Create it if needed:

```bash
mkdir -p ~/ros2_ws/src
```

Place your required ROS 2 packages into `~/ros2_ws/src`.

The current version assumes that the workspace includes the packages needed for your robot setup and polishing execution pipeline. In the previous version, `ur_custom_ik` and the executable `txt_ik_executor_force_patched` were used by the path execution flow.

---

## 7. Build the ROS 2 workspace

Build the workspace:

```bash
cd ~/ros2_ws
colcon build
```

Source the environment:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
```

To confirm that the workspace source file exists:

```bash
test -f ~/ros2_ws/install/setup.bash && echo "ROS workspace found" || echo "ROS workspace missing"
```

If the file is missing, the workspace has not been built successfully yet.

---

## 8. Install and run rosbridge

`nrs_llm` does **not** talk directly to ROS 2. It communicates through **rosbridge WebSocket**.

### 8.1 Install rosbridge if needed

If `rosbridge_server` is not installed yet:

```bash
sudo apt update
sudo apt install -y ros-humble-rosbridge-server
```

### 8.2 Run rosbridge

Open a new terminal and run:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

By default, rosbridge listens on:

```text
127.0.0.1:9090
```

### 8.3 Verify rosbridge is listening

In another terminal:

```bash
ss -ltnp | grep 9090
```

If rosbridge is running correctly, you should see a listener on port `9090`.

---

## 9. Verify the repository structure

Before connecting `nrs_llm` to Gemini CLI, confirm that these files exist:

```bash
test -f ~/nrs_llm/server.py && echo "server.py found" || echo "server.py missing"
test -f ~/ros2_ws/install/setup.bash && echo "workspace setup found" || echo "workspace setup missing"
test -f /opt/ros/humble/setup.bash && echo "ROS Humble setup found" || echo "ROS Humble setup missing"
test -x ~/nrs_llm/env_llm/bin/python && echo "venv python found" || echo "venv python missing"
```

All four checks should succeed.

---

## 10. Configure Gemini CLI MCP in `settings.json`

`nrs_llm` is intended to be launched by **Gemini CLI** as an MCP server using **stdio**.

That means:

- do **not** manually keep `python server.py` running in another terminal
- Gemini CLI should launch the server itself
- the config should source both ROS environments before starting `server.py`

### 10.1 Edit the Gemini CLI `settings.json`

Open the **same `settings.json` file that Gemini CLI is already reading for MCP configuration** and add the following server entry:

```json
{
  "mcpServers": {
    "ros-mcp": {
      "command": "/bin/bash",
      "args": [
        "-lc",
        "source /opt/ros/humble/setup.bash && source /home/eunseop/ros2_ws/install/setup.bash && cd /home/eunseop/nrs_llm && exec /home/eunseop/nrs_llm/env_llm/bin/python /home/eunseop/nrs_llm/server.py"
      ]
    }
  }
}
```

### 10.2 Important notes about this config

Replace paths if your username or directories are different.

For the current setup shown above:

- ROS 2 Humble source file: `/opt/ros/humble/setup.bash`
- ROS workspace source file: `/home/eunseop/ros2_ws/install/setup.bash`
- repository path: `/home/eunseop/nrs_llm`
- virtual environment Python: `/home/eunseop/nrs_llm/env_llm/bin/python`

### 10.3 Why `/bin/bash -lc` is used

This is important because it allows Gemini CLI to:

1. source ROS 2 Humble
2. source your ROS 2 workspace
3. change directory into the repository
4. run the correct virtual environment Python

Without this, the server may fail with missing ROS packages, missing Python modules, or broken relative paths.

---

## 11. Start Gemini CLI and verify the MCP server

Once `settings.json` is updated, start Gemini CLI from inside the repository environment:

```bash
cd ~/nrs_llm
source env_llm/bin/activate
gemini -y
```

Inside Gemini CLI, run:

```text
/mcp list
```

If everything is correct, you should see `ros-mcp` in the list with a status similar to:

```text
Ready
```

If the server is connected correctly, Gemini CLI should also show the list of available tools.

---

## 12. First recommended checks after connection

Once `/mcp list` shows `ros-mcp` as ready, test the server in this order:

1. `connect_to_robot`
2. `get_topics`
3. `get_services`
4. `get_topic_type`
5. `get_service_type`
6. `publish_once` or a read-only introspection tool

This helps distinguish between:

- MCP startup issues
- rosbridge connectivity issues
- ROS graph visibility issues
- robot-specific execution issues

---

## 13. Running the server manually for debugging

Even though Gemini CLI should launch the MCP server in normal use, manual execution is still useful for debugging.

### 13.1 Manual debug run

```bash
cd ~/nrs_llm
source env_llm/bin/activate
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
python ~/nrs_llm/server.py
```

### 13.2 Better debug check with stdout / stderr separation

```bash
timeout 5s /bin/bash -lc 'source /opt/ros/humble/setup.bash && source /home/eunseop/ros2_ws/install/setup.bash && cd /home/eunseop/nrs_llm && /home/eunseop/nrs_llm/env_llm/bin/python /home/eunseop/nrs_llm/server.py' >/tmp/ros_mcp_stdout.log 2>/tmp/ros_mcp_stderr.log

echo "===== STDOUT ====="
sed -n '1,80p' /tmp/ros_mcp_stdout.log
echo "===== STDERR ====="
sed -n '1,80p' /tmp/ros_mcp_stderr.log
```

This is useful for catching import errors such as missing `cv2` or missing `websocket` support.

---

## 14. Default paths used by the polishing pipeline

The current codebase assumes the following default paths for filtering / analysis / regeneration / execution:

### Filtering input

- `~/ros2_ws/data/ep/xyz.txt`
- `~/ros2_ws/data/ep/vxyz.txt`
- `~/ros2_ws/data/ep/fxyz.txt`
- `~/ros2_ws/data/ep/rpy.txt`

### Analysis input/output

- `~/ros2_ws/data/ep/vxyz_filtered.txt`
- `~/ros2_ws/data/ep/fxyz_filtered.txt`
- output directory: `~/ros2_ws/data/ep/polish_out_filtered`

### Regeneration

- input path: `~/ros2_ws/data/ep/real_flat_filtered.txt`
- removal map: `~/ros2_ws/data/ep/polish_out_filtered/removal_map.npz`
- output path: `~/ros2_ws/data/ep/real_flat_filtered_new2.txt`

### Path execution

- logger: `~/ros2_ws/data/ep/auto_logger.py`
- executor: `ros2 run ur_custom_ik txt_ik_executor_force_patched`

If any of these files or directories are missing, the corresponding pipeline stage may fail.

---

## 15. Common errors and fixes

### 15.1 `ModuleNotFoundError: No module named 'cv2'`

Cause:

- `opencv-python` is not installed in `env_llm`

Fix:

```bash
cd ~/nrs_llm
source env_llm/bin/activate
pip install opencv-python
```

---

### 15.2 `ModuleNotFoundError: No module named 'websocket'`

Cause:

- `websocket-client` is not installed in `env_llm`

Fix:

```bash
cd ~/nrs_llm
source env_llm/bin/activate
pip install websocket-client
```

Note: the import name is `websocket`, but the package you install is `websocket-client`.

---

### 15.3 `/mcp list` shows `Disconnected`

Common causes:

- Gemini CLI is not reading the `settings.json` file you edited
- the MCP server command is wrong
- the ROS environment is not sourced
- the virtual environment Python path is wrong
- `server.py` crashes at startup because of missing dependencies
- rosbridge is not running

Checklist:

```bash
test -x /home/eunseop/nrs_llm/env_llm/bin/python && echo OK
test -f /home/eunseop/nrs_llm/server.py && echo OK
test -f /opt/ros/humble/setup.bash && echo OK
test -f /home/eunseop/ros2_ws/install/setup.bash && echo OK
```

Then verify rosbridge:

```bash
ss -ltnp | grep 9090
```

Then run the 5-second debug command from Section 13.2.

---

### 15.4 `No executable found`

Cause:

- required ROS package was not built
- workspace was not sourced
- executable name is different from what the code expects

Fix:

```bash
cd ~/ros2_ws
colcon build
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 pkg executables ur_custom_ik
```

---

### 15.5 `No such file or directory`

Cause:

- missing files under `~/ros2_ws/data/ep`
- missing polishing scripts
- wrong path assumptions inside the code

Fix:

```bash
ls ~/ros2_ws/data/ep
```

Check that all required TXT files and scripts actually exist.

---

### 15.6 pip warns about unrelated packages such as `nrs-imitation`

If your virtual environment accidentally contains unrelated editable installs, `pip` may show dependency warnings that are not directly related to `nrs_llm`.

To check:

```bash
pip show nrs-imitation
```

If you do not want that package inside `env_llm`, remove it:

```bash
pip uninstall -y nrs-imitation
```

---

## 16. Full startup sequence (recommended)

Use the following sequence every time.

### Terminal 1: rosbridge

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

### Terminal 2: Gemini CLI

```bash
cd ~/nrs_llm
source env_llm/bin/activate
gemini -y
```

Inside Gemini CLI:

```text
/mcp list
```

Expected result:

- `ros-mcp` appears
- status is `Ready`
- the MCP tools are listed

---

## 17. Quick command summary

### One-time setup

```bash
cd ~
git clone <YOUR_REPOSITORY_URL> nrs_llm
cd ~/nrs_llm
python3 -m venv env_llm
source env_llm/bin/activate
python -m pip install --upgrade pip
pip install fastmcp pillow numpy scipy matplotlib pandas opencv-python websocket-client
```

### ROS workspace build

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build
```

### rosbridge run

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

### Gemini CLI run

```bash
cd ~/nrs_llm
source env_llm/bin/activate
gemini -y
```

---

## 18. Summary

To run `nrs_llm` successfully, you need all of the following:

1. ROS 2 Humble installed
2. a built ROS 2 workspace at `~/ros2_ws`
3. rosbridge running on port `9090`
4. the repository cloned at `~/nrs_llm`
5. the `env_llm` virtual environment created and activated
6. all required Python dependencies installed
7. Gemini CLI `settings.json` configured to launch `server.py` through `/bin/bash -lc`

If you follow this README exactly, you should be able to launch Gemini CLI, run `/mcp list`, and see `ros-mcp` in the `Ready` state.
