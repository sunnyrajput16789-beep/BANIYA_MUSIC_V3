from os import getenv
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        # 🔑 Basic Credentials
        self.API_ID = int(getenv("API_ID", 0))
        self.API_HASH = getenv("API_HASH")
        self.BOT_TOKEN = getenv("BOT_TOKEN")

        # 🗄️ Database
        self.MONGO_URL = getenv("MONGO_URL")
        self.DB_URI = self.MONGO_URL   # ✅ FINAL FIX (IMPORTANT)
        self.DB_NAME = getenv("DB_NAME", "baniya_v3")

        # 👑 Owner & Logs
        self.LOGGER_ID = int(getenv("LOGGER_ID", 0))
        self.OWNER_ID = int(getenv("OWNER_ID", 0))

        # 🎵 Limits
        self.DURATION_LIMIT = int(getenv("DURATION_LIMIT", 60)) * 60
        self.QUEUE_LIMIT = int(getenv("QUEUE_LIMIT", 20))
        self.PLAYLIST_LIMIT = int(getenv("PLAYLIST_LIMIT", 20))

        # 🤖 Assistant Sessions
        self.SESSION1 = getenv("SESSION", None)
        self.SESSION2 = getenv("SESSION2", None)
        self.SESSION3 = getenv("SESSION3", None)

        # 📢 Support Links
        self.SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/who_0003")
        self.SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/who_0003")

        # ⚙️ Features
        self.AUTO_LEAVE: bool = getenv("AUTO_LEAVE", "False").lower() == "true"
        self.AUTO_END: bool = getenv("AUTO_END", "False").lower() == "true"
        self.THUMB_GEN: bool = getenv("THUMB_GEN", "True").lower() == "true"
        self.VIDEO_PLAY: bool = getenv("VIDEO_PLAY", "True").lower() == "true"

        # 🌐 Language
        self.LANG_CODE = getenv("LANG_CODE", "en")

        # 🍪 Cookies
        self.COOKIES_URL = [
            url for url in getenv("COOKIES_URL", "").split(" ")
            if url and "batbin.me" in url
        ]

        # 🖼️ Images
        self.DEFAULT_THUMB = getenv("DEFAULT_THUMB", "https://i.ibb.co/G3JX0JJS/x.jpg")
        self.PING_IMG = getenv("PING_IMG", "https://i.ibb.co/G3JX0JJS/x.jpg")
        self.START_IMG = getenv("START_IMG", "https://i.ibb.co/G3JX0JJS/x.jpg")

    def check(self):
        missing = [
            var
            for var in [
                "API_ID",
                "API_HASH",
                "BOT_TOKEN",
                "MONGO_URL",
                "DB_NAME",
                "LOGGER_ID",
                "OWNER_ID",
                "SESSION1"
            ]
            if not getattr(self, var)
        ]
        if missing:
            raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")

# Create config instance
config = Config()
config.check()
