# Asset Acquisition — Proton Drive

`make acquire` is a fully-automated pipeline that downloads and decrypts
source assets (audio + artwork, or anything else you configure) from
Proton Drive public shares. Once the pipeline has been run successfully
on a given share, subsequent runs are no-ops because each file is
re-verified against its manifest SHA-256.

```
┌──────────────────────────────────────────────────────────────────┐
│  make acquire                                                    │
│      │                                                           │
│      ▼                                                           │
│  scripts/acquire.sh                                              │
│   ├── bootstrap .venv (if missing)                               │
│   ├── pip install -r requirements-acquire.txt (if stale)         │
│   ├── locate config/acquire.json                                 │
│   └── scripts/acquire_proton.py (for every share)                │
│         ├── GET  /drive/urls/{token}/info                        │
│         ├── SRP-6a auth (bcrypt-2y, custom-b64 salt)             │
│         ├── POST /drive/urls/{token}/auth   → AccessToken        │
│         ├── GET  /drive/urls/{token}/children                    │
│         ├── GET  /drive/urls/{token}/nodes/{id}                  │
│         ├── unwrap session key from NodeKey (OpenPGP / pgpy)     │
│         ├── download + decrypt each block (resumable)            │
│         └── verify SHA-256 against manifest                      │
└──────────────────────────────────────────────────────────────────┘
```

## 1. One-time setup

1. Create a Proton Drive public share for each asset you want to
   download. The share's URL has the form
   `https://drive.proton.me/urls/<TOKEN>#<FRAGMENT_SECRET>`. The
   fragment secret never leaves your browser; the server only stores
   its bcrypt hash.
2. Copy the template:
   ```bash
   cp config/acquire.example.json config/acquire.json
   ```
3. Fill in the `token` and `secret` for each share. **Do not commit
   `config/acquire.json` to version control.** It is in the workspace
   `.gitignore` via `config/.gitignore`.
4. (Optional) pre-install the heavy acquire-time dependencies:
   ```bash
   make acquire-deps
   ```
   The wrapper installs them on first run anyway, so this is purely
   about decoupling the slow pip step from the actual download.

## 2. Daily use

```bash
make acquire                # full run — bootstraps deps if needed
ACQUIRE_OFFLINE=1 make acquire   # verify cached files only (no network)
ACQUIRE_VERBOSE=2 make acquire  # debug-level logging
ACQUIRE_RETRIES=10 make acquire # more aggressive retry budget
```

`make acquire` exits:

* `0` — every share acquired (or already cached & verified)
* `1` — one or more shares failed; see the summary printed at the end
* `2` — configuration error (missing config, missing Python deps, …)

## 3. Config schema

```jsonc
{
  // Where files land, relative to the workspace root. Default: assets/source.
  "output_root": "assets/source",

  "shares": [
    {
      "name":     "audio",        // human-readable label, used in logs
      "token":    "X...",         // share token (URL path component)
      "secret":   "...",          // share fragment secret (URL # fragment)
      "subdir":   "audio",        // subdirectory under output_root
      "filename": "master.wav"   // exact filename to write
    },
    {
      "name":     "visual",
      "token":    "Y...",
      "secret":   "...",
      "subdir":   "visual",
      "filename": "artwork.png"
    }
  ]
}
```

If `filename` is omitted the script writes each node from the share
under the `subdir` directory using its remote filename.

## 4. How the protocol works

Proton Drive's public-share protocol is documented (in its essentials)
in this script. Briefly:

1. **`GET /info`** — returns the SRP modulus (PGP-signed), the server
   ephemeral `B`, the per-share `UrlPasswordSalt`, and an `SRPSession`
   id.
2. **SRP-6a** — the client generates a random `a`, computes
   `A = g^a mod N`, then derives the shared secret
   `S = (B - k*g^x)^(a + u*x) mod N` where `x` is built from
   `bcrypt-2y(fragment_secret, UrlPasswordSalt)`. The client sends
   `{A, M1 = H(A|B|S)}` to `/auth`.
3. **`POST /auth`** — server returns an `AccessToken` and
   `ServerProof = H(A|M1|S)`. The client MUST verify the server proof
   to detect wrong secrets or MITM tampering.
4. **`GET /children`** with `Authorization: Bearer <AccessToken>` lists
   the share's nodes.
5. **`GET /nodes/{id}`** returns the per-file `NodeKey` (an OpenPGP
   secret-key packet encrypted with the share secret), the expected
   `SHA-256`, and the list of `Blocks` (each `{URL, Size, …}`).
6. **Unwrap** — `NodeKey` is decrypted with the share secret via
   `pgpy.PGPKey.unlock(...)` to expose the per-file session key.
7. **Decrypt blocks** — each block is downloaded (resumable, retried
   on transient failures) and decrypted as a PGP literal-data message
   with the session key.
8. **Verify** — the assembled file is hashed and compared against
   `SHA-256` from the manifest. A mismatch aborts the file (and the
   share, for that run).

All network operations use exponential backoff. HTTP 429 / 5xx are
treated as transient. Access tokens live only in process memory.

## 5. Resumability, idempotency, and offline mode

* **Resumable**: encrypted blocks are cached under
  `<output>.parts/block-NNNN.pgp`. Killing `make acquire` mid-run and
  re-invoking it skips already-downloaded blocks.
* **Idempotent**: when the final plaintext file exists and its
  `SHA-256` matches the manifest, the share is treated as already
  acquired and no network calls are made.
* **Offline**: `ACQUIRE_OFFLINE=1 make acquire` (or the
  `acquire-offline` Make target) only re-verifies cached files. This
  is the recommended entry point for CI.

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Server proof mismatch — wrong share secret?` | Wrong `secret` in `config/acquire.json` | Re-copy the `#fragment` from the share URL |
| `HTTP 401` from `/children` or `/nodes/...` | Proton API changed path or required header | Re-run with `ACQUIRE_VERBOSE=2`; check for a new `x-pm-apiversion` |
| `Block N decrypt failed` | Block downloaded with HTTP 200 but bytes are a 4xx error page | Re-run (the bad block is deleted and refetched) |
| `sha256 mismatch` | A block was tampered with or the manifest is stale | Delete the partial file (`rm assets/source/...`) and re-run |
| `No acquire config found` | `config/acquire.json` missing | Copy from `config/acquire.example.json` |

## 7. Security notes

* `config/acquire.json` contains share secrets and is in
  `.gitignore`. The CI in `.github/workflows/ai-agent.yml` greps for
  hard-coded credentials and will fail the build if any are committed.
* The fragment secret is sent to Proton's API only as the
  bcrypt-2y-hashed SRP password; it is never sent in cleartext.
* Access tokens are kept in memory and never written to disk.
* For local development, the script prefers the workspace `.venv/`
  (created in the workspace root) to avoid touching system Python.
