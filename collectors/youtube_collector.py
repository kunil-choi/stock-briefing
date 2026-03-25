# collectors/youtube_collector.py
import os
import re
import requests
from datetime import datetime, timezone, timedelta

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

from config import (
    YOUTUBE_API_KEY,
    YOUTUBE_ORIGINAL_TOP50,
    POPULAR_PANELISTS,
    YOUTUBER_HOURS,
    BROADCAST_YOUTUBE,
    BROADCAST_HOURS,
)

API_KEY = YOUTUBE_API_KEY

# 주식/경제 관련 키워드 (제목 필터링)
STOCK_KEYWORDS = [
    "주식", "종목", "매수", "매도", "코스피", "코스닥", "상장", "실적",
    "반도체", "배터리", "2차전지", "바이오", "AI", "로봇", "방산", "원전",
    "ETF", "배당", "테마주", "급등", "목표가", "투자", "증시", "시황",
    "포트폴리오", "리밸런싱", "금리", "환율", "채권", "국채", "달러",
    "인플레이션", "경기", "FOMC", "연준", "GDP", "CPI", "고용",
    "부동산", "전세", "매매", "분양", "재건축", "재개발",
    "엔비디아", "테슬라", "삼성전자", "SK하이닉스", "애플", "마이크로소프트",
    "S&P", "나스닥", "다우", "미국장", "뉴욕증시", "해외주식",
    "상승", "하락", "전망", "분석", "추천", "리포트", "브리핑",
    "성공예감", "경제", "금융", "거시", "글로벌", "시장",
]


def test_api_key():
    """YouTube API 키 유효성 테스트"""
    if not API_KEY:
        print("[YouTube] API 키가 설정되지 않았습니다.")
        return False
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {"part": "snippet", "id": "dQw4w9WgXcQ", "key": API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            print("[YouTube] API 키 테스트 성공 ✅")
            return True
        else:
            err = resp.json().get("error", {})
            print(f"[YouTube] API 키 테스트 실패 ❌ 코드:{resp.status_code} 메시지:{err.get('message','')}")
            return False
    except Exception as e:
        print(f"[YouTube] API 키 테스트 오류: {e}")
        return False


def resolve_channel_id(channel_id_or_handle, api_key):
    """@handle 또는 c/ 형식을 실제 채널 ID로 변환"""
    if channel_id_or_handle.startswith("UC") and len(channel_id_or_handle) == 24:
        return channel_id_or_handle

    if channel_id_or_handle.startswith("@"):
        handle = channel_id_or_handle
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {"part": "id", "forHandle": handle.lstrip("@"), "key": api_key}
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get("items"):
                resolved = data["items"][0]["id"]
                print(f"  [ID변환] {handle} → {resolved}")
                return resolved
        except Exception as e:
            print(f"  [ID변환 실패] {handle}: {e}")

    return channel_id_or_handle


def get_recent_videos(channel_id, api_key, hours=24, max_results=15):
    """채널의 최근 N시간 이내 업로드된 영상 목록"""
    after = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "type": "video",
        "order": "date",
        "publishedAfter": after,
        "maxResults": max_results,
        "key": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()

        if "error" in data:
            err = data["error"]
            print(f"    API 오류: {err.get('code')} - {err.get('message','')}")
            if err.get("errors"):
                for e in err["errors"]:
                    print(f"      reason: {e.get('reason')}, domain: {e.get('domain')}")
            return []

        items = data.get("items", [])
        print(f"    최근 {hours}시간 영상: {len(items)}개")
        return items
    except Exception as e:
        print(f"    요청 오류: {e}")
        return []


def get_transcript(video_id, max_chars=2000):
    """유튜브 영상 자막 추출"""
    if YouTubeTranscriptApi is None:
        return ""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript(["ko"])
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript(["ko"])
            except Exception:
                return ""
        entries = transcript.fetch()
        text = " ".join([e.get("text", e.get("value", "")) if isinstance(e, dict) else str(e) for e in entries])
        return text[:max_chars]
    except Exception:
        return ""


def is_stock_related(title, description=""):
    """제목이나 설명에 주식/경제 키워드가 포함되어 있는지 확인"""
    text = (title + " " + description).lower()
    for keyword in STOCK_KEYWORDS:
        if keyword.lower() in text:
            return True
    return False


def has_popular_panelist(title, description=""):
    """인기 패널이 제목이나 설명에 언급되어 있는지 확인"""
    text = title + " " + description
    matched = []
    for panelist in POPULAR_PANELISTS:
        if panelist in text:
            matched.append(panelist)
    return matched


def search_panelist_videos(api_key, hours=24, max_per_panelist=3):
    """인기 패널명으로 유튜브 검색하여 구독자 50위 밖 채널의 영상도 수집"""
    after = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    known_channel_ids = set(YOUTUBE_ORIGINAL_TOP50.values())
    results = []

    # 패널 5명씩 묶어서 검색 (쿼터 절약)
    panelist_groups = []
    for i in range(0, len(POPULAR_PANELISTS), 5):
        group = POPULAR_PANELISTS[i:i+5]
        panelist_groups.append(" | ".join(group))

    for query in panelist_groups:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query + " 주식 경제",
            "type": "video",
            "order": "date",
            "publishedAfter": after,
            "maxResults": 10,
            "relevanceLanguage": "ko",
            "key": api_key,
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
            if "error" in data:
                print(f"  [패널검색 오류] {data['error'].get('message','')}")
                continue

            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                ch_id = snippet.get("channelId", "")
                title = snippet.get("title", "")
                desc = snippet.get("description", "")
                video_id = item.get("id", {}).get("videoId", "")

                # 이미 TOP50에 포함된 채널은 건너뛰기
                if ch_id in known_channel_ids:
                    continue

                matched_panelists = has_popular_panelist(title, desc)
                if matched_panelists:
                    ch_name = snippet.get("channelTitle", "알 수 없는 채널")
                    print(f"  [패널발견] {matched_panelists} → {ch_name}: {title}")

                    transcript = get_transcript(video_id, max_chars=1500)
                    summary = transcript if transcript else desc[:500]

                    results.append({
                        "source_type": "유튜버",
                        "source_name": f"{ch_name} (패널: {', '.join(matched_panelists)})",
                        "title": title,
                        "summary": summary,
                        "link": f"https://www.youtube.com/watch?v={video_id}",
                        "published": snippet.get("publishedAt", ""),
                        "panelists": matched_panelists,
                    })
        except Exception as e:
            print(f"  [패널검색 예외] {e}")

    print(f"[패널 검색] 총 {len(results)}개 영상 수집")
    return results


def collect_broadcast_youtube():
    """경제전문방송 유튜브 수집 (24시간 이내)"""
    print("\n=== 경제전문방송 유튜브 수집 ===")

    if not test_api_key():
        return []

    results = []

    # channels.json에서 방송 채널 로드
    try:
        from config import load_channels
        channels_data = load_channels()
        broadcast_channels = {name: info["id"] for name, info in channels_data.get("broadcast", {}).items()}
    except Exception:
        broadcast_channels = BROADCAST_YOUTUBE

    for name, channel_id in broadcast_channels.items():
        print(f"\n[방송] {name} ({channel_id})")
        resolved_id = resolve_channel_id(channel_id, API_KEY)
        videos = get_recent_videos(resolved_id, API_KEY, hours=BROADCAST_HOURS, max_results=15)

        collected = 0
        for item in videos:
            snippet = item.get("snippet", {})
            title = snippet.get("title", "")
            desc = snippet.get("description", "")
            video_id = item.get("id", {}).get("videoId", "")

            if not is_stock_related(title, desc):
                continue

            transcript = get_transcript(video_id, max_chars=1500)
            summary = transcript if transcript else desc[:500]

            results.append({
                "source_type": "경제방송",
                "source_name": name,
                "title": title,
                "summary": summary,
                "link": f"https://www.youtube.com/watch?v={video_id}",
                "published": snippet.get("publishedAt", ""),
            })
            collected += 1

        print(f"  → 경제관련 {collected}개 수집")

    print(f"\n[경제방송 합계] {len(results)}개")
    return results


def collect_youtuber():
    """오리지널 유튜브 채널 수집 (TOP50 + 패널 출연 + channels.json 추가분)"""
    print("\n=== 오리지널 유튜브 채널 수집 (TOP50 + 인기패널) ===")

    if not test_api_key():
        return []

    results = []

    # 1) channels.json의 youtuber 채널
    try:
        from config import load_channels
        channels_data = load_channels()
        json_youtubers = {name: info["id"] for name, info in channels_data.get("youtuber", {}).items()}
    except Exception:
        json_youtubers = {}

    # 2) config.py의 TOP50 채널과 병합 (중복 제거)
    all_channels = dict(YOUTUBE_ORIGINAL_TOP50)
    for name, ch_id in json_youtubers.items():
        if name not in all_channels:
            all_channels[name] = ch_id

    print(f"총 수집 대상 채널: {len(all_channels)}개")

    # 3) 각 채널에서 최근 영상 수집
    for name, channel_id in all_channels.items():
        print(f"\n[유튜버] {name}")
        resolved_id = resolve_channel_id(channel_id, API_KEY)
        videos = get_recent_videos(resolved_id, API_KEY, hours=YOUTUBER_HOURS, max_results=10)

        collected = 0
        for item in videos:
            snippet = item.get("snippet", {})
            title = snippet.get("title", "")
            desc = snippet.get("description", "")
            video_id = item.get("id", {}).get("videoId", "")

            if not is_stock_related(title, desc):
                continue

            # 인기 패널 출연 여부 체크
            panelists = has_popular_panelist(title, desc)

            transcript = get_transcript(video_id, max_chars=1500)
            summary = transcript if transcript else desc[:500]

            source_label = name
            if panelists:
                source_label = f"{name} (패널: {', '.join(panelists)})"

            results.append({
                "source_type": "유튜버",
                "source_name": source_label,
                "title": title,
                "summary": summary,
                "link": f"https://www.youtube.com/watch?v={video_id}",
                "published": snippet.get("publishedAt", ""),
                "panelists": panelists,
            })
            collected += 1

        print(f"  → {collected}개 수집")

    # 4) 인기 패널 검색으로 추가 수집 (50위 밖 채널)
    print("\n--- 인기 패널 출연 영상 추가 검색 ---")
    panelist_results = search_panelist_videos(API_KEY, hours=YOUTUBER_HOURS)
    results.extend(panelist_results)

    print(f"\n[유튜버 합계] {len(results)}개")
    return results
