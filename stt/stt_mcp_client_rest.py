import argparse
import os
import requests
import speech_recognition as sr
import json

LANGUAGE_OPTIONS = {
    "ko": ["ko-KR"],
    "en": ["en-US"],
    "both": ["ko-KR", "en-US"],
}
DEFAULT_LANGUAGE = os.getenv("STT_LANGUAGE", "ko")

def parse_args():
    parser = argparse.ArgumentParser(description="Voice command client for Gemini REST")
    parser.add_argument(
        "-l",
        "--language",
        choices=LANGUAGE_OPTIONS,
        default=DEFAULT_LANGUAGE,
        help=f"STT language: ko, en, or both (default: {DEFAULT_LANGUAGE})",
    )
    parser.add_argument("--timeout", type=float, default=15.0, help="Seconds to wait for speech to start")
    parser.add_argument("--phrase-time-limit", type=float, default=12.0, help="Maximum seconds for one command")
    parser.add_argument("--ambient-duration", type=float, default=0.8, help="Ambient noise calibration seconds")
    parser.add_argument("--pause-threshold", type=float, default=1.2, help="Silence seconds before a phrase ends")
    parser.add_argument("--energy-threshold", type=int, default=None, help="Fixed microphone energy threshold")
    parser.add_argument("--no-dynamic-energy", action="store_true", help="Disable dynamic energy threshold")
    return parser.parse_args()

# --- 사용자 설정 ---
# 1. ROS MCP 서버 정보 (화면의 주소 참고)
MCP_SERVER_URL = "ws://192.168.0.6:11311/ws" 
GEMINI_MODEL = "gemini-1.5-flash" # 안정적인 모델 사용
API_KEY = None

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

def configure_recognizer(recognizer, args):
    recognizer.pause_threshold = args.pause_threshold
    recognizer.dynamic_energy_threshold = not args.no_dynamic_energy
    if args.energy_threshold is not None:
        recognizer.energy_threshold = args.energy_threshold

def extract_google_result(result):
    if not result or not isinstance(result, dict):
        return None

    alternatives = result.get("alternative", [])
    if not alternatives:
        return None

    best = max(alternatives, key=lambda item: item.get("confidence", -1.0))
    text = best.get("transcript")
    if not text:
        return None

    return text, best.get("confidence")

def recognize_with_languages(recognizer, audio):
    results = []
    for language in LANGUAGES:
        try:
            if len(LANGUAGES) == 1:
                text = recognizer.recognize_google(audio, language=language)
                return text, language

            result = recognizer.recognize_google(audio, language=language, show_all=True)
            extracted = extract_google_result(result)
            if extracted:
                text, confidence = extracted
                results.append((text, language, confidence))
        except sr.UnknownValueError:
            continue

    if not results:
        raise sr.UnknownValueError()

    results_with_confidence = [result for result in results if result[2] is not None]
    if results_with_confidence:
        text, language, confidence = max(results_with_confidence, key=lambda result: result[2])
        print(f"✅ 인식 신뢰도: {confidence:.2f}")
        return text, language

    text, language, _ = results[0]
    print("⚠️  신뢰도 정보 없음: 첫 번째 인식 결과를 사용합니다.")
    return text, language

def get_voice_command(recognizer, args):
    with sr.Microphone() as source:
        print("\n" + "="*40)
        print(f"🎤 [대기 중] 마이크에 명령을 내리세요 ({', '.join(LANGUAGES)})...")
        recognizer.adjust_for_ambient_noise(source, duration=args.ambient_duration)
        try:
            audio = recognizer.listen(
                source,
                timeout=args.timeout,
                phrase_time_limit=args.phrase_time_limit,
            )
            print("⏳ 음성 처리 중...")
            text, language = recognize_with_languages(recognizer, audio)
            print(f"🗣️  인식된 명령 ({language}): \"{text}\"")
            return text
        except sr.WaitTimeoutError:
            print("timeout: 입력이 없어 대기 상태로 돌아갑니다.")
        except sr.UnknownValueError:
            print("warn: 음성을 이해하지 못했습니다.")
        except sr.RequestError:
            print("error: 인터넷 연결을 확인하세요.")
    return None

def main():
    global API_KEY

    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        print("❌ 오류: 'GEMINI_API_KEY' 환경 변수가 설정되지 않았습니다.")
        exit()

    print(f"🚀 클라이언트 시작 (ROS MCP: {MCP_SERVER_URL})")
    recognizer = sr.Recognizer()
    configure_recognizer(recognizer, args)
    
    while True:
        command_text = get_voice_command(recognizer, args)
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
    args = parse_args()
    LANGUAGES = LANGUAGE_OPTIONS[args.language]
    main()
