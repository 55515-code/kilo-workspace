"""Smoke tests for scripts/acquire_proton.py.

These tests verify the script's helpers without making any network
calls, so they run in any environment — including the CI container
that has no Proton Drive credentials and no internet access.

Run with:

    python3 -m pytest tests/smoke/test_acquire_proton.py -v

or, with the bundled ``scripts/test.sh``:

    bash scripts/test.sh
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

# Make the scripts/ package importable.
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import acquire_proton as ap  # noqa: E402


# ---------------------------------------------------------------------------
# _bcrypt_b64encode
# ---------------------------------------------------------------------------


def test_bcrypt_b64encode_known_vector():
    # Empty input -> empty output.
    assert ap._bcrypt_b64encode(b"") == ""
    # 1 byte: 2 output chars.
    assert len(ap._bcrypt_b64encode(b"\x00")) == 2
    # 3 bytes: 4 output chars.
    assert len(ap._bcrypt_b64encode(b"\x00\x00\x00")) == 4
    # Known vector from bcrypt's own base64 alphabet table:
    #   "A" maps to byte 0x10 (16) at index 0 in the output alphabet.
    out = ap._bcrypt_b64encode(b"\x40")  # 0x40 == 64 == 'A' in the bcrypt alphabet at idx 16
    # 0x40 = 0b0100_0000  -> top 6 bits = 0b010000 = 16 -> 'A'
    # then 2 trailing zero bits -> next char index 0 -> '.'
    assert out == "A."


# ---------------------------------------------------------------------------
# _extract_modulus
# ---------------------------------------------------------------------------


def test_extract_modulus_parses_pgp_signed_block():
    payload = base64_payload = "ZGVhZGJlZWY="  # "deadbeef"
    text = (
        "-----BEGIN PGP SIGNED MESSAGE-----\n"
        "Hash: SHA512\n"
        "\n"
        f"{payload}\n"
        "-----BEGIN PGP SIGNATURE-----\n"
        "\n"
        "iQEzBAEBCgAdFiEEAAAAAAA=ABCD\n"
        "=BBBB\n"
        "-----END PGP SIGNATURE-----\n"
    )
    assert ap._extract_modulus(text) == base64.b64decode(payload)


def test_extract_modulus_raises_on_garbage():
    with pytest.raises(ValueError):
        ap._extract_modulus("not a pgp block")


# ---------------------------------------------------------------------------
# _scrub
# ---------------------------------------------------------------------------


def test_scrub_masks_known_secret_keys():
    payload = {
        "Token": "public",
        "Secret": "do-not-leak",
        "AccessToken": "do-not-leak",
        "Password": "do-not-leak",
        "SRPSession": "do-not-leak",
        "Nested": [{"Password": "x", "Ok": 1}],
    }
    cleaned = ap._scrub(payload)
    assert cleaned["Token"] == "public"
    assert cleaned["Secret"] == "***"
    assert cleaned["AccessToken"] == "***"
    assert cleaned["Password"] == "***"
    assert cleaned["SRPSession"] == "***"
    assert cleaned["Nested"][0]["Password"] == "***"
    assert cleaned["Nested"][0]["Ok"] == 1


# ---------------------------------------------------------------------------
# require_deps
# ---------------------------------------------------------------------------


def test_require_deps_raises_when_missing(monkeypatch):
    # Force the lazy imports to look missing.
    monkeypatch.setattr(ap, "requests", None)
    monkeypatch.setattr(ap, "bcrypt", None)
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in ("pgpy", "cryptography"):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(SystemExit) as exc:
        ap.require_deps()
    msg = str(exc.value)
    assert "requests" in msg
    assert "bcrypt" in msg
    assert "pgpy" in msg
    assert "cryptography" in msg


# ---------------------------------------------------------------------------
# SRP-6a end-to-end (no network, deterministic)
# ---------------------------------------------------------------------------


def test_srp_auth_payload_is_deterministic_in_shape(monkeypatch):
    # Fix the random a so we can check the body shape.
    monkeypatch.setattr(ap.os, "urandom", lambda n: b"\x11" * n)

    modulus_pgp = (
        "-----BEGIN PGP SIGNED MESSAGE-----\n"
        "Hash: SHA512\n"
        "\n"
        + ("A" * 256)  # 256 base64 chars -> 192 bytes
        + "\n"
        + "-----BEGIN PGP SIGNATURE-----\n\n=iQEz\n=BBBB\n-----END PGP SIGNATURE-----\n"
    )
    # 192-byte modulus -> N
    modulus_bytes = b"\xAB" * 192
    info = {
        "Modulus": modulus_pgp.replace("A" * 256, _b(modulus_bytes)),
        "ServerEphemeral": base64.b64encode(b"\xCD" * 192).decode(),
        "UrlPasswordSalt": base64.b64encode(b"salt" * 4).decode(),
        "SRPSession": "session-xyz",
    }

    # Stub out bcrypt since we don't require it for this test.
    monkeypatch.setattr(
        ap,
        "_bcrypt_hash_password",
        lambda secret, salt: hashlib.sha256(secret.encode()).digest(),
    )

    body, m2, s = ap.srp_auth_payload(info, "frag")
    assert set(body) == {"ClientEphemeral", "ClientProof", "SRPSession"}
    assert body["SRPSession"] == "session-xyz"
    assert len(body["ClientEphemeral"]) > 0
    assert len(body["ClientProof"]) > 0
    assert len(m2) == 32
    assert len(s) == 192


def _b(data: bytes) -> str:
    import base64 as _b64
    return _b64.b64encode(data).decode()


# ---------------------------------------------------------------------------
# Share config / find_config
# ---------------------------------------------------------------------------


def test_share_config_from_dict_defaults(tmp_path: Path):
    cfg = ap.ShareConfig.from_dict(
        {
            "name": "audio",
            "token": "T",
            "secret": "S",
        },
        tmp_path,
    )
    assert cfg.name == "audio"
    assert cfg.output == tmp_path / "audio"
    assert cfg.token == "T"


def test_share_config_from_dict_explicit_filename(tmp_path: Path):
    cfg = ap.ShareConfig.from_dict(
        {
            "name": "audio",
            "token": "T",
            "secret": "S",
            "subdir": "tracks",
            "filename": "master.wav",
        },
        tmp_path,
    )
    assert cfg.output == tmp_path / "tracks" / "master.wav"


def test_share_config_from_dict_missing_keys(tmp_path: Path):
    with pytest.raises(ValueError):
        ap.ShareConfig.from_dict({"name": "x", "token": "t"}, tmp_path)


def test_find_config_prefers_explicit(tmp_path: Path, monkeypatch):
    cfg_file = tmp_path / "acq.json"
    cfg_file.write_text(json.dumps({"shares": []}))
    found = ap.find_config(str(cfg_file))
    assert found == cfg_file


def test_find_config_falls_back_to_env(tmp_path: Path, monkeypatch):
    cfg_file = tmp_path / "acq.json"
    cfg_file.write_text(json.dumps({"shares": []}))
    monkeypatch.setenv("ACQUIRE_CONFIG", str(cfg_file))
    assert ap.find_config(None) == cfg_file


def test_find_config_errors_when_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ACQUIRE_CONFIG", raising=False)
    with pytest.raises(SystemExit):
        ap.find_config(None)


# ---------------------------------------------------------------------------
# SHA-256 verification helper
# ---------------------------------------------------------------------------


def test_node_passes_verification_true_and_false(tmp_path: Path):
    f = tmp_path / "blob"
    f.write_bytes(b"hello world")
    good = hashlib.sha256(b"hello world").hexdigest()
    bad = "0" * 64
    assert ap._node_passes_verification(f, good) is True
    assert ap._node_passes_verification(f, bad) is False
    missing = tmp_path / "nope"
    assert ap._node_passes_verification(missing, good) is False


def test_sha256_of_file(tmp_path: Path):
    f = tmp_path / "x"
    f.write_bytes(b"abc")
    assert ap._sha256_of_file(f) == hashlib.sha256(b"abc").hexdigest()


# ---------------------------------------------------------------------------
# Safe filename + acquire CLI --help
# ---------------------------------------------------------------------------


def test_safe_filename():
    assert ap._safe_filename("a/b\\c d?.png") == "a_b_c_d_.png"
    assert ap._safe_filename("") == "file"
    assert ap._safe_filename("normal.wav") == "normal.wav"


def test_cli_help_exits_zero():
    import subprocess
    res = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "acquire_proton.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "Proton Drive" in res.stdout
