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

today = datetime.now().strftime("%Y-%m-%d")

# ========================================
# 1. 기계공학부 공지사항 확인
# ========================================
url_me = "https://me.pusan.ac.kr/new/sub05/sub05_01.asp"
res_me = requests.get(url_me, verify=False)
soup_me = BeautifulSoup(res_me.text, 'html.parser')

notices_me = soup_me.select('table tbody tr')
for notice in notices_me:
    try:
        title = notice.select_one('td.title a').text.strip()
        date_text = notice.select_one('td.date').text.strip()
        
        if today in date_text:
            send_message(f"[기계공학부] {title}")
    except AttributeError:
        continue

# ========================================
# 2. 부산대학교 본부 공지사항 확인 (일반공지 예시)
# ========================================
url_main = "https://www.pusan.ac.kr/kor/CMS/Board/Board.do?mCode=MN104"
res_main = requests.get(url_main, verify=False)
soup_main = BeautifulSoup(res_main.text, 'html.parser')

notices_main = soup_main.select('table tbody tr')
for notice in notices_main:
    try:
        # 주의: 본부 홈페이지는 태그 이름이 기계공학과 다를 수 있습니다. 
        # 예시로 'td.subject a'를 임시로 넣었습니다.
        title = notice.select_one('td.subject').text.strip()
        date_text = notice.select_one('td.date').text.strip()
        
        if today in date_text:
            send_message(f"[대학본부] {title}")
    except AttributeError:
        continue
