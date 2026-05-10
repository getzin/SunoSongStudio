# app_pages/dashboard.py

import streamlit as st

from shared.session import get_current_user
from shared.layout import app_header
from backend.db import query_one
from backend.models.users import get_api_keys
from backend.models.songs import list_songs_for_user
from backend.services.suno_service import process_pending_songs  # ⬅ only this

from shared.utils import can_use_cooldown, trigger_cooldown

from constants import (
    STATUS_COMPLETED,
    STATUS_QUEUED,
    STATUS_GENERATING,
    STATUS_FAILED,
)

COOLDOWN_KEY_SUNO_DASH = "suno_pending_check_dashboard"


# ---------------------------------------------------------
# UI Helper — metric card
# ---------------------------------------------------------
def _metric_card(label: str, value: str | int, icon: str = ""):
    st.markdown(
        f"""
        <div style="
            background-color:#1a1a1a;
            border:1px solid #2d2d2d;
            padding:1rem 1.2rem;
            border-radius:10px;
            margin-bottom:0.8rem;
        ">
            <div style="font-size:0.9rem;color:#bbbbbb;">{icon} {label}</div>
            <div style="font-size:1.6rem;font-weight:700;margin-top:0.2rem;color:#e6e6e6;">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# UI Helper — status badge
# ---------------------------------------------------------
def _status_badge(status: str) -> str:
    colors = {
        "queued": "#6666ff",
        "generating": "#ffaa33",
        "completed": "#44cc55",
        "failed": "#cc3344",
    }
    color = colors.get(status, "#888")
    return (
        f"<span style='background-color:{color};padding:0.15rem 0.45rem;"
        f"border-radius:4px;font-size:0.75rem;color:#0f0f0f;font-weight:600;'>"
        f"{status.upper()}</span>"
    )


# ---------------------------------------------------------
# Fetch counts for dashboard metrics
# ---------------------------------------------------------
def _get_stats(user_id: int) -> dict:
    stats = {}

    # Lyrics count
    row = query_one(
        "SELECT COUNT(*) AS c FROM lyrics WHERE user_id = ? AND archived = 0",
        (user_id,),
    )
    stats["lyrics_active"] = row["c"] if row else 0

    row = query_one(
        "SELECT COUNT(*) AS c FROM lyrics WHERE user_id = ? AND archived = 1",
        (user_id,),
    )
    stats["lyrics_archived"] = row["c"] if row else 0

    # Songs by status
    songs = list_songs_for_user(user_id)
    stats["songs_total"] = len(songs)
    stats["songs_completed"] = sum(1 for s in songs if s["status"] == STATUS_COMPLETED)
    stats["songs_queued"] = sum(1 for s in songs if s["status"] == STATUS_QUEUED)
    stats["songs_generating"] = sum(1 for s in songs if s["status"] == STATUS_GENERATING)
    stats["songs_failed"] = sum(1 for s in songs if s["status"] == STATUS_FAILED)

    # Total OpenAI cost across all lyrics for this user
    row = query_one(
        "SELECT COALESCE(SUM(cost), 0) AS total_cost FROM lyrics WHERE user_id = ?",
        (user_id,),
    )
    stats["openai_cost_total"] = float(row["total_cost"]) if row else 0.0

    return stats


# ---------------------------------------------------------
# Fetch API key presence
# ---------------------------------------------------------
def _get_api_status(user_id: int) -> dict:
    row = get_api_keys(user_id) or {}
    return {
        "openai": bool(row.get("openai_key")),
        "suno": bool(row.get("suno_key")),
    }


# ---------------------------------------------------------
# Main Dashboard
# ---------------------------------------------------------
def run():
    user = get_current_user()
    if not user:
        st.error("Not logged in.")
        return

    app_header("Dashboard")

    st.markdown(
        """
        <div style="margin-bottom:1.2rem;color:#cccccc;font-size:1rem;">
            Welcome to your creative hub. Track lyrics, monitor Suno jobs, and check your API setup.
        </div>
        """,
        unsafe_allow_html=True,
    )

    api_keys = get_api_keys(user["id"])
    suno_key = api_keys.get("suno_key") if api_keys else None  # ⬅ inline instead of resolve_suno_key()

    # Process pending Suno jobs — with cooldown to avoid hammering CDN
    if suno_key and can_use_cooldown(COOLDOWN_KEY_SUNO_DASH, 30):
        with st.spinner("Checking Suno job status…"):
            process_pending_songs(user["id"])
        trigger_cooldown(COOLDOWN_KEY_SUNO_DASH)

    stats = _get_stats(user["id"])
    api_status = _get_api_status(user["id"])

    # Metrics
    st.markdown("### 📊 Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        _metric_card("Active Lyrics", stats["lyrics_active"], "📜")
        _metric_card("Archived Lyrics", stats["lyrics_archived"], "🗂️")

    with col2:
        _metric_card("Total Songs", stats["songs_total"], "🎵")
        _metric_card("Completed Songs", stats["songs_completed"], "✅")

    with col3:
        _metric_card("Queued Songs", stats["songs_queued"], "⌛")
        _metric_card("Failed Songs", stats["songs_failed"], "❌")

    # One more row just for cost
    st.markdown("")
    col_cost, _, _ = st.columns(3)
    with col_cost:
        _metric_card(
            "Total OpenAI Lyrics Cost (USD)",
            f"${stats['openai_cost_total']:.4f}",
            "💰",
        )

    st.markdown("---")

    # API keys status
    st.markdown("### 🔑 API Keys Status")

    colA, colB = st.columns(2)
    with colA:
        st.markdown(
            f"**OpenAI Key:** {'<span style=\"color:#44cc55\">✔ Set</span>' if api_status['openai'] else '<span style=\"color:#cc3344\">✘ Missing</span>'}",
            unsafe_allow_html=True,
        )
    with colB:
        st.markdown(
            f"**Suno Key:** {'<span style=\"color:#44cc55\">✔ Set</span>' if api_status['suno'] else '<span style=\"color:#cc3344\">✘ Missing</span>'}",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Active Suno jobs
    st.markdown("### 🧰 Active Suno Jobs")

    pending = [
        s for s in list_songs_for_user(user["id"])
        if s["status"] in ("queued", "generating")
    ]

    if not pending:
        st.info("No active Suno jobs right now.")
    else:
        for row in pending:
            st.markdown(
                f"""
                <div style="
                    background-color:#1a1a1a;
                    border:1px solid #2d2d2d;
                    padding:0.6rem 0.9rem;
                    border-radius:8px;
                    margin-bottom:0.6rem;
                ">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <div style="font-size:1rem;font-weight:600;">
                                Track {row.get('track_label', '?')}
                            </div>
                            <div style="color:#aaaaaa;font-size:0.8rem;">
                                Job: {row.get('task_id', '—')}
                            </div>
                        </div>
                        <div>{_status_badge(row['status'])}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    st.markdown(
        """
        ### 🚀 Next Steps
        - Generate lyrics using **Lyrics Generate**
        - Convert lyrics into Suno tracks in **Songs Generate**
        - Download your music from **Songs History**
        """,
    )
