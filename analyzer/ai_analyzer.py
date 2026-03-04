# analyzer/ai_analyzer.py
import anthropic
import json
from datetime import datetime


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
            summary_text += f"- 출처: {item['source_name']} | 제목: {item['title']}\n"
            if item.get('summary'):
                summary_text += f"  내용: {item['summary'][:500]}\n"

    today = datetime.now().strftime("%Y년 %m월 %d일")

    prompt = f"""당신은 한국 주식시장 전문 AI 브리핑 애널리스트입니다.

아래는 오늘({today}) 수집된 4개 채널(뉴스, 경제방송, 증시유튜버, 애널리스트보고서)의 데이터입니다.

{summary_text}

위 데이터를 분석하여 아래 형식의 JSON을 생성해주세요:

{{
  "briefing_date": "{today}",
  "market_summary": "오늘의 전체 시장 분위기 요약 (2-3문장)",
  "hot_sectors": ["주목받는 섹터/테마 리스트"],
  "stocks": [
    {{
      "rank": 1,
      "name": "종목명",
      "overlap_count": 4,
      "mentioned_in": ["뉴스", "경제방송", "유튜버", "애널리스트"],
      "reasons": {{
        "뉴스": "이유 요약",
        "경제방송": "이유 요약",
        "유튜버": "이유 요약",
        "애널리스트": "이유 요약"
      }},
      "catalyst": "주요 상승 촉매",
      "risk": "리스크",
      "sentiment": "긍정/중립/주의"
    }}
  ],
  "overlap_analysis": "교차분석 인사이트",
  "disclaimer": "본 브리핑은 AI가 자동 생성한 참고자료이며, 투자 판단의 책임은 본인에게 있습니다."
}}

규칙:
1. overlap_count 높은 순으로 정렬
2. 실제 데이터에서 확인된 종목만 포함
3. 최소 5개 ~ 최대 20개 종목
4. JSON만 출력
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
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

    # 종목 카드 HTML
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

        sentiment = stock.get("sentiment", "중립")
        if sentiment == "긍정": sent_color = "#27ae60"; sent_icon = "🟢"
        elif sentiment == "주의": sent_color = "#e74c3c"; sent_icon = "🔴"
        else: sent_color = "#f39c12"; sent_icon = "🟡"

        reasons_html = ""
        for channel, reason in stock.get("reasons", {}).items():
            if reason:
                reasons_html += f'<div class="reason-item"><span class="reason-channel">{channel}</span><span class="reason-text">{reason}</span></div>'

        mentioned_tags = ""
        for ch in stock.get("mentioned_in", []):
            mentioned_tags += f'<span class="channel-tag">{ch}</span>'

        stocks_html += f"""
        <div class="stock-card" data-overlap="{overlap}">
            <div class="stock-header">
                <div class="stock-rank">#{stock.get("rank","")}</div>
                <div class="stock-name">{stock.get("name","")}</div>
                <span class="overlap-badge" style="background:{badge_color}">{badge_label}</span>
                <span class="sentiment-badge" style="color:{sent_color}">{sent_icon} {sentiment}</span>
            </div>
            <div class="channel-tags">{mentioned_tags}</div>
            <div class="catalyst"><strong>📈 상승 촉매:</strong> {stock.get("catalyst","")}</div>
            <div class="risk"><strong>⚠️ 리스크:</strong> {stock.get("risk","")}</div>
            <div class="reasons"><strong>📋 채널별 선정 근거:</strong>{reasons_html}</div>
        </div>"""

    sectors_html = ""
    for sector in data.get("hot_sectors", []):
        sectors_html += f'<span class="sector-tag">{sector}</span>'

    # 채널 목록 HTML
    broadcast_list = ""
    for name, info in channels_data.get("broadcast", {}).items():
        url = info.get("url", "")
        broadcast_list += f'<div class="ch-item"><a href="{url}" target="_blank">{name}</a><span class="ch-id">{info.get("id","")}</span></div>'

    youtuber_list = ""
    for name, info in channels_data.get("youtuber", {}).items():
        url = info.get("url", "")
        youtuber_list += f'<div class="ch-item"><a href="{url}" target="_blank">{name}</a><span class="ch-id">{info.get("id","")}</span></div>'

    channels_json_escaped = json.dumps(channels_data, ensure_ascii=False).replace("'", "\\'").replace("`", "\\`")

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

        /* 채널 관리 버튼 */
        .ch-manage-btn {{ position:absolute; top:20px; right:20px; width:44px; height:44px; border-radius:50%; background:var(--bg-card); border:1px solid var(--border); color:var(--accent-blue); font-size:20px; cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s; }}
        .ch-manage-btn:hover {{ background:var(--accent-blue); color:white; }}

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

        /* 채널 추가 폼 */
        .add-form {{ background:var(--bg-card); border-radius:12px; padding:20px; margin-top:16px; }}
        .add-form h3 {{ color:var(--accent-green); margin:0 0 12px 0; }}
        .form-row {{ display:flex; gap:8px; margin-bottom:10px; flex-wrap:wrap; }}
        .form-row select, .form-row input {{ background:var(--bg-primary); border:1px solid var(--border); color:var(--text-primary); padding:10px 12px; border-radius:8px; font-size:14px; }}
        .form-row select {{ width:130px; }}
        .form-row input {{ flex:1; min-width:150px; }}
        .add-btn {{ background:var(--accent-green); color:#000; border:none; padding:10px 24px; border-radius:8px; font-size:14px; font-weight:700; cursor:pointer; width:100%; margin-top:8px; transition:all 0.2s; }}
        .add-btn:hover {{ background:#40c057; }}
        .add-btn:disabled {{ background:var(--text-secondary); cursor:not-allowed; }}
        .status-msg {{ margin-top:12px; padding:10px; border-radius:8px; font-size:13px; display:none; }}
        .status-msg.success {{ display:block; background:rgba(81,207,102,0.15); color:var(--accent-green); }}
        .status-msg.error {{ display:block; background:rgba(255,107,107,0.15); color:var(--accent-red); }}
        .help-text {{ color:var(--text-secondary); font-size:12px; margin-top:8px; line-height:1.6; }}

        .market-summary {{ background:linear-gradient(135deg,#1a1f35,#1e2745); border:1px solid var(--border); border-radius:12px; padding:24px; margin-bottom:24px; }}
        .market-summary h2 {{ font-size:18px; color:var(--accent-blue); margin-bottom:12px; }}
        .market-summary p {{ color:var(--text-secondary); font-size:15px; }}
        .hot-sectors {{ margin-bottom:24px; }}
        .hot-sectors h2 {{ font-size:18px; margin-bottom:12px; }}
        .sector-tag {{ display:inline-block; background:rgba(77,171,247,0.15); color:var(--accent-blue); padding:6px 14px; border-radius:20px; font-size:13px; margin:4px; border:1px solid rgba(77,171,247,0.3); }}
        .stock-card {{ background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:24px; margin-bottom:16px; transition:all 0.2s; }}
        .stock-card:hover {{ background:var(--bg-card-hover); border-color:var(--accent-blue); }}
        .stock-card[data-overlap="4"] {{ border-left:4px solid var(--accent-red); }}
        .stock-card[data-overlap="3"] {{ border-left:4px solid var(--accent-orange); }}
        .stock-card[data-overlap="2"] {{ border-left:4px solid var(--accent-blue); }}
        .stock-header {{ display:flex; align-items:center; gap:12px; margin-bottom:12px; flex-wrap:wrap; }}
        .stock-rank {{ font-size:24px; font-weight:800; color:var(--accent-blue); min-width:40px; }}
        .stock-name {{ font-size:20px; font-weight:700; }}
        .overlap-badge {{ color:white; padding:4px 12px; border-radius:12px; font-size:12px; font-weight:600; }}
        .sentiment-badge {{ font-size:14px; font-weight:600; }}
        .channel-tags {{ margin-bottom:12px; }}
        .channel-tag {{ display:inline-block; background:rgba(255,255,255,0.06); color:var(--text-secondary); padding:3px 10px; border-radius:8px; font-size:12px; margin-right:6px; }}
        .catalyst,.risk {{ font-size:14px; margin-bottom:8px; padding:8px 12px; border-radius:8px; }}
        .catalyst {{ background:rgba(81,207,102,0.08); color:var(--accent-green); }}
        .risk {{ background:rgba(255,107,107,0.08); color:var(--accent-red); }}
        .reasons {{ margin-top:12px; font-size:14px; }}
        .reasons strong {{ display:block; margin-bottom:8px; }}
        .reason-item {{ display:flex; gap:10px; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.04); }}
        .reason-channel {{ min-width:80px; color:var(--accent-blue); font-weight:600; font-size:13px; }}
        .reason-text {{ color:var(--text-secondary); font-size:13px; }}
        .filter-bar {{ margin-bottom:20px; display:flex; gap:8px; flex-wrap:wrap; }}
        .filter-btn {{ background:var(--bg-card); color:var(--text-secondary); border:1px solid var(--border); padding:8px 16px; border-radius:8px; cursor:pointer; font-size:13px; transition:all 0.2s; }}
        .filter-btn:hover,.filter-btn.active {{ background:var(--accent-blue); color:white; border-color:var(--accent-blue); }}
        .insight {{ background:linear-gradient(135deg,#1e2745,#1a1f35); border:1px solid var(--border); border-radius:12px; padding:24px; margin-top:24px; }}
        .insight h2 {{ color:#da77f2; margin-bottom:12px; }}
        .disclaimer {{ text-align:center; color:var(--text-secondary); font-size:12px; margin-top:30px; padding:20px; border-top:1px solid var(--border); }}
        @media (max-width:600px) {{ body {{ padding:10px; }} .stock-header {{ flex-direction:column; align-items:flex-start; gap:6px; }} .header h1 {{ font-size:22px; }} .ch-manage-btn {{ top:10px; right:10px; width:36px; height:36px; font-size:16px; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI 증시 모닝브리핑</h1>
            <div class="date">{data.get("briefing_date","")}</div>
            <div class="update-time">자동 생성 시각: {datetime.now().strftime("%H:%M")}</div>
            <button class="ch-manage-btn" onclick="openPanel()" title="수집 채널 관리">📡</button>
        </div>

        <!-- 채널 관리 패널 -->
        <div class="ch-panel-overlay" id="chPanel">
            <div class="ch-panel">
                <button class="close-btn" onclick="closePanel()">✕</button>
                <h2>📡 수집 채널 관리</h2>

                <h3>📺 경제전문방송 ({len(channels_data.get("broadcast", {}))}개)</h3>
                {broadcast_list}

                <h3>🎬 증시 유튜버 ({len(channels_data.get("youtuber", {}))}개)</h3>
                {youtuber_list}

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
                    <div class="form-row">
                        <input type="text" id="addId" placeholder="채널 ID (예: UCxxxxx...)">
                    </div>
                    <button class="add-btn" id="addBtn" onclick="addChannel()">채널 추가 (다음 브리핑부터 반영)</button>
                    <div class="status-msg" id="statusMsg"></div>
                    <div class="help-text">
                        💡 <strong>채널 ID 찾는 법:</strong> 유튜브 채널 페이지 접속 → 주소창의 URL에서 /channel/ 뒤의 UC로 시작하는 문자열이 채널 ID입니다.<br>
                        또는 <a href="https://commentpicker.com/youtube-channel-id.php" target="_blank" style="color:var(--accent-blue);">이 사이트</a>에서 채널 URL을 넣으면 ID를 알려줍니다.<br>
                        ⏰ 추가한 채널은 <strong>다음 날 아침 브리핑</strong>부터 반영됩니다.
                    </div>
                </div>
            </div>
        </div>

        <div class="market-summary">
            <h2>📊 시장 요약</h2>
            <p>{data.get("market_summary","")}</p>
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
            <p>{data.get("overlap_analysis","")}</p>
        </div>
        <div class="disclaimer">{data.get("disclaimer","본 브리핑은 AI가 자동 생성한 참고자료이며, 투자 판단의 책임은 본인에게 있습니다.")}</div>
    </div>

    <script>
        const REPO = "{gh_repo}";
        const FILE_PATH = "channels.json";
        let currentChannels = JSON.parse('{channels_json_escaped}');

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

        async function addChannel() {{
            const type = document.getElementById('addType').value;
            const name = document.getElementById('addName').value.trim();
            const url = document.getElementById('addUrl').value.trim();
            const chId = document.getElementById('addId').value.trim();
            const statusMsg = document.getElementById('statusMsg');
            const btn = document.getElementById('addBtn');

            if (!name || !chId) {{
                statusMsg.className = 'status-msg error';
                statusMsg.textContent = '채널 이름과 채널 ID는 필수입니다.';
                return;
            }}

            btn.disabled = true;
            btn.textContent = '저장 중...';
            statusMsg.className = 'status-msg';
            statusMsg.style.display = 'none';

            try {{
                // 1. 현재 channels.json의 SHA 가져오기
                const getResp = await fetch(`https://api.github.com/repos/${{REPO}}/contents/${{FILE_PATH}}`, {{
                    headers: {{ 'Accept': 'application/vnd.github.v3+json' }}
                }});
                const fileData = await getResp.json();
                const sha = fileData.sha;

                // 현재 내용 디코딩
                const content = JSON.parse(atob(fileData.content));

                // 2. 새 채널 추가
                if (!content[type]) content[type] = {{}};
                content[type][name] = {{ id: chId, url: url }};

                // 3. GitHub API로 파일 업데이트
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
                    document.getElementById('addName').value = '';
                    document.getElementById('addUrl').value = '';
                    document.getElementById('addId').value = '';
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
