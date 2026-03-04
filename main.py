# main.py
import os
import json
from datetime import datetime

from config import (
    ANTHROPIC_API_KEY, YOUTUBE_API_KEY,
    NEWS_RSS_FEEDS, BROADCAST_SOURCES,
    YOUTUBE_CHANNELS, ANALYST_SOURCES
)
from collectors.news_collector import collect_news
from collectors.broadcast_collector import collect_broadcast
from collectors.youtube_collector import collect_youtube
from collectors.analyst_collector import collect_analyst
from analyzer.ai_analyzer import analyze_and_generate_html


def main():
    print(f"=== AI 증시 모닝브리핑 시작: {datetime.now()} ===")

    # 1단계: 4개 채널 데이터 수집
    all_data = []

    print("[1/4] 뉴스 RSS 수집 중...")
    news_data = collect_news(NEWS_RSS_FEEDS)
    all_data.extend(news_data)
    print(f"  → {len(news_data)}건 수집")

    print("[2/4] 경제방송 수집 중...")
    broadcast_data = collect_broadcast(BROADCAST_SOURCES)
    all_data.extend(broadcast_data)
    print(f"  → {len(broadcast_data)}건 수집")

    print("[3/4] 유튜버 영상 수집 중...")
    youtube_data = collect_youtube(YOUTUBE_CHANNELS, YOUTUBE_API_KEY)
    all_data.extend(youtube_data)
    print(f"  → {len(youtube_data)}건 수집")

    print("[4/4] 애널리스트 리포트 수집 중...")
    analyst_data = collect_analyst()
    all_data.extend(analyst_data)
    print(f"  → {len(analyst_data)}건 수집")

    print(f"\n총 {len(all_data)}건 데이터 수집 완료")

    # 수집 데이터 백업 (디버깅용)
    os.makedirs("data", exist_ok=True)
    today_str = datetime.now().strftime("%Y%m%d")
    with open(f"data/raw_{today_str}.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)

    # 2단계: AI 분석 + HTML 생성
    print("\n[AI 분석] Claude API로 교차분석 중...")
    html = analyze_and_generate_html(all_data, ANTHROPIC_API_KEY)

    # 3단계: 결과 저장 (GitHub Pages 배포용)
    os.makedirs("docs", exist_ok=True)
    output_path = "docs/index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ 브리핑 페이지 생성 완료: {output_path}")
    print(f"=== 완료: {datetime.now()} ===")


if __name__ == "__main__":
    main()