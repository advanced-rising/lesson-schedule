import pytesseract
from PIL import ImageGrab, Image
import pyautogui
import time
import schedule
from datetime import datetime
import numpy as np
import logging
import os
import cv2

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reservation.log'),
        logging.StreamHandler()
    ]
)

class GolfReservation:
    def __init__(self):
        self.app_region = None
        self.target_start_time = 20  # 목표 시작 시간 (24시간 형식)
        self.target_end_time = 22    # 목표 종료 시간 (24시간 형식)
        self.drag_distance = 200  # 끌어당길 거리 (픽셀)
        self.current_reservation = None  # 현재 예약된 시간 저장
        
    def find_app_region(self):
        """앱플레이어 영역 자동 감지"""
        try:
            # 전체 화면 캡처
            screenshot = ImageGrab.grab()
            screenshot_np = np.array(screenshot)
            
            # 이미지를 그레이스케일로 변환
            gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
            
            # OCR로 특정 텍스트 찾기 ("바로입장", "타석 색상안내" 등)
            data = pytesseract.image_to_data(gray, lang='kor', output_type=pytesseract.Output.DICT)
            
            target_texts = ["바로입장", "타석", "색상안내", "예약"]
            found_regions = []
            
            for i, text in enumerate(data['text']):
                if any(target in text for target in target_texts):
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    found_regions.append((x, y, w, h))
            
            if found_regions:
                # 발견된 모든 영역을 포함하는 경계 상자 계산
                min_x = min(r[0] for r in found_regions)
                min_y = min(r[1] for r in found_regions)
                max_x = max(r[0] + r[2] for r in found_regions)
                max_y = max(r[1] + r[3] for r in found_regions)
                
                # 여백 추가
                padding = 50
                screen_width, screen_height = screenshot.size
                
                app_region = (
                    max(0, min_x - padding),
                    max(0, min_y - padding),
                    min(screen_width, max_x + padding),
                    min(screen_height, max_y + padding)
                )
                
                logging.info(f"앱 영역 감지 성공: {app_region}")
                return app_region
            
            raise Exception("앱 영역을 찾을 수 없습니다.")
            
        except Exception as e:
            logging.error(f"앱 영역 감지 실패: {str(e)}")
            return None

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

    def pull_to_refresh(self):
        """끌어당겨 새로고침 수행"""
        try:
            if self.app_region is None:
                return
            
            # 화면 중앙 상단 지점 계산
            center_x = self.app_region[0] + (self.app_region[2] - self.app_region[0]) // 2
            start_y = self.app_region[1] + 100  # 상단에서 약간 아래 지점
            
            # 드래그 동작 수행
            pyautogui.moveTo(center_x, start_y)
            pyautogui.mouseDown()
            pyautogui.moveTo(center_x, start_y + self.drag_distance, duration=0.5)
            pyautogui.mouseUp()
            
            logging.info("끌어당겨 새로고침 완료")
            time.sleep(3)  # 새로고침 완료 대기
            
        except Exception as e:
            logging.error(f"새로고침 실패: {str(e)}")

    def select_queue_tab(self):
        """줄서기 탭 선택"""
        try:
            if self.app_region is None:
                return False
                
            # 줄서기 텍스트 찾아 클릭
            if self.click_text(self.app_region, "줄서기"):
                logging.info("줄서기 탭 선택 완료")
                time.sleep(2)  # 탭 전환 대기
                return True
                
            logging.error("줄서기 탭을 찾을 수 없습니다")
            return False
            
        except Exception as e:
            logging.error(f"줄서기 탭 선택 실패: {str(e)}")
            return False

    def is_better_time(self, new_time):
        """새로운 시간이 현재 예약된 시간보다 더 좋은지 확인"""
        if self.current_reservation is None:
            return True
            
        # 예: 더 이른 시간을 선호하는 경우
        return new_time < self.current_reservation

    def cancel_current_reservation(self):
        """현재 예약 취소"""
        try:
            # 예약 취소 버튼 찾아 클릭
            if self.click_text(self.app_region, "예약취소"):
                time.sleep(1)
                # 확인 모달에서 확인 버튼 클릭
                modal_region = self.calculate_modal_region()
                if self.click_text(modal_region, "확인"):
                    logging.info("기존 예약 취소 완료")
                    self.current_reservation = None
                    time.sleep(2)  # 취소 처리 대기
                    return True
            return False
        except Exception as e:
            logging.error(f"예약 취소 실패: {str(e)}")
            return False

    def check_reservation(self):
        """예약 가능 시간대 확인 및 예약 시도"""
        if self.app_region is None:
            self.app_region = self.find_app_region()
            if self.app_region is None:
                logging.error("앱 영역을 찾을 수 없습니다.")
                return False

        try:
            screenshot = self.capture_screen(self.app_region)
            if screenshot is None:
                return False

            text = self.extract_text_from_image(screenshot)
            now = datetime.now()
            
            available_times = []
            for line in text.splitlines():
                if "예약" in line:
                    try:
                        time_str = line.split("예약")[0].strip()
                        reservation_time = datetime.strptime(time_str, "%H:%M").replace(
                            year=now.year, month=now.month, day=now.day)
                        
                        if self.is_time_in_range(reservation_time):
                            available_times.append((reservation_time, time_str))
                    except ValueError:
                        continue
            
            # 가능한 시간들을 시간순으로 정렬
            available_times.sort()
            
            for reservation_time, time_str in available_times:
                # 현재 예약이 없거나, 더 좋은 시간대인 경우
                if self.is_better_time(reservation_time):
                    logging.info(f"더 좋은 예약 가능 시간대 발견: {time_str}")
                    
                    # 기존 예약이 있다면 취소
                    if self.current_reservation is not None:
                        if not self.cancel_current_reservation():
                            continue
                    
                    # 새로운 예약 시도
                    if self.click_text(self.app_region, time_str):
                        time.sleep(2)
                        
                        modal_region = self.calculate_modal_region()
                        if self.click_text(modal_region, "확인"):
                            logging.info(f"새로운 예약 완료: {time_str}")
                            self.current_reservation = reservation_time
                            return True
            
            logging.info("더 좋은 예약 가능 시간대가 없습니다.")
            return False
            
        except Exception as e:
            logging.error(f"예약 확인 중 오류 발생: {str(e)}")
            return False

    def calculate_modal_region(self):
        """모달 영역 계산"""
        modal_x = self.app_region[0] + (self.app_region[2] - self.app_region[0])//4
        modal_y = self.app_region[1] + (self.app_region[3] - self.app_region[1])//4
        modal_w = (self.app_region[2] - self.app_region[0])//2
        modal_h = (self.app_region[3] - self.app_region[1])//2
        return (modal_x, modal_y, modal_x + modal_w, modal_y + modal_h)

    def job(self):
        """주기적으로 실행할 작업"""
        # 줄서기 탭 선택
        if not self.select_queue_tab():
            return False
            
        # 끌어당겨 새로고침
        self.pull_to_refresh()
        
        # 예약 확인 및 시도
        return self.check_reservation()

    def run(self):
        """메인 실행 함수"""
        try:
            logging.info("앱 영역 자동 감지를 시작합니다...")
            self.app_region = self.find_app_region()
            
            if self.app_region is None:
                logging.error("앱 영역을 찾을 수 없습니다.")
                return
            
            logging.info(f"감지된 앱 영역: {self.app_region}")
            
            # 스케줄러 설정
            schedule.every(5).minutes.do(self.job)
            
            # 첫 실행
            self.job()
            
            # 메인 루프 - 예약 성공 후에도 계속 실행
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