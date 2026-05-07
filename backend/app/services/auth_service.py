from functools import lru_cache

import msal
from azure.identity import OnBehalfOfCredential

from app.config import Settings


@lru_cache(maxsize=1)
def _get_msal_app(
    client_id: str, client_secret: str, tenant_id: str
) -> msal.ConfidentialClientApplication:
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    return msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=authority,
    )


def get_foundry_token(user_assertion: str, settings: Settings) -> str:
    app = _get_msal_app(
        settings.azure_client_id,
        settings.azure_client_secret,
        settings.azure_tenant_id,
    )
    result = app.acquire_token_on_behalf_of(
        user_assertion=user_assertion,
        scopes=["https://ai.azure.com/.default"],
    )
    if "access_token" not in result:
        error = result.get(
            "error_description", result.get("error", "OBO exchange failed")
        )
        raise RuntimeError(f"OBO token acquisition failed: {error}")
    return result["access_token"]


def get_obo_credential(user_assertion: str, settings: Settings) -> OnBehalfOfCredential:
    return OnBehalfOfCredential(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret,
        user_assertion=user_assertion,
    )
