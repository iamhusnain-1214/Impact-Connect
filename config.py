import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env using a path relative to THIS file, not the current working directory.
# This matters because VS Code's "Run" button (and some other launchers) execute
# the script with the working directory set to wherever the workspace root is,
# not necessarily the folder app.py lives in - so a plain load_dotenv() call can
# silently fail to find .env and every setting below falls back to "".
#
# On Vercel there is no .env file at all - env vars are injected directly into
# the process by the platform (set in Project Settings -> Environment
# Variables), so load_dotenv() here just becomes a harmless no-op in prod.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

_DEV_SECRET = "dev_secret_change_me"


class Config:
    # Defaults to "development" so local `python app.py` never trips the
    # secret-key check below. Vercel deployment sets FLASK_ENV=production
    # explicitly (see vercel.json / README) so the check is real in prod.
    ENV = os.getenv("FLASK_ENV", "development")
    IS_PRODUCTION = ENV == "production"

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "impactconnect")

    # Hosted MySQL (PlanetScale, TiDB Cloud, Aiven, Railway) requires or
    # strongly prefers TLS. Default ON; set DB_USE_SSL=false for a plain
    # local MySQL install that has no SSL configured.
    DB_USE_SSL = os.getenv("DB_USE_SSL", "true").lower() == "true"

    # Small on purpose - see db/connection.py for why this matters on a
    # serverless target like Vercel.
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "3"))

    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", _DEV_SECRET)

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()


if Config.IS_PRODUCTION and Config.SECRET_KEY == _DEV_SECRET:
    # Fail loudly and immediately rather than silently shipping a public,
    # guessable session-signing key to production. If this fires on Vercel,
    # it means FLASK_SECRET_KEY was never set in Project Settings ->
    # Environment Variables.
    raise RuntimeError(
        "FLASK_SECRET_KEY is not set. Refusing to start in production with "
        "the default dev secret key - this would let anyone forge session "
        "cookies (including admin sessions). Set FLASK_SECRET_KEY in your "
        "environment (e.g. Vercel Project Settings -> Environment Variables)."
    )

if not Config.GROQ_API_KEY:
    print(
        f"[WARNING] GROQ_API_KEY is empty. Looked for .env at: {BASE_DIR / '.env'}\n"
        f"          The AI recommendation feature (/api/ai/recommend) will fail until this is set.\n"
        f"          Check that .env exists at that exact path and contains GROQ_API_KEY=...\n"
        f"          Get a free key at https://console.groq.com/keys"
    )