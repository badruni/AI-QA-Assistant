from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


class ThresholdTestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path

        if path == "/":
            body = (
                "<html><head><title>403 Threshold Test</title></head><body>"
                "<h1>403 Threshold Test</h1>"
                '<a href="/forbidden-1">Forbidden 1</a>'
                '<a href="/forbidden-2">Forbidden 2</a>'
                '<a href="/forbidden-3">Forbidden 3</a>'
                '<a href="/after-threshold">Must Not Be Requested</a>'
                "</body></html>"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            print("[200] GET / -> homepage with 4 ordered links", flush=True)
            return

        if path in ("/forbidden-1", "/forbidden-2", "/forbidden-3"):
            self.send_response(403)
            self.send_header("Content-Length", "0")
            self.end_headers()
            print(f"[403] GET {path}", flush=True)
            return

        if path == "/after-threshold":
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
            print("[200] GET /after-threshold -> UNEXPECTED REQUEST", flush=True)
            return

        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()
        print(f"[404] GET {path}", flush=True)

    def log_message(self, format, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 8000), ThresholdTestHandler)
print("Local HTTP 403 threshold test server is running:", flush=True)
print("  Homepage:       http://127.0.0.1:8000/", flush=True)
print("  403 responses:  /forbidden-1, /forbidden-2, /forbidden-3", flush=True)
print("  Sentinel link:  /after-threshold (must not be requested)", flush=True)
print("Press Ctrl+C to stop the server.", flush=True)

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nStopping local HTTP 403 threshold test server...", flush=True)
finally:
    server.server_close()
    print("Local server stopped.", flush=True)
