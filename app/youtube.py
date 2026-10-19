from googleapiclient.discovery import build
from app.config import settings

youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)


def get_trending_videos(region="IN", category_ids=None, max_per_category=10):
    if category_ids is None:
        category_ids = ["23", "24", "20", "17", "10"]

    all_videos = []
    for cat_id in category_ids:
        try:
            request = youtube.videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode=region,
                videoCategoryId=cat_id,
                maxResults=max_per_category,
            )
            response = request.execute()
            count = 0
            for item in response.get("items", []):
                all_videos.append({
                    "video_id": item["id"],
                    "title": item["snippet"]["title"],
                    "category_id": cat_id,
                })
                count += 1
            print(f"  Category {cat_id}: {count} videos")
        except Exception as e:
            print(f"Error fetching category {cat_id}: {e}")

    return all_videos


def fetch_top_comment(video_id):
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            order="relevance",
            textFormat="plainText",
        )
        response = request.execute()

        best = None
        for item in response.get("items", []):
            s = item["snippet"]["topLevelComment"]["snippet"]
            likes = int(s.get("likeCount", 0))
            if best is None or likes > best["comment_likes"]:
                best = {
                    "comment_text": s["textDisplay"],
                    "comment_author": s.get("authorDisplayName"),
                    "comment_likes": likes,
                    "comment_reply_count": int(item["snippet"].get("totalReplyCount", 0)),
                }
        return best
    except Exception as e:
        print(f"Comment fetch error for {video_id}: {e}")
        return None