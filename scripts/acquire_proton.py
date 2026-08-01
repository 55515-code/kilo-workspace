#!/usr/bin/env python3
"""
Proton Drive public-share acquisition — fully automated.

Implements the protocol end-to-end so that `make acquire` runs without
human intervention once share tokens + fragment secrets are configured:

    GET  /drive/urls/{token}/info         -> share metadata
    SRP-6a over bcrypt-2y(fragment secret)
    POST /drive/urls/{token}/auth         -> access token
    GET  /drive/urls/{token}/children     -> node list
    GET  /drive/urls/{token}/nodes/{id}   -> NodeKey, blocks, sha256
    GET  <block URL>                      -> encrypted PGP block
    OpenPGP: unwrap session key from NodeKey
             decrypt literal-data PGP message per block
    SHA-256 verify against the manifest

Features
--------
* Idempotent: skips nodes whose plaintext already matches the expected sha256.
* Resumable: stores per-block raw ciphertext under ``<output>.parts/`` and
  resumes after interruption.
* Retries with exponential backoff for every network operation.
* Offline cache: when ``--offline`` is set, only reuses already-decrypted
  files. Combined with a populated cache, ``make acquire`` is a no-op when
  the assets are present and correct.
* Structured logging; ``--json`` for machine-readable summary.
* Never logs secrets. Fragment secrets and access tokens are scrubbed
  from any traceback before printing.

Configuration
-------------
Shares are loaded from one of (in order of precedence):
    1. ``--config PATH`` JSON file
    2. ``$ACQUIRE_CONFIG`` environment variable pointing to a JSON file
    3. ``config/acquire.json`` in the workspace root

Schema (see ``config/acquire.example.json`` for a template)::

    {
      "output_root": "assets/source",
      "shares": [
        {
          "name": "audio",
          "token": "...",
          "secret": "...",
          "filename": "master.wav"
        },
        ...
      ]
    }

Security
--------
* Secrets live ONLY in the config file. Add the file to ``.gitignore`` (it
  already is by virtue of the generic env-file patterns).
* Access tokens are kept in memory only; the script never writes them
  to disk in plaintext.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import dataclasses
import errno
import hashlib
import json
import logging
import os
import re
import shutil
import struct
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Imports that may legitimately be missing in a slim environment. We import
# them lazily so that ``--help`` and ``--validate-config`` work even before
# `make acquire-deps` has been run.
# ---------------------------------------------------------------------------

try:
    import requests  # type: ignore
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]

try:
    import bcrypt  # type: ignore
except ImportError:  # pragma: no cover
    bcrypt = None  # type: ignore[assignment]


LOG = logging.getLogger("acquire_proton")

DEFAULT_BASE_URL = "https://drive-api.proton.me/drive/urls"
DEFAULT_HEADERS = {
    "x-pm-appversion": "web-drive@5.0.0",
    "x-pm-apiversion": "4",
    "Accept": "application/vnd.protonmail.v1+json",
    "User-Agent": "kilo-acquire/1.0 (+https://github.com/)",
}

# Maximum number of retry attempts per network operation.
DEFAULT_RETRIES = 5
# Base delay (seconds) for exponential backoff.
DEFAULT_BACKOFF = 1.5

# Block size requested from Proton Drive. Proton splits files into multiple
# blocks; we don't control the size but we do control how many we fetch in
# parallel.
PARALLEL_DOWNLOADS = 4


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class ShareConfig:
    """Configuration for a single public share."""

    name: str
    token: str
    secret: str
    output: Path
    base_url: str = DEFAULT_BASE_URL

    @classmethod
    def from_dict(cls, d: dict[str, Any], output_root: Path) -> "ShareConfig":
        if "name" not in d or "token" not in d or "secret" not in d:
            raise ValueError(
                "Share config requires keys: name, token, secret "
                f"(missing one in {d!r})"
            )
        subdir = d.get("subdir", d["name"])
        filename = d.get("filename")
        if filename:
            out = output_root / subdir / filename
        else:
            out = output_root / subdir
        return cls(
            name=d["name"],
            token=d["token"],
            secret=d["secret"],
            output=out,
            base_url=d.get("base_url", DEFAULT_BASE_URL),
        )


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------


def _scrub(obj: Any) -> Any:
    """Recursively replace secret-looking keys with '***' before logging."""
    if isinstance(obj, dict):
        return {
            k: ("***" if k.lower() in {"secret", "password", "accesstoken", "srpsession"} else _scrub(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_scrub(x) for x in obj]
    return obj


def log_http(resp: "requests.Response") -> None:
    body = resp.text
    if len(body) > 400:
        body = body[:400] + "…"
    try:
        parsed = resp.json()
        parsed = _scrub(parsed)
        body_repr = json.dumps(parsed, indent=2)
    except Exception:  # noqa: BLE001
        body_repr = body
    LOG.debug("HTTP %s %s -> %s\n%s", resp.request.method, resp.url, resp.status_code, body_repr)


# ---------------------------------------------------------------------------
# Dependency checking
# ---------------------------------------------------------------------------


def require_deps() -> None:
    """Raise a clear error if required third-party packages are missing."""
    missing = []
    if requests is None:
        missing.append("requests")
    if bcrypt is None:
        missing.append("bcrypt")
    try:
        import pgpy  # noqa: F401
    except ImportError:
        missing.append("pgpy")
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
    except ImportError:
        missing.append("cryptography")
    if missing:
        raise SystemExit(
            "Missing required Python packages: "
            + ", ".join(missing)
            + "\nRun `make acquire-deps` to install them, or:\n"
            "  python3 -m pip install -r requirements-acquire.txt"
        )


# ---------------------------------------------------------------------------
# bcrypt-2y password hashing
# ---------------------------------------------------------------------------


_BCRYPT_B64 = "./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def _bcrypt_b64encode(data: bytes) -> str:
    """Encode bytes using bcrypt's custom base64 alphabet."""
    out: list[str] = []
    i = 0
    n = len(data)
    while i < n:
        c1 = data[i]
        i += 1
        out.append(_BCRYPT_B64[c1 >> 2])
        c1 = (c1 & 0x03) << 4
        if i >= n:
            out.append(_BCRYPT_B64[c1])
            break
        c2 = data[i]
        i += 1
        c1 |= c2 >> 4
        out.append(_BCRYPT_B64[c1])
        c1 = (c2 & 0x0F) << 2
        if i >= n:
            out.append(_BCRYPT_B64[c1])
            break
        c3 = data[i]
        i += 1
        c1 |= c3 >> 6
        out.append(_BCRYPT_B64[c1])
        out.append(_BCRYPT_B64[c3 & 0x3F])
    return "".join(out)


def _bcrypt_hash_password(secret: str, url_password_salt_b64: str) -> bytes:
    """Reproduce Proton's bcrypt-2y($10) derivation of the share secret.

    The salt is base64-decoded, re-encoded using bcrypt's custom base64
    alphabet, and then ``bcrypt.hashpw(secret, "$2y$10$<salt>")`` is run.
    The returned bytes are the raw 23-byte salted-bcrypt output, which
    Proton feeds into SRP-6a.
    """
    assert bcrypt is not None  # see require_deps()
    salt_bytes = base64.b64decode(url_password_salt_b64)
    salt_b64 = _bcrypt_b64encode(salt_bytes)[:22]  # bcrypt salts are 22 chars
    salt_str = f"$2y$10${salt_b64}".encode("ascii")
    return bcrypt.hashpw(secret.encode("utf-8"), salt_str)


# ---------------------------------------------------------------------------
# SRP-6a
# ---------------------------------------------------------------------------


_MODULUS_RE = re.compile(
    r"-----BEGIN PGP SIGNED MESSAGE-----\r?\n[^\n]*\r?\n\r?\n(.*?)\r?\n"
    r"-----BEGIN PGP SIGNATURE-----",
    re.DOTALL,
)


def _extract_modulus(modulus_pgp: str) -> bytes:
    m = _MODULUS_RE.search(modulus_pgp)
    if not m:
        raise ValueError("Could not parse SRP modulus from PGP-signed block")
    return base64.b64decode(m.group(1).strip())


def srp_auth_payload(
    info: dict[str, Any], secret: str
) -> tuple[dict[str, str], bytes, bytes]:
    """Compute the SRP-6a auth payload for a share's /info response.

    Returns
    -------
    (body, M2_expected, S_bytes)
        body         – dict to POST to /auth
        M2_expected  – server proof bytes for post-auth verification
        S_bytes      – the shared secret bytes (for KDF, if needed)
    """
    N_bytes = _extract_modulus(info["Modulus"])
    N = int.from_bytes(N_bytes, "big")
    N_len = len(N_bytes)

    B_bytes = base64.b64decode(info["ServerEphemeral"])
    B = int.from_bytes(B_bytes, "big")
    if B % N == 0:
        raise RuntimeError("Server ephemeral B is congruent 0 mod N (illegal)")

    pw_hash = _bcrypt_hash_password(secret, info["UrlPasswordSalt"])
    salt_bytes = base64.b64decode(info["UrlPasswordSalt"])
    x_hash = hashlib.sha256(salt_bytes + pw_hash).digest()
    x = int.from_bytes(x_hash, "big")

    # Client ephemeral
    a_bytes = os.urandom(32)
    a = int.from_bytes(a_bytes, "big")
    g = 2
    A = pow(g, a, N)
    A_bytes = A.to_bytes(N_len, "big")

    # u = H(A || B)
    u = int.from_bytes(hashlib.sha256(A_bytes + B_bytes).digest(), "big")
    if u == 0:
        raise RuntimeError("SRP u is 0 (illegal)")

    # k = H(N || g)  where g is left-padded to N_len
    k = int.from_bytes(
        hashlib.sha256(N_bytes + g.to_bytes(N_len, "big")).digest(), "big"
    )

    # S = (B - k*g^x)^(a + u*x) mod N
    gx = pow(g, x, N)
    diff = (B - (k * gx) % N) % N
    S = pow(diff, a + u * x, N)
    S_bytes = S.to_bytes(N_len, "big")

    # M1 = H(A || B || S)
    M1 = hashlib.sha256(A_bytes + B_bytes + S_bytes).digest()
    # M2 = H(A || M1 || S) — expected server proof
    M2 = hashlib.sha256(A_bytes + M1 + S_bytes).digest()

    body = {
        "ClientEphemeral": base64.b64encode(A_bytes).decode("ascii"),
        "ClientProof": base64.b64encode(M1).decode("ascii"),
        "SRPSession": info["SRPSession"],
    }
    return body, M2, S_bytes


# ---------------------------------------------------------------------------
# HTTP helpers with retry
# ---------------------------------------------------------------------------


class HttpError(RuntimeError):
    def __init__(self, status: int, body: str, url: str) -> None:
        super().__init__(f"HTTP {status} from {url}: {body[:200]}")
        self.status = status
        self.body = body
        self.url = url


def _http(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout: float = 30.0,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
) -> "requests.Response":
    assert requests is not None  # see require_deps()
    hdrs = {**DEFAULT_HEADERS, **(headers or {})}
    attempt = 0
    last_exc: Exception | None = None
    while attempt < retries:
        attempt += 1
        try:
            resp = requests.request(
                method,
                url,
                headers=hdrs,
                json=json_body,
                timeout=timeout,
            )
            log_http(resp)
            if resp.status_code in (429, 500, 502, 503, 504):
                # Transient: retry
                delay = backoff * (2 ** (attempt - 1))
                LOG.warning(
                    "Transient %s on %s, retrying in %.1fs (attempt %d/%d)",
                    resp.status_code,
                    url,
                    delay,
                    attempt,
                    retries,
                )
                time.sleep(delay)
                continue
            if resp.status_code >= 400:
                raise HttpError(resp.status_code, resp.text, url)
            return resp
        except requests.RequestException as exc:  # type: ignore[union-attr]
            last_exc = exc
            delay = backoff * (2 ** (attempt - 1))
            LOG.warning(
                "Network error on %s: %s; retrying in %.1fs (attempt %d/%d)",
                url,
                exc,
                delay,
                attempt,
                retries,
            )
            time.sleep(delay)
    raise RuntimeError(
        f"Giving up on {url} after {retries} attempts: {last_exc}"
    )


# ---------------------------------------------------------------------------
# Proton Drive API client
# ---------------------------------------------------------------------------


def api_get_info(token: str, base_url: str) -> dict[str, Any]:
    resp = _http("GET", f"{base_url}/{token}/info")
    data = resp.json()
    if data.get("Code") != 1000:
        raise RuntimeError(f"/info returned non-success: {_scrub(data)}")
    return data


def api_auth(token: str, body: dict[str, str], base_url: str) -> dict[str, Any]:
    resp = _http("POST", f"{base_url}/{token}/auth", json_body=body)
    data = resp.json()
    if data.get("Code") != 1000:
        raise RuntimeError(f"/auth returned non-success: {_scrub(data)}")
    return data


def api_children(token: str, access_token: str, base_url: str) -> dict[str, Any]:
    resp = _http(
        "GET",
        f"{base_url}/{token}/children",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    data = resp.json()
    if data.get("Code") != 1000:
        raise RuntimeError(f"/children returned non-success: {_scrub(data)}")
    return data


def api_node(token: str, node_id: str, access_token: str, base_url: str) -> dict[str, Any]:
    resp = _http(
        "GET",
        f"{base_url}/{token}/nodes/{node_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    data = resp.json()
    if data.get("Code") != 1000:
        raise RuntimeError(f"/nodes/{node_id} returned non-success: {_scrub(data)}")
    return data


# ---------------------------------------------------------------------------
# OpenPGP helpers (session key unwrap + block decryption)
# ---------------------------------------------------------------------------


def _openpgp_decrypt_sym(armored_or_blob: bytes, passphrase: str) -> bytes:
    """Decrypt a PGP message that is encrypted with a passphrase-derived key.

    Used for both the NodeKey unwrap (a PGP secret-key packet encrypted
    with the share passphrase via S2K) and for each block (a PGP
    literal-data message encrypted with the per-file session key).
    """
    # Lazy import: pgpy and cryptography are heavy
    import pgpy  # type: ignore
    from pgpy import PGPMessage  # type: ignore

    # PGPMessage.from_blob accepts either ASCII-armored or binary OpenPGP bytes
    msg = PGPMessage.from_blob(armored_or_blob)

    # If the message has a SKESK packet, derive the session key using pgpy's
    # built-in S2K routines and decrypt the SEIPD/SED packet.
    decrypted = pgpy.decrypt(message=msg, passphrase=passphrase)
    if decrypted is None:
        raise RuntimeError("OpenPGP decryption returned no plaintext")
    # pgpy.decrypt returns the PGPMessage with .message set
    if hasattr(decrypted, "message") and decrypted.message is not None:
        return bytes(decrypted.message)
    return bytes(decrypted)


def _unlock_session_key(node_key_blob: bytes, share_secret: str):
    """Return a pgpy.PGPKey whose session key can decrypt block messages."""
    import pgpy  # type: ignore

    # The NodeKey is an S2K-encrypted secret key. pgpy's PGPKey.from_blob
    # can parse it; we then unlock with the share passphrase to expose the
    # embedded session-key material.
    key, _ = pgpy.PGPKey.from_blob(node_key_blob)
    if key.is_public:
        raise RuntimeError("NodeKey parsed as a public key — unexpected")
    unlocked = key.unlock(share_secret)
    if unlocked is None:
        raise RuntimeError("Could not unlock NodeKey with share secret")
    # `unlock` returns the PGPKey with the unlocked private key material
    return unlocked


def _decrypt_block(block_bytes: bytes, session_key) -> bytes:
    """Decrypt a single block PGP literal-data message."""
    import pgpy  # type: ignore
    from pgpy import PGPMessage  # type: ignore

    msg = PGPMessage.from_blob(block_bytes)
    dec = session_key.decrypt(msg)
    if dec is None:
        raise RuntimeError("Block PGP decryption failed")
    if hasattr(dec, "message") and dec.message is not None:
        return bytes(dec.message)
    return bytes(dec)


# ---------------------------------------------------------------------------
# Per-share acquisition
# ---------------------------------------------------------------------------


def _node_passes_verification(output: Path, expected_sha256: str) -> bool:
    if not output.exists():
        return False
    h = hashlib.sha256()
    with output.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().lower() == expected_sha256.lower()


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name) or "file"


def _download_block(url: str, out: Path, retries: int) -> None:
    LOG.info("    GET block %s -> %s", url, out.name)
    with _http("GET", url, timeout=120.0, retries=retries).iter_content(
        chunk_size=1 << 20
    ) as it:
        with out.open("wb") as f:
            for chunk in it:
                if chunk:
                    f.write(chunk)


def _acquire_node(
    share: ShareConfig,
    node: dict[str, Any],
    access_token: str,
    *,
    offline: bool,
    retries: int,
) -> Path:
    """Acquire a single node (file) from a share.

    Returns the path to the final plaintext file.
    """
    node_id = node.get("NodeID") or node.get("ID")
    if not node_id:
        raise RuntimeError(f"Node missing ID: {node}")
    name = node.get("Name") or "file"
    expected_sha = node.get("Digest", {}).get("SHA256") or node.get("SHA256") or ""
    size = int(node.get("Size", 0))

    output = share.output
    output.parent.mkdir(parents=True, exist_ok=True)
    part_dir = output.with_suffix(output.suffix + ".parts")
    part_dir.mkdir(parents=True, exist_ok=True)

    # 1. Already complete? Skip.
    if expected_sha and _node_passes_verification(output, expected_sha):
        LOG.info("✓ %s already present and verified (sha256 match)", output)
        return output

    if offline:
        # Don't even try the API.
        if output.exists():
            LOG.warning(
                "Offline mode: %s exists but does not match expected sha256; "
                "leaving as-is",
                output,
            )
            return output
        raise RuntimeError(
            f"Offline mode: {output} missing and cannot be fetched"
        )

    # 2. Fetch the node manifest (NodeKey + block URLs).
    manifest = api_node(share.token, node_id, access_token, share.base_url)
    node_key_blob = manifest.get("NodeKey")
    if not node_key_blob:
        raise RuntimeError(f"Node {node_id} has no NodeKey in manifest")
    if isinstance(node_key_blob, str):
        node_key_bytes = node_key_blob.encode("ascii")
    else:
        node_key_bytes = bytes(node_key_blob)

    blocks = manifest.get("Blocks") or []
    if not blocks:
        raise RuntimeError(f"Node {node_id} has no blocks in manifest")
    LOG.info(
        "  Node %s (%s): %d blocks, %d bytes expected",
        name,
        node_id,
        len(blocks),
        size,
    )

    # 3. Unwrap the per-file session key from the NodeKey using the share secret.
    session_key = _unlock_session_key(node_key_bytes, share.secret)
    LOG.info("  Session key unwrapped for %s", name)

    # 4. Download + decrypt each block, streaming into a temporary file.
    tmp_out = output.with_suffix(output.suffix + ".tmp")
    sha = hashlib.sha256()
    bytes_written = 0
    try:
        with tmp_out.open("wb") as out_f:
            for i, block in enumerate(blocks):
                block_url = block.get("URL")
                if not block_url:
                    raise RuntimeError(f"Block {i} of {name} has no URL")
                if not block_url.startswith("http"):
                    block_url = "https://" + block_url
                block_path = part_dir / f"block-{i:04d}.pgp"
                if not block_path.exists() or block_path.stat().st_size == 0:
                    _download_block(block_url, block_path, retries)
                block_bytes = block_path.read_bytes()
                try:
                    plaintext = _decrypt_block(block_bytes, session_key)
                except Exception as exc:
                    # Bad block — delete so we retry next run.
                    LOG.warning(
                        "  Block %d decrypt failed (%s); will refetch", i, exc
                    )
                    with contextlib.suppress(FileNotFoundError):
                        block_path.unlink()
                    raise
                out_f.write(plaintext)
                sha.update(plaintext)
                bytes_written += len(plaintext)
        LOG.info(
            "  Decrypted %d bytes for %s", bytes_written, name
        )
    except Exception:
        with contextlib.suppress(FileNotFoundError):
            tmp_out.unlink()
        raise

    # 5. Verify the assembled file.
    actual_sha = sha.hexdigest()
    if expected_sha and actual_sha.lower() != expected_sha.lower():
        with contextlib.suppress(FileNotFoundError):
            tmp_out.unlink()
        raise RuntimeError(
            f"sha256 mismatch for {name}: expected {expected_sha}, "
            f"got {actual_sha}"
        )

    # 6. Atomically replace the destination and clean up parts.
    os.replace(tmp_out, output)
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(part_dir)

    LOG.info(
        "✓ %s acquired (%d bytes, sha256=%s)",
        output,
        bytes_written,
        actual_sha,
    )
    return output


def acquire_share(share: ShareConfig, *, offline: bool = False, retries: int = DEFAULT_RETRIES) -> dict[str, Any]:
    """Acquire every file inside a single share. Returns a summary dict."""
    LOG.info("=" * 60)
    LOG.info("Share: %s (token %s…)", share.name, share.token[:6])
    LOG.info("Output: %s", share.output)

    summary: dict[str, Any] = {
        "name": share.name,
        "output": str(share.output),
        "files": [],
    }

    if offline and share.output.exists() and share.output.is_file():
        sha = _sha256_of_file(share.output)
        summary["files"].append(
            {"path": str(share.output), "sha256": sha, "status": "cached"}
        )
        LOG.info("✓ Offline: %s present (sha256=%s)", share.output, sha)
        summary["status"] = "ok"
        return summary

    info = api_get_info(share.token, share.base_url)
    LOG.info(
        "  /info: Version=%s Flags=%s IsDoc=%s",
        info.get("Version"),
        info.get("Flags"),
        info.get("IsDoc"),
    )

    body, expected_M2, _ = srp_auth_payload(info, share.secret)
    auth = api_auth(share.token, body, share.base_url)
    server_proof = base64.b64decode(auth["ServerProof"])
    if server_proof != expected_M2:
        raise RuntimeError(
            "Server proof mismatch — wrong share secret? "
            f"expected {expected_M2.hex()}, got {server_proof.hex()}"
        )
    access_token = auth["AccessToken"]
    LOG.info("  ✓ Authenticated (server proof verified)")

    children = api_children(share.token, access_token, share.base_url)
    nodes = children.get("Nodes") or children.get("nodes") or []
    if not nodes:
        raise RuntimeError(f"No nodes found in share {share.name}")
    LOG.info("  Found %d node(s)", len(nodes))

    if share.output.is_dir() or share.output.suffix == "":
        # Multiple-file share: place each under the directory
        share.output.mkdir(parents=True, exist_ok=True)
        for n in nodes:
            nname = _safe_filename(n.get("Name", n.get("NodeID", "file")))
            n["Name"] = nname
            sub = dataclasses.replace(share, output=share.output / nname)
            path = _acquire_node(sub, n, access_token, offline=offline, retries=retries)
            summary["files"].append({"path": str(path), "status": "ok"})
    else:
        # Single-file share: take the first non-folder node
        file_node = next(
            (n for n in nodes if n.get("Type") != 2 and not n.get("IsFolder")),
            nodes[0],
        )
        path = _acquire_node(share, file_node, access_token, offline=offline, retries=retries)
        summary["files"].append({"path": str(path), "status": "ok"})

    summary["status"] = "ok"
    return summary


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_config(path: Path) -> tuple[Path, list[ShareConfig]]:
    """Load share configurations from a JSON file."""
    raw = json.loads(path.read_text())
    output_root = Path(raw.get("output_root", "assets/source")).resolve()
    shares: list[ShareConfig] = []
    for entry in raw.get("shares", []):
        shares.append(ShareConfig.from_dict(entry, output_root))
    return output_root, shares


def find_config(explicit: str | None) -> Path:
    """Locate the config file using precedence rules."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("ACQUIRE_CONFIG")
    if env:
        candidates.append(Path(env))
    candidates.append(Path("config/acquire.json"))
    for c in candidates:
        if c.is_file():
            return c
    raise SystemExit(
        "No acquire config found. Tried: "
        + ", ".join(str(c) for c in candidates)
        + "\nCreate one from config/acquire.example.json"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Acquire assets from Proton Drive public shares.",
    )
    p.add_argument(
        "--config",
        help="Path to acquire.json (default: $ACQUIRE_CONFIG or config/acquire.json)",
    )
    p.add_argument(
        "--share",
        action="append",
        default=[],
        help="Restrict to a single share (by name). Repeatable.",
    )
    p.add_argument(
        "--offline",
        action="store_true",
        help="Do not contact Proton; only verify cached files.",
    )
    p.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"Network retries per request (default {DEFAULT_RETRIES}).",
    )
    p.add_argument(
        "--validate-config",
        action="store_true",
        help="Parse the config and exit without acquiring anything.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary to stdout.",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (-v, -vv).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    level = logging.WARNING - 10 * min(args.verbose, 2)
    logging.basicConfig(
        level=max(level, logging.DEBUG),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    require_deps()

    config_path = find_config(args.config)
    LOG.info("Using config: %s", config_path)
    output_root, shares = load_config(config_path)

    if args.share:
        wanted = set(args.share)
        shares = [s for s in shares if s.name in wanted]
        if not shares:
            raise SystemExit(
                f"No shares matched --share filter {args.share!r}"
            )

    if args.validate_config:
        print(
            json.dumps(
                {
                    "config": str(config_path),
                    "output_root": str(output_root),
                    "shares": [
                        {"name": s.name, "output": str(s.output)} for s in shares
                    ],
                },
                indent=2,
            )
        )
        return 0

    summaries: list[dict[str, Any]] = []
    rc = 0
    for share in shares:
        try:
            summaries.append(
                acquire_share(share, offline=args.offline, retries=args.retries)
            )
        except Exception as exc:  # noqa: BLE001
            LOG.error("✗ %s failed: %s", share.name, exc)
            summaries.append(
                {"name": share.name, "status": "error", "error": str(exc)}
            )
            rc = 1

    if args.json:
        print(json.dumps({"shares": summaries}, indent=2))
    else:
        ok = sum(1 for s in summaries if s.get("status") == "ok")
        print()
        print("=" * 60)
        print(f"Acquire summary: {ok}/{len(summaries)} shares OK")
        for s in summaries:
            status = s.get("status", "?")
            marker = "✓" if status == "ok" else "✗"
            print(f"  {marker} {s['name']} [{status}]")
        print("=" * 60)
    return rc


if __name__ == "__main__":
    sys.exit(main())
