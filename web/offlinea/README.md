# Offlinea Vulnerability Analysis

## Overview
Offlinea is a web challenge that demonstrates a complex exploit chain. It combines multiple distinct vulnerabilities across a PHP frontend and a Python (Flask) backend to achieve remote code execution (or in this case, data exfiltration). 

The challenge title, "A Bartender, a Headless Browser, and Five Locks", hints at the architecture and the five layers of security that must be bypassed to retrieve the flag.

## Architecture

The application consists of two main components:
1. PHP Frontend (bartender.php): Exposed to the public internet. It receives user input (a URL), validates it, and forwards it to the backend for rendering.
2. Flask Backend (app.py): Bound to 127.0.0.1:5000 (localhost only). It receives the URL from the PHP frontend, uses a headless Chrome browser to render the page to a PDF, and saves the URL to a SQLite database.

The flag is stored in a SQLite database (secrets table) and is only accessible via a protected endpoint (/bartender) on the Flask backend, which requires a valid JWT.

---

## The Five Locks (Vulnerability Analysis)

### 1. HTTP Parameter Pollution (HPP)
Vulnerable Code: bartender.php (Frontend) & app.py (Backend)

There is a parsing discrepancy between how the PHP frontend and the Flask backend handle duplicate URL parameters.

- PHP: $_GET['url'] takes the last occurrence of the url parameter. This value is passed into no_way_trick_me() for validation.
- Flask: request.args.get('url') takes the first occurrence of the url parameter. This value is passed into the headless browser.

Impact: An attacker can send a request with two url parameters. The first can be a malicious internal URL (for Flask to execute), and the second can be a safe public URL (to bypass PHP validation).

### 2. Server-Side Request Forgery (SSRF)
Vulnerable Code: app.py (peek_website and is_request_safe)

The Flask backend attempts to prevent SSRF by validating the IP address, but the logic is flawed.

    def is_request_safe(url, min_ttl=40):
        hostname = urlparse(url).hostname or url
        try:
            ipaddress.ip_address(hostname)
            return True # VULNERABILITY
        except ValueError:
            pass

Impact: If the hostname is a raw IP address (e.g., 127.0.0.1), the function immediately returns True without verifying if the IP is in a private/local range. This allows the attacker to force the backend to make requests to its own internal services.

### 3. Format-String Injection
Vulnerable Code: app.py (logify function)

The application logs visited URLs into a SQLite database and later renders them. The developer used Python's .format() on the user-controlled history data.

    def logify(rec):
        history = [f"ID: {row[0]} | URL: {row[1]} | Timestamp: {row[2]}" for row in rec]
        history_1 = '\n'.join(history)
        log = history_1.format(logify=logify) # VULNERABILITY
        return log

Impact: An attacker can inject format-string payloads (e.g., {logify.__globals__[app].config}) into the URL. When the /logs endpoint is rendered, the payload is executed, exposing sensitive application configuration variables, most notably SECRET_KEY.

### 4. Broken Authentication Logic (JWT)
Vulnerable Code: app.py (token_required decorator)

The JWT validation logic contains a logical flaw using the and operator.

    if not data.get('is_admin') and data.get('username') == 'bartender':
        return jsonify({'message': 'Admin access required!'}), 403

Impact: The condition only triggers a 403 Forbidden if the user is not an admin AND the username is bartender. If an attacker provides a forged JWT with {"is_admin": true}, the first condition (not True) evaluates to False. Due to short-circuit evaluation, the entire if statement is bypassed, granting access.

### 5. SSRF to Protected Endpoint
With the SECRET_KEY leaked (Lock 3) and the authentication logic bypassed (Lock 4), the attacker can forge a valid JWT. Using the SSRF vulnerability (Lock 1 & 2), the attacker can send a request to http://127.0.0.1:5000/bartender?token=FORGED_JWT. The backend will validate the forged token, execute the database query, and return the flag.

---

## The Exploit Chain Summary

1. HPP: Bypass PHP validation by sending ?url=internal&url=public.
2. SSRF: Force the Flask backend to visit http://127.0.0.1:5000/logs.
3. Plant: Use the /logs endpoint to inject a format-string payload {logify.__globals__[app].config}. The backend saves this to the database.
4. Detonate: Trigger the /logs endpoint again via SSRF. The backend executes the payload and renders the SECRET_KEY into a PDF.
5. Forge: Use the leaked SECRET_KEY to forge a JWT with {"is_admin": true}.
6. Exfiltrate: Use SSRF to access /bartender?token=JWT to retrieve the flag from the database.

---

## Remediation

1. HPP: Ensure the frontend and backend parse parameters identically (e.g., strictly enforce taking the first or last parameter, and reject requests with duplicates).
2. SSRF: Properly validate resolved IP addresses against private ranges (RFC 1918) after DNS resolution. Do not trust raw IP inputs.
3. Format-String: Never use .format() or % string formatting on user-controlled input. Use safe concatenation or templating engines with auto-escaping.
4. Auth Logic: Fix the boolean logic to explicitly check if the user is an admin: if not data.get('is_admin'): return 403.
