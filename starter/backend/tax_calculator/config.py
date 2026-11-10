import os


class Config:
    TAX_API_URL = os.environ.get("TAX_API_URL")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
