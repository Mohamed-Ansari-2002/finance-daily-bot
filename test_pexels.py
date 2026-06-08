import requests
import os

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

# Search for finance related videos
url = "https://api.pexels.com/videos/search"

params = {
    "query"      : "stock market",
    "per_page"   : 3,
    "orientation": "landscape"   # YouTube is horizontal
}

headers = {
    "Authorization": PEXELS_API_KEY
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

print("Status code:", response.status_code)
print("Total results found:", data["total_results"])
print()

# Print details of each video found
for i, video in enumerate(data["videos"], 1):
    print(f"Video {i}:")
    print(f"  ID      : {video['id']}")
    print(f"  Duration: {video['duration']} seconds")
    print(f"  Link    : {video['video_files'][0]['link']}")
    print()