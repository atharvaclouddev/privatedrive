import os
import sys
import json
import time
import socket
import secrets
import mimetypes
import zipfile
import io
import argparse
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, session,
    redirect, url_for, send_from_directory, send_file, abort
)
from werkzeug.utils import secure_filename
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
from cheroot import wsgi

from tunnel import SSHTunnel
from qr import print_qr_terminal

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_STORAGE = BASE_DIR / "data_storage"
CONFIG_FILE = BASE_DIR / "config.json"
NOTES_FILE = BASE_DIR / "notes.json"

DEFAULT_STORAGE.mkdir(exist_ok=True)

# ----------------- Configuration -----------------

def load_or_init_config():
    default_config = {
        "username": "admin",
        "password": f"Pass{secrets.randbelow(9000) + 1000}",
        "port": 8080,
        "storage_dir": str(DEFAULT_STORAGE),
        "tunnel_enabled": True,
        "secret_key": secrets.token_hex(32)
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                default_config.update(data)
        except Exception:
            pass
    with open(CONFIG_FILE, "w") as f:
        json.dump(default_config, f, indent=4)
    return default_config

config = load_or_init_config()
STORAGE_DIR = Path(config["storage_dir"])
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
dav_provider = FilesystemProvider(str(STORAGE_DIR))

def update_shared_folder(new_path_str):
    global STORAGE_DIR
    expanded = Path(os.path.expanduser(str(new_path_str).strip())).resolve()
    expanded.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR = expanded
    config["storage_dir"] = str(expanded)
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f" [!] Warning: Failed to persist config: {e}")

    if dav_provider:
        dav_provider.root_folder_path = str(expanded)
        dav_provider.root_folder_path_real = os.path.realpath(str(expanded))
    return str(expanded)

# ----------------- Helpers -----------------

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def format_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}" if unit != 'B' else f"{int(size)} B"
        size /= 1024.0
    return f"{size:.1f} PB"

def load_notes():
    if NOTES_FILE.exists():
        try:
            with open(NOTES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_notes(notes):
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)

# ----------------- Flask Web Dashboard -----------------

flask_app = Flask(__name__)
flask_app.secret_key = config["secret_key"]
flask_app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024

ssh_tunnel = None

def check_auth():
    if session.get('authenticated'):
        return True
    # Localhost auto-auth
    if request.remote_addr in ('127.0.0.1', '::1'):
        session['authenticated'] = True
        return True
    return False

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth():
            if request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

@flask_app.route('/login')
def login_page():
    if check_auth():
        return redirect(url_for('index_page'))
    return render_template('login.html')

@flask_app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    u = str(data.get('username', '')).strip()
    p = str(data.get('password', '')).strip()

    if u == config['username'] and p == config['password']:
        session['authenticated'] = True
        return jsonify({"success": True, "redirect": url_for('index_page')})
    return jsonify({"error": "Invalid username or password"}), 401

@flask_app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('authenticated', None)
    return jsonify({"success": True})

@flask_app.route('/')
@require_auth
def index_page():
    return render_template('index.html')

@flask_app.route('/api/status')
@require_auth
def api_status():
    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", config['port']))
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    
    local_base = f"http://{local_ip}:{port}"
    public_base = render_url if render_url else (ssh_tunnel.public_url if ssh_tunnel else None)

    local_drive = f"{local_base}/drive"
    public_drive = f"{public_base}/drive" if public_base else None

    return jsonify({
        "local_ip": local_ip,
        "local_base": local_base,
        "local_drive": local_drive,
        "public_base": public_base,
        "public_drive": public_drive,
        "username": config['username'],
        "password": config['password'],
        "storage_dir": str(STORAGE_DIR)
    })

@flask_app.route('/api/files', methods=['GET'])
@require_auth
def list_files():
    files = []
    for item in sorted(STORAGE_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if item.is_file():
            stat = item.stat()
            mime, _ = mimetypes.guess_type(item.name)
            files.append({
                "name": item.name,
                "size": stat.st_size,
                "size_formatted": format_bytes(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %Y %I:%M %p"),
                "mime": mime or "application/octet-stream"
            })
    return jsonify({"files": files})

@flask_app.route('/api/upload', methods=['POST'])
@require_auth
def upload_file():
    if 'files' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    uploaded_files = request.files.getlist('files')
    count = 0
    for f in uploaded_files:
        if f.filename:
            clean_name = secure_filename(f.filename)
            if not clean_name:
                clean_name = f"file_{int(time.time())}"
            f.save(STORAGE_DIR / clean_name)
            count += 1
    return jsonify({"success": True, "count": count})

@flask_app.route('/api/download/<filename>')
@require_auth
def download_file(filename):
    clean_name = secure_filename(filename)
    return send_from_directory(STORAGE_DIR, clean_name, as_attachment=True)

@flask_app.route('/api/download-all')
@require_auth
def download_all_zip():
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in STORAGE_DIR.iterdir():
            if f.is_file():
                zf.write(f, arcname=f.name)
    mem.seek(0)
    return send_file(mem, mimetype="application/zip", as_attachment=True, download_name="PrivateDrive_All.zip")

@flask_app.route('/api/files/<filename>', methods=['DELETE'])
@require_auth
def delete_file(filename):
    clean_name = secure_filename(filename)
    target = STORAGE_DIR / clean_name
    if target.exists() and target.is_file():
        target.unlink()
        return jsonify({"success": True})
    return jsonify({"error": "File not found"}), 404

@flask_app.route('/api/notes', methods=['GET', 'POST', 'DELETE'])
@require_auth
def handle_notes():
    if request.method == 'GET':
        return jsonify({"notes": load_notes()})
    elif request.method == 'POST':
        data = request.get_json(silent=True) or {}
        text = data.get('content', '').strip()
        if not text:
            return jsonify({"error": "Empty note"}), 400
        notes = load_notes()
        note = {
            "id": secrets.token_hex(4),
            "content": text,
            "created_at": datetime.now().strftime("%b %d, %I:%M %p")
        }
        notes.insert(0, note)
        save_notes(notes[:50])
        return jsonify({"success": True, "note": note})
    elif request.method == 'DELETE':
        note_id = request.args.get('id')
        notes = [n for n in load_notes() if n.get('id') != note_id]
        save_notes(notes)
        return jsonify({"success": True})

@flask_app.route('/api/storage-presets', methods=['GET'])
@require_auth
def get_storage_presets():
    home = Path.home()
    default_presets = [
        {"name": "PrivateDrive Default", "path": str(DEFAULT_STORAGE)},
        {"name": "Downloads", "path": str(home / "Downloads")},
        {"name": "Documents", "path": str(home / "Documents")},
        {"name": "Pictures", "path": str(home / "Pictures")},
        {"name": "Desktop", "path": str(home / "Desktop")}
    ]
    available = []
    for p in default_presets:
        path_obj = Path(p["path"])
        if path_obj.exists() or p["path"] == str(DEFAULT_STORAGE):
            available.append(p)
    return jsonify({
        "current": str(STORAGE_DIR),
        "presets": available
    })

@flask_app.route('/api/set-storage-dir', methods=['POST'])
@require_auth
def set_storage_dir():
    data = request.get_json(silent=True) or {}
    new_path = data.get("path", "").strip()
    if not new_path:
        return jsonify({"error": "Path cannot be empty"}), 400
    try:
        updated_path = update_shared_folder(new_path)
        return jsonify({
            "status": "ok",
            "storage_dir": updated_path,
            "message": f"Shared folder updated to: {updated_path}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@flask_app.after_request
def add_dav_headers(response):
    if request.method == 'OPTIONS':
        response.headers['DAV'] = '1, 2'
        response.headers['MS-Author-Via'] = 'DAV'
    return response

# ----------------- WebDAV Configuration -----------------

def create_dav_app():
    dav_config = {
        "mount_path": "/drive",
        "provider_mapping": {
            "/": dav_provider
        },
        "simple_dc": {
            "user_mapping": {
                "*": {
                    config["username"]: {
                        "password": config["password"]
                    }
                }
            }
        },
        "http_authenticator": {
            "accept_basic": True,
            "accept_digest": False,
            "default_to_digest": False
        },
        "hotfixes": {
            "win_accept_anonymous_options": True,
            "re_encode_path_info": True
        },
        "verbose": 0,
        "logging": {"enable": False}
    }
    return WsgiDAVApp(dav_config)

class SmartWebDAVDispatcher:
    """
    Unified WSGI dispatcher that:
    1. Routes /drive to WsgiDAV with proper mount_path namespace.
    2. Intercepts macOS AppleDouble dotfiles (._*, .DS_Store, .Trashes, .fseventsd)
       to return immediate 404s, eliminating the 5-6 min Cheroot thread pool freeze.
    3. Handles WebDAV methods on root '/' by redirecting to '/drive/', preventing 405 Method Not Allowed on Finder.
    4. Handles root OPTIONS pings with proper DAV 1,2 compliance headers.
    5. Routes everything else to Flask dashboard.
    """
    def __init__(self, flask_app, dav_app):
        self.flask_app = flask_app
        self.dav_app = dav_app
        self.dispatcher = DispatcherMiddleware(flask_app, {
            '/drive': dav_app
        })

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        method = environ.get('REQUEST_METHOD', 'GET')
        user_agent = environ.get('HTTP_USER_AGENT', '')

        # Fast-path for macOS AppleDouble / Junk dotfiles that do not exist
        # Eliminates Cheroot thread starvation on macOS Finder connections
        segments = [s for s in path.split('/') if s]
        if any(seg.startswith('._') or seg in ('.DS_Store', '.Trashes', '.fseventsd', '.Spotlight-V100') for seg in segments):
            rel_path = path.removeprefix('/drive').lstrip('/')
            full_path = STORAGE_DIR / rel_path
            if not full_path.exists():
                start_response('404 Not Found', [
                    ('Content-Type', 'text/plain'),
                    ('Content-Length', '0')
                ])
                return [b'']

        # If a WebDAV client queries root '/' without '/drive/'
        if path in ('', '/'):
            if method in ('PROPFIND', 'PROPPATCH', 'MKCOL', 'COPY', 'MOVE', 'LOCK', 'UNLOCK') or \
               'WebDAVFS' in user_agent or 'Microsoft-WebDAV' in user_agent:
                start_response('301 Moved Permanently', [
                    ('Location', '/drive/'),
                    ('Content-Type', 'text/html'),
                    ('Content-Length', '0')
                ])
                return [b'']

            if method == 'OPTIONS':
                start_response('200 OK', [
                    ('DAV', '1, 2'),
                    ('MS-Author-Via', 'DAV'),
                    ('Allow', 'OPTIONS, GET, HEAD, PROPFIND'),
                    ('Content-Type', 'text/html; charset=utf-8'),
                    ('Content-Length', '0')
                ])
                return [b'']

        return self.dispatcher(environ, start_response)

# Combine Flask + WebDAV into smart dispatcher
dav_sub_app = create_dav_app()
unified_wsgi_app = SmartWebDAVDispatcher(flask_app, dav_sub_app)

# ----------------- Tunnel & Runner -----------------

def on_tunnel_ready(url):
    drive_url = f"{url}/drive"
    mac_url = f"{url}/drive/"
    print("\n" + "="*62)
    print(" 🚀 PRIVATEDRIVE GLOBAL ACCESS READY (Any Device, Anywhere)")
    print("="*62)
    print(f" • Web Dashboard  : {url}")
    print(f" • Virtual Drive  : {drive_url}")
    print(f" • Username       : {config['username']}")
    print(f" • Password       : {config['password']}")
    print("="*62)
    print("\n[Windows 'Map Network Drive' Command (Paste in second laptop cmd)]:")
    print(f'net use Z: "{drive_url}" /user:{config["username"]} {config["password"]} /persistent:yes')
    print("\n[macOS 1-Click Terminal Command (Paste in Mac Terminal)]:")
    print(f'open "{mac_url}"')
    print("="*62)
    print_qr_terminal(url, title="Scan with Phone Camera to Open Dashboard")

def main():
    global ssh_tunnel
    parser = argparse.ArgumentParser(description="PrivateDrive - Self-hosted Virtual Network Drive")
    parser.add_argument("-d", "--dir", dest="storage_dir", help="Directory path to share as virtual drive")
    parser.add_argument("-p", "--port", type=int, help="Port to listen on")
    parser.add_argument("--no-tunnel", action="store_true", help="Disable reverse SSH tunnel")
    args, unknown = parser.parse_known_args()

    if args.storage_dir:
        update_shared_folder(args.storage_dir)
    elif unknown and not unknown[0].startswith("-"):
        update_shared_folder(unknown[0])

    if args.port:
        config["port"] = args.port
    if args.no_tunnel:
        config["tunnel_enabled"] = False

    port = int(os.environ.get("PORT", config["port"]))
    is_render = os.environ.get("RENDER") is not None
    render_external_url = os.environ.get("RENDER_EXTERNAL_URL")

    local_ip = get_local_ip()
    local_base = render_external_url if is_render else f"http://{local_ip}:{port}"
    local_drive = f"{local_base}/drive"

    print("\n" + "="*62)
    print(" 📂 PRIVATEDRIVE SERVER STARTING")
    print("="*62)
    print(f" • Server Link   : {local_base}")
    print(f" • Virtual Drive : {local_drive}")
    print(f" • Username      : {config['username']}")
    print(f" • Password      : {config['password']}")
    print(f" • Shared Folder : {STORAGE_DIR}")
    print("="*62)

    if not is_render and config.get("tunnel_enabled", True):
        print(" [*] Connecting secure HTTPS tunnel for remote access...")
        ssh_tunnel = SSHTunnel(local_port=port, on_ready=on_tunnel_ready)
        ssh_tunnel.start()
    elif is_render:
        print(f" [*] Running on Render Cloud at: {local_base}")
        print(f" [Windows Command]: net use Z: \"{local_drive}\" /user:{config['username']} {config['password']} /persistent:yes")

    server = wsgi.Server(
        ('0.0.0.0', port),
        unified_wsgi_app,
        numthreads=50,
        request_queue_size=30,
        timeout=15
    )
    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        server.stop()
        if ssh_tunnel:
            ssh_tunnel.stop()

if __name__ == '__main__':
    main()
