from pathlib import Path

from dotenv import load_dotenv


def load_env():
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
