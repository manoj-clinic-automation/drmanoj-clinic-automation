"""
Local launcher for the clinic PC.

Double-click the desktop shortcut (or open_tracker.bat) and this:
  1. forces LOCAL mode (no login) BEFORE importing the app,
  2. starts the web server bound to this PC only (127.0.0.1),
  3. waits until the server is actually answering,
  4. THEN opens the browser — so the page always loads.

It never needs a password (local PC = no network exposure).
"""

import os
# CRITICAL: set local mode BEFORE importing app, so the server-credential
# guard never fires on the clinic PC.
os.environ["TRACKER_LOCAL"] = "1"

import socket
import threading
import time
import webbrowser

HOST = "127.0.0.1"


def _free_port(preferred=5000):
    """Use 5000 if free, otherwise let the OS pick an open port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((HOST, preferred))
        s.close()
        return preferred
    except OSError:
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind((HOST, 0))
        port = s2.getsockname()[1]
        s2.close()
        return port


def _wait_then_open(url, port):
    # Poll the port until the server answers, then open the browser.
    for _ in range(60):  # up to ~6 seconds
        try:
            with socket.create_connection((HOST, port), timeout=0.25):
                break
        except OSError:
            time.sleep(0.1)
    webbrowser.open(url)


def main():
    from app import app  # safe: TRACKER_LOCAL already set above

    port = _free_port(5000)
    url = f"http://{HOST}:{port}/"
    print("=" * 56)
    print(" Dr. Manoj Agarwal Clinic — Follow-Up Tracker")
    print(f" Open in your browser:  {url}")
    print(" Keep this window OPEN while you use the tracker.")
    print(" Close this window to stop the tracker.")
    print("=" * 56)

    threading.Thread(target=_wait_then_open, args=(url, port), daemon=True).start()
    app.run(host=HOST, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
