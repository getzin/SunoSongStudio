# 🎵 SunoSongStudio

A full-featured web application for generating original music and lyrics using AI. Built with **Streamlit**, **OpenAI**, and the **Suno API**, SunoSongStudio combines powerful language models with music generation capabilities to create unique songs.

---

## ✨ Features

### 🎸 Core Functionality
- **Song Generation** – Create original music tracks using the Suno API
- **Lyrics Generation** – Generate creative lyrics with OpenAI, with customizable styles (Base, Cat, Christmas)
- **Unified Workflow** – Generate lyrics and songs seamlessly in one interface
- **History Tracking** – Keep track of all generated songs and lyrics with full metadata

### 👤 User Management
- **Authentication** – Secure login and registration with bcrypt hashing
- **Multi-user Support** – Each user has isolated song/lyrics libraries and API key settings
- **API Key Management** – Securely store OpenAI and Suno API keys per user

### 🛠️ Advanced Features
- **Song Status Tracking** – Monitor song generation progress (queued, generating, completed, failed)
- **Batch Operations** – Generate multiple songs at once
- **Custom Themes** – Dark/light mode support
- **Debug Tools** – Developer utilities for testing and troubleshooting
- **Configurable Settings** – Customize lyrics length, generation modes, and more

---

## 📋 Requirements

- **Python 3.8+**
- **Suno API Key** (get it from [acedata.cloud](https://acedata.cloud))
- **OpenAI API Key** (get it from [openai.com](https://platform.openai.com))

---

## 🚀 Quick Start

### 1. Installation

Clone the repository and install dependencies:

```bash
cd SunoSongStudio
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the project root:

```env
ADMIN_EMAIL=your_email@example.com
ADMIN_PASSWORD=your_secure_password
ENABLE_DEBUG_TOOLS=0
```

### 3. Run the Application

**Option A – Using the convenience launcher:**
```bash
python run.py
```

**Option B – Direct Streamlit:**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📚 Project Structure

```
SunoSongStudio/
├── app.py                          # Main Streamlit application entry point
├── constants.py                    # Configuration and constants
├── requirements.txt                # Python dependencies
├── run.py                          # Convenience launcher script
│
├── app_pages/                      # Streamlit multi-page app pages
│   ├── dashboard.py               # Overview and statistics dashboard
│   ├── songs_generate.py          # Song generation interface
│   ├── songs_history.py           # View and manage generated songs
│   ├── lyrics_generate.py         # Lyrics generation interface
│   ├── lyrics_history.py          # View and manage generated lyrics
│   ├── settings.py                # User settings and API key management
│   ├── debug_tools.py             # Developer utilities
│   └── (more pages...)
│
├── backend/                        # Backend business logic
│   ├── db.py                      # Database initialization and migrations
│   ├── models/
│   │   ├── users.py              # User data models
│   │   ├── songs.py              # Song data models
│   │   └── lyrics.py             # Lyrics data models
│   └── services/
│       ├── auth_service.py       # Authentication logic
│       ├── suno_service.py       # Suno API integration
│       ├── openai_service.py     # OpenAI integration
│       ├── lyrics_service.py     # Lyrics generation logic
│       ├── suno_payload_builder.py # Suno API request builder
│       └── suno_polling.py       # Song status polling
│
├── shared/                         # Shared utilities
│   ├── layout.py                 # UI component helpers
│   ├── session.py                # Session state management
│   ├── theme.py                  # Theme and styling
│   └── utils.py                  # General utilities
│
├── assets/                         # Static assets
│   ├── json/                     # OpenAI prompt templates
│   │   ├── openai_base.json
│   │   ├── openai_cat.json
│   │   └── openai_xmas.json
│   └── prompts/                  # Metaprompts for different styles
│       ├── metaprompt_base.md
│       ├── metaprompt_cat.md
│       └── metaprompt_xmas.md
│
└── data/                          # Generated content (gitignored)
    ├── app.db                    # SQLite database
    ├── audio/                    # Generated audio files
    ├── lyrics/                   # Generated lyrics
    └── video/                    # Generated videos
```

---

## 🔑 API Keys

The application requires two external API keys:

### OpenAI API Key
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create an API key in the dashboard
3. Add it in the app's **Settings** page under "OpenAI API Key"

### Suno API Key
1. Visit [acedata.cloud](https://acedata.cloud) and sign up
2. Get your API key from your account
3. Add it in the app's **Settings** page under "Suno API Key"

---

## 📖 Usage Guide

### Generating Lyrics
1. Navigate to **Lyrics Generate**
2. Enter a topic/theme for your lyrics
3. Select a generation style (Base, Cat, Christmas, etc.)
4. Choose lyrics length (min 20, max 800 words)
5. Click "Generate Lyrics"
6. View and manage all lyrics in **Lyrics History**

### Generating Songs
1. Navigate to **Songs Generate**
2. Either:
   - **Enter custom lyrics** in the text area, OR
   - **Select previously generated lyrics** from the dropdown
3. Choose song style and mood
4. Click "Generate Song"
5. The song will be queued with Suno and tracked in **Songs History**
6. Monitor progress in the **Dashboard**

### Checking Progress
- The **Dashboard** shows real-time statistics:
  - Total songs/lyrics generated
  - Queued, generating, completed, and failed counts
  - Recent activity

### Managing API Keys
1. Go to **Settings**
2. Enter your OpenAI and Suno API keys
3. Keys are securely hashed before storage

---

## ⚙️ Configuration

Key settings in `constants.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `LYRICS_MIN_WORDS` | 20 | Minimum lyrics length |
| `LYRICS_MAX_WORDS` | 800 | Maximum lyrics length |
| `ENABLE_DEBUG_TOOLS` | False | Show debug utilities page |
| `ADMIN_EMAIL` | q@q.com | Default admin account email |
| `ADMIN_PASSWORD` | 123 | Default admin account password |

---

## 🗄️ Database

The app uses **SQLite** (`app.db`) to store:
- User accounts and authentication
- Generated songs and their metadata
- Generated lyrics and their metadata
- API keys (hashed)
- Generation history

Database is automatically initialized on first run.

---

## 🔐 Security

- **Passwords**: Hashed with bcrypt
- **API Keys**: Securely stored in database (hashed)
- **Authentication**: Session-based with Streamlit's state management
- **Per-user Isolation**: Each user sees only their own content

---

## 🛠️ Development

### Adding New Generation Modes
1. Create a new prompt template in `assets/prompts/metaprompt_*.md`
2. Create a JSON template in `assets/json/openai_*.json`
3. Reference it in `openai_service.py`

### Extending the Database
1. Modify the models in `backend/models/`
2. Create a migration in `backend/db.py`
3. Run the migration with `python -c "from backend.db import run_migrations; run_migrations()"`

### Custom Pages
Add new Streamlit pages in `app_pages/` and they'll automatically appear in the sidebar.

---

## 📦 Dependencies

- **streamlit** – Web UI framework
- **python-dotenv** – Environment variable management
- **bcrypt** – Password hashing
- **openai** – OpenAI API client (v0.28.1)
- **requests** – HTTP requests for Suno API

---

## 🐛 Troubleshooting

### Songs not generating?
- Verify Suno API key is correct in Settings
- Check remaining Suno API quota
- Review logs in the `logs/` directory

### Lyrics generation fails?
- Verify OpenAI API key is valid
- Ensure you have API credits available
- Check that lyrics length is between 20-800 words

### Authentication issues?
- Clear browser cookies and cache
- Restart Streamlit app
- Check default admin credentials in `constants.py`

---

## 📝 License

This project is provided as-is for personal and educational use.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs and issues
- Suggest new features
- Submit pull requests with improvements

---

## 📞 Support

For issues with:
- **Suno API** – Visit [acedata.cloud](https://acedata.cloud) support
- **OpenAI API** – Visit [platform.openai.com/help](https://platform.openai.com/help)
- **Streamlit** – Visit [docs.streamlit.io](https://docs.streamlit.io)

---

**Happy Song Creating! 🎵✨**
