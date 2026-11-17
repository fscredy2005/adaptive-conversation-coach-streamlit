"""Regression test for the public facade; runs with unittest or pytest."""

import os
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class PreviewNoApiTest(unittest.TestCase):
    def test_disabled_preview_never_loads_voice_or_url(self):
        import streamlit as st
        import streamlit.components.v1 as components
        from streamlit.testing.v1 import AppTest

        import streamlit_support

        class User(dict):
            def __init__(self, logged_in):
                super().__init__(email="owner@example.invalid", email_verified=True)
                self.is_logged_in = logged_in

            def to_dict(self):
                return dict(self)

        original_connect = socket.socket.connect

        def offline(sock, address):
            # Windows asyncio requires a loopback socket pair.
            if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
                return original_connect(sock, address)
            raise AssertionError("Preview attempted an external connection")

        for logged_in in (False, True):
            with (
                self.subTest(logged_in=logged_in),
                patch.dict(
                    os.environ,
                    {
                        "ENABLE_VOICE_SERVICES": "0",
                        "VOICE_WEB_URL": "not-a-valid-url",
                        "ALLOWED_EMAILS": "owner@example.invalid",
                    },
                ),
            ):
                os.environ.pop("SSLKEYLOGFILE", None)
                with (
                    patch.object(st, "user", User(logged_in)),
                    patch.object(socket.socket, "connect", offline),
                    patch.object(socket.socket, "connect_ex", offline),
                    patch.object(components, "declare_component") as component,
                    patch.object(streamlit_support, "create_connection") as signer,
                    patch.object(streamlit_support, "validate_web_url") as validator,
                ):
                    app = AppTest.from_file(
                        str(ROOT / "streamlit_app.py"), default_timeout=15
                    )
                    app.session_state["voice_ticket"] = {
                        "connection": {"participantToken": "synthetic-old-token"}
                    }
                    app.run()
                    self.assertFalse(app.exception)
                    component.assert_not_called()
                    signer.assert_not_called()
                    validator.assert_not_called()
                    self.assertFalse(app.get("component_instance"))
                    self.assertFalse(app.get("iframe"))
                    self.assertFalse(app.selectbox)
                    self.assertNotIn("voice_ticket", app.session_state)
                    self.assertTrue(
                        any(
                            "disponible après configuration" in item.value
                            for item in app.info
                        )
                    )


if __name__ == "__main__":
    unittest.main()
