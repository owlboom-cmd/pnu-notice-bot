import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 기계공학부 또는 대학 본부 공지사항 URL
URL = "https://me.pusan.ac.kr/new/sub05/sub05_01.asp"

def send_message(text):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})

# 웹페이지 접속해서 데이터 가져오기
response = requests.get(URL)
soup = BeautifulSoup(response.text, 'html.parser')
today = datetime.now().strftime("%Y-%m-%d")

# 공지사항 목록 추출 (td.title, td.date 등은 실제 HTML 구조에 맞춰 수정 필요)
notices = soup.select('table tbody tr')
for notice in notices:
    try:
        title = notice.select_one('td.title a').text.strip()
        date_text = notice.select_one('td.date').text.strip()
        
        if today in date_text: # 오늘 올라온 공지만 전송
            send_message(f"오늘의 새 공지: {title}")
    except AttributeError:
        continue
