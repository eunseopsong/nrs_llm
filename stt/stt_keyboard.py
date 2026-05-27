import argparse
import os
import shutil
import speech_recognition as sr
import subprocess
import time

LANGUAGE_OPTIONS = {
    "ko": ["ko-KR"],
    "en": ["en-US"],
    "both": ["ko-KR", "en-US"],
}
DEFAULT_LANGUAGE = os.getenv("STT_LANGUAGE", "ko")

def parse_args():
    parser = argparse.ArgumentParser(description="Voice keyboard input")
    parser.add_argument(
        "-l",
        "--language",
        choices=LANGUAGE_OPTIONS,
        default=DEFAULT_LANGUAGE,
        help=f"STT language: ko, en, or both (default: {DEFAULT_LANGUAGE})",
    )
    parser.add_argument("--timeout", type=float, default=None, help="Seconds to wait for speech to start")
    parser.add_argument("--phrase-time-limit", type=float, default=12.0, help="Maximum seconds for one command")
    parser.add_argument("--ambient-duration", type=float, default=0.8, help="Ambient noise calibration seconds")
    parser.add_argument("--pause-threshold", type=float, default=1.2, help="Silence seconds before a phrase ends")
    parser.add_argument("--energy-threshold", type=int, default=None, help="Fixed microphone energy threshold")
    parser.add_argument("--no-dynamic-energy", action="store_true", help="Disable dynamic energy threshold")
    parser.add_argument(
        "--input-method",
        choices=("auto", "type", "paste"),
        default="auto",
        help="How to send recognized text to the active window (default: auto)",
    )
    parser.add_argument(
        "--paste-shortcut",
        choices=("ctrl-v", "ctrl-shift-v"),
        default="ctrl-shift-v",
        help="Paste shortcut used by the target app (default: ctrl-shift-v)",
    )
    parser.add_argument(
        "--submit-method",
        choices=("enter", "paste-newline", "none"),
        default="enter",
        help="How to submit recognized text after input (default: enter)",
    )
    parser.add_argument("--submit-delay", type=float, default=0.35, help="Seconds to wait before submit")
    parser.add_argument("--focus-delay", type=float, default=3.0, help="Seconds to wait before listening starts")
    return parser.parse_args()

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
        # 배경 소음 적응 (짧게 설정)
        recognizer.adjust_for_ambient_noise(source, duration=args.ambient_duration)
        print(f"\n🎤 [리스닝 중...] 언어: {', '.join(LANGUAGES)} / 'gemini -y' 창을 클릭해두세요!")
        
        try:
            # 음성 감지 (말이 끝날 때까지 대기)
            audio = recognizer.listen(
                source,
                timeout=args.timeout,
                phrase_time_limit=args.phrase_time_limit,
            )
            print("⏳ 변환 중...")
            
            # 텍스트로 변환
            text, language = recognize_with_languages(recognizer, audio)
            print(f"✅ 인식 언어: {language}")
            return text
            
        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            print("❌ 인식 실패 (다시 말씀해주세요)")
        except sr.RequestError:
            print("❌ 인터넷 연결 확인 필요")
    return None

def has_non_ascii(text):
    return any(ord(character) > 127 for character in text)

def set_clipboard_with_tkinter(text):
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    root.destroy()

def set_clipboard_with_command(text):
    if shutil.which("wl-copy"):
        subprocess.run(["wl-copy"], input=text, text=True, check=True)
        return
    if shutil.which("xclip"):
        subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True)
        return
    if shutil.which("xsel"):
        subprocess.run(["xsel", "--clipboard", "--input"], input=text, text=True, check=True)
        return
    raise RuntimeError("clipboard command not found")

def set_clipboard_text(text):
    errors = []
    for setter in (set_clipboard_with_command, set_clipboard_with_tkinter):
        try:
            setter(text)
            return
        except Exception as e:
            errors.append(str(e))
    raise RuntimeError("; ".join(errors))

def paste_text(keyboard, key, text, paste_shortcut):
    set_clipboard_text(text)
    time.sleep(0.05)
    if paste_shortcut == "ctrl-shift-v":
        with keyboard.pressed(key.ctrl):
            with keyboard.pressed(key.shift):
                keyboard.press("v")
                keyboard.release("v")
        return

    with keyboard.pressed(key.ctrl):
        keyboard.press("v")
        keyboard.release("v")

def send_text(keyboard, key, text, input_method):
    if input_method == "paste" or (input_method == "auto" and has_non_ascii(text)):
        paste_text(keyboard, key, text, args.paste_shortcut)
        return

    keyboard.type(text)

def submit_text(keyboard, key, submit_method):
    if submit_method == "none":
        return

    if submit_method == "paste-newline":
        paste_text(keyboard, key, "\n", args.paste_shortcut)
        return

    keyboard.press(key.enter)
    keyboard.release(key.enter)

def main():
    from pynput.keyboard import Controller, Key

    # 키보드 컨트롤러 생성
    keyboard = Controller()
    recognizer = sr.Recognizer()
    configure_recognizer(recognizer, args)

    print("="*40)
    print("⌨️  [보이스 키보드]가 시작되었습니다.")
    print("⚠️  주의: 이 스크립트는 인식된 말을 '현재 활성화된 창'에 타이핑합니다.")
    print(f"    {args.focus_delay}s 안에 'gemini -y'가 실행된 터미널을 클릭해서 활성화해 두세요.")
    print(f"    입력 방식: {args.input_method} / 붙여넣기: {args.paste_shortcut} / 제출 방식: {args.submit_method}")
    print("="*40)
    if args.focus_delay > 0:
        time.sleep(args.focus_delay)

    while True:
        text = get_voice_command(recognizer, args)
        
        if text:
            print(f"입력: {text}")
            
            # 1. 텍스트 입력
            try:
                send_text(keyboard, Key, text, args.input_method)
            except Exception as e:
                print(f"❌ 입력 실패: {e}")
                print("   한글 입력은 --input-method paste 또는 xclip/xsel/wl-copy 설치가 필요할 수 있습니다.")
                continue
            
            # 2. 잠시 대기 (붙여넣기/입력 반영 대기)
            time.sleep(args.submit_delay)
            
            # 3. 제출
            try:
                submit_text(keyboard, Key, args.submit_method)
            except Exception as e:
                print(f"❌ 제출 실패: {e}")

if __name__ == "__main__":
    args = parse_args()
    LANGUAGES = LANGUAGE_OPTIONS[args.language]
    main()
