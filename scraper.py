import os
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import re  # 💡 문자열에서 숫자 추출 등을 위한 도구 추가

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    if TOKEN and CHAT_ID:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})

today_hyphen = datetime.now().strftime("%Y-%m-%d")
today_dot = datetime.now().strftime("%Y.%m.%d")
today_short = datetime.now().strftime("%y.%m.%d")

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# ========================================
# 1. 기계공학부 공지사항 (제목 정리 및 JS 링크 추출)
# ========================================
try:
    url_me = "https://me.pusan.ac.kr/new/sub05/sub01_01.php"
    res_me = requests.get(url_me, verify=False, headers=headers)
    soup_me = BeautifulSoup(res_me.text, 'html.parser')

    rows_me = soup_me.select('table tr')
    for row in rows_me:
        tds = row.select('td')
        if len(tds) >= 4:
            # 표의 칸(td)을 하나씩 돌면서 링크(a)가 들어있는 진짜 제목 칸만 찾아냅니다.
            for td in tds:
                a_tag = td.select_one('a')
                if a_tag:
                    # 💡 1. 지저분한 엔터와 공백을 한 줄의 띄어쓰기로 깔끔하게 합칩니다.
                    raw_title = td.text.strip()
                    title = re.sub(r'\s+', ' ', raw_title) 
                    
                    date_text = tds[-2].text.strip()
                    
                    # 💡 2. 자바스크립트 코드에서 숫자(예: 5192)만 쏙 뽑아냅니다.
                    link = a_tag.get('href', '')
                    if 'javascript' in link:
                        num_match = re.search(r'\d+', link)
                        if num_match:
                            seq = num_match.group()
                            # 뽑아낸 숫자로 직접 접속 주소를 조립합니다.
                            full_link = f"https://me.pusan.ac.kr/new/sub05/sub01_01.php?mode=read&idx={seq}"
                        else:
                            full_link = url_me
                    else:
                        full_link = urljoin(url_me, link)
                    
                    if today_hyphen in date_text or today_dot in date_text or today_short in date_text:
                        send_message(f"[기계공학부] {title}\n👉 {full_link}")
                    
                    break # 글 하나를 찾았으면 옆 칸은 무시하고 다음 공지글로 넘어갑니다.
except Exception as e:
    print(f"기계공학부 오류: {e}")

# ========================================
# 2. 대학본부 공지사항 (이전과 동일)
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
