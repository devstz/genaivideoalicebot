import base64
import hashlib
import hmac
import secrets


class PasswordService:
    """Password hashing with PBKDF2-HMAC-SHA256."""

    algorithm = "pbkdf2_sha256"
    iterations = 120_000
    salt_size = 16

    def hash_password(self, password: str) -> str:
        salt = secrets.token_bytes(self.salt_size)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self.iterations,
        )
        salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii")
        digest_b64 = base64.urlsafe_b64encode(digest).decode("ascii")
        return f"{self.algorithm}${self.iterations}${salt_b64}${digest_b64}"

    def verify_password(self, password: str, password_hash: str | None) -> bool:
        if not password_hash:
            return False
        try:
            algorithm, iterations_raw, salt_b64, digest_b64 = password_hash.split("$", 3)
            if algorithm != self.algorithm:
                return False
            iterations = int(iterations_raw)
            salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
            expected_digest = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        except Exception:
            return False

        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual_digest, expected_digest)
