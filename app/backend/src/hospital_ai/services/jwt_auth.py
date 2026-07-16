"""JWT token validation service.
Dịch vụ xác thực token JWT.

Implements the security architecture documented at
docs/04-architecture/security-architecture.md:

    "The FastAPI Backend (BFF) validates incoming JWTs using the HMS
     public signature key or a shared HMAC secret."

When no JWT settings are configured (empty defaults), this service
returns None and the caller falls back to the static token map.
Khi không cấu hình JWT settings, service trả về None và cho phép hệ thống rơi về (fallback)
sử dụng bản đồ token tĩnh (static token map).
"""

import logging

import jwt
from jwt import PyJWKClient

from hospital_ai.core.config import Settings

logger = logging.getLogger(__name__)


class JwtTokenData:
    """Extracted claims from a validated JWT.
    Đối tượng chứa các thông tin (claims) được trích xuất từ token JWT hợp lệ.
    """

    def __init__(self, sub: str, email: str, name: str, role: str) -> None:
        """Khởi tạo JwtTokenData với sub (định danh người dùng), email, tên và vai trò (role)."""
        self.sub = sub
        self.email = email
        self.name = name
        self.role = role


class JwtAuthService:
    """Validates JWTs against JWKS (RS256) or HMAC secret (HS256).
    Dịch vụ xác thực JWT dựa trên JWKS (thuật toán RS256) hoặc bí mật HMAC (thuật toán HS256).

    Returns None when:
    - JWT settings are not configured (empty issuer)
    - Token is expired or invalid
    - Required cryptography package is missing for RS256
    - Token validation fails for any other reason

    Never raises to the caller — all failures return None so the
    fallback chain in deps.py can try the next authentication method.
    Không bao giờ ném ngoại lệ lên caller — mọi trường hợp lỗi đều trả về None để
    chuỗi xử lý fallback trong deps.py có thể thử phương pháp xác thực tiếp theo.
    """

    def __init__(self, settings: Settings) -> None:
        """Khởi tạo JwtAuthService với cấu hình hệ thống Settings."""
        self.settings = settings
        self._jwks_client: PyJWKClient | None = None

    def _is_configured(self) -> bool:
        """Check whether any JWT validation settings are provided.
        Kiểm tra xem các thiết lập xác thực JWT có được cấu hình trong hệ thống hay không.
        """
        return bool(self.settings.jwt_issuer and (self.settings.jwks_url or self.settings.jwt_hmac_secret))

    def _get_jwks_client(self) -> PyJWKClient | None:
        """Khởi tạo và trả về instance PyJWKClient để tải khóa công khai từ URL JWKS nếu cần."""
        if self._jwks_client is None and self.settings.jwks_url:
            try:
                self._jwks_client = PyJWKClient(self.settings.jwks_url)
            except Exception:
                logger.warning(
                    "Failed to initialise JWKS client from %s",
                    self.settings.jwks_url,
                    exc_info=True,
                )
                return None
        return self._jwks_client

    async def validate_token(self, token: str) -> JwtTokenData | None:
        """Validate a JWT and return claims, or None if invalid.
        Xác thực token JWT và trả về các thông tin (claims) của người dùng, hoặc trả về None nếu không hợp lệ.

        When RS256 is requested but cryptography is not installed,
        logs a warning and returns None so the caller can fall back.
        """
        if not self._is_configured():
            return None

        try:
            algorithm = self.settings.jwt_algorithm

            if self.settings.jwks_url:
                # RS256 / ES256 via JWKS (requires cryptography)
                try:
                    from jwt.algorithms import RSAAlgorithm  # noqa: F401
                except ImportError:
                    logger.warning(
                        "RS256/JWKS requires cryptography. Install with: pip install hospital-ai-backend[jwt-rs256]"
                    )
                    return None

                jwks_client = self._get_jwks_client()
                if jwks_client is None:
                    return None
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                key = signing_key.key
            elif self.settings.jwt_hmac_secret:
                key = self.settings.jwt_hmac_secret
            else:
                return None

            options = {"verify_exp": True}
            if not self.settings.jwt_audience:
                options["verify_aud"] = False

            payload = jwt.decode(
                token,
                key,
                algorithms=[algorithm],
                audience=self.settings.jwt_audience or None,
                issuer=self.settings.jwt_issuer or None,
                options=options,
            )

            return JwtTokenData(
                sub=payload.get("sub", ""),
                email=payload.get("email", ""),
                name=payload.get("name", ""),
                role=payload.get("role", ""),
            )
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as exc:
            logger.warning("JWT validation failed: %s", exc)
            return None
        except Exception:
            logger.exception("Unexpected error during JWT validation")
            return None
