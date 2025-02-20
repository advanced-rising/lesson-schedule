import pyautogui
import cv2
import numpy as np
import time
import random
import tkinter as tk
from threading import Thread
import threading
import keyboard
from PIL import ImageGrab, Image, ImageTk

def capture_screen_region(region):
    """지정된 영역의 스크린샷을 캡처합니다"""
    screenshot = pyautogui.screenshot(region=region)
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

def find_template_match(screen_img, template_img, threshold=None):
    """이미지 매칭을 수행하고 매칭 위치와 정확도를 반환합니다"""
    if threshold is None:
        threshold = self.threshold
        
    try:
        # 이미지 전처리
        screen_gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
        
        # 이미지 밝기 향상
        screen_gray = cv2.equalizeHist(screen_gray)
        template_gray = cv2.equalizeHist(template_gray)
        
        # 노이즈 제거
        screen_gray = cv2.GaussianBlur(screen_gray, (3, 3), 0)
        template_gray = cv2.GaussianBlur(template_gray, (3, 3), 0)
        
        # 여러 매칭 방법 시도
        methods = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]
        max_confidence = 0
        
        for method in methods:
            result = cv2.matchTemplate(screen_gray, template_gray, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            max_confidence = max(max_confidence, max_val)
            
            if max_val > threshold:
                # 디버깅을 위한 매칭 결과 출력
                print(f"매칭 발견: 방법={method}, 정확도={max_val:.3f}")
                return True, max_val
        
        # 디버깅을 위한 매칭 실패 정보 출력
        print(f"매칭 실패: 최대 정확도={max_confidence:.3f}, 임계값={threshold}")
        return False, max_confidence
            
    except Exception as e:
        print(f"템플릿 매칭 오류: {e}")
        return False, 0.0

def random_delay():
    """1초에서 2초 사이의 랜덤한 시간을 반환합니다"""
    return random.uniform(1.0, 2.0)

class FishingBot:
    def __init__(self):
        self.is_running = False
        self.fishing_thread = None
        self.templates = []  # 여러 템플릿 저장용 리스트
        
        # 여러 템플릿 이미지 로드 시도
        template_files = ['exclamation_mark.png', 'exclamation_mark2.png']
        for file in template_files:
            try:
                template = cv2.imread(file)
                if template is not None:
                    self.templates.append(template)
                    print(f"{file} 로드 성공")
                else:
                    print(f"{file} 로드 실패")
            except Exception as e:
                print(f"{file} 로드 오류: {e}")
        
        if not self.templates:
            print("경고: 사용 가능한 템플릿 이미지가 없습니다")
        
        # 메인 창 설정
        self.root = tk.Tk()
        self.root.title("낚시 매크로")
        self.root.geometry("300x150")
        
        # 투명 오버레이 창 설정
        self.overlay = tk.Toplevel(self.root)
        self.overlay.geometry("400x400")
        self.overlay.attributes('-alpha', 1.0)  # 완전 투명으로 변경
        self.overlay.attributes('-topmost', True)
        self.overlay.attributes('-transparentcolor', 'white')  # 배경색을 투명하게
        
        # 캔버스 생성
        self.canvas = tk.Canvas(self.overlay, width=400, height=400, 
                              bg='white',  # 배경을 투명하게 만들 색
                              highlightthickness=0)  # 캔버스 테두리 제거
        self.canvas.pack(fill='both', expand=True)
        
        # 테두리 그리기
        self.canvas.create_rectangle(2, 2, 398, 398,  # 여백 2픽셀
                                   outline='green',    # 테두리 색
                                   width=4)           # 테두리 두께
        
        # 오버레이 창 드래그 가능하도록 설정
        self.overlay.bind('<Button-1>', self.start_move)
        self.overlay.bind('<B1-Motion>', self.on_move)
        
        # 시작/중지 버튼
        self.toggle_button = tk.Button(self.root, text="시작", command=self.toggle_fishing)
        self.toggle_button.pack(pady=10)
        
        # 상태 레이블
        self.status_label = tk.Label(self.root, text="준비됨")
        self.status_label.pack(pady=10)
        
        # 템플릿 매칭 설정
        self.threshold = 0.6
        
        # 템플릿 이미지가 없으면 버튼 비활성화
        if not self.templates:
            self.toggle_button.config(state='disabled')
            self.status_label.config(text="템플릿 이미지 필요!")

    def start_move(self, event):
        """오버레이 창 이동 시작"""
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        """오버레이 창 이동"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.overlay.winfo_x() + deltax
        y = self.overlay.winfo_y() + deltay
        self.overlay.geometry(f"+{x}+{y}")
    
    def get_region(self):
        """현재 오버레이 창의 위치와 크기 반환"""
        x = self.overlay.winfo_x()
        y = self.overlay.winfo_y()
        return (x, y, 400, 400)
    
    def find_template_match(self, screen_img, threshold=None):
        """모든 템플릿에 대해 이미지 매칭을 수행하고 최고 정확도를 반환합니다"""
        if threshold is None:
            threshold = self.threshold
            
        try:
            # 이미지 전처리
            screen_gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
            screen_gray = cv2.equalizeHist(screen_gray)
            screen_gray = cv2.GaussianBlur(screen_gray, (3, 3), 0)
            
            max_confidence = 0
            best_template = None
            
            # 각 템플릿에 대해 매칭 시도
            for template in self.templates:
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                template_gray = cv2.equalizeHist(template_gray)
                template_gray = cv2.GaussianBlur(template_gray, (3, 3), 0)
                
                methods = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]
                
                for method in methods:
                    result = cv2.matchTemplate(screen_gray, template_gray, method)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val > max_confidence:
                        max_confidence = max_val
                        best_template = template
                    
                    if max_val > threshold:
                        print(f"매칭 발견: 정확도={max_val:.3f}")
                        return True, max_val
            
            print(f"매칭 실패: 최대 정확도={max_confidence:.3f}, 임계값={threshold}")
            return False, max_confidence
            
        except Exception as e:
            print(f"템플릿 매칭 오류: {e}")
            return False, 0.0

    def run_fishing_macro(self):
        is_fishing = False
        last_fish_time = 0
        
        try:
            while self.is_running:
                region = self.get_region()
                screen = capture_screen_region(region)
                
                if not is_fishing:
                    keyboard.press_and_release('e')
                    is_fishing = True
                    self.status_label.config(text="낚시 시작...")
                    time.sleep(1.5)
                    last_fish_time = time.time()
                    
                elif is_fishing:
                    matched, confidence = self.find_template_match(screen, threshold=0.5)
                    
                    if matched:
                        time.sleep(random.uniform(0.2, 0.4))
                        keyboard.press_and_release('e')
                        self.status_label.config(text=f"물고기 낚음! (정확도: {confidence:.3f})")
                        is_fishing = False
                        next_delay = random.uniform(1.0, 5.0)
                        time.sleep(next_delay)
                    
                    elif time.time() - last_fish_time > 20:
                        is_fishing = False
                        self.status_label.config(text="타임아웃 - 다시 시작")
                        time.sleep(random.uniform(1.0, 2.0))
                
                time.sleep(0.1)
                
        except Exception as e:
            print(f"오류 발생: {e}")
            self.status_label.config(text=f"오류: {str(e)}")
            self.is_running = False
            self.toggle_button.config(text="시작")

    def toggle_fishing(self):
        if not self.templates:
            self.status_label.config(text="템플릿 이미지가 필요합니다!")
            return
            
        if not self.is_running:
            self.is_running = True
            self.toggle_button.config(text="중지")
            self.status_label.config(text="낚시 중...")
            self.fishing_thread = Thread(target=self.run_fishing_macro)
            self.fishing_thread.daemon = True
            self.fishing_thread.start()
        else:
            self.is_running = False
            self.toggle_button.config(text="시작")
            self.status_label.config(text="대기 중...")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    bot = FishingBot()
    bot.run()