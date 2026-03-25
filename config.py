# config.py
import os
import json

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
GH_TOKEN = os.getenv("GH_TOKEN", "")

# GitHub 저장소 정보
GITHUB_REPO = "kunil-choi/stock-briefing"
CHANNELS_FILE = "channels.json"

# 채널 관리 패널 비밀번호
PANEL_PASSWORD = "stock2026!"

# === 뉴스 RSS ===
NEWS_RSS_FEEDS = {
    "한국경제": "https://www.hankyung.com/feed/stock",
    "매일경제": "https://www.mk.co.kr/rss/30100041/",
    "연합뉴스 경제": "https://www.yna.co.kr/rss/economy.xml",
    "이데일리": "https://rss.edaily.co.kr/edaily_stock.xml",
    "머니투데이": "https://rss.mt.co.kr/mt_stock.xml",
}

# === 경제전문방송 유튜브 (TV 미러링 - 24시간 이내) ===
BROADCAST_YOUTUBE = {
    "한국경제TV": "UCF8AeLlUbEpKju6v1H6p8Eg",
    "SBS Biz": "UCbMjg2EvXs_RUGW-KrdM3pw",
    "서울경제TV": "UCZKBS37Y0TmrFBfYBuBibtQ",
    "머니투데이 방송(MTN)": "UClErHbdZKUnD1NyIUeQWvuQ",
    "매일경제TV": "UCnMtEMnsGFjQgLJEEkMSHhQ",
    "KBS 1라디오(성공예감 이대호)": "UCMLJc_D3jgFcS_48G7i4V0A",
}

# === 오리지널 경제/주식 유튜브 채널 TOP 50 (TV 미러링 제외) ===
# 구독자 순 정렬, 경제·금융·글로벌경제·거시경제·주식·채권 관련 채널
YOUTUBE_ORIGINAL_TOP50 = {
    # --- Tier 1: 100만+ ---
    "슈카월드": "UCsJ6RuBiTVWOlN3n3-BbELg",
    "삼프로TV": "UCTg-AH4JkXJMUWJsFQpABJw",
    "김작가 TV": "UCvil4OAt-zShzkKHsg9EQAw",
    "신사임당": "UCep5LSsJGJfuYjU8F4bXjzA",
    "하와이 대저택": "UCO-e0J-Qsilkv_4tBa3LyYw",
    "부읽남": "UCuJq6-2TmOYSkXOFT8aPzOQ",
    "박곰희TV": "UCQ2O-UpBMM7FcEsvnS0OOVQ",
    "월급쟁이부자들TV": "UCBjV4vqkY7GmlHiKVJjABeg",
    # --- Tier 2: 50만~100만 ---
    "KBS 경제한방": "UCn_38aaCktkBLPv3EtfmiUA",
    "소수몽키": "UCaeyAzBno_gTbdoSCiiRn8Q",
    "언더스탠딩": "UCwGb4QBBMHAA2bZomsTKjOA",
    "전인구경제연구소": "UCnEOmITFJaV1VHMFgrNMuOw",
    "달란트투자": "UCi1XSt8x8tJfE4ZDYYRy4ig",
    "홍춘욱의경제강의노트": "UC6CPlceq_Xygpwm8-LW-HAg",
    "주코노미": "UCK0z8aLwGy1PWeNiNkCUJ4w",
    "이효석아카데미": "UCa8CqCBi2YsPCbVwxRMbpjg",
    # --- Tier 3: 30만~50만 ---
    "채부심": "UCD9vzSxZ69pjcnf8hgCQXVQ",
    "에임리치": "UC0-1F-9GS52XVxbJIrHoEbQ",
    "주식하는강이사": "UCkHG7tMYGjfShDBpC2jZP5w",
    "오건영": "UCvR7Tx2sIeLhFbzL7gzP4Ug",
    "한투 마켓프로": "UC0c8Q5TjKqLnYtXqxVqZ9Pg",
    # --- Tier 4: 15만~30만 ---
    "체슬리TV": "UCXST0Hq6CAmG0dmo3jgrlEw",
    "미주은TV": "UC7dOSwPp29B6F7OAb3w3aYg",
    "김범곤의주식공부": "UC0SR7J3QRQvC-oejLqWlLyA",
    "머니인사이드": "UC_3ka0D7WR4sMUMlJNIMzuA",
    "김경필 머니트레이너": "UCjv46sVeKhPJ6q_WTx5XY8g",
    "할 수 있다 알고투자": "UCKYrJz6Jo0BjpAKfEOMEkOw",
    "뉴욕주민": "UC3Y5E0Y9BWWKxDiRoO1NMHQ",
    "박세익 체슬리": "UCXST0Hq6CAmG0dmo3jgrlEw",
    "염블리": "UCwDUtnPE6jMOkiOLvadKjMQ",
    # --- Tier 5: 10만~15만 ---
    "삼성증권 투자로드": "UClvL2apKH1oNbVhWvs2Zf6Q",
    "미래에셋 스마트머니": "UClgD7B3AS4Rfjga3Q_0w5-Q",
    "NH투자증권": "UChyCAlK5v40B4U9bTsdMGow",
    "KB증권": "UC9PYScqH7lnAWdnmxhbULxw",
    "증시각도기TV": "UCe-sSksb9xhBrPoOVwuxCkQ",
    "자유인TV": "UCXjcmJHo4u0j8JuL5Q7RxVw",
    "재테크읽어주는파일럿": "UCo7hFOuYTnqz_Oy6vF7dz8w",
    "글로벌이코노믹TV": "UCbPeUCpd6t_Vv8K5HN_Y1eg",
    "JYP투자자문": "UCTEZ93bO5dMqY0SQ67CJXOA",
    "수페TV": "UCqz5sGCfETqXMRxYoTkQ-sQ",
    # --- Tier 6: 5만~10만 ---
    "안유화의 중국경제": "UC0CdpC2CgHPkfmq4LaYSH0Q",
    "이코노미스트": "UCT1Yqo3-I0mMa3PtKc-G7Ug",
    "한경 글로벌마켓": "UC0CdpC2CgHPkfmq4LaYSH0Q",
    "돈의심리학": "UClTdO1e1kFiB_oHCVU0D-Rw",
    "고경호의애프터마켓": "UCmfnteXPW6fU1OT81mvs0xg",
    "연금이야기": "UC_KsGYqJKDIz9a-BJVXqlog",
    "슬기로운시사생활": "UCRPJUJqt-5Oy8QFi4p15O6g",
    "주주클럽": "UCJfq7FlH9fEfIOt1xXA7bMg",
    "이선생TV": "UCnVMuv_HA0NpmokBQCwZ7xA",
    "유목민의 글로벌주식": "UC5BjJ8kqQqjPqWsB8RJ13Pg",
}

# === 인기 패널 목록 (최근 1개월 내 3회 이상 출연) ===
# 이 패널명이 제목/설명에 포함된 영상은 구독자 50위 밖 채널이라도 수집
POPULAR_PANELISTS = [
    "홍춘욱", "오건영", "박세익", "김학균", "이효석",
    "정용진", "강방천", "이채원", "최준철", "김경필",
    "염승환", "이선엽", "곽상준", "박문환", "허재환",
    "서영수", "김한진", "이경민", "김일구", "전종규",
    "이주열", "박종훈", "김현석", "신중호", "이창용",
]

# === 애널리스트 리포트 ===
ANALYST_SOURCES = [
    "https://finance.naver.com/research/company_list.naver",
    "https://finance.naver.com/research/industry_list.naver",
]

# 수집 시간 설정
BROADCAST_HOURS = 24
YOUTUBER_HOURS = 24
REPORT_DAYS = 1

# KRX 종목 리스트
KRX_STOCK_LIST_URL = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"


def load_channels():
    """channels.json에서 채널 목록을 로드 (웹 UI에서 추가한 채널 포함)"""
    default = {
        "broadcast": {
            "한국경제TV": {"id": "UCF8AeLlUbEpKju6v1H6p8Eg", "url": "https://www.youtube.com/@hkwowtv"},
            "SBS Biz": {"id": "UCbMjg2EvXs_RUGW-KrdM3pw", "url": "https://www.youtube.com/@SBSBiz2021"},
            "서울경제TV": {"id": "UCZKBS37Y0TmrFBfYBuBibtQ", "url": "https://www.youtube.com/@sentv"},
            "머니투데이 방송(MTN)": {"id": "UClErHbdZKUnD1NyIUeQWvuQ", "url": "https://www.youtube.com/@mtn"},
            "매일경제TV": {"id": "UCnMtEMnsGFjQgLJEEkMSHhQ", "url": "https://www.youtube.com/@MKeconomy_TV"},
            "KBS 1라디오(성공예감 이대호)": {"id": "UCMLJc_D3jgFcS_48G7i4V0A", "url": "https://www.youtube.com/@KBS_1Radio"},
        },
        "youtuber": {
            "슈카월드": {"id": "UCsJ6RuBiTVWOlN3n3-BbELg", "url": "https://www.youtube.com/@syukaworld"},
            "삼프로TV": {"id": "UCTg-AH4JkXJMUWJsFQpABJw", "url": "https://www.youtube.com/@3PROTV"},
            "신사임당": {"id": "UCep5LSsJGJfuYjU8F4bXjzA", "url": "https://www.youtube.com/@SSID"},
            "체슬리TV": {"id": "UCXST0Hq6CAmG0dmo3jgrlEw", "url": "https://www.youtube.com/@chesleytv"},
            "채부심": {"id": "UCD9vzSxZ69pjcnf8hgCQXVQ", "url": "https://www.youtube.com/@chaeboosim"},
            "김작가 TV": {"id": "UCvil4OAt-zShzkKHsg9EQAw", "url": "https://www.youtube.com/@lucky_tv"},
            "KBS 경제한방": {"id": "UCn_38aaCktkBLPv3EtfmiUA", "url": "https://www.youtube.com/@e-hanbang"},
            "하와이 대저택": {"id": "UCO-e0J-Qsilkv_4tBa3LyYw", "url": "https://www.youtube.com/@hawaiidjt"},
        },
    }
    try:
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # channels.json에 없는 기본 채널 병합
            for cat in ["broadcast", "youtuber"]:
                if cat not in data:
                    data[cat] = default[cat]
            return data
    except FileNotFoundError:
        with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
