import pyautogui
import cv2
import numpy as np
import time
import random

def capture_screen_region(region):
    """지정된 영역의 스크린샷을 캡처합니다"""
    screenshot = pyautogui.screenshot(region=region)
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

def find_template_match(screen_img, template_img, threshold=0.8):
    """이미지 매칭을 수행합니다"""
    result = cv2.matchTemplate(screen_img, template_img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val > threshold

def random_delay():
    """1초에서 2초 사이의 랜덤한 시간을 반환합니다"""
    return random.uniform(1.0, 2.0)

def fishing_macro():
    # 감지할 영역 설정 (x, y, width, height)
    REGION = (100, 100, 300, 300)  # 실제 게임에 맞게 조정 필요
    
    # 템플릿 이미지 로드 (느낌표 이미지)
    template = cv2.imread('exclamation_mark.png')  # 실제 느낌표 이미지 파일 필요
    
    # 낚시 상태 추적
    is_fishing = False
    last_fish_time = 0
    
    try:
        while True:
            current_time = time.time()
            screen = capture_screen_region(REGION)
            
            if not is_fishing:
                # 랜덤 딜레이 후 낚시 시작
                time.sleep(random_delay())
                pyautogui.press('e')
                is_fishing = True
                print("낚시 시작...")
                time.sleep(0.5)  # 낚시 시작 후 잠시 대기
                
            elif is_fishing:
                # 느낌표 감지
                if find_template_match(screen, template):
                    # 자연스러운 반응 시간 추가 (0.3-0.7초 사이 랜덤 대기)
                    time.sleep(random.uniform(0.3, 0.7))
                    pyautogui.press('e')
                    print("물고기 낚음!")
                    is_fishing = False
                    last_fish_time = current_time
                    # 다음 낚시까지 랜덤 대기
                    time.sleep(random.uniform(1.5, 2.5))
                
                # 일정 시간 동안 물고기가 안 걸리면 다시 시작
                elif current_time - last_fish_time > 15:  # 15초 타임아웃
                    is_fishing = False
                    print("타임아웃 - 다시 시작")
                    time.sleep(random.uniform(1.0, 2.0))
            
            time.sleep(0.1)  # CPU 부하 감소
            
    except KeyboardInterrupt:
        print("매크로가 중지되었습니다.")

if __name__ == "__main__":
    print("3초 후 매크로가 시작됩니다...")
    print("중지하려면 Ctrl+C를 누르세요.")
    time.sleep(3)
    fishing_macro()