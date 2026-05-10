# run.py

import os
import sys
import subprocess
import time


def main():
    """
    Convenience launcher: `python run.py`
    will internally execute: `streamlit run app.py`.
    Gracefully handles Ctrl+C interruptions.
    """
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    env = os.environ.copy()

    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Streamlit…")
        time.sleep(0.2)
    finally:
        print("✅ Clean exit.\n")


if __name__ == "__main__":
    main()
