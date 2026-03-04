# collectors/youtube_collector.py
import requests
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
    except Exception as e:
        print(f"  [API 오류] {channel_id}: {e}")
        return []

    if "items" not in data:
        print(f"  [API 응답 이상] {channel_id}: {data.get('error', {}).get('message', 'unknown')}")
        return []

    videos = []
    for item in data.get("items", []):
        videos.append({
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "description": item["snippet"].get("description", ""),
            "published": item["snippet"]["publishedAt"],
        })
    return videos


def get_transcript(video_id: str) -> str:
    """영상의 한국어 자막(자동생성 포함)을 텍스트로 추출합니다."""
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


def collect_broadcast_youtube(broadcast_channels: dict, api_key: str, hours: int = 24) -> list:
    """
    경제전문방송 유튜브 채널에서 최근 영상을 수집합니다.
    방송 프로그램 제목 + 자막에서 종목 정보를 추출합니다.
    """
    results = []

    for channel_name, channel_id in broadcast_channels.items():
        print(f"  수집 중: {channel_name} (최근 {hours}시간)")
        try:
            videos = get_recent_videos(channel_id, api_key, hours=hours, max_results=15)
            for video in videos:
                # 주식/종목 관련 영상만 필터링 (키워드 기반)
                title = video["title"]
                keywords = ["종목", "주식", "코스피", "코스닥", "매수", "매도",
                           "상승", "급등", "테마", "섹터", "반도체", "2차전지",
                           "AI", "로봇", "바이오", "실적", "목표가", "추천",
                           "전망", "분석", "투자", "증시", "시황", "마감",
                           "승부주", "관심주", "수혜주", "대장주"]

                is_stock_related = any(kw in title for kw in keywords)

                # 경제방송은 대부분 주식 관련이므로 넓게 수집
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
                    "is_stock_related": is_stock_related,
                })
            print(f"    → {len(videos)}건 수집")
        except Exception as e:
            print(f"  [경제방송 오류] {channel_name}: {e}")

    return results


def collect_youtuber(youtuber_channels: dict, api_key: str, hours: int = 48) -> list:
    """
    구독자 상위권 증시 유튜버 채널에서 최근 48시간 영상을 수집합니다.
    제목 + 자막으로 언급 종목을 파악합니다.
    """
    results = []

    for channel_name, channel_id in youtuber_channels.items():
        print(f"  수집 중: {channel_name} (최근 {hours}시간)")
        try:
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
        except Exception as e:
            print(f"  [유튜버 오류] {channel_name}: {e}")

    return results
