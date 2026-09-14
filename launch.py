"""One command starts the API and local interface. Ctrl+C stops both."""
from pathlib import Path
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent

def main():
    for port in [8000, 5173]:
        with socket.socket() as probe:
            try:
                probe.bind(('127.0.0.1', port))
            except OSError:
                raise SystemExit(f'Port {port} is in use. If Ironing Fly is already running, open http://127.0.0.1:5173/. Otherwise stop the process using that port.')
    node = shutil.which('node')
    if not node:
        raise SystemExit('Node.js 22.13+ is required for the interface. Install Node.js, then run this command again.')
    web = ROOT / 'web'
    if not (web / 'node_modules/vinext/package.json').exists():
        npm = shutil.which('npm')
        if not npm:
            raise SystemExit('npm was not found with Node.js')
        command = ['cmd', '/d', '/c', npm, 'ci'] if os.name == 'nt' else [npm, 'ci']
        subprocess.run(command, cwd=web, check=True)
    package = json.loads((web / 'node_modules/vinext/package.json').read_text(encoding='utf-8'))
    bin_path = package['bin']['vinext'] if isinstance(package['bin'], dict) else package['bin']
    cli = web / 'node_modules/vinext' / bin_path
    children = []
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    try:
        children.append(subprocess.Popen([sys.executable, str(ROOT / 'main.py')], cwd=ROOT, creationflags=flags))
        children.append(subprocess.Popen([node, str(cli), 'dev'], cwd=web, creationflags=flags))
        for _ in range(120):
            if any(child.poll() is not None for child in children):
                raise RuntimeError('A server stopped during startup; see its output above')
            try:
                with urllib.request.urlopen('http://127.0.0.1:5173/api/health', timeout=2) as response:
                    if response.status == 200:
                        break
            except (OSError, TimeoutError):
                time.sleep(.5)
        else:
            raise RuntimeError('Startup timed out; see server output above')
        print('\nIroning Fly is ready: http://127.0.0.1:5173/\nPress Ctrl+C here to stop both servers.\n', flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(.5)
    except KeyboardInterrupt:
        print('\nStopping Ironing Fly…')
    finally:
        for child in reversed(children):
            child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()

if __name__ == '__main__':
    main()
