import os
import requests
import speech_recognition as sr
import json

# --- 사용자 설정 ---
# 1. API 키 설정 (또는 환경 변수 사용)
API_KEY = os.getenv("GEMINI_API_KEY") 
if not API_KEY:
    print("❌ 오류: 'GEMINI_API_KEY' 환경 변수가 설정되지 않았습니다.")
    exit()

# 2. ROS MCP 서버 정보 (화면의 주소 참고)
MCP_SERVER_URL = "ws://192.168.0.6:11311/ws" 
GEMINI_MODEL = "gemini-1.5-flash" # 안정적인 모델 사용
LANGUAGE = 'en-US'

# --- Gemini REST API 도구 정의 ---
# Gemini에게 "나는 이런 도구를 가지고 있어"라고 알려주는 정의입니다.
tools_payload = {
    "function_declarations": [
        {
            "name": "execute_joint_movement",
            "description": "Move the robot joints to specified target positions.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "joint_names": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "List of joint names (e.g. ['joint1'])"
                    },
                    "positions": {
                        "type": "ARRAY",
                        "items": {"type": "NUMBER"},
                        "description": "List of target positions in radians"
                    }
                },
                "required": ["joint_names", "positions"]
            }
        }
    ]
}

def call_gemini_rest(text):
    """SDK 대신 REST API를 사용하여 Gemini 호출"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": text}]
        }],
        "tools": [tools_payload] # 도구 정의 포함
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Gemini API 호출 오류: {e}")
        return None

def get_voice_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n" + "="*40)
        print(f"🎤 [대기 중] 마이크에 명령을 내리세요 ({LANGUAGE})...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5)
            print("⏳ 음성 처리 중...")
            text = r.recognize_google(audio, language=LANGUAGE)
            print(f"🗣️  인식된 명령: \"{text}\"")
            return text
        except sr.WaitTimeoutError:
            print("timeout: 입력이 없어 대기 상태로 돌아갑니다.")
        except sr.UnknownValueError:
            print("warn: 음성을 이해하지 못했습니다.")
        except sr.RequestError:
            print("error: 인터넷 연결을 확인하세요.")
    return None

def main():
    print(f"🚀 클라이언트 시작 (ROS MCP: {MCP_SERVER_URL})")
    
    while True:
        command_text = get_voice_command()
        if not command_text:
            continue

        # Gemini 호출
        result = call_gemini_rest(command_text)
        
        if not result:
            continue

        # 응답 분석
        try:
            candidates = result.get('candidates', [{}])
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])

            for part in parts:
                # 1. 함수 호출(Function Call)이 있는 경우
                if 'functionCall' in part:
                    fc = part['functionCall']
                    func_name = fc['name']
                    args = fc['args']
                    
                    print(f"\n✅ [Gemini] 도구 사용 요청 감지!")
                    print(f"   - 함수명: {func_name}")
                    print(f"   - 인자값: {args}")
                    
                    # NOTE: 여기에 실제 ROS MCP 서버로 JSON을 보내는 코드를 추가하면 로봇이 움직입니다.
                    # 현재는 화면 출력으로 확인만 합니다.
                    
                # 2. 일반 텍스트 응답인 경우
                elif 'text' in part:
                    print(f"\n💬 [Gemini] {part['text']}")

        except Exception as e:
            print(f"응답 처리 중 오류: {e}")

if __name__ == "__main__":
    main()