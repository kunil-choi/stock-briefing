# collectors/youtube_collector.py
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime, timedelta

def get_recent_videos(channel_id: str, api_key: str, max_results: int = 5) -> list:
    """YouTube Data API로 채널의 최근 영상 목록을 가져옵니다."""
    url = "https://www.googleapis.com/youtube/v3/search"
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")

    params = {
        "part": "snippet",
        "channelId": channel_id,
        "order": "date",
        "publishedAfter": yesterday,
        "maxResults": max_results,
        "type": "video",
        "key": api_key,
    }
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    videos = []
    for item in data.get("items", []):
        videos.append({
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "published": item["snippet"]["publishedAt"],
        })
    return videos


def get_transcript(video_id: str) -> str:
    """영상의 한국어 자막(자동생성 포함)을 텍스트로 추출합니다."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["ko"]
        )
        return " ".join([t["text"] for t in transcript_list])
    except Exception:
        try:
            # 자동 생성 자막 시도
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["ko-auto", "ko"]
            )
            return " ".join([t["text"] for t in transcript_list])
        except Exception as e:
            print(f"[자막추출 실패] {video_id}: {e}")
            return ""


def collect_youtube(channels: dict, api_key: str) -> list:
    """
    등록된 증시 유튜버 채널에서 최근 영상 제목 + 자막을 수집합니다.
    자막에서 종목명 추출은 AI 분석 단계에서 수행합니다.
    """
    results = []

    for channel_name, channel_id in channels.items():
        try:
            videos = get_recent_videos(channel_id, api_key)
            for video in videos:
                transcript = get_transcript(video["video_id"])
                results.append({
                    "source_type": "유튜버",
                    "source_name": channel_name,
                    "title": video["title"],
                    "summary": transcript[:3000],  # AI 분석용 (토큰 절약)
                    "link": f"https://www.youtube.com/watch?v={video['video_id']}",
                    "published": video["published"],
                })
        except Exception as e:
            print(f"[유튜브수집 오류] {channel_name}: {e}")

    return results