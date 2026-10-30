import os
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime

# SSL 보안 경고 메시지 숨기기
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

URL = "https://me.pusan.ac.kr/new/sub05/sub05_01.asp"

def send_message(text):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})

# verify=False 를 추가하여 웹사이트 보안 인증서 검사를 무시하고 접속
response = requests.get(URL, verify=False)
soup = BeautifulSoup(response.text, 'html.parser')
today = datetime.now().strftime("%Y-%m-%d")

notices = soup.select('table tbody tr')
for notice in notices:
    try:
        title = notice.select_one('td.title a').text.strip()
        date_text = notice.select_one('td.date').text.strip()
        
        if today in date_text: # 오늘 올라온 공지만 전송
            send_message(f"오늘의 새 공지: {title}")
    except AttributeError:
        continue
