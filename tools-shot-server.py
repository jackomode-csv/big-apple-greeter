# Screenshot harness for the migration.
#
# Serving rather than opening file:// so the pages can be doctored on the way
# out without writing anything into the repo. With ?shot=1 the response gets a
# stylesheet that makes a screenshot deterministic:
#   - .reveal forced visible. The site fades content in on scroll and the
#     override that disables it lives in a reduced-motion query, so a
#     screenshot with no JS is otherwise a blank page.
#   - transitions and animations off, so nothing is caught mid-move.
#   - video hidden behind its poster, so the diff is not comparing whichever
#     frame each run happened to land on.
import http.server, io, os, re, socketserver, sys

ROOT = r'C:\Users\Jack Murray\OneDrive\Documents\big-apple-greeter'
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8100

SHOT = b"""<style id="shot-mode">
  .reveal, .reveal * { opacity: 1 !important; transition: none !important; }
  *, *::before, *::after {
    transition: none !important;
    animation: none !important;
    scroll-behavior: auto !important;
  }
  video { visibility: hidden !important; }
  .logo-video { visibility: hidden !important; }
  .logo-svg { display: block !important; }
</style></head>"""


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def send_head(self):
        p = self.translate_path(self.path)
        if not p.lower().endswith('.html') or not os.path.isfile(p):
            return super().send_head()
        body = io.open(p, 'rb').read()
        if 'shot=1' in self.path:
            body = body.replace(b'</head>', SHOT, 1)
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        return io.BytesIO(body)

    def log_message(self, *a):
        pass


class S(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


print('shot server on %d' % PORT)
sys.stdout.flush()
S(('127.0.0.1', PORT), H).serve_forever()
