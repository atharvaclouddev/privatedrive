# PrivateDrive 🚀

> **Turn any computer into a self-hosted, secure Virtual Network Drive (`Z:\`) accessible from anywhere across the globe — with zero third-party cloud storage, zero port-forwarding, and 100% free.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![WebDAV](https://img.shields.io/badge/Protocol-WebDAV%20%7C%20HTTPS-green)](#)
[![Platforms](https://img.shields.io/badge/Clients-Windows%20%7C%20macOS%20%7C%20Linux%20%7C%20iOS%20%7C%20Android-lightgrey)](#)

---

## 💡 The Problem It Solves

Small businesses, accountants, and engineers frequently run software that requires a **single source of truth** (e.g. **TallyPrime**, **Marg**, **Busy ERP**, **AutoCAD**, multi-user **Excel** sheets, or local databases).

* **Cloud Sync (Google Drive / Dropbox) Fails Here:** Syncing database files creates conflicting copies, duplicate voucher numbers, and index corruption.
* **Traditional VPNs / Static IPs:** Expensive, require public static IPs, and involve complex router port-forwarding.

**PrivateDrive solves this:** It runs a lightweight server on your main machine, exposes an encrypted HTTPS WebDAV tunnel, and allows secondary laptops to mount it as a **native Drive (`Z:\`)**. Every keystroke and file save writes **live to the host hard drive**.

---

## 🏗️ Architecture

```text
[ Main Host Computer ]
(Stores live database / data folder)
       │
       ├── WebDAV Engine (WsgiDAV + Cheroot Multi-threaded WSGI)
       ├── Web Dashboard & REST API (Flask)
       └── Reverse HTTPS Tunnel (OpenSSH / Zero-Config)
                  │
             [ Encrypted TLS Tunnel ]
                  │
       ┌──────────┴──────────────────────────────────────┐
       │                                                 │
[ Windows Laptop ]                                [ Mobile / Mac ]
Mounts natively as:                              Finder / iOS Files App
"Drive Z:\" in File Explorer                     Native WebDAV Client
(Tally / Excel reads & saves live)               (Browse, view, upload)
```

---

## 🌟 Key Features

* **⚡ Native Drive Mapping:** Mounts as an actual drive letter (`Z:\`) in Windows File Explorer or a network share in macOS Finder.
* **🔒 Single Source of Truth:** No file downloads or transfers. Applications read and write records directly to the host machine.
* **🌐 Zero-Config Global Tunnel:** Automatic reverse SSH tunnel provides an instant, valid HTTPS link (`https://*.app.lhr.life`). No static IP, dynamic DNS, or port forwarding required.
* **🛡️ Built-in Security:** Protected by HTTP Basic Authentication, path sanitization, and end-to-end TLS encryption.
* **🖥️ Cross-Platform Web Dashboard:** Includes a sleek dark-themed browser interface with drag-and-drop file upload, ZIP downloader, and shared clipboard.
* **📱 1-Scan Mobile Pairing:** Automatically prints an ASCII QR code in the terminal for instant phone connection.

---

## 🚀 Quick Start (In 30 Seconds)

### 1. Clone & Install
```bash
git clone https://github.com/your-username/privatedrive.git
cd privatedrive
pip install -r requirements.txt
```

### 2. Start the Server
* **On Windows:** Double-click `run.bat` (or run `python app.py`)
* **On Linux / macOS:** Run `./run.sh` (or `python3 app.py`)

The terminal will print:
```text
==============================================================
 🚀 PRIVATEDRIVE GLOBAL ACCESS READY (Any Device, Anywhere)
==============================================================
 • Web Dashboard  : https://xyz.app.lhr.life
 • Virtual Drive  : https://xyz.app.lhr.life/drive
 • Username       : admin
 • Password       : PassXXXX
==============================================================

[Windows 'Map Network Drive' Command (Paste in second laptop cmd)]:
net use Z: "https://xyz.app.lhr.life/drive" /user:admin PassXXXX /persistent:yes
```

---

## 💻 How to Connect from Any Device

### 🪟 Windows (Map Drive Z:)
Open **Command Prompt** (not administrator) on your second laptop and run:
```cmd
net use Z: "https://xyz.app.lhr.life/drive" /user:admin YourPassword /persistent:yes
```
*Open File Explorer → **Drive `Z:\`** is now accessible under "This PC"!*

### 🍎 macOS
1. Open **Finder** → press <kbd>Cmd</kbd> + <kbd>K</kbd>.
2. Paste: `https://xyz.app.lhr.life/drive`
3. Enter your username and password.

### 📱 iPhone / iPad
1. Open the built-in **Files** app.
2. Tap the **•••** icon → **Connect to Server**.
3. Enter `https://xyz.app.lhr.life/drive` and log in.

### 🤖 Android
1. Install **Cx File Explorer** (or Solid Explorer).
2. Go to **Network** → **+ (New Location)** → **Remote** → **WebDAV**.
3. Enter your Drive URL and credentials.

---

## ⚙️ Configuration

Configuration is stored in `config.json` (auto-generated on first launch if absent):
```json
{
    "username": "admin",
    "password": "YourCustomPassword",
    "port": 8080,
    "storage_dir": "data_storage",
    "tunnel_enabled": true
}
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to check the [issues page](https://github.com/your-username/privatedrive/issues).

## 📄 License

This project is licensed under the [MIT License](LICENSE).
