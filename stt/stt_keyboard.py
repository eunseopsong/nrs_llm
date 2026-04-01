import speech_recognition as sr
from pynput.keyboard import Controller, Key
import time

# 키보드 컨트롤러 생성
keyboard = Controller()
LANGUAGE = 'en-US' # 명령은 영어로

def get_voice_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        # 배경 소음 적응 (짧게 설정)
        r.adjust_for_ambient_noise(source, duration=0.5)
        print("\n🎤 [리스닝 중...] 'gemini -y' 창을 클릭해두세요!")
        
        try:
            # 음성 감지 (말이 끝날 때까지 대기)
            audio = r.listen(source, timeout=None)
            print("⏳ 변환 중...")
            
            # 텍스트로 변환
            text = r.recognize_google(audio, language=LANGUAGE)
            return text
            
        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            print("❌ 인식 실패 (다시 말씀해주세요)")
        except sr.RequestError:
            print("❌ 인터넷 연결 확인 필요")
    return None

def main():
    print("="*40)
    print("⌨️  [보이스 키보드]가 시작되었습니다.")
    print("⚠️  주의: 이 스크립트는 인식된 말을 '현재 활성화된 창'에 타이핑합니다.")
    print("    반드시 'gemini -y'가 실행된 터미널을 클릭해서 활성화해 두세요!")
    print("="*40)

    while True:
        text = get_voice_command()
        
        if text:
            print(f"입력: {text}")
            
            # 1. 텍스트 타이핑
            keyboard.type(text)
            
            # 2. 잠시 대기 (입력 씹힘 방지)
            time.sleep(0.1)
            
            # 3. 엔터키 입력
            keyboard.press(Key.enter)
            keyboard.release(Key.enter)

if __name__ == "__main__":
    main()