import logging
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

_bearer = HTTPBearer()


@lru_cache(maxsize=1)
def _get_jwks_client(tenant_id: str) -> PyJWKClient:
    uri = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    return PyJWKClient(uri, cache_jwk_set=True, lifespan=3600)


async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> dict:
    token = credentials.credentials
    client = _get_jwks_client(settings.azure_tenant_id)
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        valid_issuers = [
            f"https://login.microsoftonline.com/{settings.azure_tenant_id}/v2.0",
            f"https://sts.windows.net/{settings.azure_tenant_id}/",
        ]
        # Azure AD v2 may set aud as bare GUID or api:// URI — accept both
        audience = settings.azure_audience
        guid = audience.removeprefix("api://")
        valid_audiences = [audience, guid]
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=valid_audiences,
            options={"verify_iss": False},
        )
        if claims.get("iss") not in valid_issuers:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid issuer",
            )
        claims["token"] = token
        return claims
    except jwt.ExpiredSignatureError:
        logger.warning("auth failed: token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError as exc:
        logger.warning("auth failed: %s | audience=%s tenant=%s", exc, settings.azure_audience, settings.azure_tenant_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
