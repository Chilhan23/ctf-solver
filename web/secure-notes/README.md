# Secure Notes - Vulnerability Analysis

## Overview
This challenge exploits a Node.js application utilizing MongoDB and Mongoose. The objective is to bypass the localhost IP check on the `/flag` endpoint by chaining a NoSQL Injection with a Prototype Pollution vulnerability.

## The Vulnerabilities

### 1. NoSQL Injection (Mass Assignment)
In the `/update` endpoint, the application passes user-controlled input directly into the database query:
    await Note.findByIdAndUpdate(noteId, req.body);
Because there is no input sanitization, an attacker can supply MongoDB operators (like `$rename`) inside the JSON body.

### 2. Prototype Pollution (CVE-2023-3696)
The application uses a vulnerable version of Mongoose (<= 7.2.4). When the `$rename` operator is used with the `__proto__` key, Mongoose allows the attacker to modify the base `Object.prototype`.

## The Gadget: Why `_peername.address`?
The `/flag` endpoint relies on `req.connection.remoteAddress`. Under the hood in Node.js (net.js), this property is a getter that ultimately resolves to `this._peername.address`. 
By polluting `Object.prototype._peername.address` with "127.0.0.1", every subsequent socket inherits this value. When the application checks the remote address, it is tricked into believing the request originates from localhost.

## Exploit Chain

1. **Plant:** Create a note where the `title` is set to `127.0.0.1` and `content` is set to `IPv4`. The application returns a `noteId`.
2. **Pollute:** Send a POST request to `/update` using the `$rename` operator to move the values from the `title` and `content` fields into the `__proto__._peername` object.
   Payload:
       {
         "noteId": "<noteId>",
         "$rename": {
           "title": "__proto__._peername.address",
           "content": "__proto__._peername.family"
         }
       }
3. **Exfiltrate:** Send a GET request to `/flag`. The IP check passes, and the flag is returned.

## Remediation
1. Strip or explicitly allowlist properties in `req.body` before passing them to Mongoose (do not allow keys starting with `$`).
2. Update Mongoose to a secure version (>= 8.0.0) that prevents Prototype Pollution via update helpers.
