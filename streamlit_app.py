"""Main browser entry point. WebRTC stays inside the existing LiveKit UI."""

import os

import streamlit as st
import streamlit.components.v1 as components

from streamlit_support import authorized_user, create_connection, validate_web_url

st.set_page_config(
    page_title="Adaptive Conversation Coach", page_icon="🎙", layout="centered"
)
st.title("Adaptive Conversation Coach")
st.caption("Une conversation continue en temps réel · Français / English")

KEYS = (
    "VOICE_WEB_URL",
    "ENABLE_VOICE_SERVICES",
    "LIVEKIT_URL",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
    "ALLOWED_EMAILS",
)
try:
    secrets = dict(st.secrets)
except FileNotFoundError:
    secrets = {}
settings = {key: str(os.environ.get(key, secrets.get(key, ""))) for key in KEYS}
enabled = settings["ENABLE_VOICE_SERVICES"] == "1"
logged_in = getattr(st.user, "is_logged_in", False)
authenticated = authorized_user(
    logged_in, st.user.to_dict(), settings["ALLOWED_EMAILS"]
)
# Never trust authentication flags in component values, query parameters or widgets.
if not authenticated or not enabled:
    cached = st.session_state.get("voice_ticket") or {}
    if cached.get("connection"):
        st.session_state.pop("voice_ticket", None)
if not authenticated:
    auth = secrets.get("auth", {})
    ready = settings["ALLOWED_EMAILS"] and all(
        auth.get(key)
        for key in (
            "redirect_uri",
            "cookie_secret",
            "client_id",
            "client_secret",
            "server_metadata_url",
        )
    )
    st.info("La page est publique. L’accès vocal est réservé au compte autorisé.")
    if logged_in:
        st.warning("Ce compte n’est pas autorisé ou son adresse n’est pas vérifiée.")
        if st.button("Se déconnecter"):
            st.logout()
    elif ready and st.button("Se connecter"):
        st.login()
    if enabled:
        st.session_state.voice_status = "disconnected"
        if not ready:
            st.error(
                "Accès vocal bloqué : configurez OIDC et ALLOWED_EMAILS côté serveur."
            )
        st.stop()
elif st.button("Se déconnecter"):
    st.session_state.pop("voice_ticket", None)
    st.logout()

if not enabled:
    st.session_state.pop("voice_ticket", None)
    st.session_state.voice_status = "disconnected"
    st.info(
        "Aperçu sans API : services vocaux désactivés. "
        "Le module vocal sera disponible après configuration."
    )
    st.stop()

web_url = settings["VOICE_WEB_URL"] or "http://localhost:3000/streamlit"
try:
    web_url = validate_web_url(web_url)
except ValueError as error:
    st.error(str(error))
    st.stop()

active = st.session_state.get("voice_status") in ("connecting", "connected")
language = st.selectbox(
    "Langue / Language",
    ["fr", "en"],
    format_func=lambda code: "Français" if code == "fr" else "English",
    disabled=active,
)
mode = st.selectbox(
    "Mode",
    ["free", "interview"],
    format_func=lambda code: "Conversation libre" if code == "free" else "Entretien",
    disabled=active,
)
st.caption("Entretien : questions successives, sans évaluation ni score de coaching.")
status = st.session_state.get("voice_status", "disconnected")
st.write(
    "Connexion : "
    + {
        "connecting": "connexion en cours",
        "connected": "connectée",
        "disconnected": "déconnectée",
    }.get(status, "déconnectée")
)
st.caption(
    "Les boutons démarrer/terminer, les états d’écoute/réponse et la transcription sont dans la zone vocale ci-dessous."
)

voice = components.declare_component("adaptive_livekit_voice", url=web_url)
value = voice(
    language=language,
    mode=mode,
    servicesEnabled=enabled,
    ticket=st.session_state.get("voice_ticket"),
    key=f"voice-{language}-{mode}-{st.session_state.get('voice_generation', 0)}",
    default=None,
)
if isinstance(value, dict):
    if value.get("action") == "connect":
        request_id = value.get("requestId")
        previous = st.session_state.get("voice_ticket") or {}
        if (
            isinstance(request_id, str)
            and 0 < len(request_id) <= 100
            and request_id != previous.get("requestId")
        ):
            try:
                connection = create_connection(
                    settings, language, mode, authenticated=authenticated
                )
                ticket = {"requestId": request_id, "connection": connection}
            except (ValueError, PermissionError) as error:
                ticket = {"requestId": request_id, "error": str(error)}
            st.session_state.voice_ticket = ticket
            st.rerun()
    elif (
        value.get("action") == "status"
        and value.get("status") in ("connecting", "connected", "disconnected")
        and st.session_state.get("voice_status") != value["status"]
    ):
        st.session_state.voice_status = value["status"]
        st.rerun()

if active and st.button(
    "Réinitialiser la zone vocale",
    help="À utiliser si le module ne répond plus. Coupe la connexion en supprimant le composant.",
):
    st.session_state.voice_status = "disconnected"
    st.session_state.pop("voice_ticket", None)
    st.session_state.voice_generation = st.session_state.get("voice_generation", 0) + 1
    st.rerun()

st.caption(
    "Aucun enregistrement audio par l’application. La voix transite par les services configurés ; la transcription automatique peut contenir des erreurs."
)
