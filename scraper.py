import os
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})

# 1. 봇 연결 테스트: 실행될 때 무조건 텔레그램으로 메시지를 보냅니다.
send_message("🚨 [테스트] 파이썬 코드가 실행되었습니다!")

today_hyphen = datetime.now().strftime("%Y-%m-%d") # 2026-10-30 형태
today_dot = datetime.now().strftime("%Y.%m.%d")    # 2026.10.30 형태
print(f"오늘 날짜 기준: {today_hyphen} 또는 {today_dot}")

# ========================================
# 2. 기계공학부 확인
# ========================================
url_me = "https://me.pusan.ac.kr/new/sub05/sub05_01.asp"
res_me = requests.get(url_me, verify=False)
soup_me = BeautifulSoup(res_me.text, 'html.parser')

notices_me = soup_me.select('table tbody tr')
for notice in notices_me:
    try:
        title = notice.select_one('td.title a').text.strip()
        date_text = notice.select_one('td.date').text.strip()
        print(f"[기계공학부 찾음] {date_text} | {title}") # 깃허브 화면에 기록 남기기
        
        # 날짜에 하이픈(-)이나 마침표(.)가 들어가 있으면 전송
        if today_hyphen in date_text or today_dot in date_text:
            send_message(f"[기계공학부] {title}")
    except AttributeError:
        continue

# ========================================
# 3. 대학 본부 확인
# ========================================
url_main = "https://www.pusan.ac.kr/kor/CMS/Board/Board.do?mCode=MN104"
res_main = requests.get(url_main, verify=False)
soup_main = BeautifulSoup(res_main.text, 'html.parser')

notices_main = soup_main.select('table tbody tr')
for notice in notices_main:
    try:
        title = notice.select_one('td.Subject a').text.strip()
        date_text = notice.select_one('td.date').text.strip()
        print(f"[대학본부 찾음] {date_text} | {title}") # 깃허브 화면에 기록 남기기
        
        if today_hyphen in date_text or today_dot in date_text:
            send_message(f"[대학본부] {title}")
    except AttributeError:
        continue
