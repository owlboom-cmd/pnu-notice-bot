import os
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

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
# 1. 기계공학부 공지사항 (주소 php로 수정됨!)
# ========================================
try:
    url_me = "https://me.pusan.ac.kr/new/sub05/sub01_01.php"
    res_me = requests.get(url_me, verify=False, headers=headers)
    # php 페이지는 보통 utf-8을 사용하므로 기존 euc-kr 강제 변환 코드는 제거했습니다.
    soup_me = BeautifulSoup(res_me.text, 'html.parser')

    rows_me = soup_me.select('table tr')
    for row in rows_me:
        tds = row.select('td')
        if len(tds) >= 4:
            title_tag = row.select_one('a')
            if title_tag:
                title = title_tag.text.strip()
                date_text = tds[-2].text.strip() # 보통 표의 뒤에서 두 번째 칸이 날짜
                
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
            
            link = title_tag.get('href', '')
            full_link = urljoin(url_main, link)
            
            if today_hyphen in date_text or today_dot in date_text or today_short in date_text:
                send_message(f"[대학본부] {title}\n👉 {full_link}")
except Exception as e:
    print(f"대학본부 오류: {e}")
