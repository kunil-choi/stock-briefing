# analyzer/ai_analyzer.py
import anthropic
import json
from datetime import datetime

def analyze_and_generate_html(
    all_data: list,
    api_key: str,
    template_path: str = "templates/briefing_template.html"
) -> str:
    """
    수집된 전체 데이터를 Claude API에 보내서:
    1) 4개 채널별 언급 종목 추출
    2) 겹치는 종목 교차 분석
    3) 우선순위 결정 + 근거 요약
    4) HTML 브리핑 페이지 생성
    """
    client = anthropic.Anthropic(api_key=api_key)

    # 데이터를 채널별로 정리
    by_type = {}
    for item in all_data:
        t = item["source_type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(item)

    # 요약 데이터 구성 (토큰 절약을 위해 제목+요약만)
    summary_text = ""
    for source_type, items in by_type.items():
        summary_text += f"\n\n=== [{source_type}] ===\n"
        for item in items:
            summary_text += (
                f"- 출처: {item['source_name']} | "
                f"제목: {item['title']}\n"
            )
            if item['summary']:
                summary_text += f"  내용 요약: {item['summary'][:500]}\n"

    today = datetime.now().strftime("%Y년 %m월 %d일")

    prompt = f"""당신은 한국 주식시장 전문 AI 브리핑 애널리스트입니다.

아래는 오늘({today}) 수집된 4개 채널(뉴스, 경제방송, 증시유튜버, 애널리스트보고서)의 데이터입니다.

{summary_text}

---

위 데이터를 분석하여 아래 형식의 JSON을 생성해주세요:

{{
  "briefing_date": "{today}",
  "market_summary": "오늘의 전체 시장 분위기 요약 (2-3문장)",
  "hot_sectors": ["주목받는 섹터/테마 리스트"],
  "stocks": [
    {{
      "rank": 1,
      "name": "종목명",
      "code": "종목코드(알면)",
      "overlap_count": 4개 채널 중 몇 개에서 언급되었는지 (1~4),
      "mentioned_in": ["뉴스", "경제방송", "유튜버", "애널리스트"],
      "reasons": {{
        "뉴스": "뉴스에서 언급된 이유/맥락 요약",
        "경제방송": "방송에서 언급된 이유/맥락 요약",
        "유튜버": "유튜버가 언급한 이유/맥락 요약",
        "애널리스트": "리포트에서의 투자의견/목표가 요약"
      }},
      "catalyst": "주요 상승 촉매/모멘텀",
      "risk": "주의해야 할 리스크",
      "sentiment": "긍정/중립/주의 중 하나"
    }}
  ],
  "overlap_analysis": "겹치는 종목이 많이 나타나는 패턴에 대한 인사이트",
  "disclaimer": "본 브리핑은 AI가 자동 생성한 참고자료이며, 투자 판단의 책임은 본인에게 있습니다."
}}

중요 규칙:
1. overlap_count가 높은 종목을 우선 순위로 배치하세요.
2. 같은 overlap_count면 언급 강도/빈도가 높은 순으로 정렬하세요.
3. 실제 데이터에서 확인된 종목만 포함하세요. 추측하지 마세요.
4. 각 채널에서 언급되지 않았으면 해당 reasons는 빈 문자열로 두세요.
5. 최소 5개 ~ 최대 20개 종목을 추출하세요.

JSON만 출력하세요. 다른 텍스트는 포함하지 마세요.
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    # JSON 파싱
    response_text = message.content[0].text
    # JSON 블록 추출
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    analysis = json.loads(response_text.strip())
    html = generate_html(analysis)
    return html


def generate_html(data: dict) -> str:
    """분석 결과 JSON을 시각적인 HTML 브리핑 페이지로 변환합니다."""

    stocks_html = ""
    for stock in data.get("stocks", []):
        # 겹침 정도에 따른 색상
        overlap = stock.get("overlap_count", 1)
        if overlap >= 4:
            badge_color = "#e74c3c"
            badge_label = "⭐ 4채널 겹침"
        elif overlap >= 3:
            badge_color = "#e67e22"
            badge_label = "🔥 3채널 겹침"
        elif overlap >= 2:
            badge_color = "#f39c12"
            badge_label = "📌 2채널 겹침"
        else:
            badge_color = "#95a5a6"
            badge_label = "1채널 언급"

        # 감성에 따른 색상
        sentiment = stock.get("sentiment", "중립")
        if sentiment == "긍정":
            sent_color = "#27ae60"
            sent_icon = "🟢"
        elif sentiment == "주의":
            sent_color = "#e74c3c"
            sent_icon = "🔴"
        else:
            sent_color = "#f39c12"
            sent_icon = "🟡"

        # 각 채널별 근거
        reasons_html = ""
        for channel, reason in stock.get("reasons", {}).items():
            if reason:
                reasons_html += f"""
                <div class="reason-item">
                    <span class="reason-channel">{channel}</span>
                    <span class="reason-text">{reason}</span>
                </div>"""

        # 언급 채널 태그
        mentioned_tags = ""
        for ch in stock.get("mentioned_in", []):
            mentioned_tags += f'<span class="channel-tag">{ch}</span>'

        stocks_html += f"""
        <div class="stock-card" data-overlap="{overlap}">
            <div class="stock-header">
                <div class="stock-rank">#{stock.get("rank", "")}</div>
                <div class="stock-name">{stock.get("name", "")}</div>
                <span class="overlap-badge" style="background:{badge_color}">{badge_label}</span>
                <span class="sentiment-badge" style="color:{sent_color}">{sent_icon} {sentiment}</span>
            </div>
            <div class="channel-tags">{mentioned_tags}</div>
            <div class="catalyst">
                <strong>📈 상승 촉매:</strong> {stock.get("catalyst", "")}
            </div>
            <div class="risk">
                <strong>⚠️ 리스크:</strong> {stock.get("risk", "")}
            </div>
            <div class="reasons">
                <strong>📋 채널별 선정 근거:</strong>
                {reasons_html}
            </div>
        </div>"""

    # 핫 섹터 태그
    sectors_html = ""
    for sector in data.get("hot_sectors", []):
        sectors_html += f'<span class="sector-tag">{sector}</span>'

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 증시 모닝브리핑 - {data.get("briefing_date", "")}</title>
    <style>
        :root {{
            --bg-primary: #0a0e17;
            --bg-card: #151b2b;
            --bg-card-hover: #1a2236;
            --text-primary: #e8eaf6;
            --text-secondary: #8892b0;
            --accent-red: #ff6b6b;
            --accent-orange: #ffa94d;
            --accent-green: #51cf66;
            --accent-blue: #4dabf7;
            --border: #2a3450;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont,
                         'Segoe UI', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.7;
            padding: 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}

        /* 헤더 */
        .header {{
            text-align: center;
            padding: 40px 20px 30px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 28px;
            background: linear-gradient(135deg, #4dabf7, #da77f2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .header .date {{
            color: var(--text-secondary);
            font-size: 16px;
        }}
        .header .update-time {{
            color: var(--accent-blue);
            font-size: 13px;
            margin-top: 4px;
        }}

        /* 시장 요약 */
        .market-summary {{
            background: linear-gradient(135deg, #1a1f35, #1e2745);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .market-summary h2 {{
            font-size: 18px;
            color: var(--accent-blue);
            margin-bottom: 12px;
        }}
        .market-summary p {{
            color: var(--text-secondary);
            font-size: 15px;
        }}

        /* 핫 섹터 */
        .hot-sectors {{
            margin-bottom: 24px;
        }}
        .hot-sectors h2 {{
            font-size: 18px;
            margin-bottom: 12px;
        }}
        .sector-tag {{
            display: inline-block;
            background: rgba(77, 171, 247, 0.15);
            color: var(--accent-blue);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            margin: 4px;
            border: 1px solid rgba(77, 171, 247, 0.3);
        }}

        /* 종목 카드 */
        .stock-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 16px;
            transition: all 0.2s;
        }}
        .stock-card:hover {{
            background: var(--bg-card-hover);
            border-color: var(--accent-blue);
        }}
        .stock-card[data-overlap="4"] {{
            border-left: 4px solid var(--accent-red);
        }}
        .stock-card[data-overlap="3"] {{
            border-left: 4px solid var(--accent-orange);
        }}
        .stock-card[data-overlap="2"] {{
            border-left: 4px solid var(--accent-blue);
        }}
        .stock-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }}
        .stock-rank {{
            font-size: 24px;
            font-weight: 800;
            color: var(--accent-blue);
            min-width: 40px;
        }}
        .stock-name {{
            font-size: 20px;
            font-weight: 700;
        }}
        .overlap-badge {{
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .sentiment-badge {{
            font-size: 14px;
            font-weight: 600;
        }}
        .channel-tags {{
            margin-bottom: 12px;
        }}
        .channel-tag {{
            display: inline-block;
            background: rgba(255,255,255,0.06);
            color: var(--text-secondary);
            padding: 3px 10px;
            border-radius: 8px;
            font-size: 12px;
            margin-right: 6px;
        }}
        .catalyst, .risk {{
            font-size: 14px;
            margin-bottom: 8px;
            padding: 8px 12px;
            border-radius: 8px;
        }}
        .catalyst {{
            background: rgba(81, 207, 102, 0.08);
            color: var(--accent-green);
        }}
        .risk {{
            background: rgba(255, 107, 107, 0.08);
            color: var(--accent-red);
        }}
        .reasons {{
            margin-top: 12px;
            font-size: 14px;
        }}
        .reasons strong {{
            display: block;
            margin-bottom: 8px;
            color: var(--text-primary);
        }}
        .reason-item {{
            display: flex;
            gap: 10px;
            padding: 6px 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }}
        .reason-channel {{
            min-width: 80px;
            color: var(--accent-blue);
            font-weight: 600;
            font-size: 13px;
        }}
        .reason-text {{
            color: var(--text-secondary);
            font-size: 13px;
        }}

        /* 분석 인사이트 */
        .insight {{
            background: linear-gradient(135deg, #1e2745, #1a1f35);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-top: 24px;
        }}
        .insight h2 {{
            color: #da77f2;
            margin-bottom: 12px;
        }}

        /* 면책조항 */
        .disclaimer {{
            text-align: center;
            color: var(--text-secondary);
            font-size: 12px;
            margin-top: 30px;
            padding: 20px;
            border-top: 1px solid var(--border);
        }}

        /* 필터 버튼 */
        .filter-bar {{
            margin-bottom: 20px;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .filter-btn {{
            background: var(--bg-card);
            color: var(--text-secondary);
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
        }}
        .filter-btn:hover, .filter-btn.active {{
            background: var(--accent-blue);
            color: white;
            border-color: var(--accent-blue);
        }}

        @media (max-width: 600px) {{
            body {{ padding: 10px; }}
            .stock-header {{ flex-direction: column; align-items: flex-start; gap: 6px; }}
            .header h1 {{ font-size: 22px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 AI 증시 모닝브리핑</h1>
            <div class="date">{data.get("briefing_date", "")}</div>
            <div class="update-time">자동 생성 시각: {datetime.now().strftime("%H:%M")}</div>
        </div>

        <div class="market-summary">
            <h2>📊 시장 요약</h2>
            <p>{data.get("market_summary", "")}</p>
        </div>

        <div class="hot-sectors">
            <h2>🔥 오늘의 핫 섹터</h2>
            {sectors_html}
        </div>

        <div class="filter-bar">
            <button class="filter-btn active" onclick="filterStocks('all')">전체</button>
            <button class="filter-btn" onclick="filterStocks(4)">⭐ 4채널 겹침</button>
            <button class="filter-btn" onclick="filterStocks(3)">🔥 3채널 겹침</button>
            <button class="filter-btn" onclick="filterStocks(2)">📌 2채널 이상</button>
        </div>

        <div id="stocks-container">
            {stocks_html}
        </div>

        <div class="insight">
            <h2>🧠 AI 교차분석 인사이트</h2>
            <p>{data.get("overlap_analysis", "")}</p>
        </div>

        <div class="disclaimer">
            {data.get("disclaimer", "본 브리핑은 AI가 자동 생성한 참고자료이며, 투자 판단의 책임은 본인에게 있습니다.")}
        </div>
    </div>

    <script>
        function filterStocks(minOverlap) {{
            const cards = document.querySelectorAll('.stock-card');
            const btns = document.querySelectorAll('.filter-btn');
            btns.forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');

            cards.forEach(card => {{
                const overlap = parseInt(card.dataset.overlap);
                if (minOverlap === 'all' || overlap >= minOverlap) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>"""
    return html