# shared/session.py

import streamlit as st


def set_current_user(user: dict):
    st.session_state["user"] = user


def get_current_user():
    return st.session_state.get("user")


def logout():
    # Clear all session state on logout to avoid stale navigation/cooldowns
    st.session_state.clear()
