"""
config.py — PulseHR Application Configuration
Supports both JSON-file (demo) and MySQL (production) modes.
"""
import os


class Config:
    # ── Flask Core ────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dd2897e8fae2c89db17817775b2d8873e9b868508803935fe8b33ddaccd3fd80')
    DEBUG      = os.environ.get('DEBUG', 'True').lower() == 'true'

    # ── MySQL Credentials ─────────────────────────────────────────────────────
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'localhost')
    MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', '3306'))
    MYSQL_USER     = os.environ.get('MYSQL_USER',     'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'Root12345')
    MYSQL_DB       = os.environ.get('MYSQL_DB',       'pulsehr')

    # ── SQLAlchemy — URI built from individual env vars so it's always fresh ──
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.environ.get('MYSQL_USER','root')}"
        f":{os.environ.get('MYSQL_PASSWORD','Root12345')}"
        f"@{os.environ.get('MYSQL_HOST','localhost')}"
        f":{os.environ.get('MYSQL_PORT','3306')}"
        f"/{os.environ.get('MYSQL_DB','pulsehr')}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO                = False   # set True to log SQL

    # ── Session ───────────────────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY   = True
    SESSION_COOKIE_SAMESITE   = 'Lax'
    PERMANENT_SESSION_LIFETIME = 1800    # 30 minutes

    # ── App-level ─────────────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB upload limit
