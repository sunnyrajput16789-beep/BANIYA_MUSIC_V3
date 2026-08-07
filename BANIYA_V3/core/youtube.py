import os
import re
from typing import Union

import aiohttp
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.aio import VideosSearch, Playlist

import config
from BANIYA_V3.core.dir import DOWNLOAD_DIR
from BANIYA_V3.helpers import Media

API_URL = getattr(config, "API_URL", None) or os.environ.get("SHRUTI_API_URL", "https://api.shrutibots.site")
VIDEO_API_URL = getattr(config, "VIDEO_API_URL", None) or API_URL
API_KEY = getattr(config, "API_KEY", None) or os.environ.get("SHRUTI_API_KEY", "ShrutiBotskrapUNcnsGRSgg1eawKn")


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


async def download_song(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            endpoints = [
                (f"{API_URL}/download", {"url": video_id, "type": "audio", "api_key": API_KEY}),
                (f"{API_URL}/song/{video_id}?api={API_KEY}", {})
            ]
            for url, params in endpoints:
                try:
                    async with session.get(
                        url,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=300)
                    ) as resp:
                        if resp.status == 200:
                            if "application/json" in resp.content_type:
                                data = await resp.json()
                                dl_link = data.get("link") or data.get("download_url") or data.get("url")
                                if dl_link:
                                    async with session.get(dl_link) as dl_resp:
                                        if dl_resp.status == 200:
                                            with open(file_path, "wb") as f:
                                                async for chunk in dl_resp.content.iter_chunked(131072):
                                                    f.write(chunk)
                                            break
                            else:
                                with open(file_path, "wb") as f:
                                    async for chunk in resp.content.iter_chunked(131072):
                                        f.write(chunk)
                                break
                except Exception:
                    continue
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return None


async def download_video(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    v_base = VIDEO_API_URL or API_URL
    try:
        async with aiohttp.ClientSession() as session:
            endpoints = [
                (f"{v_base}/download", {"url": video_id, "type": "video", "api_key": API_KEY}),
                (f"{v_base}/video/{video_id}?api={API_KEY}", {})
            ]
            for url, params in endpoints:
                try:
                    async with session.get(
                        url,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=600)
                    ) as resp:
                        if resp.status == 200:
                            if "application/json" in resp.content_type:
                                data = await resp.json()
                                dl_link = data.get("link") or data.get("download_url") or data.get("url")
                                if dl_link:
                                    async with session.get(dl_link) as dl_resp:
                                        if dl_resp.status == 200:
                                            with open(file_path, "wb") as f:
                                                async for chunk in dl_resp.content.iter_chunked(131072):
                                                    f.write(chunk)
                                            break
                            else:
                                with open(file_path, "wb") as f:
                                    async for chunk in resp.content.iter_chunked(131072):
                                        f.write(chunk)
                                break
                except Exception:
                    continue
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return None


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def valid(self, link: str) -> bool:
        """True if `link` is a YouTube URL (used to tell a YT link apart from a raw stream/m3u8 link)."""
        return bool(link) and bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]
            

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, limit, user_id, link: str, video: bool = False) -> list:
        """Resolve a YouTube playlist link into a list of Media objects (called as
        yt.playlist(config.PLAYLIST_LIMIT, mention, url, video))."""
        if "&" in link:
            link = link.split("&")[0]
        try:
            plist = await Playlist.get(link)
        except Exception:
            return []
        videos = (plist.get("videos") or [])[: int(limit)]
        tracks = []
        for data in videos:
            if not data:
                continue
            vidid = data.get("id")
            if not vidid:
                continue
            duration_min = data.get("duration")
            tracks.append(
                Media(
                    id=vidid,
                    duration=duration_min or "0:00",
                    duration_sec=int(time_to_seconds(duration_min)) if duration_min else 0,
                    title=data.get("title"),
                    url=data.get("link") or (self.base + vidid),
                    user=user_id,
                    video=video,
                )
            )
        return tracks

    async def search(self, query: str, message_id: int = 0, video: bool = False) -> Union["Media", None]:
        """Resolve a search query or a YouTube link into a Media object (metadata only,
        not downloaded yet). Called as yt.search(query_or_url, sent.id, video=video)."""
        if not query:
            return None
        try:
            track_details, vidid = await self.track(query)
        except Exception:
            return None
        if not vidid:
            return None
        duration_min = track_details.get("duration_min")
        return Media(
            id=vidid,
            duration=duration_min or "0:00",
            duration_sec=int(time_to_seconds(duration_min)) if duration_min else 0,
            title=track_details.get("title"),
            url=track_details.get("link") or (self.base + vidid),
            message_id=message_id,
            video=video,
        )

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    if "dash" not in str(format["format"]).lower():
                        formats_available.append(
                            {
                                "format": format["format"],
                                "filesize": format.get("filesize"),
                                "format_id": format["format_id"],
                                "ext": format["ext"],
                                "format_note": format["format_note"],
                                "yturl": link,
                            }
                        )
                except Exception:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(self, videoid: str, video: bool = False) -> Union[str, None]:
        """Download the track/video for a YouTube video id via the Shruti API and return
        the local file path (or None on failure). Called as
        yt.download(file.id, video=video)."""
        if not videoid:
            return None
        try:
            if video:
                return await download_video(videoid)
            return await download_song(videoid)
        except Exception:
            return None

    async def save_cookies(self, urls) -> None:
        """No-op: downloads go through the Shruti API, so YouTube cookies aren't needed.
        Kept so `if config.COOKIES_URL: await yt.save_cookies(...)` in __main__.py doesn't crash."""
        return None


YouTube = YouTubeAPI()
