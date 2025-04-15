import yt_dlp
from datetime import datetime, timedelta
import time
import threading
import pygame
import sys

# Platform-specific non-blocking input
import os
if os.name == 'nt':  # Windows
    import msvcrt
else:
    import select

running = False
waiting = True
search_thread = None
start_time = datetime.now()

# Extra UI state for tracking last check, check count, and videos found
extra_ui_state = {
    "last_check": None,
    "check_count": 0,
    "videos_found": 0
}

def normalize_string(s):
    return s.lower().strip()

def search_youtube(term, max_results=20):
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    search_term_with_date = f"\"{term}\" after:{yesterday}"
    search_url = f"ytsearchdate{max_results}:{search_term_with_date}"

    flat_opts = {
        "quiet": True,
        "extract_flat": True,
        "dump_single_json": True,
    }

    with yt_dlp.YoutubeDL(flat_opts) as ydl:
        result = ydl.extract_info(search_url, download=False)

    entries = result.get("entries", [])
    full_entries = []
    full_opts = {"quiet": True}

    with yt_dlp.YoutubeDL(full_opts) as ydl:
        for entry in entries:
            url = entry.get("url") or entry.get("webpage_url")
            try:
                full_info = ydl.extract_info(url, download=False)
                full_entries.append(full_info)
            except yt_dlp.utils.DownloadError:
                continue

    print(f"\nSearch URL: https://www.youtube.com/results?search_query={search_term_with_date}\n")
    return full_entries

def is_uploaded_today(entry):
    upload_date = entry.get("upload_date")
    if upload_date:
        upload_date_obj = datetime.strptime(str(upload_date), "%Y%m%d")
        return upload_date_obj.date() == datetime.today().date()
    return False

def load_seen_videos():
    try:
        with open("seen_videos.txt", "r") as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

def save_seen_video(str):

    # Save both the title and the short URL
    with open("seen_videos.txt", "a") as file:
        file.write(f"{str}\n")

def run_manual_check():
    search_term = "line rider"
    normalized_search_term = normalize_string(search_term)

    print(f"\nSearching for: {search_term}")
    results = search_youtube(search_term)
    if not results:
        print("No search results found.")
        return

    seen_videos = load_seen_videos()
    found = False

    skipped = 0

    for entry in results:
        title = entry.get("title")
        url = entry.get("url") or entry.get("webpage_url")
        uploader = entry.get('uploader', 'Unknown author')
        upload_date = entry.get("upload_date", "Unknown")
        video_id = entry.get("id")
        short_url = f"https://youtu.be/{video_id}"
        video_str = title + " | " + uploader + " | " + short_url

        name = title + " | " + uploader
        normalized_title = normalize_string(title)

        if normalized_search_term not in normalized_title :
            skipped += 1
            continue

        print(f"\n Checking: {title} by {uploader}")
        print(f"   URL: {short_url}")
        print(f"   Upload Date: {upload_date}")
        print(f"   Already seen: {'✅' if video_str in seen_videos else '❌'}")

        if video_str not in seen_videos:
            print(f"\n Title: {title}")
            print(f" Link: {short_url}")
            print(f" Uploaded: {datetime.strptime(str(entry['upload_date']), '%Y%m%d')}")
            found = True
            save_seen_video(video_str)
            seen_videos.add(name)
            extra_ui_state["videos_found"] += 1

    # Update UI state
    print(f"\nskipped: {skipped}")
    extra_ui_state["check_count"] += 1       

def loop_search():
    global running, waiting
    while running:
        waiting = False
        run_manual_check()
        print(f"Last check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Waiting 5 minutes until next check...\n")
        waiting = True
        for _ in range(60 * check_rate):
            if not running:
                break
            time.sleep(1)

def start_checking():
    global search_thread, running
    if not running:
        running = True
        search_thread = threading.Thread(target=loop_search, daemon=True)
        search_thread.start()
        print("\nStarted searching.")

def stop_checking():
    global running
    if running:
        running = False
        print("Stopping...")

def get_console_input():
    if os.name == 'nt':  # Windows
        if msvcrt.kbhit():
            return input("> ").strip().lower()
    else:  # Unix/Linux/Mac
        if select.select([sys.stdin], [], [], 0.0)[0]:
            return sys.stdin.readline().strip().lower()
    return None

def main_loop():
    global check_rate

    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("YouTube Checker")
    font = pygame.font.SysFont(None, 32)
    small_font = pygame.font.SysFont(None, 24)
    clock = pygame.time.Clock()

    bg_color = (40, 40, 40)
    button_color = (90, 90, 90)
    text_color = (230, 230, 230)
    active_color = (120, 180, 120)
    stop_color = (180, 120, 120)
    slow_color = (200, 200, 100)  # yellow

    start_btn = pygame.Rect(125, 60, 150, 40)
    stop_btn = pygame.Rect(125, 120, 150, 40)
    quit_btn = pygame.Rect(125, 180, 150, 40)
    slow_mode_btn = pygame.Rect(10, 10, 130, 30)

    slow_mode = False
    check_rate = 5  # default

    print("Type 'start', 'stop', 'exit', or use the buttons in the window.\n")

    while True:
        screen.fill(bg_color)

        def draw_button(text, rect, color):
            pygame.draw.rect(screen, color, rect)
            label = font.render(text, True, text_color)
            screen.blit(label, label.get_rect(center=rect.center))

        draw_button("Start", start_btn, active_color if not running else button_color)
        draw_button("Stop", stop_btn, stop_color if running else button_color)
        draw_button("Quit", quit_btn, button_color)

        # Slow mode button
        slow_label = "Slow Mode"
        draw_button(slow_label, slow_mode_btn, slow_color if slow_mode else button_color)

        uptime = datetime.now() - start_time
        uptime_text = small_font.render(f"Uptime: {str(uptime).split('.')[0]}", True, text_color)
        screen.blit(uptime_text, (10, 235))

        if extra_ui_state["last_check"]:
            last_check_label = small_font.render(f"Last check: {extra_ui_state['last_check']}", True, text_color)
            screen.blit(last_check_label, (10, 240))

        count_label = small_font.render(
            f"Checks: {extra_ui_state['check_count']}   Videos Found: {extra_ui_state['videos_found']}",
            True, text_color
        )
        screen.blit(count_label, (10, 265))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_checking()
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn.collidepoint(event.pos):
                    start_checking()
                elif stop_btn.collidepoint(event.pos):
                    stop_checking()
                elif quit_btn.collidepoint(event.pos):
                    stop_checking()
                    pygame.quit()
                    return
                elif slow_mode_btn.collidepoint(event.pos):
                    slow_mode = not slow_mode
                    check_rate = 30 if slow_mode else 5
                    print(f"Slow mode {'enabled' if slow_mode else 'disabled'} — check_rate set to {check_rate}")

        command = get_console_input()
        if command:
            if command == "start":
                start_checking()
            elif command == "stop":
                stop_checking()
            elif command == "exit":
                stop_checking()
                pygame.quit()
                return
            else:
                print("Unknown command. Use 'start', 'stop', or 'exit'.")

        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    main_loop()
