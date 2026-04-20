import yt_dlp
import json

def test_search(query):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'extract_flat': True,
    }
    search_query = f"ytsearch5:{query}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            print("Search successful")
            if 'entries' in info:
                for entry in info['entries']:
                    print(f" - {entry.get('title')} ({entry.get('id')})")
            else:
                print("No entries found")
    except Exception as e:
        print(f"Search failed: {e}")

if __name__ == "__main__":
    test_search("robotics hand sign language")
