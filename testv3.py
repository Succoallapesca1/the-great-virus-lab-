
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from threading import Lock, Thread
from urllib.parse import urlparse
import json
import socket
import time
import os

PORT = 8080
messages = []
lock = Lock()

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wi-Fi Announcements</title>
<style>
body {
    background:#101010;color:white;
    font-family:Arial;padding:25px;
}
h2 {color:#ff4040}
#messages {
    background:#202020;padding:15px;
    border-radius:12px;min-height:200px;
}
.msg {
    background:#303030;padding:14px;
    margin:10px 0;border-radius:10px;
}
small {color:#aaa}
</style>
</head>
<body>
<h2>📡 Wi-Fi Network Announcements</h2>
<p>Connected to the local announcement page.</p>
<div id="messages">Waiting for messages...</div>
<script>
let last = 0;
async function update() {
    try {
        const r = await fetch('/messages?after=' + last);
        const data = await r.json();
        const box = document.getElementById('messages');

        if(data.length) {
            if(last === 0) box.innerHTML = '';
            data.forEach(m => {
                const div = document.createElement('div');
                div.className = 'msg';

                const content = document.createElement('div');
                content.textContent = m.text;

                const time = document.createElement('small');
                time.textContent = m.time;

                div.append(content, time);
                box.appendChild(div);
                last = Math.max(last, m.id);
            });
        }
    } catch(e) {}
}
setInterval(update, 1000);
update();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(self.path)

        if path.path == "/":
            data = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        elif path.path == "/messages":
            from urllib.parse import parse_qs
            after = int(parse_qs(path.query).get("after", ["0"])[0])

            with lock:
                result = [
                    m for m in messages if m["id"] > after
                ]

            data = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        else:
            self.send_error(404)

    def log_message(self, *args):
        pass


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def sender():
    print("\nType a message and press ENTER.")
    print("Type /quit to stop.\n")

    while True:
        try:
            text = input("> ").strip()

            if text == "/quit":
                os._exit(0)

            if not text:
                continue

            with lock:
                messages.append({
                    "id": len(messages) + 1,
                    "text": text[:2000],
                    "time": time.strftime("%H:%M:%S")
                })

            print("[SENT] Message published to local webpage.")

        except (EOFError, KeyboardInterrupt):
            os._exit(0)


if __name__ == "__main__":
    ip = get_ip()

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)

    print("=" * 48)
    print("       CART3R.JAILBREAK WIFI ANNOUNCER")
    print("=" * 48)
    print(f"\nLocal webpage: http://{ip}:{PORT}")
    print("Share this address with devices you authorize.")
    print("Allow Python through your PRIVATE network firewall.")
    print("\nWaiting for messages...")

    Thread(target=sender, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
