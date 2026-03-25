# analyzer/ai_analyzer.py
import anthropic
import json
from datetime import datetime, timezone, timedelta

from config import PANEL_PASSWORD

KST = timezone(timedelta(hours=9))


def analyze_and_generate_html(all_data, api_key, channels_data=None, gh_repo=""):
    client = anthropic.Anthropic(api_key=api_key)

    by_type = {}
    for item in all_data:
        t = item["source_type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(item)

    summary_text = ""
    for source_type, items in by_type.items():
        summary_text += f"\n\n=== [{source_type}] ===\n"
        for item in items:
            summary_text += f"- 출처: {item['source_name']} | 제목: {item['title']} | 링크: {item.get('link','')}\n"
            if item.get('summary'):
                summary_text += f"  내용: {item['summary'][:500]}\n"

    today = datetime.now(KST).strftime("%Y년 %m월 %d일")

    prompt = f"""당신은 한국 주식시장 전문 AI 브리핑 애널리스트입니다.

아래는 오늘({today}) 수집된 4개 채널(뉴스, 경제방송, 증시유튜버, 애널리스트보고서)의 데이터입니다.

{summary_text}

위 데이터를 분석하여 아래 형식의 JSON을 생성해주세요:

{{
  "briefing_date": "{today}",
  "market_summary": {{
    "topic1": {{
      "title": "첫 번째 핵심 주제 제목",
      "content": "해당 주제에 대한 상세 분석 3~5문장"
    }},
    "topic2": {{
      "title": "두 번째 핵심 주제 제목",
      "content": "해당 주제에 대한 상세 분석 3~5문장"
    }},
    "topic3": {{
      "title": "세 번째 핵심 주제 제목",
      "content": "해당 주제에 대한 상세 분석 3~5문장"
    }}
  }},
  "hot_sectors": ["주목받는 섹터/테마 리스트"],
  "stocks": [
    {{
      "rank": 1,
      "name": "종목명",
      "description": "이 종목이 어떤 회사인지, 주요 사업영역, 최근 이슈 등 2~3문장 설명",
      "price_trend": "최근 주가 동향과 증시 흐름 속에서의 위치 2~3문장",
      "overlap_count": 4,
      "mentioned_in": ["뉴스", "경제방송", "유튜버", "애널리스트"],
      "reasons": {{
        "뉴스": {{
          "text": "뉴스에서 언급된 이유/맥락 요약",
          "source": "출처 매체명",
          "link": "해당 기사 또는 영상 URL"
        }},
        "경제방송": {{
          "text": "방송에서 언급된 이유/맥락 요약",
          "source": "출처 방송명",
          "link": "해당 영상 URL"
        }},
        "유튜버": {{
          "text": "유튜버가 언급한 이유/맥락 요약",
          "source": "출처 유튜버명",
          "link": "해당 영상 URL"
        }},
        "애널리스트": {{
          "text": "리포트 투자의견/목표가 요약",
          "source": "출처 증권사명",
          "link": "해당 리포트 URL"
        }}
      }},
      "catalyst": "주요 상승 촉매/모멘텀",
      "risk": "주의해야 할 리스크",
      "signal": "매수추천/중립/매도추천 중 하나"
    }}
  ],
  "overlap_analysis": "여기에 매우 상세한 교차분석 인사이트를 작성해주세요. 최소 400자 이상으로 다음 내용을 포함하세요: (1) 오늘 4개 채널에서 공통적으로 주목하는 종목과 그 이유 분석, (2) 현재 시장에서 형성되고 있는 투자 심리와 자금 흐름의 방향, (3) 섹터별 순환매 패턴과 향후 주목할 테마 전망, (4) 개인 투자자가 오늘 주의해야 할 리스크 요인과 대응 전략, (5) 단기 트레이딩 관점에서의 시사점과 중장기 투자자에게 주는 메시지. 구체적인 종목명과 수치를 포함하여 실질적인 투자 참고가 되도록 작성하세요.",
  "disclaimer": "본 브리핑은 AI가 자동 생성한 참고자료이며, 투자 판단의 책임은 본인에게 있습니다."
}}

중요 규칙:
1. overlap_count가 높은 종목을 우선 순위로 배치하세요.
2. 같은 overlap_count면 언급 강도/빈도가 높은 순으로 정렬하세요.
3. 실제 데이터에서 확인된 종목만 포함하세요. 추측하지 마세요.
4. 각 채널에서 언급되지 않았으면 해당 reasons는 빈 객체로 두세요.
5. 최소 5개 ~ 최대 20개 종목을 추출하세요.
6. reasons의 link는 반드시 수집 데이터에 있는 실제 URL을 사용하세요.
7. signal은 반드시 "매수추천", "중립", "매도추천" 중 하나만 사용하세요.
8. description에는 해당 기업의 사업 내용과 최근 핵심 이슈를 포함하세요.
9. price_trend에는 최근 주가 흐름, 시장 대비 강약, 거래량 변화 등을 포함하세요.
10. overlap_analysis는 반드시 400자 이상 상세하게 작성하세요.

JSON만 출력하세요. 다른 텍스트는 포함하지 마세요.
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    analysis = json.loads(response_text.strip())
    html = generate_html(analysis, channels_data, gh_repo)
    return html


def generate_html(data, channels_data=None, gh_repo=""):
    if channels_data is None:
        channels_data = {"broadcast": {}, "youtuber": {}}

    now_kst = datetime.now(KST).strftime("%H:%M")

    # === 시장 요약 (3가지 주제) ===
    market_summary = data.get("market_summary", {})
    if isinstance(market_summary, str):
        market_html = f"<p>{market_summary}</p>"
    else:
        market_html = ""
        for key in ["topic1", "topic2", "topic3"]:
            topic = market_summary.get(key, {})
            if topic:
                market_html += f"""
                <div class="topic-card">
                    <div class="topic-title">{topic.get("title","")}</div>
                    <div class="topic-content">{topic.get("content","")}</div>
                </div>"""

    # === 종목 카드 ===
    stocks_html = ""
    for stock in data.get("stocks", []):
        overlap = stock.get("overlap_count", 1)
        if overlap >= 4:
            badge_color = "#e74c3c"; badge_label = "⭐ 4채널 겹침"
        elif overlap >= 3:
            badge_color = "#e67e22"; badge_label = "🔥 3채널 겹침"
        elif overlap >= 2:
            badge_color = "#f39c12"; badge_label = "📌 2채널 겹침"
        else:
            badge_color = "#95a5a6"; badge_label = "1채널 언급"

        signal = stock.get("signal", "중립")
        if signal == "매수추천":
            sig_color = "#27ae60"; sig_icon = "🟢"; sig_bg = "rgba(81,207,102,0.1)"
        elif signal == "매도추천":
            sig_color = "#e74c3c"; sig_icon = "🔴"; sig_bg = "rgba(255,107,107,0.1)"
        else:
            sig_color = "#f39c12"; sig_icon = "🟡"; sig_bg = "rgba(255,169,77,0.1)"

        # 채널별 근거 (클릭 가능 링크)
        reasons_html = ""
        for channel, info in stock.get("reasons", {}).items():
            if isinstance(info, dict) and info.get("text"):
                source = info.get("source", "")
                link = info.get("link", "")
                if link:
                    source_tag = f'<a href="{link}" target="_blank" class="reason-source">[{source}]</a>'
                else:
                    source_tag = f'<span class="reason-source-nolink">[{source}]</span>'
                reasons_html += f"""
                <div class="reason-item">
                    <span class="reason-channel">{channel}</span>
                    <span class="reason-text">{source_tag} {info["text"]}</span>
                </div>"""
            elif isinstance(info, str) and info:
                reasons_html += f"""
                <div class="reason-item">
                    <span class="reason-channel">{channel}</span>
                    <span class="reason-text">{info}</span>
                </div>"""

        mentioned_tags = ""
        for ch in stock.get("mentioned_in", []):
            mentioned_tags += f'<span class="channel-tag">{ch}</span>'

        # 종목 설명 + 주가 동향
        description = stock.get("description", "")
        price_trend = stock.get("price_trend", "")

        stocks_html += f"""
        <div class="stock-card" data-overlap="{overlap}">
            <div class="stock-header">
                <div class="stock-rank">#{stock.get("rank","")}</div>
                <div class="stock-name">{stock.get("name","")}</div>
                <span class="overlap-badge" style="background:{badge_color}">{badge_label}</span>
                <span class="signal-badge" style="color:{sig_color};background:{sig_bg}">{sig_icon} {signal}</span>
            </div>
            <div class="channel-tags">{mentioned_tags}</div>
            <div class="stock-desc">
                <div class="desc-section">
                    <strong>🏢 종목 소개</strong>
                    <p>{description}</p>
                </div>
                <div class="desc-section">
                    <strong>📉 최근 주가 동향</strong>
                    <p>{price_trend}</p>
                </div>
            </div>
            <div class="catalyst"><strong>📈 상승 촉매:</strong> {stock.get("catalyst","")}</div>
            <div class="risk"><strong>⚠️ 리스크:</strong> {stock.get("risk","")}</div>
            <div class="reasons"><strong>📋 채널별 선정 근거:</strong>{reasons_html}</div>
        </div>"""

    sectors_html = ""
    for sector in data.get("hot_sectors", []):
        sectors_html += f'<span class="sector-tag">{sector}</span>'

    # === 채널 목록 ===
    broadcast_list = ""
    for name, info in channels_data.get("broadcast", {}).items():
        url = info.get("url", "")
        broadcast_list += f'<div class="ch-item"><a href="{url}" target="_blank">{name}</a><span class="ch-id">{info.get("id","")[:15]}...</span></div>'

    youtuber_list = ""
    for name, info in channels_data.get("youtuber", {}).items():
        url = info.get("url", "")
        youtuber_list += f'<div class="ch-item"><a href="{url}" target="_blank">{name}</a><span class="ch-id">{info.get("id","")[:15]}...</span></div>'

    channels_json_escaped = json.dumps(channels_data, ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'").replace("`", "\\`")

    # 인사이트
    overlap_analysis = data.get("overlap_analysis", "")

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 증시 모닝브리핑 - {data.get("briefing_date","")}</title>
    <style>
        :root {{ --bg-primary:#0a0e17; --bg-card:#151b2b; --bg-card-hover:#1a2236; --text-primary:#e8eaf6; --text-secondary:#8892b0; --accent-red:#ff6b6b; --accent-orange:#ffa94d; --accent-green:#51cf66; --accent-blue:#4dabf7; --border:#2a3450; }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:var(--bg-primary); color:var(--text-primary); line-height:1.7; padding:20px; }}
        .container {{ max-width:900px; margin:0 auto; }}

        .header {{ text-align:center; padding:40px 20px 30px; border-bottom:1px solid var(--border); margin-bottom:30px; position:relative; }}
        .header h1 {{ font-size:28px; background:linear-gradient(135deg,#4dabf7,#da77f2); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:8px; }}
        .header .date {{ color:var(--text-secondary); font-size:16px; }}
        .header .update-time {{ color:var(--accent-blue); font-size:13px; margin-top:4px; }}

        .ch-manage-btn {{ position:absolute; top:20px; right:20px; width:44px; height:44px; border-radius:50%; background:var(--bg-card); border:1px solid var(--border); color:var(--accent-blue); font-size:20px; cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s; }}
        .ch-manage-btn:hover {{ background:var(--accent-blue); color:white; }}

        /* 시장 요약 3주제 */
        .market-summary {{ margin-bottom:24px; }}
        .market-summary h2 {{ font-size:18px; color:var(--accent-blue); margin-bottom:16px; }}
        .topic-card {{ background:linear-gradient(135deg,#1a1f35,#1e2745); border:1px solid var(--border); border-radius:12px; padding:20px; margin-bottom:12px; }}
        .topic-title {{ font-size:16px; font-weight:700; color:var(--accent-orange); margin-bottom:8px; }}
        .topic-content {{ color:var(--text-secondary); font-size:14px; line-height:1.8; }}

        .hot-sectors {{ margin-bottom:24px; }}
        .hot-sectors h2 {{ font-size:18px; margin-bottom:12px; }}
        .sector-tag {{ display:inline-block; background:rgba(77,171,247,0.15); color:var(--accent-blue); padding:6px 14px; border-radius:20px; font-size:13px; margin:4px; border:1px solid rgba(77,171,247,0.3); }}

        /* 종목 카드 */
        .stock-card {{ background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:24px; margin-bottom:16px; transition:all 0.2s; }}
        .stock-card:hover {{ background:var(--bg-card-hover); border-color:var(--accent-blue); }}
        .stock-card[data-overlap="4"] {{ border-left:4px solid var(--accent-red); }}
        .stock-card[data-overlap="3"] {{ border-left:4px solid var(--accent-orange); }}
        .stock-card[data-overlap="2"] {{ border-left:4px solid var(--accent-blue); }}
        .stock-header {{ display:flex; align-items:center; gap:12px; margin-bottom:12px; flex-wrap:wrap; }}
        .stock-rank {{ font-size:24px; font-weight:800; color:var(--accent-blue); min-width:40px; }}
        .stock-name {{ font-size:20px; font-weight:700; }}
        .overlap-badge {{ color:white; padding:4px 12px; border-radius:12px; font-size:12px; font-weight:600; }}
        .signal-badge {{ padding:4px 14px; border-radius:12px; font-size:13px; font-weight:700; }}
        .channel-tags {{ margin-bottom:12px; }}
        .channel-tag {{ display:inline-block; background:rgba(255,255,255,0.06); color:var(--text-secondary); padding:3px 10px; border-radius:8px; font-size:12px; margin-right:6px; }}

        /* 종목 설명 + 주가 동향 */
        .stock-desc {{ margin-bottom:12px; }}
        .desc-section {{ background:rgba(255,255,255,0.03); border-radius:8px; padding:12px 14px; margin-bottom:8px; }}
        .desc-section strong {{ display:block; font-size:13px; margin-bottom:6px; color:var(--text-primary); }}
        .desc-section p {{ color:var(--text-secondary); font-size:13px; line-height:1.7; }}

        .catalyst,.risk {{ font-size:14px; margin-bottom:8px; padding:8px 12px; border-radius:8px; }}
        .catalyst {{ background:rgba(81,207,102,0.08); color:var(--accent-green); }}
        .risk {{ background:rgba(255,107,107,0.08); color:var(--accent-red); }}

        .reasons {{ margin-top:12px; font-size:14px; }}
        .reasons strong {{ display:block; margin-bottom:8px; }}
        .reason-item {{ display:flex; gap:10px; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.04); }}
        .reason-channel {{ min-width:80px; color:var(--accent-blue); font-weight:600; font-size:13px; }}
        .reason-text {{ color:var(--text-secondary); font-size:13px; line-height:1.6; }}
        .reason-source {{ color:var(--accent-orange); text-decoration:none; font-weight:600; cursor:pointer; }}
        .reason-source:hover {{ text-decoration:underline; color:var(--accent-blue); }}
        .reason-source-nolink {{ color:var(--accent-orange); font-weight:600; }}

        .filter-bar {{ margin-bottom:20px; display:flex; gap:8px; flex-wrap:wrap; }}
        .filter-btn {{ background:var(--bg-card); color:var(--text-secondary); border:1px solid var(--border); padding:8px 16px; border-radius:8px; cursor:pointer; font-size:13px; transition:all 0.2s; }}
        .filter-btn:hover,.filter-btn.active {{ background:var(--accent-blue); color:white; border-color:var(--accent-blue); }}

        /* 인사이트 (확장) */
        .insight {{ background:linear-gradient(135deg,#1e2745,#1a1f35); border:1px solid var(--border); border-radius:12px; padding:30px; margin-top:24px; }}
        .insight h2 {{ color:#da77f2; margin-bottom:16px; font-size:20px; }}
        .insight-content {{ color:var(--text-secondary); font-size:14px; line-height:2.0; white-space:pre-line; }}

        .disclaimer {{ text-align:center; color:var(--text-secondary); font-size:12px; margin-top:30px; padding:20px; border-top:1px solid var(--border); }}

        /* 채널 관리 패널 */
        .ch-panel-overlay {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:1000; }}
        .ch-panel-overlay.active {{ display:flex; align-items:center; justify-content:center; }}
        .ch-panel {{ background:var(--bg-primary); border:1px solid var(--border); border-radius:16px; width:90%; max-width:600px; max-height:85vh; overflow-y:auto; padding:30px; }}
        .ch-panel h2 {{ font-size:20px; color:var(--accent-blue); margin-bottom:20px; }}
        .ch-panel h3 {{ font-size:16px; color:var(--accent-orange); margin:20px 0 10px; }}
        .ch-panel .close-btn {{ float:right; background:none; border:none; color:var(--text-secondary); font-size:24px; cursor:pointer; }}
        .ch-panel .close-btn:hover {{ color:var(--accent-red); }}
        .ch-item {{ display:flex; align-items:center; justify-content:space-between; padding:10px 12px; background:var(--bg-card); border-radius:8px; margin-bottom:8px; }}
        .ch-item a {{ color:var(--accent-blue); text-decoration:none; font-weight:600; font-size:14px; }}
        .ch-item a:hover {{ text-decoration:underline; }}
        .ch-id {{ color:var(--text-secondary); font-size:11px; font-family:monospace; }}
        .add-form {{ background:var(--bg-card); border-radius:12px; padding:20px; margin-top:16px; }}
        .add-form h3 {{ color:var(--accent-green); margin:0 0 12px 0; }}
        .form-row {{ display:flex; gap:8px; margin-bottom:10px; flex-wrap:wrap; }}
        .form-row select,.form-row input {{ background:var(--bg-primary); border:1px solid var(--border); color:var(--text-primary); padding:10px 12px; border-radius:8px; font-size:14px; }}
        .form-row select {{ width:130px; }}
        .form-row input {{ flex:1; min-width:150px; }}
        .add-btn {{ background:var(--accent-green); color:#000; border:none; padding:10px 24px; border-radius:8px; font-size:14px; font-weight:700; cursor:pointer; width:100%; margin-top:8px; transition:all 0.2s; }}
        .add-btn:hover {{ background:#40c057; }}
        .add-btn:disabled {{ background:var(--text-secondary); cursor:not-allowed; }}
        .status-msg {{ margin-top:12px; padding:10px; border-radius:8px; font-size:13px; display:none; }}
        .status-msg.success {{ display:block; background:rgba(81,207,102,0.15); color:var(--accent-green); }}
        .status-msg.error {{ display:block; background:rgba(255,107,107,0.15); color:var(--accent-red); }}
        .help-text {{ color:var(--text-secondary); font-size:12px; margin-top:8px; line-height:1.6; }}

        /* 동적 추가 채널 표시 */
        #dynamicBroadcast, #dynamicYoutuber {{ }}
        .ch-item.new {{ border:1px solid var(--accent-green); }}

        @media (max-width:600px) {{
            body {{ padding:10px; }}
            .stock-header {{ flex-direction:column; align-items:flex-start; gap:6px; }}
            .header h1 {{ font-size:22px; }}
            .ch-manage-btn {{ top:10px; right:10px; width:36px; height:36px; font-size:16px; }}
            .reason-item {{ flex-direction:column; gap:4px; }}
            .reason-channel {{ min-width:auto; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI 증시 모닝브리핑</h1>
            <div class="date">{data.get("briefing_date","")}</div>
            <div class="update-time">자동 생성 시각(KST): {now_kst}</div>
            <button class="ch-manage-btn" onclick="openPanel()" title="수집 채널 관리">📡</button>
        </div>

        <!-- 채널 관리 패널 -->
        <div class="ch-panel-overlay" id="chPanel">
            <div class="ch-panel">
                <button class="close-btn" onclick="closePanel()">✕</button>
                <h2>📡 수집 채널 관리</h2>

                <h3>📺 경제전문방송</h3>
                <div id="broadcastList">{broadcast_list}</div>
                <div id="dynamicBroadcast"></div>

                <h3>🎬 증시 유튜버</h3>
                <div id="youtuberList">{youtuber_list}</div>
                <div id="dynamicYoutuber"></div>

                <div class="add-form">
                    <h3>➕ 새 채널 추가</h3>
                    <div class="form-row">
                        <select id="addType">
                            <option value="broadcast">경제방송</option>
                            <option value="youtuber">유튜버</option>
                        </select>
                        <input type="text" id="addName" placeholder="채널 이름 (예: 머니투데이)">
                    </div>
                    <div class="form-row">
                        <input type="text" id="addUrl" placeholder="유튜브 채널 주소 (예: https://www.youtube.com/@channelname)">
                    </div>
                    <button class="add-btn" id="addBtn" onclick="addChannel()">채널 추가 (다음 브리핑부터 반영)</button>
                    <div class="status-msg" id="statusMsg"></div>
                    <div class="help-text">
                        💡 유튜브 채널 주소만 입력하면 됩니다. 채널 ID는 자동으로 추출됩니다.<br>
                        ⏰ 추가한 채널은 <strong>다음 날 아침 브리핑</strong>부터 데이터 수집에 반영됩니다.
                    </div>
                </div>
            </div>
        </div>

        <div class="market-summary">
            <h2>📊 시장 요약</h2>
            {market_html}
        </div>

        <div class="hot-sectors">
            <h2>🔥 오늘의 핫 섹터</h2>
            {sectors_html}
        </div>

        <div class="filter-bar">
            <button class="filter-btn active" onclick="filterStocks('all')">전체</button>
            <button class="filter-btn" onclick="filterStocks(4)">⭐ 4채널</button>
            <button class="filter-btn" onclick="filterStocks(3)">🔥 3채널</button>
            <button class="filter-btn" onclick="filterStocks(2)">📌 2채널+</button>
        </div>

        <div id="stocks-container">{stocks_html}</div>

        <div class="insight">
            <h2>🧠 AI 교차분석 인사이트</h2>
            <div class="insight-content">{overlap_analysis}</div>
        </div>

        <div class="disclaimer">{data.get("disclaimer","본 브리핑은 AI가 자동 생성한 참고자료이며, 투자 판단의 책임은 본인에게 있습니다.")}</div>
    </div>

    <script>
        const REPO = "{gh_repo}";
        const FILE_PATH = "channels.json";

        function openPanel() {{ document.getElementById('chPanel').classList.add('active'); }}
        function closePanel() {{ document.getElementById('chPanel').classList.remove('active'); }}
        document.getElementById('chPanel').addEventListener('click', function(e) {{
            if (e.target === this) closePanel();
        }});

        function filterStocks(min) {{
            const cards = document.querySelectorAll('.stock-card');
            const btns = document.querySelectorAll('.filter-btn');
            btns.forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            cards.forEach(c => {{
                const o = parseInt(c.dataset.overlap);
                c.style.display = (min === 'all' || o >= min) ? 'block' : 'none';
            }});
        }}

        // URL에서 채널 ID 자동 추출
        async function extractChannelId(url) {{
            // @handle 형식에서 채널 ID 추출 시도
            // YouTube 페이지를 직접 조회할 수 없으므로 URL 자체를 ID 대용으로 사용
            // 실제로는 YouTube API로 채널 검색하여 ID를 가져옴
            const apiKey = ''; // 클라이언트에서는 API 키 없이 처리
            
            // UC로 시작하는 ID가 URL에 있으면 추출
            const channelMatch = url.match(/channel\\/(UC[\\w-]+)/);
            if (channelMatch) return channelMatch[1];
            
            // @handle 형식이면 handle 그대로 저장 (서버에서 변환)
            const handleMatch = url.match(/@([\\w-]+)/);
            if (handleMatch) return "@" + handleMatch[1];
            
            // /c/ 형식
            const cMatch = url.match(/\\/c\\/([\\w-]+)/);
            if (cMatch) return "c/" + cMatch[1];

            return url; // 그대로 반환
        }}

        async function addChannel() {{
            const type = document.getElementById('addType').value;
            const name = document.getElementById('addName').value.trim();
            const url = document.getElementById('addUrl').value.trim();
            const statusMsg = document.getElementById('statusMsg');
            const btn = document.getElementById('addBtn');

            if (!name || !url) {{
                statusMsg.className = 'status-msg error';
                statusMsg.textContent = '채널 이름과 유튜브 주소는 필수입니다.';
                return;
            }}

            btn.disabled = true;
            btn.textContent = '저장 중...';
            statusMsg.className = 'status-msg';
            statusMsg.style.display = 'none';

            try {{
                // 채널 ID 추출
                const channelId = await extractChannelId(url);

                // 1. 현재 channels.json 가져오기
                const getResp = await fetch(`https://api.github.com/repos/${{REPO}}/contents/${{FILE_PATH}}`, {{
                    headers: {{ 'Accept': 'application/vnd.github.v3+json' }}
                }});
                const fileData = await getResp.json();
                const sha = fileData.sha;
                const content = JSON.parse(atob(fileData.content));

                // 2. 새 채널 추가
                if (!content[type]) content[type] = {{}};
                content[type][name] = {{ id: channelId, url: url }};

                // 3. GitHub에 저장
                const token = prompt('GitHub Personal Access Token을 입력하세요:');
                if (!token) {{
                    btn.disabled = false;
                    btn.textContent = '채널 추가 (다음 브리핑부터 반영)';
                    return;
                }}

                const updateResp = await fetch(`https://api.github.com/repos/${{REPO}}/contents/${{FILE_PATH}}`, {{
                    method: 'PUT',
                    headers: {{
                        'Accept': 'application/vnd.github.v3+json',
                        'Authorization': `token ${{token}}`,
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        message: `📡 채널 추가: ${{name}}`,
                        content: btoa(unescape(encodeURIComponent(JSON.stringify(content, null, 2)))),
                        sha: sha
                    }})
                }});

                if (updateResp.ok) {{
                    statusMsg.className = 'status-msg success';
                    statusMsg.textContent = `✅ "${{name}}" 채널이 추가되었습니다! 다음 아침 브리핑부터 반영됩니다.`;

                    // 화면에 즉시 반영
                    const targetDiv = type === 'broadcast' 
                        ? document.getElementById('dynamicBroadcast')
                        : document.getElementById('dynamicYoutuber');
                    
                    const newItem = document.createElement('div');
                    newItem.className = 'ch-item new';
                    newItem.innerHTML = `<a href="${{url}}" target="_blank">${{name}}</a><span class="ch-id" style="color:var(--accent-green);">✅ 새로 추가됨</span>`;
                    targetDiv.appendChild(newItem);

                    // 입력 필드 초기화
                    document.getElementById('addName').value = '';
                    document.getElementById('addUrl').value = '';
                }} else {{
                    const err = await updateResp.json();
                    statusMsg.className = 'status-msg error';
                    statusMsg.textContent = `❌ 저장 실패: ${{err.message}}`;
                }}
            }} catch (e) {{
                statusMsg.className = 'status-msg error';
                statusMsg.textContent = `❌ 오류: ${{e.message}}`;
            }}

            btn.disabled = false;
            btn.textContent = '채널 추가 (다음 브리핑부터 반영)';
        }}
    </script>
</body>
</html>"""
    return html
