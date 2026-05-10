# app_pages/lyrics_generate.py

import streamlit as st

from shared.layout import require_login, app_header
from shared.session import get_current_user
from backend.services.lyrics_service import generate_lyrics
from shared.utils import can_use_cooldown, trigger_cooldown
from constants import MODE_NORMAL, MODE_CAT, MODE_XMAS

COOLDOWN_KEY_LYRICS = "lyrics_generate_cooldown"


# ---------------------------------------------------------
# Pretty label for dropdown
# ---------------------------------------------------------
def _format_mode(mode: str) -> str:
    if mode == MODE_CAT:
        return "🐱 Cat Mode (Kawaii)"
    if mode == MODE_XMAS:
        return "🎄 Christmas Mode"
    return "✨ Normal"


# ---------------------------------------------------------
# Main Page
# ---------------------------------------------------------
def run():
    require_login()
    app_header("Generate Lyrics")

    user = get_current_user()

    st.markdown(
        """
        <div style="margin-bottom:1rem;color:#cccccc;font-size:1rem;">
            Create complete lyrics using OpenAI, with structured sections,
            themes, onomatopoeia, and stylistic controls.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------
    # Card: Settings
    # ---------------------------------------------------------
    with st.container():
        st.markdown(
            """
            <div class="suno-card">
                <h3 style="margin-top:0;">🎨 Generation Settings</h3>
            """,
            unsafe_allow_html=True,
        )

        mode = st.selectbox(
            "Theme",
            [MODE_NORMAL, MODE_CAT, MODE_XMAS],
            format_func=_format_mode,
        )

        language = st.text_input("Language", "English")
        artist = st.text_input("Artist / Style", "Rockstar")
        genre = st.text_input("Genre / Mood", "Cozy")

        # Title options
        auto_title = st.checkbox(
            "Auto-generate title from lyrics",
            value=True,
            help="If disabled, you can enter a custom title.",
        )

        manual_title = ""
        if not auto_title:
            manual_title = st.text_input(
                "Custom song title",
                value="",
                placeholder="Enter your song title…",
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # Advanced JSON-driven controls
    # ---------------------------------------------------------
    with st.expander("Advanced Lyrics Controls (JSON fields)"):
        topics_text = st.text_area(
            "Topics (comma or one per line)",
            value="",
            placeholder="love, heartbreak, neon lights\ncity skyline",
        )

        semantic = st.text_area(
            "Semantic / mood instructions",
            value="",
            placeholder="intimate, confessional tone; strong visual imagery; bittersweet but hopeful",
        )

        subgenre = st.text_input(
            "Subgenre (optional)",
            value="",
            placeholder="synth-pop, city pop, metalcore, etc.",
        )

        forbidden_words_text = st.text_input(
            "Forbidden words (comma or one per line)",
            value="",
            placeholder="stars, shadows, echoes",
        )

        formatting_text = st.text_area(
            "Formatting rules (one per line or comma-separated)",
            value="",
            placeholder="line break after each 4-line stanza\nno chorus labels in all caps",
        )

        finalsteps_text = st.text_area(
            "Final steps (post-processing instructions)",
            value="",
            placeholder="wrap 4 strongest rhymes in round brackets\nensure last line feels conclusive",
        )

        onomatopoeia_text = st.text_input(
            "Onomatopoeia list (comma or one per line)",
            value="",
            placeholder="boom, crash, whoosh, tick-tock",
        )

    st.markdown("")

    # ---------------------------------------------------------
    # Generate button
    # ---------------------------------------------------------
    can_generate = can_use_cooldown(COOLDOWN_KEY_LYRICS, 60)

    if not can_generate:
        st.info("⏳ Please wait a bit before generating again.")

    generate_btn = st.button(
        "✨ Generate Lyrics",
        disabled=not can_generate,
    )

    # ---------------------------------------------------------
    # Run generation
    # ---------------------------------------------------------
    if generate_btn:
        try:
            with st.spinner("Creating lyrics…"):
                lyrics_id, title, emoji, text = generate_lyrics(
                    user=user,
                    mode=mode,
                    language=language,
                    artist=artist,
                    genre=genre,
                    auto_title=auto_title,
                    manual_title=manual_title,
                    topics_text=topics_text,
                    semantic=semantic,
                    subgenre=subgenre,
                    forbidden_words_text=forbidden_words_text,
                    formatting_text=formatting_text,
                    finalsteps_text=finalsteps_text,
                    onomatopoeia_text=onomatopoeia_text,
                )
            trigger_cooldown(COOLDOWN_KEY_LYRICS)

            # Success message
            st.success(f"Lyrics generated: {emoji} **{title}**")

            # ---------------------------------------------------------
            # Card: Lyrics Output
            # ---------------------------------------------------------
            st.markdown(
                """
                <div class="suno-card" style="margin-top:1rem;">
                    <h3 style="margin-top:0;">📄 Generated Lyrics</h3>
                """,
                unsafe_allow_html=True,
            )

            st.text_area(
                "Lyrics",
                text,
                height=450,
                disabled=True,
            )

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error generating lyrics: {e}")
