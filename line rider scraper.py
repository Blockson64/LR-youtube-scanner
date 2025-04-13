import yt_dlp
from datetime import datetime, timedelta
import re
import time
import threading


running = False  # Global control flag for loop


def normalize_string(s):
    """Normalize the string by removing special characters and converting to lowercase."""
    return s.lower().strip()


def search_youtube(term, max_results=20):
    """Search YouTube for videos uploaded after yesterday and return metadata entries."""
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    search_term_with_date = f"\"{term}\" after:{yesterday}"
    search_url = f"ytsearch{max_results}:{search_term_with_date}"

    # Step 1: Flat extract (metadata only, avoids live errors)
    flat_opts = {
        "quiet": True,
        "extract_flat": True,
        "dump_single_json": True,
    }

    with yt_dlp.YoutubeDL(flat_opts) as ydl:
        result = ydl.extract_info(search_url, download=False)

    entries = result.get("entries", [])

    # Step 2: Fully extract metadata for each valid URL
    full_entries = []
    full_opts = {"quiet": True}
    with yt_dlp.YoutubeDL(full_opts) as ydl:
        for entry in entries:
            url = entry.get("url") or entry.get("webpage_url")
            try:
                full_info = ydl.extract_info(url, download=False)
                full_entries.append(full_info)
            except yt_dlp.utils.DownloadError:
                continue  # Skip videos that can't be accessed

    print(f"\nSearch URL: https://www.youtube.com/results?search_query={search_term_with_date}\n")
    return full_entries


def is_uploaded_today(entry):
    """Check if the video was uploaded today using the upload_date field."""
    upload_date = entry.get("upload_date")
    if upload_date:
        upload_date_obj = datetime.strptime(str(upload_date), "%Y%m%d")
        return upload_date_obj.date() == datetime.today().date()
    return False


def load_seen_videos():
    """Load the list of already seen videos from 'seen_videos.txt'."""
    try:
        with open("seen_videos.txt", "r") as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()


def save_seen_video(title):
    """Save a new video title to 'seen_videos.txt'."""
    with open("seen_videos.txt", "a") as file:
        file.write(title + "\n")


def run_manual_check():
    search_term = "line rider"
    normalized_search_term = normalize_string(search_term)

    print(f"\nNormalized search term: '{normalized_search_term}'\n")
    print(f"\nSearching for: {search_term}")
    results = search_youtube(search_term)

    if not results:
        print("No search results found.")
        return

    seen_videos = load_seen_videos()  # Load previously seen videos

    found = False
    for entry in results:
        title = entry.get("title")
        url = entry.get("url") or entry.get("webpage_url")
        uploader = entry.get('uploader', 'Unknown author')
        name = title + " | " + uploader
        normalized_title = normalize_string(title)

        if normalized_search_term not in normalized_title:
            continue

        if is_uploaded_today(entry):
            # Check if the video has already been seen
            if name in seen_videos:
                continue  # Skip already seen video

            # Print video details for a new video
            print(f"\n📺 Title: {title}")
            print(f"🔗 Link: {url}")
            print(f"🕒 Uploaded: {datetime.strptime(str(entry['upload_date']), '%Y%m%d')}")
            found = True

            # Save the new video title to the seen list
            save_seen_video(name)
            seen_videos.add(name)  # Update the in-memory set

    if not found:
        print("No new videos uploaded today matching the search term were found.")


def loop_search():
    global running
    while running:
        run_manual_check()
        print("\nWaiting 5 minutes until next check...\n")
        time.sleep(300)


if __name__ == "__main__":
    print("Type 'start' to begin checking for 'line rider' every 5 minutes.")
    print("Type 'stop' to end the loop.")
    print("Type 'exit' to quit the program.\n")

    search_thread = None

    while True:
        command = input("> ").strip().lower()

        if command == "start":
            if not running:
                running = True
                search_thread = threading.Thread(target=loop_search, daemon=True)
                search_thread.start()
                print("Started searching.\n")
            else:
                print("Already running.\n")

        elif command == "stop":
            if running:
                running = False
                print("Stopping... Will end after current check finishes.\n")
            else:
                print("Not running.\n")

        elif command == "exit":
            running = False
            print("Exiting program.")
            break

        else:
            print("Unknown command. Use 'start', 'stop', or 'exit'.\n")
