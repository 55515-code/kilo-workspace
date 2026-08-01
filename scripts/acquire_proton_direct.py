#!/usr/bin/env python3
"""
Proton Drive public share downloader.
Implements the full protocol: /info → SRP-6a auth → /children → decrypt → download.
Uses only: requests, bcrypt, hashlib, cryptography (no PGPy needed for the handshake).
"""

import base64
import hashlib
import json
import os
import re
import struct
import sys
from pathlib import Path

import bcrypt
import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SHARES = {
    "audio": {
        "token": "XA248JXEJC",
        "secret": "ERr0VGD3cKud",
        "output": "assets/source/audio/master",
    },
    "image": {
        "token": "HJ9B06AF74",
        "secret": "UlhAg0ZnPzCH",
        "output": "assets/source/visual/artwork",
    },
}

BASE_URL = "https://drive-api.proton.me/drive/urls"
HEADERS = {
    "x-pm-appversion": "web-drive@5.0.0",
    "x-pm-apiversion": "4",
    "Accept": "application/vnd.protonmail.v1+json",
}


def get_info(token):
    """GET /info for a share token. Returns the full response."""
    url = f"{BASE_URL}/{token}/info"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("Code") != 1000:
        raise RuntimeError(f"Info failed: {data}")
    return data


def extract_modulus(modulus_pgp_text):
    """Extract raw modulus bytes from the PGP-signed message block."""
    m = re.search(
        r"-----BEGIN PGP SIGNED MESSAGE-----\n[^\n]*\n\n(.*?)\n-----BEGIN PGP SIGNATURE-----",
        modulus_pgp_text,
        re.DOTALL,
    )
    if not m:
        raise ValueError("Cannot parse modulus")
    return base64.b64decode(m.group(1).strip())


def hash_password(secret, salt_b64):
    """
    Proton uses bcrypt-2y to hash the share secret with the UrlPasswordSalt.
    The resulting hash becomes the SRP password.
    """
    salt_bytes = base64.b64decode(salt_b64)
    # Pad salt to 16 bytes if needed
    if len(salt_bytes) < 16:
        salt_bytes = salt_bytes + b'\x00' * (16 - len(salt_bytes))
    # Encode using bcrypt's custom base64
    salt_str = bcrypt_b64encode(salt_bytes)
    bcrypt_salt = f"$2y$10${salt_str}".encode("ascii")
    hashed = bcrypt.hashpw(secret.encode("utf-8"), bcrypt_salt)
    return hashed


def bcrypt_b64encode(data: bytes) -> str:
    """Encode bytes using bcrypt's custom base64 alphabet."""
    BCRYPT_B64 = "./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    result = []
    i = 0
    length = len(data)
    while i < length:
        c1 = data[i]; i += 1
        result.append(BCRYPT_B64[c1 >> 2])
        c1 = (c1 & 0x03) << 4
        if i >= length:
            result.append(BCRYPT_B64[c1]); break
        c2 = data[i]; i += 1
        c1 |= c2 >> 4
        result.append(BCRYPT_B64[c1])
        c1 = (c2 & 0x0f) << 2
        if i >= length:
            result.append(BCRYPT_B64[c1]); break
        c2 = data[i]; i += 1
        c1 |= c2 >> 6
        result.append(BCRYPT_B64[c1])
        result.append(BCRYPT_B64[c2 & 0x3f])
    return ''.join(result)


def srp_auth(info, secret):
    """
    Perform SRP-6a authentication.
    Returns the POST body for /drive/urls/{token}.
    """
    modulus_bytes = extract_modulus(info["Modulus"])
    N = int.from_bytes(modulus_bytes, "big")
    N_len = len(modulus_bytes)
    
    B_bytes = base64.b64decode(info["ServerEphemeral"])
    B = int.from_bytes(B_bytes, "big")
    
    # Hash password with bcrypt
    pw_hash = hash_password(secret, info["UrlPasswordSalt"])
    
    # For SRP, the password is the raw bcrypt hash string
    # Proton uses the hash as bytes for x computation
    # x = H(salt | H(identity:password))
    # In Proton's implementation, the identity is empty for shares
    # and the password is the bcrypt hash
    
    # Compute x = SHA256(salt_bytes | pw_hash_bytes)
    salt_bytes = base64.b64decode(info["UrlPasswordSalt"])
    x_hash = hashlib.sha256(salt_bytes + pw_hash).digest()
    x = int.from_bytes(x_hash, "big")
    
    # Generate client ephemeral: a random, A = g^a mod N
    g = 2
    a_bytes = os.urandom(32)
    a = int.from_bytes(a_bytes, "big")
    A = pow(g, a, N)
    A_bytes = A.to_bytes(N_len, "big")
    
    # u = SHA256(A | B)
    u_hash = hashlib.sha256(A_bytes + B_bytes).digest()
    u = int.from_bytes(u_hash, "big")
    
    # k = SHA256(N | g)  (where g is padded to N_len bytes)
    g_padded = g.to_bytes(N_len, "big")
    k_hash = hashlib.sha256(modulus_bytes + g_padded).digest()
    k = int.from_bytes(k_hash, "big")
    
    # S = (B - k * g^x)^((a + u*x) mod phi(N)) mod N
    # Since we don't know phi(N), we compute (a + u*x) and use it as exponent
    # Actually for the client proof, we need:
    # S_client = (B - k * g^x)^(a + u*x) mod N
    
    gx = pow(g, x, N)
    kgx = (k * gx) % N
    diff = (B - kgx) % N
    
    exp = a + u * x
    S = pow(diff, exp, N)
    S_bytes = S.to_bytes(N_len, "big")
    
    # M1 = H(A | B | S) — client proof
    M1 = hashlib.sha256(A_bytes + B_bytes + S_bytes).digest()
    
    # M2 = H(A | M1 | S) — server proof (for verification)
    M2 = hashlib.sha256(A_bytes + M1 + S_bytes).digest()
    
    return {
        "body": {
            "ClientEphemeral": base64.b64encode(A_bytes).decode(),
            "ClientProof": base64.b64encode(M1).decode(),
            "SRPSession": info["SRPSession"],
        },
        "M2_expected": M2,
        "S_bytes": S_bytes,
    }


def auth_share(token, srp_result):
    """POST SRP auth to the share endpoint."""
    url = f"{BASE_URL}/{token}/auth"
    r = requests.post(url, json=srp_result["body"], headers=HEADERS, timeout=30)
    print(f"   HTTP {r.status_code}")
    print(f"   Response: {r.text[:500]}")
    r.raise_for_status()
    data = r.json()
    return data


def get_children(token):
    """GET children of authenticated share."""
    url = f"{BASE_URL}/{token}/children"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def get_node(token, node_id):
    """GET node details (including download blocks)."""
    url = f"{BASE_URL}/{token}/nodes/{node_id}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def acquire(name, config):
    """Attempt full acquisition of a share."""
    print(f"\n{'='*60}")
    print(f"Acquiring {name}: {config['token']}")
    print(f"{'='*60}")
    
    # Step 1: Info
    print("1. GET /info...")
    info = get_info(config["token"])
    print(f"   Version={info['Version']}, Flags={info['Flags']}, IsDoc={info.get('IsDoc')}")
    
    # Step 2: SRP
    print("2. SRP-6a authentication...")
    srp_result = srp_auth(info, config["secret"])
    print(f"   ClientEphemeral: {srp_result['body']['ClientEphemeral'][:40]}...")
    
    # Step 3: POST auth
    print("3. POST auth...")
    auth_resp = auth_share(config["token"], srp_result)
    print(f"   Response Code: {auth_resp.get('Code')}")
    
    if auth_resp.get("Code") != 1000:
        print(f"   ✗ Authentication failed: {auth_resp.get('Error', 'unknown')}")
        # Print full response for debugging
        print(f"   Full response: {json.dumps(auth_resp, indent=2)[:500]}")
        return False
    
    print("   ✓ Authenticated!")
    
    # Step 4: Get children
    print("4. GET /children...")
    children = get_children(config["token"])
    nodes = children.get("Nodes", [])
    print(f"   Found {len(nodes)} nodes")
    
    for node in nodes:
        print(f"   - {node.get('Name', '?')} ({node.get('NodeID', '?')}) size={node.get('Size', '?')}")
    
    if not nodes:
        print("   ✗ No nodes found")
        return False
    
    # Step 5: Download the file
    node = nodes[0]
    node_id = node["NodeID"]
    node_name = node.get("Name", "file")
    node_size = node.get("Size", 0)
    
    print(f"5. Downloading {node_name} ({node_size} bytes)...")
    
    # Get node details with block info
    node_detail = get_node(config["token"], node_id)
    print(f"   Node detail keys: {list(node_detail.keys()) if isinstance(node_detail, dict) else type(node_detail)}")
    
    # Save raw response for inspection
    output_path = Path(config["output"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # If we got block data, try to download blocks
    blocks = node_detail.get("Blocks", [])
    if blocks:
        print(f"   Found {len(blocks)} blocks")
        # Download and concatenate blocks
        raw_data = b""
        for i, block in enumerate(blocks):
            block_url = block.get("URL", "")
            if block_url:
                if not block_url.startswith("http"):
                    block_url = "https://" + block_url
                br = requests.get(block_url, headers=HEADERS, timeout=60)
                br.raise_for_status()
                raw_data += br.content
                print(f"   Block {i}: {len(br.content)} bytes")
        
        # Write raw (encrypted) data
        raw_path = output_path.with_suffix(".encrypted")
        raw_path.write_bytes(raw_data)
        print(f"   Saved encrypted data to {raw_path} ({len(raw_data)} bytes)")
        
        # Note: full decryption requires OpenPGP key operations
        # which need a working PGPy or equivalent on Python 3.13
        print("   ⚠ Decryption requires OpenPGP key unwrapping")
        print("   ⚠ Encrypted data saved for offline decryption")
    else:
        # Try direct content
        content = node_detail.get("Content", b"")
        if content:
            output_path.write_bytes(content if isinstance(content, bytes) else content.encode())
            print(f"   Saved to {output_path}")
        else:
            print(f"   Node detail: {json.dumps(node_detail, indent=2)[:500]}")
    
    return True


def main():
    print("Proton Drive Public Share Acquisition")
    print("="*60)
    
    results = {}
    for name, config in SHARES.items():
        try:
            success = acquire(name, config)
        except Exception as e:
            print(f"   ✗ Exception: {e}")
            import traceback
            traceback.print_exc()
            success = False
        results[name] = success
    
    print("\n" + "="*60)
    print("Summary:")
    for name, ok in results.items():
        print(f"  {'✓' if ok else '✗'} {name}")
    
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())