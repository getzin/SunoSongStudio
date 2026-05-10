from pathlib import Path
import os
from dotenv import load_dotenv

# ----------------------------------------
# ENV LOADING
# ----------------------------------------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ----------------------------------------
# ADMIN ACCOUNT
# ----------------------------------------
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "q@q.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123")

# ----------------------------------------
# APP META
# ----------------------------------------
APP_NAME = "SunoSongStudio"

# ----------------------------------------
# PATHS
# ----------------------------------------
DATA_DIR = BASE_DIR / "data"
LYRICS_DIR = DATA_DIR / "lyrics"
AUDIO_DIR = DATA_DIR / "audio"
VIDEO_DIR = DATA_DIR / "video"
LOG_DIR = BASE_DIR / "logs"

DB_PATH = DATA_DIR / "app.db"

for d in [DATA_DIR, LYRICS_DIR, AUDIO_DIR, VIDEO_DIR, LOG_DIR]:
    d.mkdir(exist_ok=True, parents=True)

# ----------------------------------------
# FEATURE TOGGLES
# ----------------------------------------
ENABLE_DEBUG_TOOLS = os.getenv("ENABLE_DEBUG_TOOLS", "0") == "1"

# ----------------------------------------
# LYRICS LIMITS
# ----------------------------------------
LYRICS_MIN_WORDS = 20
LYRICS_MAX_WORDS = 800

# ----------------------------------------
# SUNO API
# ----------------------------------------
ACE_AUDIO_URL = "https://api.acedata.cloud/suno/audios"
ACE_TASKS_URL = "https://api.acedata.cloud/suno/tasks"

STATUS_QUEUED = "queued"
STATUS_GENERATING = "generating"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

def generate_track_label(i: int) -> str:
    return "A" if i == 0 else "B"

# ----------------------------------------
# OPENAI MODES
# ----------------------------------------
MODE_NORMAL = "normal"
MODE_CAT = "cat"
MODE_XMAS = "xmas"

# ----------------------------------------
# SUNO MODELS
# ----------------------------------------
SUNO_MODELS = [
    "chirp-v5",
    "chirp-v4",
    "chirp-v3-5",
    "chirp-v3-0",
]

VOCAL_GENDERS = ["male", "female", "mixed"]

# ----------------------------------------
# SONG PRESETS
# ----------------------------------------
SONG_PRESETS = {
    "None": {},

    # =====================================================
    # 1. POP / ALT / INDIE
    # =====================================================
    "Modern Pop": {
        "genre": "Modern Pop",
        "style": "Bright punchy synths, clean drums, catchy melodic vocals, polished mix",
        "tags": ["pop", "radio", "clean"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Alt Indie Dream": {
        "genre": "Indie Dream Pop",
        "style": "Soft reverb-heavy textures, floating vocals, nostalgic atmosphere",
        "tags": ["indie", "dreamy", "ambientpop"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Bedroom Pop": {
        "genre": "Bedroom Pop",
        "style": "Lo-fi warmth, intimate whispered vocals, soft synth pads",
        "tags": ["lofi", "indie", "soft"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },

    # =====================================================
    # 2. EDM / ELECTRONIC / DANCE
    # =====================================================
    "EDM Festival": {
        "genre": "EDM",
        "style": "Huge supersaws, emotional breakdowns, high-energy dance drop",
        "tags": ["edm", "dance", "festival"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Drum and Bass — Liquid": {
        "genre": "Liquid Drum and Bass",
        "style": "Fast but smooth rhythms, airy pads, deep emotional vocals",
        "tags": ["dnb", "liquid", "fast"],
        "vocal_gender": "mixed",
        "model": "chirp-v5",
    },
    "Future Bounce": {
        "genre": "Future Bounce",
        "style": "Bouncy basslines, chopped vocals, uplifting synths",
        "tags": ["bounce", "edm", "energetic"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Future Garage": {
        "genre": "Future Garage",
        "style": "Shuffling percussion, melancholy pads, lush emotional textures",
        "tags": ["garage", "chillstep", "ambient"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Hyperpop": {
        "genre": "Hyperpop",
        "style": "Glitchy bright tones, pitch-shifted vocals, chaotic energetic fun",
        "tags": ["hyperpop", "glitch", "experimental"],
        "vocal_gender": "mixed",
        "model": "chirp-v5",
    },
    "Synthwave Nightdrive": {
        "genre": "Synthwave",
        "style": "Retro analog synths, neon atmosphere, cinematic bass pulse",
        "tags": ["synthwave", "retro", "80s"],
        "vocal_gender": "male",
        "model": "chirp-v5",
    },

    # =====================================================
    # 3. ROCK / METAL
    # =====================================================
    "Alt Rock Drive": {
        "genre": "Alternative Rock",
        "style": "Punchy guitars, gritty emotional vocals, energetic groove",
        "tags": ["rock", "alt", "guitar"],
        "vocal_gender": "male",
        "model": "chirp-v5",
    },
    "Metalcore Heavy": {
        "genre": "Metalcore",
        "style": "Aggressive guitars, breakdowns, harsh/clean vocal blend",
        "tags": ["metalcore", "heavy", "breakdown"],
        "vocal_gender": "mixed",
        "model": "chirp-v5",
    },
    "Blues Rock Groove": {
        "genre": "Blues Rock",
        "style": "Warm overdriven guitars, soulful expressive vocal style",
        "tags": ["blues", "rock", "groove"],
        "vocal_gender": "male",
        "model": "chirp-v5",
    },

    # =====================================================
    # 4. HIP-HOP / RAP
    # =====================================================
    "Melodic Trap": {
        "genre": "Melodic Trap",
        "style": "Moody pads, autotuned emotional hooks, smooth rap-sung flow",
        "tags": ["trap", "melodic", "hiphop"],
        "vocal_gender": "male",
        "model": "chirp-v5",
    },
    "Boom Bap Classic": {
        "genre": "Boom Bap",
        "style": "Dusty drums, chopped soulful samples, rhythmic punchy delivery",
        "tags": ["boom bap", "hiphop", "retro"],
        "vocal_gender": "male",
        "model": "chirp-v5",
    },
    "UK Drill Minimal": {
        "genre": "Drill",
        "style": "Sliding 808s, cold atmospheric pads, aggressive rhythmic vocals",
        "tags": ["drill", "trap", "street"],
        "vocal_gender": "male",
        "model": "chirp-v5",
    },
    "Cloud Rap Ethereal": {
        "genre": "Cloud Rap",
        "style": "Dreamy reverb-heavy synths, drifting autotuned vocals, spacey vibe",
        "tags": ["cloud", "trap", "ambient"],
        "vocal_gender": "male",
        "model": "chirp-v5",
    },

    # =====================================================
    # 5. REGGAE / DANCEHALL / DUB
    # =====================================================
    "Reggae Roots": {
        "genre": "Reggae",
        "style": "Warm skanking guitars, relaxed groove, uplifting soulful vocals",
        "tags": ["reggae", "roots", "island"],
        "vocal_gender": "male",
        "model": "chirp-v5",
    },
    "Dancehall Modern": {
        "genre": "Dancehall",
        "style": "Snappy rhythms, tropical percussion, confident rhythmic vocals",
        "tags": ["dancehall", "caribbean", "island"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Dub Echo Space": {
        "genre": "Dub",
        "style": "Heavy bass, spaced-out echoes, deep hypnotic vocal fragments",
        "tags": ["dub", "reggae", "echo"],
        "vocal_gender": "male",
        "model": "chirp-v5",
    },

    # =====================================================
    # 6. INTERNATIONAL / WORLD
    # =====================================================
    "Afrobeats Chill": {
        "genre": "Afrobeats",
        "style": "Rhythmic percussion, warm guitars, upbeat harmonic progressions",
        "tags": ["afrobeat", "world", "tropical"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Afro Fusion Uptempo": {
        "genre": "Afro Fusion",
        "style": "Modern African pop blend, energetic percussion, joyful vocals",
        "tags": ["afrofusion", "world", "dance"],
        "vocal_gender": "male",
        "model": "chirp-v5",
    },
    "Bollywood Pop Fusion": {
        "genre": "Bollywood Pop",
        "style": "Vibrant melodic phrasing, cinematic percussion, expressive vocals",
        "tags": ["bollywood", "indian", "fusion"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Latin Salsa Pop": {
        "genre": "Salsa Pop",
        "style": "Bright brass, energetic percussion, dance-forward rhythms",
        "tags": ["salsa", "latin", "dance"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },

    # =====================================================
    # 7. AESTHETIC / RETRO / SPECIALTY
    # =====================================================
    "City Pop Retro": {
        "genre": "City Pop",
        "style": "Smooth nostalgic synths, funky basslines, soft warm vocals",
        "tags": ["citypop", "retro", "jpop"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Kawaii Cute Pop": {
        "genre": "Kawaii Pop",
        "style": "Sparkly cheerful synths, energetic cutesy vocals, glittery charm",
        "tags": ["kawaii", "anime", "cute"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Chiptune Gamewave": {
        "genre": "Chiptune",
        "style": "8-bit leads, arcade-style tones, playful energetic vocals",
        "tags": ["chiptune", "8bit", "videogame"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },

    # =====================================================
    # 8. ACOUSTIC / FOLK / FANTASY
    # =====================================================
    "Acoustic Folk": {
        "genre": "Folk",
        "style": "Warm acoustic guitars, storytelling vocals, earthy natural tone",
        "tags": ["folk", "acoustic", "soft"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Celtic Fantasy": {
        "genre": "Celtic Folk",
        "style": "Flutes, harps, mystical harmonies, ethereal airy vocals",
        "tags": ["celtic", "fantasy", "mystical"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },

    # =====================================================
    # 9. CINEMATIC / AMBIENT
    # =====================================================
    "Cinematic Trailer": {
        "genre": "Cinematic",
        "style": "Epic percussion, soaring strings, emotional dynamic vocals",
        "tags": ["cinematic", "epic", "trailer"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Dark Ambient": {
        "genre": "Ambient",
        "style": "Deep drones, shadowy textures, slow atmospheric vocals",
        "tags": ["ambient", "dark", "texture"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Space Ambient": {
        "genre": "Space Ambient",
        "style": "Floating pads, cosmic tone, ethereal drifting vocals",
        "tags": ["ambient", "space", "cosmic"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
    "Meditation Flow": {
        "genre": "Meditation",
        "style": "Slow gentle drones, soft breathy layers, calming minimalism",
        "tags": ["meditation", "calm", "wellness"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },

    # =====================================================
    # 10. VOCAL-ONLY / ACAPELLA
    # =====================================================
    "Acapella": {
        "genre": "Acapella",
        "style": "Pure isolated vocals, light reverb, rich harmonies, no instrumental backing",
        "tags": ["acapella", "vocals", "no_instruments"],
        "vocal_gender": "mixed",
        "model": "chirp-v5",
    },
    "Choir Cinematic": {
        "genre": "Cinematic Choir",
        "style": "Layered choral harmonies, cathedral ambience, powerful emotional vocal swells",
        "tags": ["choir", "cinematic", "choral", "epic"],
        "vocal_gender": "mixed",
        "model": "chirp-v5",
    },
    "Vocal Beatbox": {
        "genre": "Beatbox",
        "style": "Percussive vocal sounds, rhythmic pops and kicks, tight human-made grooves",
        "tags": ["beatbox", "vocal percussion", "rhythmic"],
        "vocal_gender": "male",
        "model": "chirp-v5",
    },
    "Group Harmony Pop": {
        "genre": "Harmony Pop",
        "style": "Multi-singer harmonies, bright layered vocals, uplifting pop choir energy",
        "tags": ["harmonies", "group vocals", "pop"],
        "vocal_gender": "mixed",
        "model": "chirp-v5",
    },
    "Whisper Vocals": {
        "genre": "Ambient Pop",
        "style": "Soft intimate whispered vocals, breathy textures, close-miked emotional tone",
        "tags": ["whisper", "soft", "breathy", "intimate"],
        "vocal_gender": "female",
        "model": "chirp-v5",
    },
}
