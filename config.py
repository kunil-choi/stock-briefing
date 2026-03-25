# config.py
import os
import json

# === API 키 ===
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
GH_TOKEN = os.environ.get("GH_TOKEN", "")

# === GitHub 저장소 정보 (채널 수정 API용) ===
GITHUB_REPO = "kunil-choi/stock-briefing"
CHANNELS_FILE = "channels.json"

# === 1. 뉴스 RSS 피드 목록 ===
NEWS_RSS_FEEDS = {
    "한국경제_증권": "https://www.hankyung.com/feed/finance",
    "매일경제_증권": "https://www.mk.co.kr/rss/30100041/",
    "연합뉴스_경제": "https://www.yna.co.kr/rss/economy.xml",
    "이데일리_증권": "https://www.edaily.co.kr/rss/edaily_stock.xml",
    "머니투데이_증권": "https://rss.mt.co.kr/mt_stock.xml",
}

# === 2~3. 유튜브 채널은 channels.json에서 로드 ===
def load_channels():
    default = {
        "broadcast": {
            "한국경제TV": {"id": "UCF8AeLlUbEpKju6v1H6p8Eg", "url": "https://www.youtube.com/@hkwowtv"},
            "SBS Biz": {"id": "UCbMjg2EvXs_RUGW-KrdM3pw", "url": "https://www.youtube.com/@SBSBiz2021"},
            "서울경제TV": {"id": "UCZKBS37Y0TmrFBfYBuBibtQ", "url": "https://www.youtube.com/@sentv"},
            "머니투데이 방송(MTN)": {"id": "UClErHbdZKUnD1NyIUeQWvuQ", "url": "https://www.youtube.com/@mtn"},
            "매일경제TV": {"id": "UCnMtEMnsGFjQgLJEEkMSHhQ", "url": "https://www.youtube.com/@MKeconomy_TV"},
            "KBS 1라디오(성공예감 이대호)": {"id": "UCMLJc_D3jgFcS_48G7i4V0A", "url": "https://www.youtube.com/@KBS_1Radio"}
        },
        "youtuber": {
            "슈카월드": {"id": "UCsJ6RuBiTVWOlN3n3-BbELg", "url": "https://www.youtube.com/@syukaworld"},
            "삼프로TV": {"id": "UCTg-AH4JkXJMUWJsFQpABJw", "url": "https://www.youtube.com/@3PROTV"},
            "신사임당": {"id": "UCep5LSsJGJfuYjU8F4bXjzA", "url": "https://www.youtube.com/@SSID"},
            "체슬리TV": {"id": "UCXST0Hq6CAmG0dmo3jgrlEw", "url": "https://www.youtube.com/@chesleytv"},
            "채부심": {"id": "UCD9vzSxZ69pjcnf8hgCQXVQ", "url": "https://www.youtube.com/@chaeboosim"},
            "김작가 TV": {"id": "UCvil4OAt-zShzkKHsg9EQAw", "url": "https://www.youtube.com/@lucky_tv"},
            "KBS 경제한방": {"id": "UCn_38aaCktkBLPv3EtfmiUA", "url": "https://www.youtube.com/@e-hanbang"},
            "하와이 대저택": {"id": "UCO-e0J-Qsilkv_4tBa3LyYw", "url": "https://www.youtube.com/@hawaiidjt"}
        }
    }
    try:
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default

# === 4. 애널리스트 리포트 소스 ===
ANALYST_SOURCES = {
    "네이버금융_리서치": "https://finance.naver.com/research/",
    "한경컨센서스": "https://markets.hankyung.com/consensus",
}

# === 수집 시간 범위 ===
BROADCAST_HOURS = 24
YOUTUBER_HOURS = 48

# 채널 관리 패널 비밀번호 (원하는 값으로 변경 가능)
PANEL_PASSWORD = "kbs2026!"


