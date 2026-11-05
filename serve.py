"""Serve the built, browser-local studio. Python 3 standard library only."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port', type=int, default=8765)
parser.add_argument('--no-open', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parent / 'dist'
if not (root / 'index.html').is_file():
    parser.error('Built app is missing. In the source project, run npm ci and npm run build first.')
try:
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(SimpleHTTPRequestHandler, directory=str(root)))
except OSError as error:
    parser.error(f'Could not start port {args.port}: {error}. Try --port 8766.')
url = f'http://127.0.0.1:{args.port}/'
print(f'\nC.A.R.E. MRI Research Studio\n{url}\nImages are processed in the browser. Press Ctrl+C to close.\n', flush=True)
if not args.no_open:
    webbrowser.open(url)
try:
    server.serve_forever()
except KeyboardInterrupt:
    print('\nStudio closed.')
finally:
    server.server_close()
