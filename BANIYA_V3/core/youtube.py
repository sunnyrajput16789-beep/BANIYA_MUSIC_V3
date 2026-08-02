import os
import re
import yt_dlp
import random
import asyncio
import aiohttp
from pathlib import Path

from py_yt import Playlist, VideosSearch
from BANIYA_V3 import logger
from BANIYA_V3.helpers import Track, utils

# Fast Download API
API_URL = "ShrutiBotsj2rEdiXb50MK8hnK5xvy"

class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "anony/cookies"
        self.warned = False
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

    def get_cookies(self):
        if not self.checked:
            if os.path.exists(self.cookie_dir):
                for file in os.listdir(self.cookie_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(f"{self.cookie_dir}/{file}")
            self.checked = True
        return random.choice(self.cookies) if self.cookies else None

    async def save_cookies(self, urls: list[str]) -> None:
        if not os.path.exists(self.cookie_dir):
            os.makedirs(self.cookie_dir)
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    name = url.split("/")[-1]
                    link = "https://batbin.me/raw/" + name
                    async with session.get(link) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            with open(f"{self.cookie_dir}/{name}.txt", "wb") as fw:
                                fw.write(content)
                except Exception as e:
                    logger.error(f"Cookie Save Error: {e}")
        logger.info(f"Cookies updated in {self.cookie_dir}.")

    async def download_from_api(self, video_id: str, video: bool) -> str | None:
        """Bypasses YouTube blocking using external API"""
        mode = "video" if video else "audio"
        ext = "mp4" if video else "mp3"
        file_path = f"downloads/{video_id}.{ext}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/download", params={"url": video_id, "type": mode}, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        token = data.get("download_token")
                        if token:
                            stream_url = f"{API_URL}/stream/{video_id}?type={mode}&token={token}"
                            async with session.get(stream_url, timeout=300) as fresp:
                                if fresp.status in [200, 302]:
                                    with open(file_path, "wb") as f:
                                        async for chunk in fresp.content.iter_chunked(16384):
                                            f.write(chunk)
                                    return file_path
        except:
            pass
        return None

    async def download(self, video_id: str, video: bool = False) -> str | None:
        url = self.base + video_id
        ext = "mp4" if video else "webm"
        filename = f"downloads/{video_id}.{ext}"

        if Path(filename).exists():
            return filename

        # 1. First attempt: External API (Bypass YouTube blocking)
        api_file = await self.download_from_api(video_id, video)
        if api_file:
            return api_file

        # 2. Second attempt: yt-dlp with Android Spoofing (Harder to block)
        cookie = self.get_cookies()
        ydl_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "cookiefile": cookie,
            # Android Spoofing
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                    "player_skip": ["webpage", "configs"],
                }
            }
        }

        if video:
            ydl_opts["format"] = "bestvideo[height<=720]+bestaudio/best"
            ydl_opts["merge_output_format"] = "mp4"
        else:
            ydl_opts["format"] = "bestaudio/best"

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                    return filename
                except Exception as e:
                    logger.error(f"yt-dlp failed: {e}")
                    return None

        return await asyncio.to_thread(_download)

    # Search aur Playlist functions pehle jaise hi rahenge
    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        try:
            _search = VideosSearch(query, limit=1)
            results = await _search.next()
            if results and results["result"]:
                data = results["result"][0]
                return Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name"),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    message_id=m_id,
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                    url=data.get("link"),
                    view_count=data.get("viewCount", {}).get("short"),
                    video=video,
                )
        except:
            return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails")[-1].get("url").split("?")[0],
                    url=data.get("link").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except:
            pass
        return tracks
        
