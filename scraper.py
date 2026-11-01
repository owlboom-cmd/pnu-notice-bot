
import os
import re
import json
import requests

from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

# ========================================
# 1. 기본 설정
# ========================================

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

STATE_FILE = Path("notice_state.json")
MAX_HISTORY = 300

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

session = requests.Session()
session.headers.update(HEADERS)

URL_ME = "https://me.pusan.ac.kr/new/sub05/sub01_01.php"
URL_MAIN = "https://www.pusan.ac.kr/kor/CMS/Board/Board.do?mCode=MN095"


# ========================================
# 2. 텔레그램 메시지 전송
# ========================================

def send_message(text):
    if not TOKEN or not CHAT_ID:
        raise ValueError("텔레그램 환경변수가 설정되지 않았습니다.")

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=15
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(f"Telegram 전송 실패: {result}")


# ========================================
# 3. 기존 공지 기록 불러오기
# ========================================

def load_state():

    if not STATE_FILE.exists():
        return None

    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(f"공지 기록 파일 오류: {e}")


def save_state(state):

    temp_file = STATE_FILE.with_suffix(".tmp")

    with temp_file.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    temp_file.replace(STATE_FILE)


# ========================================
# 4. 게시글 고유번호 추출
# ========================================

def get_post_id(link):

    parsed = urlparse(link)
    params = parse_qs(parsed.query)

    # 일반적인 게시판 게시글 번호
    for key in ["idx", "no", "seq", "articleNo", "nttId"]:
        if key in params:
            return str(params[key][0])

    # JavaScript 링크에 포함된 번호
    match = re.search(r"\d+", link)

    if match:
        return match.group()

    # 고유번호를 찾을 수 없는 경우 링크 사용
    return link


# ========================================
# 5. 기계공학부 공지사항 크롤링
# ========================================

def get_me_notices():

    response = session.get(URL_ME, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    notices = []

    for row in soup.select("table tr"):

        tds = row.select("td")

        if len(tds) < 4:
            continue

        title_tag = None

        for td in tds:
            a_tag = td.select_one("a")

            if a_tag and a_tag.get_text(strip=True):
                title_tag = a_tag
                break

        if not title_tag:
            continue

        title = re.sub(
            r"\s+",
            " ",
            title_tag.get_text(" ", strip=True)
        )

        link = title_tag.get("href", "").strip()

        if not link:
            continue

        if "javascript" in link.lower():

            post_id = get_post_id(link)

            full_link = (
                f"{URL_ME}?mode=read&idx={post_id}"
            )

        else:

            full_link = urljoin(URL_ME, link)
            post_id = get_post_id(full_link)

        notices.append({
            "id": post_id,
            "title": title,
            "link": full_link,
            "source": "기계공학부"
        })

    return notices


# ========================================
# 6. 부산대학교 대학본부 공지사항 크롤링
# ========================================

def get_main_notices():

    response = session.get(URL_MAIN, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    notices = []

    rows = soup.select(
        ".board-list-table tbody tr, "
        "table.board-list tbody tr"
    )

    for row in rows:

        title_tag = row.select_one(
            "td.subject a, .subject a, a"
        )

        if not title_tag:
            continue

        title = re.sub(
            r"\s+",
            " ",
            title_tag.get_text(" ", strip=True)
        )

        link = title_tag.get("href", "").strip()

        if not title or not link:
            continue

        full_link = urljoin(URL_MAIN, link)

        post_id = get_post_id(full_link)

        notices.append({
            "id": post_id,
            "title": title,
            "link": full_link,
            "source": "부산대학교"
        })

    return notices


# ========================================
# 7. 새로운 공지사항 확인
# ========================================

def check_new_notices(notices, previous_ids):

    previous = set(previous_ids)

    new_notices = [
        notice for notice in notices
        if notice["id"] not in previous
    ]

    # 오래된 공지부터 전송
    return list(reversed(new_notices))


# ========================================
# 8. 메인 실행
# ========================================

def main():

    print("공지사항 확인 시작")

    state = load_state()

    # 첫 실행: 기존 공지를 기준점으로 저장
    first_run = state is None

    if first_run:
        state = {
            "me": [],
            "main": []
        }

    # 사이트별로 독립적으로 수집
    sources = [
        ("me", get_me_notices),
        ("main", get_main_notices)
    ]

    for key, scraper in sources:

        try:

            notices = scraper()

            if not notices:
                print(f"{key}: 공지가 없거나 게시글을 찾지 못했습니다.")
                continue

            previous_ids = state.get(key, [])

            if first_run:

                state[key] = [
                    notice["id"]
                    for notice in notices
                ][:MAX_HISTORY]

                print(f"{key}: 기존 공지 {len(notices)}개 기준 등록")
                continue

            new_notices = check_new_notices(
                notices,
                previous_ids
            )

            print(f"{key}: 새로운 공지 {len(new_notices)}개")

            for notice in new_notices:

                message = (
                    f"📢 [{notice['source']}] 새 공지사항\n\n"
                    f"📌 {notice['title']}\n\n"
                    f"🔗 {notice['link']}"
                )

                send_message(message)

                print(f"전송 완료: {notice['title']}")

            # 성공적으로 수집하고 새 공지 전송까지 완료한 경우에만 기록
            new_ids = [
                notice["id"] for notice in notices
            ]

            combined = list(dict.fromkeys(
                new_ids + previous_ids
            ))

            state[key] = combined[:MAX_HISTORY]

        except Exception as e:

            print(f"{key} 처리 오류: {e}")

            # 실패한 사이트의 이전 기록은 유지
            continue

    save_state(state)

    print("공지사항 확인 종료")


if __name__ == "__main__":
    main()
