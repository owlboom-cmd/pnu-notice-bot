import os
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    if not TOKEN or not CHAT_ID:
        print("❌ 에러: 깃허브 Secrets에 텔레그램 토큰이나 챗 ID가 없습니다!")
        return
    res = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})
    print(f"텔레그램 전송 상태: {res.status_code} (200이면 성공)")

send_message("🚨 [테스트] 파이썬 코드가 실행되었습니다!")

today = datetime.now().strftime("%Y-%m-%d")
today_dot = datetime.now().strftime("%Y.%m.%d")
today_short = datetime.now().strftime("%y.%m.%d") # 26.10.30 형태까지 대비
print(f"오늘 날짜: {today} / {today_dot} / {today_short}")

# 사람이 크롬 브라우저로 접속한 것처럼 위장하는 장치
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

urls = {
    "기계공학부": "https://me.pusan.ac.kr/new/sub05/sub05_01.asp",
    "대학본부": "https://www.pusan.ac.kr/kor/CMS/Board/Board.do?mCode=MN104"
}

for name, url in urls.items():
    print(f"\n================ {name} ===============")
    res = requests.get(url, verify=False, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 게시판 형태(표 또는 리스트)에 상관없이 모조리 긁어옵니다.
    items = soup.select('tr, li')
    print(f"[{name}] 웹페이지에서 {len(items)}개의 줄을 찾았습니다.")
    
    for item in items:
        title_tag = item.select_one('.Subject a, .title a, .board-title a, a')
        date_tag = item.select_one('.date, .board-date')
        
        if title_tag and date_tag:
            title = title_tag.text.strip()
            date_text = date_tag.text.strip()
            print(f"발견: {date_text} | {title}")
            
            if today in date_text or today_dot in date_text or today_short in date_text:
                send_message(f"[{name}] {title}")
