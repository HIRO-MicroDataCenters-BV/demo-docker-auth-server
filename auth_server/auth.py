from typing import Any, cast

import base64
import hashlib
import random
import time

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_pem_private_key,
)
from cryptography.x509 import load_pem_x509_certificate
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError

from .config import ALGO, ISSUER, SERVICE


class InvalidToken(Exception):
    ...


class Option:
    def __init__(
        self,
        issuer: str,
        typ: str,
        name: str,
        account: str,
        service: str,
        actions: list[str],
    ):
        self.issuer = issuer
        self.typ = typ
        self.name = name
        self.account = account
        self.service = service
        self.actions = actions


class Token:
    def __init__(self, token: str, access_token: str):
        self.token = token
        self.access_token = access_token


def load_cert_and_key(cert_file: str, key_file: str) -> tuple[bytes, bytes]:
    with open(cert_file, "rb") as pub_key_file:
        pub_key_txt = pub_key_file.read()
        pub_key = load_pem_x509_certificate(pub_key_txt, backend=default_backend())
        pub_key_pem = pub_key.public_key().public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo,
        )

    with open(key_file, "rb") as prv_key_file:
        prv_key_txt = prv_key_file.read()
        prv_key = load_pem_private_key(
            prv_key_txt, password=None, backend=default_backend()
        )
        prv_key_pem = prv_key.private_bytes(
            encoding=Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    return pub_key_pem, prv_key_pem


def pub_key_pem_to_der(pub_key_pem: bytes) -> bytes:
    return serialization.load_pem_public_key(pub_key_pem).public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def get_kid_from_cert(pub_key_pem: bytes) -> str:
    pub_key_der = pub_key_pem_to_der(pub_key_pem)
    sha256_hash = hashlib.sha256(pub_key_der).digest()
    truncated_hash = sha256_hash[0:30]
    base32_encoded = base64.b32encode(truncated_hash)
    kid_parts = [
        base32_encoded[i : i + 4].decode("utf-8")
        for i in range(0, len(base32_encoded), 4)
    ]
    kid = ":".join(kid_parts)
    return kid


def create_token_option(service: str, account: str, scope: str) -> Option:
    parts = scope.split(":")

    opt_type = parts[0] if len(parts) > 0 else ""
    name = parts[1] if len(parts) > 1 else ""
    actions = parts[2].split(",") if len(parts) > 2 else []

    return Option(
        issuer=ISSUER,
        typ=opt_type,
        name=name,
        account=account,
        service=service,
        actions=actions,
    )


def create_token(
    public_key: bytes,
    private_key: bytes,
    opt: Option,
    actions: list[str],
) -> Token:
    key_id = get_kid_from_cert(public_key)
    header = {
        "typ": "JWT",
        "alg": ALGO,
        "kid": key_id,
    }

    now = int(time.time())
    exp = now + int(time.time() + 24 * 3600)

    claim = {
        "iss": opt.issuer,
        "sub": opt.account,
        "aud": opt.service,
        "exp": exp,
        "nbf": now - 10,
        "iat": now,
        "jti": str(random.randint(1, 1000000)),
        "access": [{"type": opt.typ, "name": opt.name, "actions": actions}],
    }

    token = jwt.encode(claim, private_key, algorithm=ALGO, headers=header)
    return Token(token=token, access_token=token)


def validate_token(token: str, public_key: bytes) -> dict[str, Any]:
    try:
        decoded_token = jwt.decode(
            token,
            public_key,
            algorithms=[ALGO],
            audience=SERVICE,
            issuer=ISSUER,
        )
        return cast(dict[str, Any], decoded_token)
    except ExpiredSignatureError:
        raise InvalidToken("Token expired")
    except InvalidTokenError:
        raise InvalidToken("Invalid token")
    except PyJWTError as e:
        raise InvalidToken(f"Token validation error: {e}")
