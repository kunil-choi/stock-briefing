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

# === 2. 경제방송 뉴스 RSS/페이지 ===
BROADCAST_SOURCES = {
    "한경TV": "https://www.wowtv.co.kr/",
    "SBS_Biz": "https://biz.sbs.co.kr/",
    "MBN": "https://mbnmoney.mbn.co.kr/",
    "매일경제TV": "https://mbn.co.kr/",
}

# === 3. 증시 유튜버 채널 ID (관심 채널 추가/삭제 가능) ===
YOUTUBE_CHANNELS = {
    "삼프로TV": "UCTg-AH4JkXJMUWJsFQpABJw",
    "슈카월드": "UCsJ6RuBiTVWOlN3n3-BbELg",
    "신사임당": "UCep5LSsJGJfuYjU8F4bXjzA",
    "소수몽키": "UCg7iGERb6g2JhGZPtnttFmA",
    # 원하는 채널 추가
}

# === 4. 애널리스트 리포트 소스 ===
ANALYST_SOURCES = {
    "네이버금융_리서치": "https://finance.naver.com/research/",
    "한경컨센서스": "https://markets.hankyung.com/consensus",
    "FnGuide": "https://comp.fnguide.com/",
}

# === 한국 주식 종목명 패턴 (정규식으로 종목 추출 시 사용) ===
# KRX 상장 종목 리스트는 별도로 로드
KRX_STOCK_LIST_URL = "http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"