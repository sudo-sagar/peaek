import sqlite3

conn = sqlite3.connect("comments.db")

total = conn.execute("SELECT COUNT(*) FROM trending_comments").fetchone()[0]
recent = conn.execute(
    "SELECT COUNT(*) FROM trending_comments "
    "WHERE last_seen > datetime('now', '-1 hour')"
).fetchone()[0]
stale = conn.execute(
    "SELECT COUNT(*) FROM trending_comments "
    "WHERE last_seen < datetime('now', '-24 hours')"
).fetchone()[0]

print(f"Total comments:    {total}")
print(f"Seen last hour:    {recent}")
print(f"Stale (>24h):      {stale}")