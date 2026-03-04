# config.py
import os

# === API 키 (GitHub Secrets에서 가져옴) ===
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

# === 1. 뉴스 RSS 피드 목록 ===
NEWS_RSS_FEEDS = {
    "한국경제_증권": "https://www.hankyung.com/feed/finance",
    "매일경제_증권": "https://www.mk.co.kr/rss/30100041/",
    "연합뉴스_경제": "https://www.yna.co.kr/rss/economy.xml",
    "이데일리_증권": "https://www.edaily.co.kr/rss/edaily_stock.xml",
    "머니투데이_증권": "https://rss.mt.co.kr/mt_stock.xml",
}

# === 2. 경제전문방송 유튜브 채널 (24시간 이내 수집) ===
BROADCAST_YOUTUBE = {
    "한국경제TV": "UCF8AeLlUbEpKju6v1H6p8Eg",
    "SBS Biz": "UCbMjg2EvXs_RUGW-KrdM3pw",
    "서울경제TV": "UCZKBS37Y0TmrFBfYBuBibtQ",
}

# === 3. 증시 유튜버 (구독자 상위, 48시간 이내 수집) ===
YOUTUBE_CHANNELS = {
    "슈카월드": "UCsJ6RuBiTVWOlN3n3-BbELg",
    "삼프로TV": "UCTg-AH4JkXJMUWJsFQpABJw",
    "신사임당": "UCep5LSsJGJfuYjU8F4bXjzA",
}

# === 4. 애널리스트 리포트 소스 ===
ANALYST_SOURCES = {
    "네이버금융_리서치": "https://finance.naver.com/research/",
    "한경컨센서스": "https://markets.hankyung.com/consensus",
}

# === 수집 시간 범위 설정 ===
BROADCAST_HOURS = 24   # 경제방송: 24시간 이내
YOUTUBER_HOURS = 48    # 증시 유튜버: 48시간 이내

# === KRX 상장 종목 리스트 URL ===
KRX_STOCK_LIST_URL = "http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"

