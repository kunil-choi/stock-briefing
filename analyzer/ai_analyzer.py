import anthropic
import json
from datetime import datetime, timezone, timedelta
from config import PANEL_PASSWORD

KST = timezone(timedelta(hours=9))

def analyze_and_generate_html(all_data, api_key, channels_data=None, gh_repo=""):
    """Claude API를 사용하여 데이터를 분석하고 HTML을 생성합니다."""
    
    # 데이터를 소스 타입별로 그룹화
    grouped = {}
    for item in all_data:
        source_type = item.get("source_type", "unknown")
        if source_type not in grouped:
            grouped[source_type] = []
        grouped[source_type].append(item)
    
    # 요약 텍스트 생성
    summary_parts = []
    for source_type, items in grouped.items():
        summary_parts.append(f"\n=== {source_type} ({len(items)}건) ===")
        for item in items:
            title = item.get("title", "")
            content = item.get("content", "")[:500]
            channel = item.get("channel_name", "")
            link = item.get("link", "")
            summary_parts.append(f"[{channel}] {title}")
            if content:
                summary_parts.append(f"  내용: {content}")
            if link:
                summary_parts.append(f"  링크: {link}")
    
    full_summary = "\n".join(summary_parts)
    
    prompt = f"""당신은 한국 주식시장 전문 AI 애널리스트입니다.

아래는 오늘 수집된 경제 뉴스, 방송, 유튜브, 애널리스트 리포트 데이터입니다:

{full_summary}

위 데이터를 종합 분석하여 아래 JSON 형식으로 결과를 작성해주세요:

{{
  "briefing_date": "YYYY년 MM월 DD일",
  "market_summary": [
    {{"title": "주제1", "content": "설명 (200자 이상)"}},
    {{"title": "주제2", "content": "설명 (200자 이상)"}},
    {{"title": "주제3", "content": "설명 (200자 이상)"}}
  ],
  "hot_sectors": ["섹터1", "섹터2", "섹터3", "섹터4", "섹터5"],
  "stocks": [
    {{
      "rank": 1,
      "name": "종목명",
      "overlap_count": 4,
      "reasons": {{
        "채널명1": {{"text": "추천 사유", "source": "출처명", "link": "URL"}},
        "채널명2": {{"text": "추천 사유", "source": "출처명", "link": "URL"}}
      }},
      "description": "종목 설명 (100자 이상)",
      "price_trend": "최근 주가 흐름",
      "catalyst": "상승 촉매",
      "risk": "리스크 요인",
      "signal": "긍정전망/중립/부정전망 중 하나"
    }}
  ],
  "hidden_picks": [
    {{
      "name": "종목명",
      "source_name": "발굴 채널명",
      "source_link": "URL",
      "reason": "추천 사유 (200자 이상)",
      "potential": "향후 가능성 분석 (200자 이상)",
      "catalyst": "핵심 촉매",
      "risk": "리스크",
      "signal": "긍정전망/중립/부정전망 중 하나"
    }}
  ],
  "overlap_analysis": "겹침 종목 심층 분석 (400자 이상)",
  "disclaimer": "본 브리핑은 AI가 자동 생성한 참고 자료이며, 투자 판단의 근거로 사용할 수 없습니다."
}}

규칙:
1. stocks는 overlap_count가 높은 순으로 최대 10개
2. hidden_picks는 1개 채널에서만 언급됐지만 잠재력 높은 종목 최대 5개
3. 모든 텍스트는 한국어로 작성
4. reasons의 각 채널별 text는 해당 채널에서 실제 언급된 내용 기반
5. link는 실제 수집된 URL만 사용 (없으면 빈 문자열)
6. hot_sectors는 가장 많이 언급된 섹터 5개
7. signal은 "긍정전망", "중립", "부정전망" 중 하나만 사용
8. JSON만 출력하고 다른 텍스트는 포함하지 마세요"""

    client = anthropic.Anthropic(api_key=api_key)
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    # JSON 추출
    try:
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0]
        else:
            json_str = response_text
        
        data = json.loads(json_str.strip())
    except json.JSONDecodeError:
        data = {
            "briefing_date": datetime.now(KST).strftime("%Y년 %m월 %d일"),
            "market_summary": [{"title": "데이터 파싱 오류", "content": "AI 응답을 파싱하는 중 오류가 발생했습니다."}],
            "hot_sectors": [],
            "stocks": [],
            "hidden_picks": [],
            "overlap_analysis": "",
            "disclaimer": "본 브리핑은 AI가 자동 생성한 참고 자료이며, 투자 판단의 근거로 사용할 수 없습니다."
        }
    
    # briefing_data.json 저장
    with open("data/briefing_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    html = generate_html(data, channels_data, gh_repo)
    return html


def generate_html(data, channels_data=None, gh_repo=""):
    """분석 데이터를 HTML 페이지로 변환합니다."""
    
    now = datetime.now(KST)
    update_time = now.strftime("%Y-%m-%d %H:%M KST")
    briefing_date = data.get("briefing_date", now.strftime("%Y년 %m월 %d일"))
    market_summary = data.get("market_summary", [])
    hot_sectors = data.get("hot_sectors", [])
    stocks = data.get("stocks", [])
    hidden_picks = data.get("hidden_picks", [])
    overlap_analysis = data.get("overlap_analysis", "")
    disclaimer = data.get("disclaimer", "")
    
    # 채널 데이터 처리
    broadcast_channels = {}
    youtuber_channels = {}
    if channels_data:
        broadcast_channels = channels_data.get("broadcast", {})
        youtuber_channels = channels_data.get("youtuber", {})
    
    # --- CSS ---
    css = """
    <style>
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #111827;
            --bg-card: #1a2332;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --accent-blue: #4dabf7;
            --accent-orange: #ffa94d;
            --accent-green: #51cf66;
            --accent-red: #ff6b6b;
            --accent-purple: #b197fc;
            --border-color: rgba(255,255,255,0.08);
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary); color: var(--text-primary);
            line-height: 1.7; min-height: 100vh;
        }
        .container { max-width: 900px; margin: 0 auto; padding: 20px 16px; }
        
        /* Header */
        .header { text-align: center; padding: 30px 0 20px; position: relative; }
        .header h1 { font-size: 1.8em; font-weight: 800; margin-bottom: 8px; }
        .header h1 span { background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .update-time { color: var(--text-secondary); font-size: 0.85em; }
        .source-info { color: var(--text-secondary); font-size: 0.8em; margin-top: 4px; }
        .settings-btn {
            position: absolute; top: 30px; right: 0;
            background: var(--bg-card); border: 1px solid var(--border-color);
            color: var(--text-secondary); width: 40px; height: 40px;
            border-radius: 10px; cursor: pointer; font-size: 1.2em;
            display: flex; align-items: center; justify-content: center;
            transition: all 0.2s;
        }
        .settings-btn:hover { color: var(--accent-blue); border-color: var(--accent-blue); }
        
        /* Summary Cards */
        .summary-section { margin: 24px 0; }
        .summary-section h2 { font-size: 1.2em; margin-bottom: 12px; color: var(--accent-blue); }
        .summary-card {
            background: var(--bg-card); border: 1px solid var(--border-color);
            border-radius: 12px; padding: 16px; margin-bottom: 10px;
        }
        .summary-card h3 { font-size: 1em; color: var(--accent-orange); margin-bottom: 6px; }
        .summary-card p { font-size: 0.9em; color: var(--text-secondary); }
        
        /* Sectors */
        .sectors { display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0; }
        .sector-tag {
            background: rgba(77,171,247,0.1); border: 1px solid rgba(77,171,247,0.3);
            color: var(--accent-blue); padding: 6px 14px; border-radius: 20px;
            font-size: 0.82em; font-weight: 600;
        }
        
        /* Filter */
        .filter-bar { display: flex; gap: 8px; margin: 20px 0 12px; flex-wrap: wrap; }
        .filter-btn {
            background: var(--bg-card); border: 1px solid var(--border-color);
            color: var(--text-secondary); padding: 6px 14px; border-radius: 8px;
            font-size: 0.82em; cursor: pointer; transition: all 0.2s;
        }
        .filter-btn.active, .filter-btn:hover {
            background: var(--accent-blue); color: white; border-color: var(--accent-blue);
        }
        
        /* Stock Cards */
        .stock-card {
            background: var(--bg-card); border: 1px solid var(--border-color);
            border-radius: 14px; padding: 18px; margin-bottom: 12px;
            transition: border-color 0.2s;
        }
        .stock-card:hover { border-color: var(--accent-blue); }
        .stock-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
        .stock-rank {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            color: white; width: 28px; height: 28px; border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 0.85em;
        }
        .stock-name { font-size: 1.15em; font-weight: 700; }
        .badge {
            padding: 3px 10px; border-radius: 6px; font-size: 0.75em; font-weight: 700;
        }
        .badge-overlap { background: rgba(255,169,77,0.15); color: var(--accent-orange); }
        .badge-signal {
            padding: 3px 10px; border-radius: 6px; font-size: 0.75em; font-weight: 700;
        }
        .stock-desc { color: var(--text-secondary); font-size: 0.88em; margin-bottom: 10px; }
        .stock-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
        .meta-item { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 10px; }
        .meta-label { font-size: 0.75em; color: var(--text-secondary); margin-bottom: 3px; }
        .meta-value { font-size: 0.85em; }
        
        /* Reasons */
        .reasons-section { border-top: 1px solid var(--border-color); padding-top: 10px; }
        .reasons-title { font-size: 0.82em; color: var(--accent-blue); margin-bottom: 8px; font-weight: 600; }
        .reason-item { 
            display: flex; align-items: flex-start; gap: 8px; 
            margin-bottom: 6px; font-size: 0.85em; 
        }
        .reason-channel {
            background: rgba(177,151,252,0.15); color: var(--accent-purple);
            padding: 2px 8px; border-radius: 4px; font-size: 0.78em;
            font-weight: 600; white-space: nowrap; flex-shrink: 0;
        }
        .reason-text { color: var(--text-secondary); }
        .reason-source-nolink { color: var(--accent-orange); font-weight: 600; }
        .view-btn {
            display: inline-block; background: rgba(77,171,247,0.15);
            color: var(--accent-blue); padding: 2px 10px; border-radius: 6px;
            font-size: 11px; font-weight: 600; text-decoration: none;
            margin-left: 6px; border: 1px solid rgba(77,171,247,0.3);
            white-space: nowrap;
        }
        .view-btn:hover { background: var(--accent-blue); color: white; }
        
        /* Hidden Picks */
        .hidden-section { margin: 30px 0; }
        .hidden-section h2 { font-size: 1.2em; color: var(--accent-purple); margin-bottom: 12px; }
        .hidden-card {
            background: var(--bg-card); border: 1px solid rgba(177,151,252,0.3);
            border-radius: 14px; padding: 18px; margin-bottom: 12px;
        }
        .hidden-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
        .hidden-name { font-size: 1.1em; font-weight: 700; }
        .hidden-source { font-size: 0.85em; color: var(--text-secondary); }
        .hidden-reason, .hidden-potential { font-size: 0.88em; color: var(--text-secondary); margin-bottom: 8px; }
        .hidden-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
        
        /* Analysis */
        .analysis-section {
            background: var(--bg-card); border: 1px solid var(--border-color);
            border-radius: 14px; padding: 20px; margin: 24px 0;
        }
        .analysis-section h2 { font-size: 1.1em; color: var(--accent-green); margin-bottom: 10px; }
        .analysis-section p { font-size: 0.9em; color: var(--text-secondary); }
        
        /* Disclaimer */
        .disclaimer {
            text-align: center; color: var(--text-secondary);
            font-size: 0.78em; padding: 20px 0; border-top: 1px solid var(--border-color);
            margin-top: 30px;
        }
        
        /* Panel Overlay */
        .panel-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.8); z-index: 1000; overflow-y: auto;
        }
        .panel-content {
            max-width: 600px; margin: 40px auto; background: var(--bg-secondary);
            border-radius: 16px; padding: 24px; border: 1px solid var(--border-color);
        }
        .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .panel-header h2 { font-size: 1.2em; }
        .panel-close {
            background: none; border: none; color: var(--text-secondary);
            font-size: 1.5em; cursor: pointer;
        }
        .channel-group { margin-bottom: 20px; }
        .channel-group h3 { font-size: 0.95em; color: var(--accent-blue); margin-bottom: 8px; }
        .channel-item {
            display: flex; justify-content: space-between; align-items: center;
            background: var(--bg-card); padding: 10px 14px; border-radius: 8px;
            margin-bottom: 6px; font-size: 0.85em;
        }
        .add-form { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
        .add-form input, .add-form select {
            background: var(--bg-card); border: 1px solid var(--border-color);
            color: var(--text-primary); padding: 8px 12px; border-radius: 8px;
            font-size: 0.85em; flex: 1; min-width: 120px;
        }
        .add-form button {
            background: var(--accent-blue); color: white; border: none;
            padding: 8px 16px; border-radius: 8px; cursor: pointer;
            font-weight: 600; font-size: 0.85em;
        }
        .token-input {
            width: 100%; background: var(--bg-card); border: 1px solid var(--border-color);
            color: var(--text-primary); padding: 8px 12px; border-radius: 8px;
            font-size: 0.85em; margin-bottom: 12px;
        }
        
        @media (max-width: 600px) {
            .container { padding: 12px 10px; }
            .header h1 { font-size: 1.4em; }
            .stock-meta, .hidden-meta { grid-template-columns: 1fr; }
        }
    </style>
    """
    
    # --- Market Summary HTML ---
    summary_html = ""
    for item in market_summary:
        summary_html += f"""
        <div class="summary-card">
            <h3>{item.get("title", "")}</h3>
            <p>{item.get("content", "")}</p>
        </div>"""
    
    # --- Sectors HTML ---
    sectors_html = ""
    for sector in hot_sectors:
        sectors_html += f'<span class="sector-tag">{sector}</span>'
    
    # --- Stock Cards HTML ---
    stocks_html = ""
    all_signals = set()
    for stock in stocks:
        rank = stock.get("rank", "")
        name = stock.get("name", "")
        overlap = stock.get("overlap_count", 0)
        signal = stock.get("signal", "중립")
        description = stock.get("description", "")
        price_trend = stock.get("price_trend", "")
        catalyst = stock.get("catalyst", "")
        risk = stock.get("risk", "")
        reasons = stock.get("reasons", {})
        
        all_signals.add(signal)
        
        if signal == "긍정전망":
            sig_color = "#27ae60"; sig_icon = "🟢"; sig_bg = "rgba(81,207,102,0.1)"
        elif signal == "부정전망":
            sig_color = "#e74c3c"; sig_icon = "🔴"; sig_bg = "rgba(255,107,107,0.1)"
        else:
            sig_color = "#f39c12"; sig_icon = "🟡"; sig_bg = "rgba(255,169,77,0.1)"
        
        # Reasons HTML
        reasons_html = ""
        for channel, info in reasons.items():
            if isinstance(info, dict):
                text = info.get("text", "")
                source = info.get("source", "")
                link = info.get("link", "")
            else:
                text = str(info)
                source = ""
                link = ""
            
            if link:
                source_tag = f'<span class="reason-source-nolink">[{source}]</span>'
                view_btn = f'<a href="{link}" target="_blank" class="view-btn">직접 보기 →</a>'
            else:
                source_tag = f'<span class="reason-source-nolink">[{source}]</span>'
                view_btn = ""
            
            reasons_html += f"""
                <div class="reason-item">
                    <span class="reason-channel">{channel}</span>
                    <span class="reason-text">{source_tag} {text} {view_btn}</span>
                </div>"""
        
        stocks_html += f"""
        <div class="stock-card" data-signal="{signal}">
            <div class="stock-header">
                <div class="stock-rank">{rank}</div>
                <span class="stock-name">{name}</span>
                <span class="badge badge-overlap">{overlap}개 채널</span>
                <span class="badge-signal" style="background:{sig_bg}; color:{sig_color};">{sig_icon} {signal}</span>
            </div>
            <div class="stock-desc">{description}</div>
            <div class="stock-meta">
                <div class="meta-item"><div class="meta-label">📈 주가 흐름</div><div class="meta-value">{price_trend}</div></div>
                <div class="meta-item"><div class="meta-label">🚀 촉매</div><div class="meta-value">{catalyst}</div></div>
                <div class="meta-item"><div class="meta-label">⚠️ 리스크</div><div class="meta-value">{risk}</div></div>
                <div class="meta-item"><div class="meta-label">📊 시그널</div><div class="meta-value" style="color:{sig_color};">{sig_icon} {signal}</div></div>
            </div>
            <div class="reasons-section">
                <div class="reasons-title">📋 채널별 선정 근거</div>
                {reasons_html}
            </div>
        </div>"""
    
    # --- Hidden Picks HTML ---
    hidden_html = ""
    for pick in hidden_picks:
        pname = pick.get("name", "")
        source_name = pick.get("source_name", "")
        source_link = pick.get("source_link", "")
        reason = pick.get("reason", "")
        potential = pick.get("potential", "")
        p_catalyst = pick.get("catalyst", "")
        p_risk = pick.get("risk", "")
        p_signal = pick.get("signal", "중립")
        
        if p_signal == "긍정전망":
            ps_color = "#27ae60"; ps_icon = "🟢"; ps_bg = "rgba(81,207,102,0.1)"
        elif p_signal == "부정전망":
            ps_color = "#e74c3c"; ps_icon = "🔴"; ps_bg = "rgba(255,107,107,0.1)"
        else:
            ps_color = "#f39c12"; ps_icon = "🟡"; ps_bg = "rgba(255,169,77,0.1)"
        
        if source_link:
            source_tag = f'<span class="reason-source-nolink">{source_name}</span> <a href="{source_link}" target="_blank" class="view-btn">직접 보기 →</a>'
        else:
            source_tag = f'<span class="reason-source-nolink">{source_name}</span>'
        
        hidden_html += f"""
        <div class="hidden-card">
            <div class="hidden-header">
                <span class="hidden-name">💎 {pname}</span>
                <span class="badge-signal" style="background:{ps_bg}; color:{ps_color};">{ps_icon} {p_signal}</span>
            </div>
            <div class="hidden-source">발굴: {source_tag}</div>
            <div class="hidden-reason"><strong>선정 사유:</strong> {reason}</div>
            <div class="hidden-potential"><strong>향후 가능성:</strong> {potential}</div>
            <div class="hidden-meta">
                <div class="meta-item"><div class="meta-label">🚀 촉매</div><div class="meta-value">{p_catalyst}</div></div>
                <div class="meta-item"><div class="meta-label">⚠️ 리스크</div><div class="meta-value">{p_risk}</div></div>
            </div>
        </div>"""
    
    # --- Filter buttons ---
    filter_html = '<button class="filter-btn active" onclick="filterStocks(\'all\')">전체</button>'
    for sig in ["긍정전망", "중립", "부정전망"]:
        filter_html += f'<button class="filter-btn" onclick="filterStocks(\'{sig}\')">{sig}</button>'
    
    # --- Channel list for panel ---
    broadcast_list_html = ""
    for name, info in broadcast_channels.items():
        ch_id = info.get("id", "") if isinstance(info, dict) else info
        broadcast_list_html += f'<div class="channel-item"><span>{name}</span><span style="color:var(--text-secondary);font-size:0.8em;">{ch_id}</span></div>'
    
    youtuber_list_html = ""
    for name, info in youtuber_channels.items():
        ch_id = info.get("id", "") if isinstance(info, dict) else info
        youtuber_list_html += f'<div class="channel-item"><span>{name}</span><span style="color:var(--text-secondary);font-size:0.8em;">{ch_id}</span></div>'
    
    # --- Full HTML ---
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 주식 브리핑</title>
    {css}
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span>AI 주식 브리핑</span></h1>
            <div class="update-time">자동 생성: {update_time}</div>
            <div class="source-info">📰 언론 뉴스 · 📡 경제방송 프로그램 · 🎬 경제 유튜브 TOP50 · 📊 애널리스트 리포트를 분석</div>
            <button class="settings-btn" onclick="openPanel()">📡</button>
        </div>
        
        <div class="summary-section">
            <h2>📊 시장 요약</h2>
            {summary_html}
        </div>
        
        <div class="summary-section">
            <h2>🔥 HOT 섹터</h2>
            <div class="sectors">{sectors_html}</div>
        </div>
        
        <div class="filter-bar">
            {filter_html}
        </div>
        
        <div id="stockList">
            {stocks_html}
        </div>
        
        <div class="hidden-section">
            <h2>💎 히든 픽 — 잠재력 발굴 종목</h2>
            {hidden_html}
        </div>
        
        <div class="analysis-section">
            <h2>🔍 AI 겹침 분석</h2>
            <p>{overlap_analysis}</p>
        </div>
        
        <div class="disclaimer">{disclaimer}</div>
    </div>
    
    <!-- Channel Management Panel -->
    <div class="panel-overlay" id="panelOverlay">
        <div class="panel-content">
            <div class="panel-header">
                <h2>📡 채널 관리</h2>
                <button class="panel-close" onclick="closePanel()">✕</button>
            </div>
            
            <input type="password" class="token-input" id="ghToken" placeholder="GitHub Personal Access Token">
            
            <div class="channel-group">
                <h3>📺 경제방송</h3>
                <div id="broadcastList">{broadcast_list_html}</div>
            </div>
            
            <div class="channel-group">
                <h3>🎬 유튜버</h3>
                <div id="youtuberList">{youtuber_list_html}</div>
            </div>
            
            <div class="channel-group">
                <h3>➕ 채널 추가</h3>
                <div class="add-form">
                    <select id="addType">
                        <option value="broadcast">경제방송</option>
                        <option value="youtuber">유튜버</option>
                    </select>
                    <input type="text" id="addName" placeholder="채널 이름">
                    <input type="text" id="addUrl" placeholder="YouTube 채널 URL">
                    <button onclick="addChannel()">추가</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const REPO = "{gh_repo}";
        const PANEL_PASS = "{PANEL_PASSWORD}";
        let panelUnlocked = false;
        
        let channelsData = {{
            broadcast: {json.dumps(broadcast_channels, ensure_ascii=False)},
            youtuber: {json.dumps(youtuber_channels, ensure_ascii=False)}
        }};
        
        function openPanel() {{
            if (!panelUnlocked) {{
                const pw = prompt("관리자 비밀번호를 입력하세요:");
                if (pw === null) return;
                if (pw !== PANEL_PASS) {{
                    alert("비밀번호가 틀렸습니다.");
                    return;
                }}
                panelUnlocked = true;
            }}
            document.getElementById('panelOverlay').style.display = 'block';
        }}
        
        function closePanel() {{
            document.getElementById('panelOverlay').style.display = 'none';
        }}
        
        function filterStocks(signal) {{
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            document.querySelectorAll('.stock-card').forEach(card => {{
                if (signal === 'all' || card.dataset.signal === signal) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
        
        function extractChannelId(url) {{
            // Handle @handle format
            const handleMatch = url.match(/@([\\w-]+)/);
            if (handleMatch) return url;
            
            // Handle /channel/ID format
            const channelMatch = url.match(/\\/channel\\/([\\w-]+)/);
            if (channelMatch) return channelMatch[1];
            
            return url;
        }}
        
        async function addChannel() {{
            const type = document.getElementById('addType').value;
            const name = document.getElementById('addName').value.trim();
            const url = document.getElementById('addUrl').value.trim();
            const token = document.getElementById('ghToken').value.trim();
            
            if (!name || !url) {{
                alert("채널 이름과 URL을 입력해주세요.");
                return;
            }}
            if (!token) {{
                alert("GitHub Token을 입력해주세요.");
                return;
            }}
            
            const channelId = extractChannelId(url);
            channelsData[type][name] = {{
                "id": channelId,
                "url": url
            }};
            
            // Save to GitHub
            try {{
                const apiUrl = `https://api.github.com/repos/${{REPO}}/contents/channels.json`;
                
                // Get current file SHA
                const getResp = await fetch(apiUrl, {{
                    headers: {{ 'Authorization': `token ${{token}}` }}
                }});
                const getData = await getResp.json();
                const sha = getData.sha;
                
                // Update file
                const content = btoa(unescape(encodeURIComponent(JSON.stringify(channelsData, null, 2))));
                const putResp = await fetch(apiUrl, {{
                    method: 'PUT',
                    headers: {{
                        'Authorization': `token ${{token}}`,
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        message: `Add channel: ${{name}}`,
                        content: content,
                        sha: sha
                    }})
                }});
                
                if (putResp.ok) {{
                    alert(`${{name}} 채널이 추가되었습니다!`);
                    // Update UI
                    const listId = type === 'broadcast' ? 'broadcastList' : 'youtuberList';
                    const newItem = document.createElement('div');
                    newItem.className = 'channel-item';
                    newItem.innerHTML = `<span>${{name}}</span><span style="color:var(--text-secondary);font-size:0.8em;">${{channelId}}</span>`;
                    document.getElementById(listId).appendChild(newItem);
                    document.getElementById('addName').value = '';
                    document.getElementById('addUrl').value = '';
                }} else {{
                    throw new Error('저장 실패');
                }}
            }} catch (e) {{
                alert("저장 실패: " + e.message);
            }}
        }}
        
        // Close panel on overlay click
        document.getElementById('panelOverlay').addEventListener('click', function(e) {{
            if (e.target === this) closePanel();
        }});
    </script>
</body>
</html>"""
    
    return html
