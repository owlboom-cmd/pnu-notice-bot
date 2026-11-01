
import os
import re
import json
import requests
import urllib3

# ========================================
# 게시 날짜 추출
# ========================================

def get_post_date(row):

    date_pattern = (
        r"\d{4}[-./]\d{1,2}[-./]\d{1,2}"
        r"|\d{2}[-./]\d{1,2}[-./]\d{1,2}"
    )

    for td in row.select("td"):

        text = td.get_text(" ", strip=True)

        match = re.search(date_pattern, text)

        if match:
            return match.group()

    return "날짜 정보 없음"

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

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

# 기계공학부 공지사항
URL_ME = "https://me.pusan.ac.kr/new/sub05/sub01_01.php"

# 부산대학교 대학본부 공지사항
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
        return {}

    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(f"공지 기록 파일 오류: {e}")


# ========================================
# 4. 공지 기록 저장
# ========================================

def save_state(state):

    temp_file = STATE_FILE.with_suffix(".tmp")

    with temp_file.open("w", encoding="utf-8") as f:
        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2
        )

    temp_file.replace(STATE_FILE)


# ========================================
# 5. 게시글 고유번호 추출
# ========================================

def get_post_id(link):

    parsed = urlparse(link)
    params = parse_qs(parsed.query)

    keys = [
        "idx",
        "no",
        "seq",
        "articleNo",
        "nttId",
        "boardSeq",
        "bbsSeq",
        "boardNo",
        "postNo"
    ]

    for key in keys:

        if key in params:
            return str(params[key][0])

    # JavaScript 링크에서만 숫자 추출
    if link.lower().startswith("javascript"):

        match = re.search(r"\d+", link)

        if match:
            return match.group()

    # 게시글 번호를 찾지 못하면 URL 자체를 사용
    return link


# ========================================
# 6. 기계공학부 공지사항 크롤링
# ========================================

def get_me_notices():

    response = session.get(
    URL_ME,
    timeout=20,
    verify=False
)

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    notices = []

    rows = soup.select("table tr")

    for row in rows:

        tds = row.select("td")

        if len(tds) < 4:
            continue

        title_tag = None

        # 실제 제목이 들어 있는 링크 찾기
        for td in tds:

            a_tag = td.select_one("a")

            if a_tag and a_tag.get_text(strip=True):

                title_tag = a_tag
                break

        if not title_tag:
            continue

        # 제목 공백 정리
        title = re.sub(
            r"\s+",
            " ",
            title_tag.get_text(" ", strip=True)
        )

        link = title_tag.get("href", "").strip()

        if not link:
            continue

        # JavaScript 링크 처리
        if "javascript" in link.lower():

            post_id = get_post_id(link)

            full_link = (
                f"{URL_ME}?mode=read&idx={post_id}"
            )

        else:

            full_link = urljoin(
                URL_ME,
                link
            )

            post_id = get_post_id(full_link)

        notices.append({

    "id": post_id,
    "title": title,
    "date": get_post_date(row),
    "link": full_link,
    "source": "기계공학부"

})

    return notices


# ========================================
# 7. 부산대학교 대학본부 공지사항 크롤링
# ========================================

def get_main_notices():

    response = session.get(
        URL_MAIN,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

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

        full_link = urljoin(
            URL_MAIN,
            link
        )

        post_id = get_post_id(full_link)

        notices.append({

    "id": post_id,
    "title": title,
    "date": get_post_date(row),
    "link": full_link,
    "source": "부산대학교"

})

    return notices


# ========================================
# 8. 새로운 공지사항 확인
# ========================================

def check_new_notices(notices, previous_ids):

    previous = set(previous_ids)

    new_notices = [

        notice
        for notice in notices
        if notice["id"] not in previous

    ]

    # 오래된 공지부터 전송
    return list(reversed(new_notices))


# ========================================
# 9. 메인 실행
# ========================================

def main():

    print("================================")
    print("부산대학교 공지사항 확인 시작")
    print("================================")

    
    state = load_state()

    # 홈페이지별 독립적인 기록 관리
    sources = [

        ("me", get_me_notices),

        ("main", get_main_notices)

    ]

    for key, scraper in sources:

        try:

            print(f"\n[{key}] 공지사항 수집 중...")

            # 공지사항 수집
            notices = scraper()

            if not notices:

                print(
                    f"[{key}] 공지를 찾지 못했습니다."
                )

                continue

            print(
                f"[{key}] 전체 공지 {len(notices)}개 발견"
            )

            # 최초 실행 또는 해당 사이트의 최초 성공 실행
            if key not in state:

                state[key] = [

                    notice["id"]
                    for notice in notices

                ][:MAX_HISTORY]

                print(
                    f"[{key}] 기존 공지를 기준점으로 등록했습니다."
                )

                continue

            # 기존 공지 번호 불러오기
            previous_ids = state[key]

            # 새로운 공지 확인
            new_notices = check_new_notices(
                notices,
                previous_ids
            )

            print(
                f"[{key}] 새로운 공지 {len(new_notices)}개 발견"
            )

            # 새로운 공지 전송
            test_notice = {
    "source": "기계공학부",
    "title": "텔레그램 알림 기능 테스트",
    "date": "2026-11-01",
    "link": URL_ME
}

message = (
    f"📢 부산대학교 신규 공지사항\n\n"
    f"📍 게시판: {test_notice['source']}\n"
    f"📌 제목: {test_notice['title']}\n"
    f"📅 게시 날짜: {test_notice['date']}\n\n"
    f"🔗 공지 원문:\n"
    f"{test_notice['link']}"
)

send_message(message)

                print(
                    f"전송 완료: {notice['title']}"
                )

            # 기존 기록과 새로운 공지 기록 합치기
            new_ids = [

                notice["id"]
                for notice in notices

            ]

            combined = list(dict.fromkeys(

                new_ids + previous_ids

            ))

            # 최대 300개까지 저장
            state[key] = combined[:MAX_HISTORY]

        except Exception as e:

            print(
                f"[{key}] 오류 발생: {e}"
            )

            # 오류가 발생하면 기존 기록 유지
            continue

    # 공지 기록 저장
    save_state(state)

    print("\n================================")
    print("공지사항 확인 종료")
    print("================================")


# ========================================
# 10. 프로그램 시작
# ========================================
def test_telegram_message():

    test_notice = {
        "source": "기계공학부",
        "title": "텔레그램 공지 알림 테스트",
        "date": "2026-11-01",
        "link": URL_ME
    }

    message = (
        "📢 부산대학교 신규 공지사항\n\n"
        f"📍 게시판: {test_notice['source']}\n"
        f"📌 제목: {test_notice['title']}\n"
        f"📅 게시 날짜: {test_notice['date']}\n\n"
        f"🔗 공지 원문:\n{test_notice['link']}"
    )

    send_message(message)

    print("테스트 메시지 전송 완료")


if __name__ == "__main__":

    main()
