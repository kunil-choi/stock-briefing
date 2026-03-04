# main.py
import os
import json
from datetime import datetime

from config import (
    ANTHROPIC_API_KEY, YOUTUBE_API_KEY,
    NEWS_RSS_FEEDS, BROADCAST_YOUTUBE, YOUTUBE_CHANNELS,
    BROADCAST_HOURS, YOUTUBER_HOURS
)
from collectors.news_collector import collect_news
from collectors.youtube_collector import collect_broadcast_youtube, collect_youtuber
from collectors.analyst_collector import collect_analyst
from analyzer.ai_analyzer import analyze_and_generate_html


def main():
    print(f"=== AI 증시 모닝브리핑 시작: {datetime.now()} ===")

    all_data = []

    # 1. 뉴스 RSS 수집
    print("\n[1/4] 뉴스 RSS 수집 중...")
    news_data = collect_news(NEWS_RSS_FEEDS)
    all_data.extend(news_data)
    print(f"  → 총 {len(news_data)}건 수집")

    # 2. 경제전문방송 유튜브 수집 (24시간 이내)
    print(f"\n[2/4] 경제전문방송 유튜브 수집 중 (최근 {BROADCAST_HOURS}시간)...")
    broadcast_data = collect_broadcast_youtube(
        BROADCAST_YOUTUBE, YOUTUBE_API_KEY, hours=BROADCAST_HOURS
    )
    all_data.extend(broadcast_data)
    print(f"  → 총 {len(broadcast_data)}건 수집")

    # 3. 증시 유튜버 수집 (48시간 이내)
    print(f"\n[3/4] 증시 유튜버 수집 중 (최근 {YOUTUBER_HOURS}시간)...")
    youtuber_data = collect_youtuber(
        YOUTUBE_CHANNELS, YOUTUBE_API_KEY, hours=YOUTUBER_HOURS
    )
    all_data.extend(youtuber_data)
    print(f"  → 총 {len(youtuber_data)}건 수집")

    # 4. 애널리스트 리포트 수집
    print("\n[4/4] 애널리스트 리포트 수집 중...")
    analyst_data = collect_analyst()
    all_data.extend(analyst_data)
    print(f"  → 총 {len(analyst_data)}건 수집")

    print(f"\n========== 전체 {len(all_data)}건 데이터 수집 완료 ==========")

    # 수집 데이터 백업
    os.makedirs("data", exist_ok=True)
    today_str = datetime.now().strftime("%Y%m%d")
    with open(f"data/raw_{today_str}.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)

    # AI 분석 + HTML 생성
    print("\n[AI 분석] Claude API로 교차분석 중...")
    html = analyze_and_generate_html(all_data, ANTHROPIC_API_KEY)

    # 결과 저장
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ 브리핑 페이지 생성 완료: docs/index.html")
    print(f"=== 완료: {datetime.now()} ===")


if __name__ == "__main__":
    main()
