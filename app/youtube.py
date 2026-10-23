from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from app.config import settings

youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)

# All 15 Main YouTube Categories
CATEGORY_QUERIES = {
    "1": "film trailer",
    "2": "cars vehicles",
    "10": "music video",
    "15": "pets animals",
    "17": "sports highlights",
    "18": "short movie",
    "19": "travel vlog",
    "20": "gaming",
    "22": "vlog",
    "23": "standup comedy",
    "24": "entertainment",
    "25": "news",
    "26": "howto style",
    "27": "education",
    "28": "science technology"
}

def get_trending_videos(region="IN", category_ids=None, max_per_category=3):
    if category_ids is None:
        category_ids = list(CATEGORY_QUERIES.keys())

    all_videos = []
    
    # Calculate dates
    one_day_ago = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat().replace("+00:00", "Z")

    for cat_id in category_ids:
        query = CATEGORY_QUERIES.get(cat_id, "viral")
        
        try:
            # Try searching for videos from the LAST 24 HOURS
            request = youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                order="viewCount",
                publishedAfter=one_day_ago,
                regionCode=region,
                maxResults=max_per_category,
            )
            response = request.execute()
            items = response.get("items", [])

            # FALLBACK: If a category has no viral videos in the last 24 hours,
            # look back 3 days so the category isn't empty.
            if not items:
                print(f"  Category {cat_id} empty for 24h. Falling back to 3 days...")
                request = youtube.search().list(
                    part="snippet",
                    q=query,
                    type="video",
                    order="viewCount",
                    publishedAfter=three_days_ago,
                    regionCode=region,
                    maxResults=max_per_category,
                )
                response = request.execute()
                items = response.get("items", [])

            count = 0
            for item in items:
                all_videos.append({
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "category_id": cat_id,
                })
                count += 1
            
            print(f"  Category {cat_id} ('{query}'): {count} videos")
            
        except Exception as e:
            print(f"Error searching category {cat_id}: {e}")

    return all_videos
def fetch_top_comment(video_id):
    """Fetch the single highest-liked comment for a video. 1 quota unit."""
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