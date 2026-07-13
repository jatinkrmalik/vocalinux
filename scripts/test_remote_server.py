#!/usr/bin/env python3
"""
Vocalinux Remote API Test Server

A simple mock server for testing Vocalinux's remote API feature.
Supports whisper.cpp (/inference) and OpenAI/FunASR-compatible
(/v1/audio/transcriptions) formats.

Usage:
    python test_remote_server.py [--port PORT] [--delay SECONDS]

Examples:
    python test_remote_server.py                    # Default: port 8080, no delay
    python test_remote_server.py --port 9000        # Custom port
    python test_remote_server.py --delay 2          # Simulate 2s processing delay
"""

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


class RemoteAPITestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for testing Vocalinux remote API."""

    def log_message(self, format, *args):
        """Custom log format with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {args[0]}")

    def do_GET(self):
        """Handle GET requests (health check and OpenAI models endpoint)."""
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "status": "ok",
                "message": "Vocalinux Remote API Test Server",
                "endpoints": [
                    "/inference (whisper.cpp format)",
                    "/v1/audio/transcriptions (OpenAI/FunASR format)",
                    "/v1/models (OpenAI models list)",
                ],
            }
            self.wfile.write(json.dumps(response, indent=2).encode())

        elif self.path == "/v1/models":
            # OpenAI-compatible models endpoint
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "data": [
                    {
                        "id": "whisper-1",
                        "object": "model",
                        "created": 1234567890,
                        "owned_by": "openai",
                    },
                    {
                        "id": "sensevoice",
                        "object": "model",
                        "created": 1767225600,
                        "owned_by": "mock",
                    },
                ],
                "object": "list",
            }
            self.wfile.write(json.dumps(response, indent=2).encode())

        elif self.path == "/inference":
            # whisper.cpp server health check
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"status": "ok", "model": "mock-whisper"}
            self.wfile.write(json.dumps(response, indent=2).encode())

        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"error": "Not found"}
            self.wfile.write(json.dumps(response, indent=2).encode())

    def do_POST(self):
        """Handle POST requests (transcription endpoints)."""
        # Simulate processing delay if configured
        if self.server.delay > 0:
            time.sleep(self.server.delay)

        if self.path in ["/inference", "/v1/audio/transcriptions"]:
            # Parse multipart form data (simplified - just read the body)
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            # Extract filename if present
            filename = "audio.wav"
            if b"filename=" in body:
                # Simple extraction from multipart data
                try:
                    start = body.index(b'filename="') + 10
                    end = body.index(b'"', start)
                    filename = body[start:end].decode("utf-8", errors="ignore")
                except (ValueError, IndexError):
                    pass

            # Generate mock transcription based on filename
            transcription = self._generate_mock_transcription(filename)

            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            if self.path == "/inference":
                # whisper.cpp format
                response = {"text": transcription}
            else:
                # OpenAI/FunASR-compatible format
                response = {"text": transcription}

            self.wfile.write(json.dumps(response, indent=2).encode())
            print(f"  → Transcribed '{filename}': {transcription}")

        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"error": "Not found"}
            self.wfile.write(json.dumps(response, indent=2).encode())

    def _generate_mock_transcription(self, filename: str) -> str:
        """Generate a mock transcription based on the filename."""
        # Different responses based on filename to make testing more interesting
        if "test" in filename.lower():
            return "This is a test transcription from the mock server."
        elif "hello" in filename.lower():
            return "Hello, this is Vocalinux testing the remote API."
        elif "long" in filename.lower():
            return (
                "This is a longer transcription to test how the system handles "
                "multiple sentences and proper text injection into applications. "
                "The quick brown fox jumps over the lazy dog."
            )
        else:
            return "Mock transcription from test server."


class DelayedHTTPServer(HTTPServer):
    """HTTP Server with configurable delay."""

    def __init__(self, server_address, RequestHandlerClass, delay=0):
        self.delay = delay
        super().__init__(server_address, RequestHandlerClass)


def main():
    parser = argparse.ArgumentParser(
        description="Vocalinux Remote API Test Server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0,
        help="Simulated processing delay in seconds (default: 0)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Vocalinux Remote API Test Server")
    print("=" * 60)
    print(f"Listening on: http://{args.host}:{args.port}")
    print(f"Processing delay: {args.delay}s")
    print()
    print("Endpoints:")
    print("  GET  /                          - Server info")
    print("  GET  /v1/models                 - OpenAI models list")
    print("  GET  /inference                 - whisper.cpp health check")
    print("  POST /inference                 - whisper.cpp transcription")
    print("  POST /v1/audio/transcriptions   - OpenAI/FunASR transcription")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    try:
        server = DelayedHTTPServer(
            (args.host, args.port), RemoteAPITestHandler, delay=args.delay
        )
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except Exception as e:
        print(f"\nError: {e}")
        if args.port < 1024:
            print("Note: Ports below 1024 require root privileges.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
