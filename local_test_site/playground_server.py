from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

HOST = "127.0.0.1"
PORT = 8000
ROOT = Path(__file__).resolve().parent / "playground"

class PlaygroundHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def translate_path(self, path):
        relative = unquote(urlsplit(path).path).lstrip("/")
        candidate = (ROOT / relative).resolve()
        try:
            candidate.relative_to(ROOT.resolve())
        except ValueError:
            return str(ROOT / "__blocked_path__")
        return str(candidate)

    def log_message(self, fmt, *args):
        safe_path = urlsplit(self.path).path[:180]
        status = args[1] if len(args) > 1 else "-"
        print(f"{self.command} {safe_path} - {status}")

if __name__ == "__main__":
    if not ROOT.is_dir():
        raise SystemExit(f"Web root tidak ditemukan: {ROOT}")
    print(f"MyDreamZone Local QA Playground: http://{HOST}:{PORT}/")
    print("Server hanya menerima koneksi loopback. Tekan Ctrl+C untuk berhenti.")
    try:
        ThreadingHTTPServer((HOST, PORT), PlaygroundHandler).serve_forever()
    except OSError as exc:
        raise SystemExit(f"Gagal menjalankan server pada {HOST}:{PORT}: {exc}")
