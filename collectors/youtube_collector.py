# collectors/youtube_collector.py
import requests
import json
from datetime import datetime, timedelta


def get_recent_videos(channel_id: str, api_key: str, hours: int = 24, max_results: int = 10) -> list:
    """YouTube Data API로 채널의 최근 영상 목록을 가져옵니다."""
    url = "https://www.googleapis.com/youtube/v3/search"
    since = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "part": "snippet",
        "channelId": channel_id,
        "order": "date",
        "publishedAfter": since,
        "maxResults": max_results,
        "type": "video",
        "key": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()

        # 에러 응답 상세 출력
        if "error" in data:
            print(f"    [API 에러] 코드: {data['error'].get('code')}")
            print(f"    [API 에러] 메시지: {data['error'].get('message')}")
            for err in data["error"].get("errors", []):
                print(f"    [API 에러] 이유: {err.get('reason')} / {err.get('domain')}")
            return []

        items = data.get("items", [])
        print(f"    API 응답: {len(items)}건 (pageInfo: {data.get('pageInfo', {})})")

        videos = []
        for item in items:
            vid_id = item.get("id", {}).get("videoId", "")
            title = item.get("snippet", {}).get("title", "")
            desc = item.get("snippet", {}).get("description", "")
            published = item.get("snippet", {}).get("publishedAt", "")
            if vid_id:
                videos.append({
                    "video_id": vid_id,
                    "title": title,
                    "description": desc,
                    "published": published,
                })
        return videos

    except Exception as e:
        print(f"    [요청 오류] {e}")
        return []


def get_transcript(video_id: str) -> str:
    """영상의 한국어 자막을 텍스트로 추출합니다."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["ko"]
        )
        return " ".join([t["text"] for t in transcript_list])
    except Exception:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["ko-auto"]
            )
            return " ".join([t["text"] for t in transcript_list])
        except Exception:
            return ""


def test_api_key(api_key: str) -> bool:
    """YouTube API 키가 작동하는지 간단히 테스트합니다."""
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": "dQw4w9WgXcQ",  # 테스트용 영상
        "key": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "error" in data:
            print(f"  [API 키 테스트 실패] {data['error'].get('message')}")
            return False
        print(f"  [API 키 테스트 성공] 키가 정상 작동합니다.")
        return True
    except Exception as e:
        print(f"  [API 키 테스트 오류] {e}")
        return False


def collect_broadcast_youtube(broadcast_channels: dict, api_key: str, hours: int = 24) -> list:
    """경제전문방송 유튜브 채널에서 최근 영상을 수집합니다."""
    results = []

    # API 키 먼저 테스트
    if not api_key:
        print("  [경고] YOUTUBE_API_KEY가 비어 있습니다!")
        return results

    test_api_key(api_key)

    for channel_name, channel_id in broadcast_channels.items():
        print(f"  수집 중: {channel_name} (채널ID: {channel_id}, 최근 {hours}시간)")
        videos = get_recent_videos(channel_id, api_key, hours=hours, max_results=15)

        for video in videos:
            title = video["title"]

            # 주식 관련 키워드 필터
            keywords = ["종목", "주식", "코스피", "코스닥", "매수", "매도",
                       "상승", "급등", "테마", "섹터", "반도체", "2차전지",
                       "AI", "로봇", "바이오", "실적", "목표가", "추천",
                       "전망", "분석", "투자", "증시", "시황", "마감",
                       "승부주", "관심주", "수혜주", "대장주", "ETF",
                       "삼성", "SK", "LG", "현대", "카카오", "네이버",
                       "배터리", "자동차", "조선", "방산", "원전", "금리"]

            is_stock_related = any(kw in title for kw in keywords)

            transcript = ""
            if is_stock_related:
                transcript = get_transcript(video["video_id"])

            results.append({
                "source_type": "경제방송",
                "source_name": channel_name,
                "title": title,
                "summary": transcript[:3000] if transcript else video["description"][:500],
                "link": f"https://www.youtube.com/watch?v={video['video_id']}",
                "published": video["published"],
            })

        print(f"    → {len(videos)}건 수집")

    return results


def collect_youtuber(youtuber_channels: dict, api_key: str, hours: int = 48) -> list:
    """구독자 상위권 증시 유튜버 채널에서 최근 영상을 수집합니다."""
    results = []

    if not api_key:
        print("  [경고] YOUTUBE_API_KEY가 비어 있습니다!")
        return results

    for channel_name, channel_id in youtuber_channels.items():
        print(f"  수집 중: {channel_name} (채널ID: {channel_id}, 최근 {hours}시간)")
        videos = get_recent_videos(channel_id, api_key, hours=hours, max_results=10)

        for video in videos:
            transcript = get_transcript(video["video_id"])

            results.append({
                "source_type": "유튜버",
                "source_name": channel_name,
                "title": video["title"],
                "summary": transcript[:3000] if transcript else video["description"][:500],
                "link": f"https://www.youtube.com/watch?v={video['video_id']}",
                "published": video["published"],
            })

        print(f"    → {len(videos)}건 수집")

    return results
