**Peaek** (Peak + Peek) is a mobile application that surfaces the absolute most-liked comments from today's trending YouTube videos in India. 

Instead of scrolling through thousands of spam comments, Peaek curates the single **Top Comment** from the top 3 trending videos across 15 different categories (Comedy, Gaming, Tech, Sports, etc.). It provides a friction-free, snackable feed of pure internet gold, complete with a "Reveal the video" button to watch the source.

---

## Architecture

Peaek is built as a decoupled **Full-Stack Mobile Application** with a React Native frontend and a Python FastAPI backend.
graph TD
    A["Mobile App (React Native / Expo)"]
    B["Backend API (FastAPI on Render)"]
    C["YouTube Data API v3"]
    D["Database (Supabase / PostgreSQL)"]

    A -->|HTTPS| B
    B --> C
    B --> D

1. The Backend (/app)
Framework: FastAPI (Python)

Database: SQLite via SQLAlchemy (Accumulate Model)

Hosting: Render

Data Fetching: A background task (APScheduler) runs every 6 hours. It queries the YouTube Data API chart=mostPopular endpoint for 15 specific categories in India (regionCode="IN").

Data Processing: It fetches the top 100 comments for the trending videos, ranks them by likeCount, filters out spam/emojis, and stores the single highest-liked comment in the database.

2. The Frontend (/mobile)
Framework: React Native (Expo SDK 54)

UI/UX: Custom design with dynamic horizontal category tabs, safe-area handling, and a fixed bottom navigation bar.

Features:

Category filtering (All, Comedy, Gaming, etc.)

Device ID generation (via AsyncStorage) for anonymous tracking.

Native Share Sheet integration.

In-app feedback modal.

Pull-to-refresh and graceful empty states.

## Tech Stack
Layer	Technology	Purpose
Mobile App	React Native, Expo	Cross-platform Android UI
Backend	FastAPI, Python 3.13	High-performance async API
Database	SQLite, SQLAlchemy	Lightweight relational data storage
Scheduler	APScheduler	Automated 6-hour data refreshes
External API	YouTube Data API v3	Source of trending videos & comments
Hosting	Render	Cloud backend deployment
Build Tool	Gradle	Compiling native Android APK
Keep-Alive	UptimeRobot	Prevent Render free-tier cold starts


📂 Project Structure
text
peaek/
├── app/                      # Backend (Python FastAPI)
│   ├── main.py               # Entry point, CORS, APScheduler setup
│   ├── config.py             # Environment variables
│   ├── database.py           # SQLite connection setup
│   ├── models.py             # SQLAlchemy tables (TopComment, UserDevice, Feedback)
│   ├── schemas.py            # Pydantic models for API responses
│   ├── curators.py           # Logic for fetching, filtering, and saving comments
│   ├── youtube.py            # YouTube API integration (trending fetch & comment sort)
│   └── routers/              # API Routes
│       ├── cards.py          # GET /api/cards
│       ├── feedback.py       # POST /api/feedback
│       └── users.py          # POST /api/users/ping, GET /api/users/count
│
├── mobile/                   # Frontend (React Native)
│   ├── App.js                # Main UI component & API fetchers
│   ├── app.json              # Expo configuration
│   ├── assets/               # Icons and splash screens
│   └── android/              # Native Android project (generated via prebuild)
│
├── requirements.txt          # Python dependencies
└── README.md

## API Endpoints
Backend (FastAPI)
GET /api/cards?limit=50&category=23 - Fetches the curated top comments. (Leave category blank to get all).

GET /api/cards/by-category?per_category=3 - Fetches grouped cards by category (used for the "All" tab).

POST /api/feedback - Accepts { user_id, text } for user feedback.

POST /api/users/ping - Accepts { device_id, app_version } to track active installations.

GET /api/users/count - Returns total devices and 24h active users.

POST /admin/refresh-cards - Manually triggers the YouTube data fetch pipeline.

External
YouTube Data API v3:

videos.list (chart=mostPopular) - Fetches top trending videos per category.

commentThreads.list - Fetches top 100 comments sorted by relevance/likes.

## Local Setup & Development
1. Backend Setup
bash
# Clone the repo
git clone https://github.com/sudo-sagar/peaek.git
cd peaek

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add environment variables
echo "YOUTUBE_API_KEY=your_youtube_api_key_here" > .env

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

2. Mobile App Setup
bash
cd mobile

# Install node modules
npm install

# Start Expo development server
npx expo start
(Scan the QR code with Expo Go on your phone to view the app).


## Design Decisions & Edge Cases
The 1-Day / 3-Day Fallback:
To ensure the app is never empty, the backend searches for videos trending in the last 24 hours. If a specific category (like Pets or Tech) has no viral uploads that day, it automatically widens the search to 3 days to fill the feed.

The Accumulate Model:
Comments are not wiped on every refresh. The database uses a last_seen timestamp. Comments are updated if they are still trending, and deleted only if they haven't been seen in 24 hours.

Render Cold Starts:
Because Render's free tier sleeps after 15 minutes of inactivity, an external ping is set up via UptimeRobot to hit the /health endpoint every 5 minutes, ensuring 0-second load times for users.

API Quota Safety:
The backend leverages chart=mostPopular (1 quota unit per call) rather than search.list (100 units per call), ensuring the app can run 24/7 on the free YouTube API tier.

## Author
Built by Sagar
If you enjoy the app, please leave a ⭐ on the repo!

## NOTE
why no use of llm

1. The "Speed and Cost" Argument
"A trending video gets thousands of comments within the first hour. If I ran every single comment through an LLM to score them for 'funniness,' it would take too long and cost too much money."

"By relying on YouTube's own algorithm (fetching the top 100 comments sorted by 'relevance') and then picking the one with the most likes, I'm letting human behavior do the filtering. If 5,000 people liked a comment, it's guaranteed to be funny/most liked. No LLM can beat human consensus."

"It costs $0.00 in AI API fees."

2. The "Tone and Culture" Argument (Crucial for India)
"Humor is incredibly subjective and culturally specific. An LLM (trained mostly on English data) might not understand Indian slang, Hindi/Punjabi wordplay, or specific regional inside jokes."

"A comment like 'Bhai iska popat ho gaya' might be hilarious to an Indian audience, but an LLM might flag it as nonsense or negative. Human likes are the ultimate, unbiased judge of what's actually funny to this specific audience."

3. The "Freshness" Argument
"LLMs have a knowledge cutoff and can hallucinate. The top comment on a video uploaded 2 hours ago is brand new. The likes and engagement are happening right now. I don't need an AI to guess if it's funny when the like count is already proving it."

4. The "It's a Curation App, Not a Generation App" Argument
"Peaek isn't an AI tool. It's a curation tool. Just like Reddit or Hacker News, the value isn't in generating content—it's in finding the best content that already exists. The 'algorithm' is the crowd."

"Right now, I use human likes to find the top comment. In the future, I plan to use an LLM to act as a translation and context layer. For example, if the top comment is in Tamil, I can use an LLM to translate it to Hindi or English so the whole country can understand it, without losing the original flavor."


