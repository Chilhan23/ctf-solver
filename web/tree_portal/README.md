# Trea Portal - Solver

Fastify + JWT + XPath challenge. Bypass the username check on `/api/user`
using duplicate query params, then inject XPath to read the admin profile (flag).

## Vulnerability

1. Type confusion on the guard in `routes/user.ts`:
       if (typeof username === 'string' && username !== tokenPayload.username)
   `req.query.username` becomes an **array** when the key appears twice
   (`?username=a&username=b`), so `typeof` is not `'string'` and the guard is skipped.
2. The blacklist in `services/userService.ts` uses `input.includes(pattern)`.
   For an array, `Array.prototype.includes` does an exact element match, not a
   substring match, so the payload inside an array element slips through.
3. The query is built with a template literal:
       xpath.select1(`//user[username='${username}']`, doc)
   `${array}` becomes `"admin,' or '1'='1"`, so the final XPath becomes:
       //user[username='admin,' or '1'='1']
   `'1'='1'` is always true, `select1` returns the first user (admin), and the
   response includes the `flag` field.

## Exploit Chain

1. Register a normal user -> get JWT.
2. GET /api/user with duplicate `username` params:
       ?username=admin&username=%27%20or%20%271%27%3D%271
3. Response contains admin's profile including `flag`.

## Usage

    pip install requests
    python solver.py http://target:port

## Remediation

1. Cast input explicitly: `const username = String(req.query.username)`.
2. Reject arrays: `if (Array.isArray(req.query.username)) return 400`.
3. Validate query params with a Fastify JSON schema (`type: 'string'`).
4. Use XPath variable binding instead of string interpolation.
5. Do not return sensitive fields (`flag`) from a public profile endpoint.

## Disclaimer

For CTF / your own lab only. Do not use against systems you don't own.
