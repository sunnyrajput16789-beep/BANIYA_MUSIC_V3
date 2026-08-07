# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import re
import yt_dlp
import random
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, List, Union

from py_yt import Playlist, VideosSearch
from youtubesearchpython import VideosSearch as NewVideosSearch

from BANIYA_V3 import config, logger
from BANIYA_V3.helpers import Track, utils

# Fast Download API
API_URL = "https://shrutibots.site"
DOWNLOAD_DIR = "downloads"

# Create download directory if not exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "BANIYA_V3/cookies"  # Changed from "anony/cookies"
        self.warned = False
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

    def get_cookies(self) -> Optional[str]:
        """Get random cookie file path"""
        if not self.checked:
            if os.path.exists(self.cookie_dir):
                for file in os.listdir(self.cookie_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(f"{self.cookie_dir}/{file}")
            self.checked = True
        return random.choice(self.cookies) if self.cookies else None

    async def save_cookies(self, urls: List[str]) -> None:
        """Save cookies from URLs"""
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
                            cookie_path = f"{self.cookie_dir}/{name}.txt"
                            with open(cookie_path, "wb") as fw:
                                fw.write(content)
                            logger.info(f"Cookie saved: {cookie_path}")
                except Exception as e:
                    logger.error(f"Cookie Save Error for {url}: {e}")
        
        logger.info(f"Cookies updated in {self.cookie_dir}.")

    async def download_from_api(self, video_id: str, video: bool) -> Optional[str]:
        """Bypasses YouTube blocking using external API"""
        mode = "video" if video else "audio"
        ext = "mp4" if video else "mp3"
        file_path = f"{DOWNLOAD_DIR}/{video_id}.{ext}"
        
        # Check if already downloaded
        if Path(file_path).exists() and Path(file_path).stat().st_size > 0:
            return file_path
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get download token
                async with session.get(
                    f"{API_URL}/download", 
                    params={"url": video_id, "type": mode}, 
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        return None
                    
                    data = await resp.json()
                    token = data.get("download_token")
                    
                    if not token:
                        return None
                    
                    # Download file
                    stream_url = f"{API_URL}/stream/{video_id}?type={mode}&token={token}"
                    
                    async with session.get(
                        stream_url, 
                        timeout=aiohttp.ClientTimeout(total=300)
                    ) as fresp:
                        if fresp.status in [200, 302]:
                            # Handle redirects
                            if fresp.status == 302:
                                redirect_url = fresp.headers.get('Location')
                                if not redirect_url:
                                    return None
                                async with session.get(redirect_url) as redir_resp:
                                    if redir_resp.status != 200:
                                        return None
                                    with open(file_path, "wb") as f:
                                        async for chunk in redir_resp.content.iter_chunked(16384):
                                            f.write(chunk)
                            else:
                                with open(file_path, "wb") as f:
                                    async for chunk in fresp.content.iter_chunked(16384):
                                        f.write(chunk)
                            
                            # Verify download
                            if Path(file_path).exists() and Path(file_path).stat().st_size > 0:
                                logger.info(f"Downloaded via API: {file_path}")
                                return file_path
        except Exception as e:
            logger.error(f"API download error for {video_id}: {e}")
        
        return None

    async def download_with_ytdlp(self, video_id: str, video: bool = False) -> Optional[str]:
        """Download using yt-dlp with Android spoofing"""
        url = self.base + video_id
        ext = "mp4" if video else "mp3"
        filename = f"{DOWNLOAD_DIR}/{video_id}.{ext}"

        # Check if already exists
        if Path(filename).exists() and Path(filename).stat().st_size > 0:
            return filename

        cookie = self.get_cookies()
        
        # yt-dlp options with Android spoofing to bypass blocking
        ydl_opts = {
            "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "ignoreerrors": True,
            "cookiefile": cookie,
            # Android Spoofing - Important for bypassing blocks
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                    "player_skip": ["webpage", "configs"],
                    "skip": ["dash", "hls"],
                }
            }
        }

        if video:
            ydl_opts["format"] = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"
            ydl_opts["merge_output_format"] = "mp4"
        else:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        def _download():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                    
                    # Find the downloaded file
                    if video:
                        final_file = f"{DOWNLOAD_DIR}/{video_id}.mp4"
                    else:
                        final_file = f"{DOWNLOAD_DIR}/{video_id}.mp3"
                    
                    if Path(final_file).exists() and Path(final_file).stat().st_size > 0:
                        return final_file
                    return None
            except Exception as e:
                logger.error(f"yt-dlp download failed for {video_id}: {e}")
                return None

        # Run download in thread pool
        return await asyncio.to_thread(_download)

    async def download(self, video_id: str, video: bool = False) -> Optional[str]:
        """
        Download video/audio from YouTube with multiple fallback methods
        
        Args:
            video_id: YouTube video ID
            video: True for video download, False for audio only
        
        Returns:
            Path to downloaded file or None if failed
        """
        # Method 1: External API (Fastest, bypasses blocks)
        api_file = await self.download_from_api(video_id, video)
        if api_file:
            return api_file

        # Method 2: yt-dlp with Android spoofing
        ytdlp_file = await self.download_with_ytdlp(video_id, video)
        if ytdlp_file:
            return ytdlp_file

        logger.error(f"All download methods failed for {video_id}")
        return None

    async def search(self, query: str, m_id: int, video: bool = False) -> Optional[Track]:
        """Search for a single video/audio"""
        try:
            # Try with new version first
            try:
                search = NewVideosSearch(query, limit=1)
                results = await search.next()
            except:
                # Fallback to old version
                search = VideosSearch(query, limit=1)
                results = await search.next()
            
            if results and results.get("result"):
                data = results["result"][0]
                
                # Get thumbnail URL
                thumbnails = data.get("thumbnails", [])
                thumbnail = thumbnails[-1].get("url", "").split("?")[0] if thumbnails else ""
                
                # Get view count
                view_count = data.get("viewCount", {})
                if isinstance(view_count, dict):
                    view_count = view_count.get("short", "")
                
                return Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration", "0:00"),
                    duration_sec=utils.to_seconds(data.get("duration", "0:00")),
                    message_id=m_id,
                    title=data.get("title", "Unknown")[:50],  # Increased limit
                    thumbnail=thumbnail,
                    url=data.get("link", ""),
                    view_count=str(view_count),
                    video=video,
                )
        except Exception as e:
            logger.error(f"Search error for '{query}': {e}")
        
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> List[Track]:
        """Get tracks from a YouTube playlist"""
        tracks = []
        
        try:
            # Clean URL
            if "&" in url:
                url = url.split("&")[0]
            
            plist = await Playlist.get(url)
            videos = plist.get("videos", [])
            
            for data in videos[:limit]:
                if not data:
                    continue
                
                # Get thumbnail
                thumbnails = data.get("thumbnails", [])
                thumbnail = thumbnails[-1].get("url", "").split("?")[0] if thumbnails else ""
                
                # Get video link without playlist
                video_url = data.get("link", "")
                if "&list=" in video_url:
                    video_url = video_url.split("&list=")[0]
                
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration", "0:00"),
                    duration_sec=utils.to_seconds(data.get("duration", "0:00")),
                    title=data.get("title", "Unknown")[:50],
                    thumbnail=thumbnail,
                    url=video_url,
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
                
        except Exception as e:
            logger.error(f"Playlist error for {url}: {e}")
        
        return tracks

    async def get_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        match = self.regex.search(url)
        if match:
            return match.group(5)  # The video/playlist ID
        return None

    async def is_playlist(self, url: str) -> bool:
        """Check if URL is a playlist"""
        match = self.regex.search(url)
        if match and match.group(3) and "playlist" in match.group(3):
            return True
        return False


# Create global instance
youtube = YouTube()
