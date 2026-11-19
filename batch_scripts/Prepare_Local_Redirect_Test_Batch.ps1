# AI QA Assistant - Prepare Local Redirect Test
# Creates a separate local test server; does not modify test_server.py or project data.

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LocalTestDir = Join-Path $ProjectRoot "local_test_site"
$ProjectConfig = Join-Path $ProjectRoot "projects\LOCAL_SCANNER_TEST\project_config.json"
$OriginalServer = Join-Path $LocalTestDir "test_server.py"
$RedirectServer = Join-Path $LocalTestDir "redirect_test_server.py"

Write-Host "=== PREPARE LOCAL REDIRECT TEST ==="

if (-not (Test-Path $ProjectConfig -PathType Leaf)) {
    throw "Konfigurasi LOCAL_SCANNER_TEST tidak ditemukan. Hentikan proses."
}
if (-not (Test-Path $OriginalServer -PathType Leaf)) {
    throw "test_server.py asli tidak ditemukan. Hentikan proses."
}
if (Test-Path $RedirectServer) {
    throw "File redirect_test_server.py sudah ada. Tidak akan ditimpa."
}

$Config = Get-Content $ProjectConfig -Raw | ConvertFrom-Json
if ($Config.project_id -ne "LOCAL_SCANNER_TEST") {
    throw "Project ID tidak sesuai."
}
if ($Config.base_url -ne "http://127.0.0.1:8000") {
    throw "Base URL proyek tidak sesuai: $($Config.base_url)"
}

$OriginalHashBefore = (Get-FileHash $OriginalServer -Algorithm SHA256).Hash

$ServerCode = @'
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


class MainHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:8001/target")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            print("[8000] GET /redirect -> 302 to 127.0.0.1:8001/target", flush=True)
            return

        body = b"<html><head><title>Local Redirect Test</title></head><body><h1>Main local server</h1></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
        print(f"[8000] GET {self.path} -> 200", flush=True)

    def log_message(self, format, *args):
        pass


class DestinationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<html><head><title>Redirect Destination</title></head><body><h1>Destination reached</h1></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
        print(f"[8001] DESTINATION REQUEST RECEIVED: GET {self.path}", flush=True)

    def log_message(self, format, *args):
        pass


main_server = ThreadingHTTPServer(("127.0.0.1", 8000), MainHandler)
destination_server = ThreadingHTTPServer(("127.0.0.1", 8001), DestinationHandler)

destination_thread = Thread(
    target=destination_server.serve_forever,
    name="redirect-destination-server",
    daemon=True,
)
destination_thread.start()

print("Local redirect test servers are running:", flush=True)
print("  Main:        http://127.0.0.1:8000/", flush=True)
print("  Redirect:    http://127.0.0.1:8000/redirect", flush=True)
print("  Destination: http://127.0.0.1:8001/target", flush=True)
print("Press Ctrl+C to stop both servers.", flush=True)

try:
    main_server.serve_forever()
except KeyboardInterrupt:
    print("\nStopping local redirect test servers...", flush=True)
finally:
    main_server.shutdown()
    destination_server.shutdown()
    main_server.server_close()
    destination_server.server_close()
    print("Both local servers stopped.", flush=True)
'@

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($RedirectServer, $ServerCode, $Utf8NoBom)

$OriginalHashAfter = (Get-FileHash $OriginalServer -Algorithm SHA256).Hash
if ($OriginalHashBefore -ne $OriginalHashAfter) {
    Remove-Item $RedirectServer -Force
    throw "Integritas test_server.py berubah. File persiapan dibatalkan."
}

Write-Host "File server redirect dibuat: $RedirectServer"
Write-Host "SHA256 test_server.py asli tetap sama: $OriginalHashAfter"

& (Join-Path $ProjectRoot ".venv-scanner\Scripts\python.exe") -m py_compile $RedirectServer
if ($LASTEXITCODE -ne 0) {
    throw "Validasi sintaks redirect_test_server.py gagal."
}

Write-Host "Validasi sintaks Python: OK"
Write-Host "test_server.py asli tidak diubah."
