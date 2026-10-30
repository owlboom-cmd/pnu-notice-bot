import os
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    if TOKEN and CHAT_ID:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})

# 날짜 서식 준비
today_hyphen = datetime.now().strftime("%Y-%m-%d") # 2026-10-30
today_dot = datetime.now().strftime("%Y.%m.%d")    # 2026.10.30
today_short = datetime.now().strftime("%y.%m.%d")  # 26.10.30

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# ========================================
# 1. 기계공학부 공지사항
# ========================================
try:
    url_me = "https://me.pusan.ac.kr/new/sub05/sub05_01.asp"
    res_me = requests.get(url_me, verify=False, headers=headers)
    res_me.encoding = 'euc-kr' # ASP 페이지 한글 인코딩
    soup_me = BeautifulSoup(res_me.text, 'html.parser')

    rows_me = soup_me.select('table tr')
    for row in rows_me:
        tds = row.select('td')
        if len(tds) >= 4: # 번호, 제목, 작성자, 날짜 표 구조
            title_tag = row.select_one('a')
            if title_tag:
                title = title_tag.text.strip()
                date_text = tds[-2].text.strip() # 보통 뒤에서 두 번째 칸이 날짜
                
                if today_hyphen in date_text or today_dot in date_text or today_short in date_text:
                    send_message(f"[기계공학부] {title}")
except Exception as e:
    print(f"기계공학부 크롤링 중 오류 발생: {e}")

# ========================================
# 2. 대학본부 공지사항 (공지사항 전용 mCode=MN095)
# ========================================
try:
    url_main = "https://www.pusan.ac.kr/kor/CMS/Board/Board.do?mCode=MN095"
    res_main = requests.get(url_main, verify=False, headers=headers)
    soup_main = BeautifulSoup(res_main.text, 'html.parser')

    # 실제 공지사항 테이블의 행만 정확히 추출
    rows_main = soup_main.select('.board-list-table tbody tr, table.board-list tbody tr')
    for row in rows_main:
        title_tag = row.select_one('td.subject a, .subject a, a')
        date_tag = row.select_one('td.date, .date')
        
        if title_tag and date_tag:
            title = title_tag.text.strip()
            date_text = date_tag.text.strip()
            
            if today_hyphen in date_text or today_dot in date_text or today_short in date_text:
                send_message(f"[대학본부] {title}")
except Exception as e:
    print(f"대학본부 크롤링 중 오류 발생: {e}")
