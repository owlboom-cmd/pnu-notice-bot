import os
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin # 링크를 합쳐주는 기능 추가

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    if TOKEN and CHAT_ID:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})

# 기존의 datetime.now() 코드를 지우고 아래처럼 어제 날짜로 적습니다.
today_hyphen = "2026-10-30"
today_dot = "2026.10.30"
today_short = "26.10.30"

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# ========================================
# 1. 기계공학부 공지사항
# ========================================
try:
    url_me = "https://me.pusan.ac.kr/new/sub05/sub05_01.asp"
    res_me = requests.get(url_me, verify=False, headers=headers)
    res_me.encoding = 'euc-kr'
    soup_me = BeautifulSoup(res_me.text, 'html.parser')

    rows_me = soup_me.select('table tr')
    for row in rows_me:
        tds = row.select('td')
        if len(tds) >= 4:
            title_tag = row.select_one('a')
            if title_tag:
                title = title_tag.text.strip()
                date_text = tds[-2].text.strip()
                
                # 💡 링크 추출 및 전체 주소로 만들기
                link = title_tag.get('href', '')
                full_link = urljoin(url_me, link) 
                
                if today_hyphen in date_text or today_dot in date_text or today_short in date_text:
                    send_message(f"[기계공학부] {title}\n👉 {full_link}")
except Exception as e:
    print(f"기계공학부 오류: {e}")

# ========================================
# 2. 대학본부 공지사항
# ========================================
try:
    url_main = "https://www.pusan.ac.kr/kor/CMS/Board/Board.do?mCode=MN095"
    res_main = requests.get(url_main, verify=False, headers=headers)
    soup_main = BeautifulSoup(res_main.text, 'html.parser')

    rows_main = soup_main.select('.board-list-table tbody tr, table.board-list tbody tr')
    for row in rows_main:
        title_tag = row.select_one('td.subject a, .subject a, a')
        date_tag = row.select_one('td.date, .date')
        
        if title_tag and date_tag:
            title = title_tag.text.strip()
            date_text = date_tag.text.strip()
            
            # 💡 링크 추출 및 전체 주소로 만들기
            link = title_tag.get('href', '')
            full_link = urljoin(url_main, link)
            
            if today_hyphen in date_text or today_dot in date_text or today_short in date_text:
                send_message(f"[대학본부] {title}\n👉 {full_link}")
except Exception as e:
    print(f"대학본부 오류: {e}")
