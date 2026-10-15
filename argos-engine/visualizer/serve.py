#!/usr/bin/env python3
"""Launch the prebuilt ARGOS viewer using only Python's standard library."""

import argparse
import base64
import hashlib
import http.server
import json
import re
import sys
import webbrowser
from functools import partial
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent


def check_package():
    manifest = json.loads((DIRECTORY / 'provenance.json').read_text(encoding='utf-8'))
    page_bytes = (DIRECTORY / 'index.html').read_bytes()
    if hashlib.sha256(page_bytes).hexdigest() != manifest['viewer_sha256']:
        raise ValueError('index.html does not match provenance.json')
    page = page_bytes.decode('utf-8')
    match = re.search(r'id="ar-embedded-model">([^<]+)</script>', page)
    if not match:
        raise ValueError('The embedded CAD model is missing')
    model = base64.b64decode(match.group(1), validate=True)
    if model[:4] != b'glTF' or hashlib.sha256(model).hexdigest() != manifest['model_sha256']:
        raise ValueError('The embedded CAD model does not match its source hash')
    meta_match = re.search(r'id="ar-embedded-meta">(.*?)</script>', page, re.S)
    metadata = json.loads(meta_match.group(1)) if meta_match else {}
    if len(metadata) != manifest['modeled_instances']:
        raise ValueError('The modeled-instance count does not match the manifest')
    print('PACKAGE_OK: ARGOS H1 v3.5.1; {} modeled instances; model SHA-256 verified'.format(len(metadata)), flush=True)


class ViewerHandler(http.server.SimpleHTTPRequestHandler):
    def list_directory(self, path):
        self.send_error(404, 'Directory listing is not enabled')
        return None

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-browser', action='store_true', help='Print the URL without opening the default browser')
    parser.add_argument('--port', type=int, default=0, help='Local port; 0 selects an available port (default)')
    parser.add_argument('--check', action='store_true', help='Verify the package without starting a server')
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error('--port must be between 0 and 65535')
    try:
        check_package()
        if args.check:
            return 0
        handler = partial(ViewerHandler, directory=str(DIRECTORY))
        with http.server.ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
            url = 'http://127.0.0.1:{}/#engine-model'.format(server.server_address[1])
            print('LAUNCH_URL=' + url, flush=True)
            print('Press Ctrl+C to stop this viewer server.', flush=True)
            if not args.no_browser:
                try:
                    webbrowser.open(url)
                except webbrowser.Error:
                    print('Open LAUNCH_URL in your browser.', flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print('\nViewer server stopped.', flush=True)
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print('Cannot launch viewer: {}'.format(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
