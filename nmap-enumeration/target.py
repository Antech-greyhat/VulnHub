#!/usr/bin/env python3
"""Small HTTP fixtures alongside real SSH, FTP, and DNS training services."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import signal
import socket
import ssl
import subprocess
import sys
import threading
from urllib.parse import urlsplit

HOME = Path("/opt/mfano")
PORTAL_TITLE = "Mfano Network Practice"
ARCHIVE_TITLE = "Mfano Archive Inventory"


class PracticeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, _format, *args):
        pass

    def reply(self, *, head=False):
        path = urlsplit(self.path).path
        role = self.server.role
        if path == "/robots.txt":
            body = "User-agent: *\nDisallow: /staff-notices/\nDisallow: /archive-transfer/\n"
            content_type = "text/plain"
        elif path in ("/", "/staff-notices/", "/archive-transfer/"):
            title = ARCHIVE_TITLE if role == "archive" else PORTAL_TITLE
            body = (f"<!doctype html><title>{title}</title><h1>{title}</h1>"
                    "<p>FAKE school records. Read-only Nmap service practice.</p>")
            content_type = "text/html"
        else:
            self.send_error(404)
            return
        data = body.encode("ascii")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Lab-Role", role)
        self.end_headers()
        if not head:
            self.wfile.write(data)

    def do_GET(self):
        self.reply()

    def do_HEAD(self):
        self.reply(head=True)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Allow", "GET, HEAD, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()


class PracticeServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        # Version probes often close connections before sending an HTTP request.
        if isinstance(sys.exc_info()[1], (ConnectionResetError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)


def make_http_server(role, address, port, certificate=None, key=None):
    server = PracticeServer((address, port), PracticeHandler)
    server.daemon_threads = True
    server.role = role
    if certificate is not None:
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certificate, key)
            server.socket = context.wrap_socket(server.socket, server_side=True)
        except (OSError, ssl.SSLError):
            server.server_close()
            raise
    return server


def health(role):
    ports = (21, 22, 53, 80, 443, 31337) if role == "portal" else (18080,)
    try:
        for port in ports:
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                pass
    except OSError:
        return 1
    return 0


def serve(role):
    stopped = threading.Event()
    servers = []
    processes = []
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    signal.signal(signal.SIGINT, lambda *_: stopped.set())

    def start_http(port, certificate=None, key=None):
        server = make_http_server(role, "0.0.0.0", port, certificate, key)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)

    try:
        if role == "portal":
            Path("/run/sshd").mkdir(mode=0o755, exist_ok=True)
            Path("/run/vsftpd/empty").mkdir(mode=0o755, parents=True, exist_ok=True)
            for command in (
                ["/usr/sbin/sshd", "-D", "-e", "-f", str(HOME / "config/sshd_config")],
                ["/usr/sbin/vsftpd", str(HOME / "config/vsftpd.conf")],
                ["/usr/sbin/dnsmasq", "--keep-in-foreground", "--conf-file=" + str(HOME / "config/dnsmasq.conf")],
            ):
                # vsftpd sends early startup errors to its command descriptor
                # (stdin), before accepting a socket. Route those to Docker logs.
                startup_input = sys.stdout if command[0].endswith("/vsftpd") else subprocess.DEVNULL
                processes.append(subprocess.Popen(command, stdin=startup_input))
            start_http(80)
            start_http(31337)
            start_http(443, HOME / "certs/training.crt", HOME / "certs/training.key")
        else:
            start_http(18080)
        while not stopped.wait(0.5):
            for process in processes:
                code = process.poll()
                if code is not None:
                    name = Path(process.args[0]).name
                    print(f"Training service {name} exited ({code}); inspect its startup error above.",
                          file=sys.stderr)
                    return 1
        return 0
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("portal", "archive", "health"))
    parser.add_argument("role", choices=("portal", "archive"), nargs="?", default="portal")
    args = parser.parse_args()
    return health(args.role) if args.mode == "health" else serve(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
