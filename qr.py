import urllib.request
import urllib.parse

def print_qr_terminal(url, title="Scan with Phone to Connect"):
    print("\n" + "="*58)
    print(f"  {title}")
    print("="*58)
    try:
        req_url = f"https://qrenco.de/{urllib.parse.quote(url, safe='')}"
        req = urllib.request.Request(req_url, headers={'User-Agent': 'curl/8.0'})
        with urllib.request.urlopen(req, timeout=2.5) as response:
            content = response.read().decode('utf-8', errors='replace')
            for line in content.splitlines():
                print("  " + line)
    except Exception:
        print("\n  [Open this link on any device]:")
        print(f"  --> {url}\n")
    print("="*58 + "\n")
