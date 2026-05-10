# app_pages/debug_tools.py

import streamlit as st
import openai
import requests

from shared.session import get_current_user
from backend.models.users import get_api_keys
from constants import ENABLE_DEBUG_TOOLS, ACE_TASKS_URL


def run():
    user = get_current_user()

    if not user.get("is_admin") or not ENABLE_DEBUG_TOOLS:
        st.error("Debug Tools disabled.")
        return

    st.subheader("Admin Debug Tools")

    keys = get_api_keys(user["id"]) or {}
    openai_key = keys.get("openai_key")
    suno_key = keys.get("suno_key")

    # OpenAI Test
    st.markdown("## Test OpenAI")
    prompt = st.text_input("Prompt", "Hello AI!", key="dbg_openai_prompt")
    if st.button("Run OpenAI Test"):
        if not openai_key:
            st.error("No OpenAI key set.")
        else:
            openai.api_key = openai_key
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
            )
            st.json(resp)

    st.markdown("---")

    # AceData Test
    st.markdown("## Test AceData Task Creation")

    if st.button("Send Dummy AceData Task"):
        if not suno_key:
            st.error("Missing AceData key.")
        else:
            try:
                r = requests.post(
                    ACE_TASKS_URL,
                    headers={
                        "X-Api-Key": suno_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "input_text": "test",
                        "make_instrumental": True,
                        "model": "chirp-v3-0",
                        "prompt": "debug",
                        "tags": [],
                        "title": "debug test",
                    },
                )
                st.json(r.json())
            except Exception as e:
                st.error(f"Error: {e}")
