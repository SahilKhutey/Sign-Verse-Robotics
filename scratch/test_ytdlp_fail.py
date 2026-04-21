import yt_dlp

def test_download_fail():
    youtube_url = "https://www.youtube.com/watch?v=LwGS-wg02gQ" # The problematic video
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "retries": 10,
        "ignoreerrors": True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Attempting extract_info...")
            info = ydl.extract_info(youtube_url, download=False)
            print(f"Info extracted: {info is not None}")
            if info is None:
                print("Info is None (ignoreerrors=True worked)")
            else:
                print("Downloading...")
                ydl.download([youtube_url])
    except Exception as e:
        print(f"Caught Exception: {type(e).__name__} - {e}")
    except BaseException as e:
        print(f"Caught BaseException: {type(e).__name__} - {e}")

if __name__ == "__main__":
    test_download_fail()
