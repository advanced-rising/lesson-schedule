# pip install pytesseract pillow pyautogui schedule opencv-python numpy

# Tesseract 경로 설정 (Windows에서 필요)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# https://github.com/tesseract-ocr/tessdata

import pytesseract
from PIL import ImageGrab, Image
import pyautogui
import time
import schedule
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import logging
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reservation.log'),
        logging.StreamHandler()
    ]
)

class RegionSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("골프 예약 영역 선택")
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-topmost', True)
        
        # 전체 화면 크기
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 초기 창 크기 설정
        self.root.geometry(f"400x600+100+100")
        
        self.frame = ttk.Frame(self.root, padding="3")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 컨트롤 버튼들
        self.btn_confirm = ttk.Button(self.frame, text="영역 확정", command=self.confirm_region)
        self.btn_confirm.grid(row=0, column=0, padx=5, pady=5)
        
        # 위치 정보 표시
        self.position_label = ttk.Label(self.frame, text="위치: ")
        self.position_label.grid(row=1, column=0, padx=5, pady=5)
        
        # 도움말
        help_text = """
        사용 방법:
        1. 이 창을 앱플레이어의 예약 화면 영역에 맞게 조절하세요
        2. 창이 예약 버튼들을 모두 포함하도록 하세요
        3. '영역 확정' 버튼을 클릭하세요
        """
        self.help_label = ttk.Label(self.frame, text=help_text, wraplength=350)
        self.help_label.grid(row=2, column=0, padx=5, pady=5)
        
        self.root.bind('<Configure>', self.on_window_configure)
        self.selected_region = None
        
    def on_window_configure(self, event):
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        self.position_label.config(text=f"위치: x={x}, y={y}, w={width}, h={height}")
        
    def confirm_region(self):
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        self.selected_region = (x, y, x + width, y + height)
        self.root.destroy()
        
    def get_region(self):
        self.root.mainloop()
        return self.selected_region

class GolfReservation:
    def __init__(self):
        self.app_region = None
        self.target_start_time = 20  # 목표 시작 시간 (24시간 형식)
        self.target_end_time = 22    # 목표 종료 시간 (24시간 형식)
        
    def capture_screen(self, region=None):
        """화면 캡처"""
        try:
            screenshot = ImageGrab.grab(bbox=region)
            return screenshot
        except Exception as e:
            logging.error(f"화면 캡처 실패: {str(e)}")
            return None

    def extract_text_from_image(self, image):
        """이미지에서 텍스트 추출"""
        try:
            text = pytesseract.image_to_string(image, lang='kor')
            return text.strip()
        except Exception as e:
            logging.error(f"텍스트 추출 실패: {str(e)}")
            return ""

    def find_text_location(self, image, search_text):
        """이미지에서 특정 텍스트의 위치를 찾는 함수"""
        try:
            data = pytesseract.image_to_data(image, lang='kor', output_type=pytesseract.Output.DICT)
            
            for i, text in enumerate(data['text']):
                if search_text in text:
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    return (x + w//2, y + h//2)
            return None
        except Exception as e:
            logging.error(f"텍스트 위치 찾기 실패: {str(e)}")
            return None

    def click_text(self, region, text):
        """특정 영역에서 텍스트를 찾아 클릭"""
        try:
            screenshot = self.capture_screen(region)
            if screenshot is None:
                return False
                
            location = self.find_text_location(screenshot, text)
            if location:
                x, y = location
                click_x = region[0] + x
                click_y = region[1] + y
                pyautogui.click(click_x, click_y)
                logging.info(f"클릭 성공: {text} at ({click_x}, {click_y})")
                return True
            return False
        except Exception as e:
            logging.error(f"텍스트 클릭 실패: {str(e)}")
            return False

    def is_time_in_range(self, target_time):
        """시간이 목표 범위 안에 있는지 확인"""
        target_hour = target_time.hour
        return self.target_start_time <= target_hour <= self.target_end_time

    def refresh_app(self):
        """앱 새로고침"""
        try:
            pyautogui.hotkey('f5')
            logging.info("앱 새로고침 완료")
            time.sleep(5)
        except Exception as e:
            logging.error(f"앱 새로고침 실패: {str(e)}")

    def check_reservation(self):
        """예약 가능 시간대 확인 및 예약 시도"""
        if self.app_region is None:
            logging.error("앱 영역이 설정되지 않았습니다.")
            return False

        try:
            screenshot = self.capture_screen(self.app_region)
            if screenshot is None:
                return False

            text = self.extract_text_from_image(screenshot)
            now = datetime.now()

            for line in text.splitlines():
                if "예약" in line:
                    try:
                        time_str = line.split("예약")[0].strip()
                        reservation_time = datetime.strptime(time_str, "%H:%M").replace(
                            year=now.year, month=now.month, day=now.day)
                        
                        if self.is_time_in_range(reservation_time):
                            logging.info(f"예약 가능 시간대 발견: {time_str}")
                            
                            if self.click_text(self.app_region, time_str):
                                time.sleep(2)
                                
                                # 모달 영역 계산
                                modal_x = self.app_region[0] + (self.app_region[2] - self.app_region[0])//4
                                modal_y = self.app_region[1] + (self.app_region[3] - self.app_region[1])//4
                                modal_w = (self.app_region[2] - self.app_region[0])//2
                                modal_h = (self.app_region[3] - self.app_region[1])//2
                                modal_region = (modal_x, modal_y, modal_x + modal_w, modal_y + modal_h)
                                
                                if self.click_text(modal_region, "확인"):
                                    logging.info("예약 완료!")
                                    return True
                    except ValueError:
                        continue
            
            logging.info("예약 가능한 시간대가 없습니다.")
            return False
            
        except Exception as e:
            logging.error(f"예약 확인 중 오류 발생: {str(e)}")
            return False

    def job(self):
        """주기적으로 실행할 작업"""
        self.refresh_app()
        if self.check_reservation():
            logging.info("예약 성공! 프로그램을 종료합니다.")
            return True
        return False

    def run(self):
        """메인 실행 함수"""
        try:
            # 영역 선택
            selector = RegionSelector()
            logging.info("앱 영역을 선택해주세요.")
            self.app_region = selector.get_region()
            
            if self.app_region is None:
                logging.error("영역이 선택되지 않았습니다.")
                return
            
            logging.info(f"선택된 영역: {self.app_region}")
            
            # 스케줄러 설정
            schedule.every(5).minutes.do(self.job)
            
            # 첫 실행
            if self.job():
                return
            
            # 메인 루프
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            logging.info("프로그램이 사용자에 의해 종료되었습니다.")
        except Exception as e:
            logging.error(f"프로그램 실행 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    # Tesseract 경로 설정 (Windows의 경우)
    if os.name == 'nt':  # Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    reservation = GolfReservation()
    reservation.run()