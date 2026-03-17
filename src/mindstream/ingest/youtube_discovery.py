from __future__ import annotations

import re
import sys
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as ET

import requests

from mindstream.storage.models import DiscoveryResult, VideoMetadata

YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
YT_NAMESPACE = "http://www.youtube.com/xml/schemas/2015"
NAMESPACES = {"atom": ATOM_NAMESPACE, "yt": YT_NAMESPACE}
REQUEST_TIMEOUT_SECONDS = 15
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}
CHANNEL_ID_PATTERN = re.compile(r'"channelId":"(UC[A-Za-z0-9_-]+)"')
EXTERNAL_ID_PATTERN = re.compile(r'"externalId":"(UC[A-Za-z0-9_-]+)"')
CANONICAL_CHANNEL_PATTERN = re.compile(r'(?:https://www\.youtube\.com|/channel/)/channel/(UC[A-Za-z0-9_-]+)')
CANONICAL_CHANNEL_ABSOLUTE_PATTERN = re.compile(r'https://www\.youtube\.com/channel/(UC[A-Za-z0-9_-]+)')
CANONICAL_CHANNEL_RELATIVE_PATTERN = re.compile(r'/channel/(UC[A-Za-z0-9_-]+)')
META_CHANNEL_ID_PATTERN = re.compile(
    r'<meta[^>]*itemprop=["\']channelId["\'][^>]*content=["\'](UC[A-Za-z0-9_-]+)["\']',
    re.IGNORECASE,
)
OG_TITLE_PATTERN = re.compile(
    r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
DATE_PUBLISHED_PATTERN = re.compile(
    r'<meta[^>]*itemprop=["\']datePublished["\'][^>]*content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def read_channel_inputs(path: str) -> list[str]:
    lines: list[str] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            lines.append(line)
    return lines


def extract_channel_id_from_html(html: str) -> str | None:
    match = CHANNEL_ID_PATTERN.search(html)
    if match:
        print("Matched channelId")
        return match.group(1)

    match = EXTERNAL_ID_PATTERN.search(html)
    if match:
        print("Matched externalId")
        return match.group(1)

    match = CANONICAL_CHANNEL_ABSOLUTE_PATTERN.search(html)
    if not match:
        match = CANONICAL_CHANNEL_RELATIVE_PATTERN.search(html)
    if match:
        print("Matched canonical channel URL")
        return match.group(1)

    match = META_CHANNEL_ID_PATTERN.search(html)
    if match:
        print("Matched meta channelId")
        return match.group(1)

    return None


def resolve_channel_id(url: str) -> str | None:
    print(f"Resolving channel id from: {url}")
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) >= 2 and path_parts[0] == "channel" and path_parts[1].startswith("UC"):
        print(f"Resolved channel id: {path_parts[1]}")
        return path_parts[1]

    try:
        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        print(f"Response status code: {response.status_code}")
        print(f"Final response URL: {response.url}")
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to resolve channel id for source: {url}")
        print(f"Resolution error: {exc}")
        return None

    channel_id = extract_channel_id_from_html(response.text)
    if channel_id:
        print(f"Resolved channel id: {channel_id}")
        return channel_id

    print(f"Failed to resolve channel id for source: {url}")
    return None


def _extract_video_id_from_entry(entry: ET.Element) -> str | None:
    video_id = entry.findtext("yt:videoId", default="", namespaces=NAMESPACES)
    if video_id:
        return video_id.strip()

    entry_id = entry.findtext(f"{{{ATOM_NAMESPACE}}}id", default="")
    if not entry_id:
        entry_id = entry.findtext("atom:id", default="", namespaces=NAMESPACES)
    if not entry_id:
        return None

    return entry_id.rsplit(":", 1)[-1].strip() or None


def fetch_channel_videos(channel_id: str, max_results: int) -> list[VideoMetadata]:
    response = requests.get(
        YOUTUBE_RSS_URL.format(channel_id=channel_id),
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers=REQUEST_HEADERS,
        allow_redirects=True,
    )
    response.raise_for_status()

    root = ET.fromstring(response.text)
    channel_name = root.findtext("atom:title", default=None, namespaces=NAMESPACES)
    videos: list[VideoMetadata] = []
    for entry in root.findall("atom:entry", NAMESPACES):
        video_id = _extract_video_id_from_entry(entry)
        if not video_id:
            continue
        title = entry.findtext("atom:title", default=None, namespaces=NAMESPACES)
        published_at = entry.findtext("atom:published", default=None, namespaces=NAMESPACES)
        videos.append(
            VideoMetadata(
                video_id=video_id,
                video_url=f"https://www.youtube.com/watch?v={video_id}",
                title=title,
                published_at=published_at,
                channel=channel_name,
            )
        )
        if len(videos) >= max_results:
            break

    print(f"Fetched {len(videos)} videos from channel {channel_id}")
    return videos


def _extract_video_metadata_from_html(html: str) -> tuple[str | None, str | None]:
    title_match = OG_TITLE_PATTERN.search(html)
    published_match = DATE_PUBLISHED_PATTERN.search(html)
    title = title_match.group(1) if title_match else None
    published_at = published_match.group(1) if published_match else None
    return title, published_at


def fetch_video_metadata(video: VideoMetadata) -> VideoMetadata:
    try:
        response = requests.get(
            video.video_url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        print(f"Video metadata status code: {response.status_code}")
        print(f"Video metadata final URL: {response.url}")
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to fetch video metadata for {video.video_url}: {exc}")
        return video

    title, published_at = _extract_video_metadata_from_html(response.text)
    if title:
        print("Matched video title from og:title")
    if published_at:
        print("Matched video published date from meta itemprop")

    return VideoMetadata(
        video_id=video.video_id,
        video_url=video.video_url,
        title=title,
        published_at=published_at,
        channel=video.channel,
    )


def parse_video_url(url: str) -> VideoMetadata | None:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/")
    else:
        video_id = parse_qs(parsed.query).get("v", [None])[0]

    if not video_id:
        return None

    return VideoMetadata(
        video_id=video_id,
        video_url=url,
        title=None,
        published_at=None,
        channel=None,
    )


def _mark_skipped(result: DiscoveryResult, source: str) -> None:
    if source not in result.skipped_sources:
        result.skipped_sources.append(source)
        print(f"Skipping source: {source}")


def discover_videos(sources: list[str], max_per_channel: int = 2) -> DiscoveryResult:
    result = DiscoveryResult()
    seen_video_ids: set[str] = set()

    for source in sources:
        print(f"Discovering videos from source: {source}")
        try:
            parsed = urlparse(source)
            hostname = (parsed.hostname or "").lower()

            if "youtube.com" in hostname or "youtu.be" in hostname:
                video = parse_video_url(source)
                if video is not None:
                    if video.video_id not in seen_video_ids:
                        result.videos.append(fetch_video_metadata(video))
                        seen_video_ids.add(video.video_id)
                    continue

                channel_id = resolve_channel_id(source)
                if not channel_id:
                    _mark_skipped(result, source)
                    continue

                try:
                    videos = fetch_channel_videos(channel_id, max_per_channel)
                except requests.RequestException as exc:
                    message = f"Failed to fetch channel feed for {source}: {exc}"
                    result.errors.append(message)
                    print(message)
                    _mark_skipped(result, source)
                    continue
                except ET.ParseError as exc:
                    message = f"Failed to parse channel feed for {source}: {exc}"
                    result.errors.append(message)
                    print(message)
                    _mark_skipped(result, source)
                    continue

                for video in videos:
                    if video.video_id in seen_video_ids:
                        continue
                    result.videos.append(video)
                    seen_video_ids.add(video.video_id)
                continue

            _mark_skipped(result, source)
        except Exception as exc:
            message = f"Unexpected discovery error for {source}: {exc}"
            result.errors.append(message)
            print(message)
            _mark_skipped(result, source)

    return result


if __name__ == "__main__":
    input_sources = sys.argv[1:] or [
        "https://www.youtube.com/@TwoMinutePapers",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ]
    discovery = discover_videos(input_sources, max_per_channel=2)
    print(f"Discovered videos: {len(discovery.videos)}")
    print(f"Skipped sources: {len(discovery.skipped_sources)}")
    print(f"Errors: {len(discovery.errors)}")
    for video in discovery.videos:
        print(f"- {video.video_id} | {video.title} | {video.published_at}")
