# app_pages/settings.py

import streamlit as st

from backend.models.users import get_api_keys, upsert_api_keys
from shared.session import get_current_user
from shared.layout import app_header


def run():
    user = get_current_user()
    app_header("Settings")

    st.markdown(
        """
        <div style="margin-bottom:1rem;color:#cccccc;font-size:1rem;">
            Manage your API keys and account configuration.
            These keys are stored securely in your local database and never leave your machine.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------
    # Load existing keys
    # ---------------------------------------------------------
    api = get_api_keys(user["id"]) or {}
    openai_key = api.get("openai_key", "")
    suno_key = api.get("suno_key", "")

    # ---------------------------------------------------------
    # API KEYS CARD
    # ---------------------------------------------------------
    st.markdown(
        """
        <div class="suno-card">
            <h3 style="margin-top:0;">🔑 API Keys</h3>
            <div style="color:#bbbbbb;font-size:0.9rem;margin-bottom:0.8rem;">
                Add or update the API keys needed for generating lyrics and Suno tracks.
                Your keys are encrypted at rest and never transmitted anywhere except
                directly to the respective APIs.
            </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("keys_form"):
        new_openai = st.text_input(
            "OpenAI API Key",
            value=openai_key,
            type="password",
            placeholder="sk-...",
            help="Required for generating lyrics."
        )

        new_suno = st.text_input(
            "Suno / AceData Key",
            value=suno_key,
            type="password",
            placeholder="acedata_live_xxx",
            help="Required for generating audio via Suno."
        )

        submitted = st.form_submit_button("Save Changes")

        if submitted:
            upsert_api_keys(
                user["id"],
                openai_key=new_openai.strip(),
                suno_key=new_suno.strip(),
            )
            st.success("API keys saved successfully!")

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # ACCOUNT INFO CARD
    # ---------------------------------------------------------
    st.markdown("")
    st.markdown(
        """
        <div class="suno-card" style="margin-top:1rem;">
            <h3 style="margin-top:0;">👤 Account Information</h3>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="color:#cccccc;font-size:0.95rem;">
            <strong>Email:</strong> {user['email']}<br>
            <strong>Username:</strong> {user['username']}<br>
            <strong>Admin:</strong> {"Yes" if user.get("is_admin") else "No"}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")


    # ---------------------------------------------------------
    # INFO BOX
    # ---------------------------------------------------------
    st.info(
        "Tip: Ensure both keys are set before generating lyrics or Suno tracks. "
        "If a key is missing, related features will be disabled."
    )
