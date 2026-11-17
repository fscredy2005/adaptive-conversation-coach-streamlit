"""Streamlit integration helpers. Signing a JWT never calls a LiveKit service."""

import json
from collections.abc import Mapping
from datetime import timedelta
from urllib.parse import urlsplit
from uuid import uuid4

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def validate_web_url(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path.rstrip("/") != "/streamlit"
        or (parsed.scheme != "https" and parsed.hostname not in LOCAL_HOSTS)
    ):
        raise ValueError(
            "VOICE_WEB_URL doit être une URL HTTPS /streamlit (HTTP autorisé sur localhost uniquement)."
        )
    return value.rstrip("/")


def remote_web(value: str) -> bool:
    return urlsplit(validate_web_url(value)).hostname not in LOCAL_HOSTS


def authorized_user(logged_in: bool, claims: Mapping, allowed_emails: str) -> bool:
    """Only identity verified by Streamlit's OIDC session can authorize voice."""
    allowed = {
        email.strip().casefold() for email in allowed_emails.split(",") if email.strip()
    }
    email = claims.get("email")
    return (
        logged_in is True
        and claims.get("email_verified") is True
        and isinstance(email, str)
        and email.casefold() in allowed
    )


def create_connection(
    settings: Mapping[str, str],
    language: str,
    mode: str,
    *,
    authenticated: bool = False,
) -> dict:
    if authenticated is not True:
        raise PermissionError("Authentification et autorisation requises.")
    if settings.get("ENABLE_VOICE_SERVICES") != "1":
        raise ValueError("Services vocaux désactivés.")
    if language not in ("fr", "en") or mode not in ("free", "interview"):
        raise ValueError("Langue ou mode invalide.")
    for key in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"):
        if not settings.get(key):
            raise ValueError(f"Configuration manquante : {key}")
    parsed = urlsplit(settings["LIVEKIT_URL"])
    if parsed.scheme != "wss" or not parsed.hostname:
        raise ValueError("LIVEKIT_URL doit utiliser wss://.")
    # Import lazily: the disabled preview never needs to initialize an SDK.
    from livekit import api

    room_name = f"coach-{uuid4()}"
    token = (
        api.AccessToken(settings["LIVEKIT_API_KEY"], settings["LIVEKIT_API_SECRET"])
        .with_identity(f"user-{uuid4()}")
        .with_name("You")
        .with_ttl(timedelta(minutes=5))
        .with_grants(
            api.VideoGrants(
                room=room_name,
                room_join=True,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .with_room_config(
            api.RoomConfiguration(
                agents=[
                    api.RoomAgentDispatch(
                        agent_name="adaptive-conversation-coach",
                        metadata=json.dumps({"language": language, "mode": mode}),
                    )
                ]
            )
        )
        .to_jwt()
    )
    return {
        "serverUrl": settings["LIVEKIT_URL"],
        "roomName": room_name,
        "participantName": "You",
        "participantToken": token,
    }
