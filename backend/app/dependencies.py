from typing import Annotated

from fastapi import Depends

from app.config import Settings, get_settings
from app.middleware.auth import validate_token


async def get_current_user(token_claims: dict = Depends(validate_token)) -> dict:
    return token_claims


CurrentUser = Annotated[dict, Depends(get_current_user)]
AppSettings = Annotated[Settings, Depends(get_settings)]
