from http.server import BaseHTTPRequestHandler, HTTPServer


class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/forbidden":
            status = 403
            body = b"Access Forbidden"
        elif self.path == "/server-error":
            status = 500
            body = b"Internal Server Error"
        else:
            status = 200
            body = b"<html><head><title>Local QA Test</title></head><body><h1>Local Test Server</h1></body></html>"

        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)


server = HTTPServer(("127.0.0.1", 8000), TestHandler)
print("Local QA Test Server berjalan di http://127.0.0.1:8000")
server.serve_forever()
