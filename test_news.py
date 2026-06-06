import feedparser

# Google News RSS - Finance for India
url = "https://news.google.com/rss/search?q=stock+market+india&hl=en-IN&gl=IN&ceid=IN:en"

feed = feedparser.parse(url)

# Print feed title to confirm it's working
print("Feed title:", feed.feed.title)
print("Total articles found:", len(feed.entries))
print("---")

# Print first 5 articles
for i, entry in enumerate(feed.entries[:5]):
    print(f"Article {i+1}:")
    print("  Title  :", entry.title)
    print("  Link   :", entry.link)
    print("  Published:", entry.get("published", "N/A"))
    print()