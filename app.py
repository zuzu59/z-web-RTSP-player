#!/usr/bin/env python3
"""Minimal RTSP-to-browser viewer powered by FFmpeg and Python's stdlib."""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8089"))
ROOT = Path(__file__).resolve().parent
_camera_url: str | None = None
_camera_lock = threading.Lock()


def validate_rtsp_url(value: object) -> str | None:
    """Return a validation error, or None if value is a plausible RTSP URL."""
    if not isinstance(value, str) or not value.strip():
        return "Saisissez l’URL RTSP de votre caméra."
    value = value.strip()
    try:
        parsed = urlsplit(value)
        # Accessing .port also validates malformed ports.
        port = parsed.port
    except ValueError:
        return "L’URL contient un port invalide."
    if parsed.scheme.lower() != "rtsp":
        return "L’URL doit commencer par rtsp://."
    if not parsed.hostname:
        return "L’URL doit contenir l’adresse IP ou le nom d’hôte de la caméra."
    if port is not None and not 1 <= port <= 65535:
        return "Le port doit être compris entre 1 et 65535."
    if not re.match(r"^[\w.-]+$", parsed.hostname, re.UNICODE):
        return "L’adresse de la caméra n’est pas valide."
    return None


class Handler(BaseHTTPRequestHandler):
    server_version = "CamViewer/1.0"

    def _json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            data = (ROOT / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif path == "/status":
            with _camera_lock:
                configured = _camera_url is not None
            self._json(200, {"configured": configured})
        elif path == "/stream":
            self._stream()
        else:
            self._json(404, {"error": "Page introuvable."})

    def do_POST(self) -> None:
        global _camera_url
        if self.path != "/connect":
            self._json(404, {"error": "Page introuvable."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 8192:
                self._json(413, {"error": "L’URL est trop longue."})
                return
            body = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"error": "Requête invalide."})
            return
        url = body.get("url") if isinstance(body, dict) else None
        error = validate_rtsp_url(url)
        if error:
            self._json(400, {"error": error})
            return
        with _camera_lock:
            _camera_url = url.strip()
        self._json(200, {"connected": True})

    def _stream(self) -> None:
        with _camera_lock:
            url = _camera_url
        if not url:
            self._json(409, {"error": "Configurez d’abord l’URL de la caméra."})
            return

        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-rtsp_transport", "tcp",
            "-i", url, "-an", "-c:v", "mjpeg", "-q:v", "5", "-f", "mpjpeg",
            "-boundary_tag", "camviewer", "pipe:1",
        ]
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except OSError:
            self._json(503, {"error": "FFmpeg est introuvable sur le serveur."})
            return

        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=camviewer")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            assert process.stdout is not None
            while True:
                chunk = process.stdout.read1(4096)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def log_message(self, fmt: str, *args: object) -> None:
        # Avoid writing RTSP credentials or request URLs to logs.
        if self.path not in ("/", "/status", "/connect", "/stream"):
            return
        print(f"[{self.log_date_time_string()}] {self.address_string()} {fmt % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Visionneuse caméra disponible sur http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
