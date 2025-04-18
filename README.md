# Line Rider YouTube Checker

This tool looks for new **Line Rider** videos on YouTube, checks for uploads from the last 24 hours, and logs them. It also avoids showing the same videos more than once.

### Features:
- Only checks **Line Rider** videos from the last 24 hours.
- Saves the video title, uploader, and a short link in `seen_videos.txt`.
- Has a simple UI to start/stop the checker.

### Setup:
1. Create a folder for the project.
2. Clone or download the repo into that folder.
3. Install the required libraries:
    ```bash
    pip install yt-dlp pygame
    ```

### Usage:
1. Run the script:
    ```bash
    python "line rider scraper.py"
    ```
2. You can either use the buttons in the UI or type in the console:
    - Type `start` to start checking.
    - Type `stop` to stop checking.
    - Type `exit` to quit.

The program will log the details of new videos to `seen_videos.txt`.

### Notes:
- It is recommended to put the project in its own folder for easier management.
