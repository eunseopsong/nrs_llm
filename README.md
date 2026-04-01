# ros-mcp-server

ROS 2 환경에서 rosbridge를 통해 토픽, 서비스, 메시지 구조를 조회하고,  
추가적으로 폴리싱 데이터의 필터링 / 분석 / 경로 재생성 / 경로 실행까지 수행할 수 있는 MCP 서버입니다.

이 프로젝트는 현재 **Ubuntu + ROS 2 + rosbridge + 별도 ROS workspace(`~/ros2_ws`)** 환경을 기준으로 구성되어 있습니다.  
따라서 다른 환경에서 실행할 경우, 아래의 디렉토리 구조와 ROS 패키지 구성을 맞추는 것이 중요합니다.

---

## Features

- rosbridge를 통한 ROS 2 topic / service introspection
- topic subscribe / publish
- service call
- 네트워크 진단 (`ping_robot`, `connect_to_robot`)
- raw polishing log filtering
- polishing analysis
- regeneration path 생성
- txt 기반 polishing path 실행 및 자동 로깅

---

## Recommended Environment

- Ubuntu 22.04
- ROS 2 Humble
- Python 3.10+
- `rosbridge_server`
- `colcon` build 가능한 ROS 2 workspace

---

## Assumptions in the Current Version

현재 버전은 다음 환경을 전제로 작성되어 있습니다.

- rosbridge WebSocket 기본 주소: `127.0.0.1:9090`
- ROS workspace 경로: `~/ros2_ws`
- 데이터 경로: `~/ros2_ws/data/ep`
- 가공 실행 패키지: `ur_custom_ik`
- 실행 노드: `txt_ik_executor_force_patched`

즉, 실행 환경에서도 가능하면 동일한 경로 구조를 유지하는 것을 권장합니다.

---

## Recommended Directory Layout

```bash
~/ros-mcp-server
~/ros2_ws
├── src
│   └── ... (ROS 2 packages, including ur_custom_ik)
├── install
├── build
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
````

---

## Setup

### 1. Clone the repository

```bash id="xz557q"
cd ~
git clone <REPOSITORY_URL> ros-mcp-server
```

### 2. Prepare the ROS 2 workspace

```bash id="xcf1s5"
cd ~
mkdir -p ros2_ws/src
```

필요한 ROS 2 패키지들(예: `ur_custom_ik`)을 `~/ros2_ws/src` 아래에 배치합니다.

---

### 3. Build the ROS workspace

```bash id="xwlrxq"
cd ~/ros2_ws
colcon build
source install/setup.bash
```

매 터미널마다 아래 source를 수행하는 것을 권장합니다.

```bash id="p7cwx6"
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
```

---

### 4. Install Python dependencies

```bash id="7gbis9"
cd ~/ros-mcp-server
pip install fastmcp pillow
```

추가적으로 데이터 처리 스크립트에 따라 다음 패키지가 필요할 수 있습니다.

```bash id="9caum5"
pip install numpy scipy matplotlib pandas
```

가능하다면 `requirements.txt`를 구성한 뒤 다음 방식으로 설치하는 것을 권장합니다.

```bash id="mcjlwm"
pip install -r requirements.txt
```

---

## Running rosbridge

이 서버는 ROS 2와 직접 연결되지 않고 **rosbridge WebSocket**을 통해 통신합니다.
따라서 먼저 rosbridge를 실행해야 합니다.

```bash id="v10rdq"
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

기본 포트는 `9090`입니다.

정상 실행 여부는 다음으로 확인할 수 있습니다.

```bash id="t7g3ft"
ss -ltnp | grep 9090
```

---

## Running the MCP Server

기본적으로 `stdio` transport를 사용합니다.

```bash id="ffxsvs"
cd ~/ros-mcp-server
python3 server.py
```

환경변수로 transport를 바꾸고 싶다면 예를 들어:

```bash id="m7em8a"
export MCP_TRANSPORT=streamable-http
export MCP_HOST=127.0.0.1
export MCP_PORT=9000
python3 server.py
```

---

## Pre-run Checklist

실행 전에 아래 항목을 확인하십시오.

* [ ] `~/ros2_ws`가 존재하는가
* [ ] `~/ros2_ws/install/setup.bash`가 생성되었는가
* [ ] `ur_custom_ik` 패키지가 빌드되었는가
* [ ] `ros2 run ur_custom_ik txt_ik_executor_force_patched`가 가능한가
* [ ] `~/ros2_ws/data/ep` 아래에 필요한 txt / python 스크립트가 존재하는가
* [ ] rosbridge가 `127.0.0.1:9090`에서 실행 중인가

---

## Recommended First Tests

가공 실행 전에 아래 순서로 먼저 테스트하는 것을 권장합니다.

1. `connect_to_robot()`
2. `get_topics()`
3. `get_services()`
4. `get_topic_type('/your_topic')`
5. `subscribe_once(...)`

이 단계에서 실패하면 rosbridge 또는 ROS 환경 문제일 가능성이 큽니다.

---

## Default Paths Used by the Data Pipeline

현재 서버 코드는 다음 경로들을 기본값으로 사용합니다.

### Filtering

* `~/ros2_ws/data/ep/xyz.txt`
* `~/ros2_ws/data/ep/vxyz.txt`
* `~/ros2_ws/data/ep/fxyz.txt`
* `~/ros2_ws/data/ep/rpy.txt`

### Analysis

* `~/ros2_ws/data/ep/vxyz_filtered.txt`
* `~/ros2_ws/data/ep/fxyz_filtered.txt`
* 결과 디렉토리: `~/ros2_ws/data/ep/polish_out_filtered`

### Regeneration

* 입력 경로: `~/ros2_ws/data/ep/real_flat_filtered.txt`
* removal map: `~/ros2_ws/data/ep/polish_out_filtered/removal_map.npz`
* 출력 경로: `~/ros2_ws/data/ep/real_flat_filtered_new2.txt`

### Path Execution

* logger: `~/ros2_ws/data/ep/auto_logger.py`
* executor: `ros2 run ur_custom_ik txt_ik_executor_force_patched`

즉, 위 경로들 중 하나라도 없으면 실행이 실패할 수 있습니다.

---

## Common Errors

### 1) `No executable found`

원인:

* `ur_custom_ik`가 빌드되지 않음
* `source ~/ros2_ws/install/setup.bash`를 안 함
* 실행 파일 이름이 다름

해결:

```bash id="xj0s6n"
cd ~/ros2_ws
colcon build
source install/setup.bash
ros2 pkg executables ur_custom_ik
```

---

### 2) `No such file or directory`

원인:

* `~/ros2_ws/data/ep/...` 경로가 없음
* txt / python 스크립트가 누락됨

해결:

```bash id="6he3fh"
ls ~/ros2_ws/data/ep
```

필요한 파일이 모두 존재하는지 확인하십시오.

---

### 3) topic / service 조회 실패

원인:

* rosbridge 미실행
* 9090 포트 문제
* ROS 환경 source 안 됨

해결:

```bash id="i0gbkv"
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

---

### 4) filtering / analysis만 실패

원인:

* `filter_logs_txt.py`, `polish_pipeline.py` 누락
* Python 패키지 미설치
* 입력 txt 형식 불일치

해결:

* 스크립트 존재 여부 확인
* `numpy`, `scipy`, `matplotlib`, `pandas` 설치 여부 확인
* 입력 파일 형식을 직접 점검

---

## Notes

현재 버전은 경로가 비교적 고정된 형태로 구성되어 있으므로,
가장 안정적인 실행 방법은 아래 항목을 동일하게 유지하는 것입니다.

* 저장소 위치: `~/ros-mcp-server`
* ROS workspace 위치: `~/ros2_ws`
* 데이터 위치: `~/ros2_ws/data/ep`
* rosbridge 포트: `9090`

즉, 코드를 수정하기보다는 환경 구조를 먼저 맞추는 방식이 가장 간단합니다.

---

## Future Improvements

향후 다음과 같은 개선을 권장합니다.

* `~/ros2_ws` 하드코딩 제거
* 환경변수 기반 workspace path 지정
* `requirements.txt` 정리
* 입력 파일 존재 여부 검사 추가
* 샘플 입력 파일 제공
* 데이터 형식 문서화

---

## Summary

이 프로젝트를 실행하려면 다음 4가지가 핵심입니다.

1. ROS 2 workspace가 정상적으로 빌드되어 있을 것
2. rosbridge가 실행 중일 것
3. `~/ros2_ws/data/ep` 경로와 관련 스크립트/데이터가 존재할 것
4. `ur_custom_ik` 패키지와 executor가 정상 실행될 것

현재 버전은 환경 재현형 구성에 가깝기 때문에,
동일한 폴더 구조를 유지하는 것이 가장 안정적입니다.

이제 원하면 다음으로  
**더 짧고 GitHub 느낌 나는 최종 README 버전**으로 한 번 더 압축해줄게.
```
