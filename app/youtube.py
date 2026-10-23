from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from app.config import settings

youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)

# 5 hyper-specific subqueries per category
CATEGORY_QUERIES = {
    "1": ["bollywood trailer reaction", "marvel trailer breakdown", "anime edit amv", "3d animated short film", "movie explained in hindi"],
    "2": ["supercar exhaust india", "offroad thar modification", "royal enfield custom build", "car delivery vlog", "bike stunt india"],
    "10": ["lofi hindi remix", "acoustic cover hindi", "90s bollywood songs", "punjabi pop song", "indian classical fusion"],
    "15": ["funny cat compilation", "dog stealing food", "parrot talking funny", "cute puppy vlog", "animal rescue india"],
    "17": ["india cricket highlights", "kabaddi best raids", "football skills india", "olympics india", "wwe funny moments"],
    "18": ["emotional short film", "award winning short film", "comedy short film india", "thriller short film", "sci-fi short film"],
    "19": ["backpacking travel vlog", "street food tour vlog", "luxury hotel review", "solo travel vlog india", "extreme adventure sports"],
    "20": ["bgmi funny moments", "gta 5 roleplay india", "free fire highlights", "minecraft hindi", "valorant clutch"],
    "22": ["indian street food vlog", "village cooking vlog", "daily routine vlog india", "morning routine aesthetic", "family vlog funny"],
    "23": ["hindi stand up comedy", "comedy roast video", "crowd work stand up", "comedy sketch india", "dark comedy hindi"],
    "24": ["celebrity interview funny", "reality show fights", "talk show funny moments", "award show moments", "behind the scenes bollywood"],
    "25": ["indian street interview funny", "public reaction prank", "what is your salary", "reality of india", "funny news bloopers"],
    "26": ["easy 5 minute recipes", "quick hairstyle tutorial", "diy room decor", "fashion haul india", "makeup transformation"],
    "27": ["coding tutorial for beginners", "study motivation", "jee advanced motivation", "upsc strategy", "english speaking practice"],
    "28": ["smartphone unboxing review", "tech gadget review", "iphone vs android camera", "budget laptop review", "ai tools tutorial"]
}


def get_trending_videos(region="IN", category_ids=None):
    if category_ids is None:
        category_ids = list(CATEGORY_QUERIES.keys())

    all_videos = []
    one_day_ago = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat().replace("+00:00", "Z")

    for cat_id in category_ids:
        queries = CATEGORY_QUERIES.get(cat_id, ["viral"])
        
        for query in queries:
            try:
                # Try 24 hours first
                request = youtube.search().list(
                    part="snippet",
                    q=query,
                    type="video",
                    order="viewCount",
                    publishedAfter=one_day_ago,
                    regionCode=region,
                    maxResults=1,
                )
                response = request.execute()
                items = response.get("items", [])

                # Fallback to 3 days if empty
                if not items:
                    request = youtube.search().list(
                        part="snippet",
                        q=query,
                        type="video",
                        order="viewCount",
                        publishedAfter=three_days_ago,
                        regionCode=region,
                        maxResults=1,
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
                print(f"Error searching category {cat_id} query '{query}': {e}")

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