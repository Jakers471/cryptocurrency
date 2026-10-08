"""Serve the UI locally and open it in the browser.

Usage (from the project root):  python3 serve.py            -> http://127.0.0.1:8765/ui/
                                python3 serve.py --no-open  (just serve)
Only listens on this machine (127.0.0.1). Ctrl+C to stop.
Needed because browsers block file:// pages from reading neighbouring files on macOS.
"""
import functools
import http.server
import sys
import webbrowser

from core import paths

PORT = 8765


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # no per-request spam in the terminal
        pass


def main():
    url = f"http://127.0.0.1:{PORT}/ui/"
    handler = functools.partial(Quiet, directory=paths.ROOT)
    try:
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    except OSError:  # port taken: most likely the scanner is already being served
        print(f"Already running at {url} (opening it). To restart it: lsof -ti :{PORT} | xargs kill")
        webbrowser.open(url)
        return
    with srv:
        print(f"Alt Scanner at {url}  (Ctrl+C to stop)", flush=True)
        if "--no-open" not in sys.argv:
            webbrowser.open(url)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
