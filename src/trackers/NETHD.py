# Upload Assistant © 2025 Audionut & wastaken7 — Licensed under UAPL v1.0
import os
import platform
import re
from typing import Any, Optional, Union, cast
from urllib.parse import urlparse

import aiofiles
import httpx
from bs4 import BeautifulSoup

from src.bbcode import BBCODE
from src.console import console
from src.get_desc import DescriptionBuilder
from src.trackers.COMMON import COMMON

Meta = dict[str, Any]
Config = dict[str, Any]


class NETHD:

    def __init__(self, config: Config) -> None:
        self.config: Config = config
        self.tracker = 'NETHD'
        self.source_flag = 'nethd.org'
        self.banned_groups: list[str] = []

        tracker_config = self.config.get('TRACKERS', {}).get(self.tracker, {})
        tracker_config_dict = cast(dict[str, Any], tracker_config) if isinstance(tracker_config, dict) else {}
        url_from_config = str(tracker_config_dict.get('url', 'https://nethd.org'))
        parsed_url = urlparse(url_from_config)
        self.config_url = parsed_url.netloc or 'nethd.org'
        self.base_url = f'https://{self.config_url}'

        self.torrent_url = f'{self.base_url}/details.php?id='
        self.announce_url = str(tracker_config_dict.get('announce_url', f'{self.base_url}/announce.php'))
        self.passkey = ''
        if 'passkey=' in self.announce_url:
            self.passkey = self.announce_url.split('passkey=')[1].split('&')[0]
        self.upload_url = f'{self.base_url}/takeupload.php'

        self.session = httpx.AsyncClient(headers={
            'User-Agent': f'Upload Assistant ({platform.system()} {platform.release()})'
        }, timeout=60.0)

    async def validate_credentials(self, meta: Meta) -> bool:
        common = COMMON(config=self.config)
        cookiefile = f"{meta['base_dir']}/data/cookies/NETHD.txt"
        if os.path.exists(cookiefile):
            cookies = await common.parseCookieFile(cookiefile)
            async with httpx.AsyncClient(cookies=cookies, timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(f'{self.base_url}/upload.php')
                if 'logout.php' in resp.text:
                    return True
                else:
                    console.print(f'[bold red]{self.tracker}: Cookie validation failed. Please re-export your cookies.')
                    return False
        else:
            console.print(
                f"{self.tracker}: [red]Cookie file not found.[/red]\n"
                f"{self.tracker}: Please export your cookies to: [yellow]{cookiefile}[/yellow]\n"
                f'{self.tracker}: Cookies can be exported using browser extensions like "cookies.txt" (Firefox) or "Get cookies.txt LOCALLY" (Chrome).'
            )
            return False

    async def get_category_id(self, meta: Meta) -> int:
        """
        NETHD categories (field name: 'type'):
            401 = Movie
            402 = Music
            403 = Game
            404 = Software
            405 = Image
            406 = Book
        """
        return 401

    async def get_subcategory_id(self, meta: Meta) -> int:
        """
        NETHD subcategories/genres (field name: 'subcategory'):
            423 = Action       424 = Comedy       425 = Animation
            431 = Sci-Fi       551 = Horror       427 = Thriller
            429 = Crime        430 = Documentary  432 = Drama
            433 = Sport        512 = Musical      511 = TV Show
            550 = TV Series    437 = Fantasy      537 = War
            438 = Collection / Pack  538 = Adventure
            435 = SmartPhone   439 = Others
        """
        category = str(meta.get('category', ''))

        # TV content
        if category == 'TV':
            if int(meta.get('tv_pack', 0) or 0) != 0:
                return 550  # TV Series (pack)
            return 511  # TV Show (single episode)

        # Movie — try to detect genre from meta
        genres_value = meta.get('genres', '')
        genres = ', '.join(cast(list[str], genres_value)) if isinstance(genres_value, list) else str(genres_value)
        genres_lower = genres.lower()

        keywords_value = meta.get('keywords', '')
        keywords = ', '.join(cast(list[str], keywords_value)) if isinstance(keywords_value, list) else str(keywords_value)
        keywords_lower = keywords.lower()

        combined = genres_lower + ' ' + keywords_lower

        # Map genres to NETHD subcategory IDs (ordered by priority)
        genre_map: list[tuple[list[str], int]] = [
            (['animation', 'anime'], 425),
            (['documentary'], 430),
            (['horror'], 551),
            (['sci-fi', 'science fiction'], 431),
            (['thriller'], 427),
            (['action'], 423),
            (['comedy'], 424),
            (['crime'], 429),
            (['drama'], 432),
            (['fantasy'], 437),
            (['war'], 537),
            (['adventure'], 538),
            (['sport'], 433),
            (['musical', 'music'], 512),
        ]

        for keywords_list, sub_id in genre_map:
            for keyword in keywords_list:
                if keyword in combined:
                    return sub_id

        return 439  # Others (default)

    async def get_source_id(self, meta: Meta) -> int:
        """
        NETHD source types (field name: 'source'):
            411 = Bluray       555 = Remux        556 = Encode
            410 = WEB-DL      413 = HDTV         414 = DVD
            513 = SD           530 = Other
        """
        meta_type = str(meta.get('type', ''))

        source_map: dict[str, int] = {
            'DISC': 411,        # Bluray disc
            'REMUX': 555,       # Remux
            'ENCODE': 556,      # Encode
            'WEBDL': 410,       # WEB-DL
            'WEBRIP': 556,      # WEB-Rip → Encode
            'HDTV': 413,        # HDTV
            'DVDRIP': 414,      # DVD
        }

        # BDMV is Bluray disc
        if meta.get('is_disc', '') == 'BDMV':
            return 411
        if meta.get('is_disc', '') == 'DVD':
            return 414

        return source_map.get(meta_type, 530)  # Default: Other

    async def get_standard_id(self, meta: Meta) -> int:
        """
        NETHD standard/resolution (field name: 'standard'):
            415 = 1080p        416 = 720p         417 = mHD
            418 = SD           419 = 4K           557 = 8K
        """
        resolution = str(meta.get('resolution', ''))

        standard_map: dict[str, int] = {
            '2160p': 419,   # 4K
            '1080p': 415,   # 1080p
            '1080i': 415,   # 1080i → 1080p
            '720p': 416,    # 720p
            '576p': 418,    # SD
            '576i': 418,    # SD
            '480p': 418,    # SD
            '480i': 418,    # SD
            '4320p': 557,   # 8K
        }

        return standard_map.get(resolution, 418)  # Default: SD

    async def edit_name(self, meta: Meta) -> str:
        nethd_name = str(meta.get('name', ''))
        # NexusPHP trackers generally accept standard torrent names
        # Just normalize whitespace
        nethd_name = ' '.join(nethd_name.split())
        return nethd_name

    async def edit_desc(self, meta: Meta) -> str:
        builder = DescriptionBuilder(self.tracker, self.config)
        desc_parts: list[str] = []

        # Custom Header
        desc_parts.append(await builder.get_custom_header())

        # Logo
        logo_resize_url = str(meta.get('tmdb_logo', ''))
        if logo_resize_url:
            desc_parts.append(f"[center][img]https://image.tmdb.org/t/p/w300/{logo_resize_url}[/img][/center]")

        # TV
        title, episode_image, episode_overview = await builder.get_tv_info(meta, resize=True)
        if episode_overview:
            desc_parts.append(f'[center]{title}[/center]')

            if episode_image:
                desc_parts.append(f"[center][img]{episode_image}[/img][/center]")

            desc_parts.append(f'[center]{episode_overview}[/center]')

        # File information
        mediainfo = await builder.get_mediainfo_section(meta)
        if mediainfo:
            desc_parts.append(f'[quote]{mediainfo}[/quote]')

        bdinfo = await builder.get_bdinfo_section(meta)
        if bdinfo:
            desc_parts.append(f'[quote]{bdinfo}[/quote]')

        # User description
        desc_parts.append(await builder.get_user_description(meta))

        # Tonemapped Header
        desc_parts.append(await builder.get_tonemapped_header(meta))

        # Screenshot Header
        desc_parts.append(await builder.screenshot_header())

        # Screenshots — use standard BBCode [img] tags
        images_value = meta.get('image_list', [])
        images: list[dict[str, Any]] = []
        if isinstance(images_value, list):
            images_list = cast(list[Any], images_value)
            images.extend(
                [
                    cast(dict[str, Any], item)
                    for item in images_list
                    if isinstance(item, dict)
                ]
            )
        if images:
            screenshots_block = ''
            for image in images:
                raw_url = str(image.get('raw_url', ''))
                img_url = str(image.get('img_url', ''))
                if raw_url and img_url:
                    screenshots_block += f"[url={raw_url}][img]{img_url}[/img][/url] "
            desc_parts.append('[center]\n' + screenshots_block + '[/center]')

        # Signature
        desc_parts.append(
            f"[right][url=https://github.com/bioidaika/Upload-Assistant][size=1]{meta.get('ua_signature', '')}[/size][/url][/right]"
        )

        description = '\n\n'.join(part for part in desc_parts if part.strip())

        # BBCode cleanup for NexusPHP compatibility
        bbcode = BBCODE()
        description = description.replace('[user]', '').replace('[/user]', '')
        description = bbcode.convert_spoiler_to_hide(description)
        description = bbcode.remove_img_resize(description)
        description = bbcode.convert_comparison_to_centered(description, 1000)
        description = bbcode.remove_extra_lines(description)

        async with aiofiles.open(f"{meta['base_dir']}/tmp/{meta['uuid']}/[{self.tracker}]DESCRIPTION.txt", 'w', encoding='utf-8') as description_file:
            await description_file.write(description)

        return description

    async def search_existing(self, meta: Meta, _disctype: str) -> list[dict[str, Optional[str]]]:
        common = COMMON(config=self.config)
        cookiefile = f"{meta['base_dir']}/data/cookies/NETHD.txt"
        if not os.path.exists(cookiefile):
            console.print(f"[bold red]{self.tracker}: Missing Cookie File. (data/cookies/NETHD.txt)")
            return []
        cookies = await common.parseCookieFile(cookiefile)

        # Use IMDb ID or title for search
        imdb_id = int(meta.get('imdb_id', 0) or 0)
        if imdb_id != 0:
            search_term = f"tt{meta.get('imdb', '')}"
            search_area = 4  # IMDb search
        else:
            search_term = str(meta.get('title', ''))
            search_area = 0  # Title search

        search_url = f'{self.base_url}/torrents.php'
        params: dict[str, Union[str, int]] = {
            'search': search_term,
            'search_area': search_area,
            'search_mode': 0,
            'incldead': 0,
        }

        results: list[dict[str, Optional[str]]] = []

        try:
            async with httpx.AsyncClient(cookies=cookies, timeout=30.0, follow_redirects=True) as client:
                response = await client.get(search_url, params=params)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # NETHD uses table.torrent, and specific SEO URLs
                    rows = soup.select('table.torrent tr')
                    if not rows:
                        rows = soup.select('table.torrents tr')
                    
                    if not rows:
                        rows = soup.find_all('tr')

                    for row in rows:
                        # Find the link to details or torrent page
                        name_tag = row.find('a', attrs={'href': re.compile(r'(details\.php\?id=|torrent-)')})
                        if not name_tag:
                            continue

                        # Extract name from multiple sources to avoid truncation (e.g., from apostrophes)
                        name = name_tag.text.strip()
                        title = name_tag.get('title')
                        if title and len(title) > len(name):
                            name = title
                        
                        # Use SEO slug as fallback if it contains more info (like resolution)
                        href = name_tag.get('href', '')
                        # More flexible regex to handle optional leading slash and capture slug
                        slug_match = re.search(r'/?(.+)-torrent-\d+\.html', href)
                        if slug_match:
                            slug = slug_match.group(1).replace('-', ' ')
                            # If slug is longer or has resolution that name lacks
                            if len(slug) > len(name) or (re.search(r'\d{3,4}p', slug) and not re.search(r'\d{3,4}p', name)):
                                name = slug

                        link = f"{self.base_url}/{href}" if href else None
                        size = None

                        # Find size: usually in a cell with units
                        cells = row.find_all('td')
                        for cell in cells:
                            cell_text = cell.text.strip()
                            # Common units
                            if re.search(r'\d+(\.\d+)?\s*(GiB|MiB|TiB|GB|MB|TB)', cell_text, re.IGNORECASE):
                                size = cell_text
                                break

                        if name:
                            results.append({
                                'name': name,
                                'size': size,
                                'link': link
                            })
                else:
                    console.print(f'[bold red]{self.tracker}: HTTP request failed. Status: {response.status_code}')

        except httpx.TimeoutException:
            console.print(f'{self.tracker}: Timeout while searching for existing torrents.')
            return []
        except httpx.RequestError as e:
            console.print(f'{self.tracker}: Network error while searching: {e.__class__.__name__}.')
            return []
        except Exception as e:
            console.print(f'{self.tracker}: Unexpected error while searching: {e}')
            return []

        return results

    async def upload(self, meta: Meta, _disctype: str) -> bool:
        common = COMMON(config=self.config)
        await common.create_torrent_for_upload(meta, self.tracker, self.source_flag)

        # Prepare description
        desc_file = f"{meta['base_dir']}/tmp/{meta['uuid']}/[{self.tracker}]DESCRIPTION.txt"
        if not os.path.exists(desc_file):
            await self.edit_desc(meta)
        async with aiofiles.open(desc_file, encoding='utf-8') as f:
            nethd_desc = await f.read()

        # Prepare torrent file
        torrent_path = f"{meta['base_dir']}/tmp/{meta['uuid']}/[{self.tracker}].torrent"
        async with aiofiles.open(torrent_path, 'rb') as torrent_file:
            torrent_bytes = await torrent_file.read()

        nethd_name = await self.edit_name(meta)

        # Build small_descr (short description) using year and tags
        small_descr = ""
        if meta.get('year'):
            small_descr = f"({meta['year']})"
        
        # Vietnamese Audio/Subtitle check
        audio_langs = meta.get('audio_languages', [])
        if not isinstance(audio_langs, list):
            audio_langs = [str(audio_langs)]
        
        sub_langs = meta.get('subtitle_languages', [])
        if not isinstance(sub_langs, list):
            sub_langs = [str(sub_langs)]

        # Check for Vietnamese in Audio
        if any(lang.lower() in ['vietnamese', 'vi', 'vi-vn'] for lang in audio_langs):
            small_descr += " (TM/LT)"
            
        # Check for Vietnamese in Subtitles
        if any(lang.lower() in ['vietnamese', 'vi', 'vi-vn'] for lang in sub_langs):
            small_descr += " (VietSub)"
        
        # Add TMDB ID
        tmdb_id = meta.get('tmdb_id') or meta.get('tmdb')
        if tmdb_id and tmdb_id != 0:
            tmdb_type = 'tv' if meta.get('category') == 'TV' else 'movie'
            small_descr += f" {tmdb_type}/{tmdb_id}"

        small_descr = small_descr.strip()

        # Poster from TMDB
        poster = ''
        if meta.get('poster'):
            poster = str(meta['poster'])

        # IMDb URL
        imdb_url = ''
        if int(meta.get('imdb_id', 0) or 0) != 0:
            imdb_url = f"https://www.imdb.com/title/tt{meta.get('imdb', '')}/"

        # Form data matching NETHD upload form
        data: dict[str, Any] = {
            'name': nethd_name,
            'small_descr': small_descr,
            'poster': poster,
            'type': await self.get_category_id(meta),          # Category (401=Movie)
            'subcategory': await self.get_subcategory_id(meta), # Genre
            'source': await self.get_source_id(meta),           # Source (Bluray/Remux/Encode/WEB-DL...)
            'standard': await self.get_standard_id(meta),       # Standard (1080p/720p/4K...)
            'url': imdb_url,
            'descr': nethd_desc,
            'team_sel': 0,
        }

        files = {
            'file': (f"{self.tracker}.torrent", torrent_bytes, "application/x-bittorrent"),
        }

        # Debug mode
        if meta.get('debug'):
            console.print(f"[cyan]{self.tracker} Upload URL: {self.upload_url}")
            console.print(f"[cyan]{self.tracker} Form Data:")
            for k, v in data.items():
                if k == 'descr':
                    console.print(f"  {k}: [truncated, {len(str(v))} chars]")
                else:
                    console.print(f"  {k}: {v}")
            meta['tracker_status'][self.tracker]['status_message'] = "Debug mode enabled, not uploading."
            await common.create_torrent_for_upload(meta, f"{self.tracker}_DEBUG", f"{self.tracker}_DEBUG", announce_url="https://fake.tracker")
            return True

        # Upload
        cookiefile = f"{meta['base_dir']}/data/cookies/NETHD.txt"
        if not os.path.exists(cookiefile):
            console.print(f"[bold red]{self.tracker}: Missing Cookie File. (data/cookies/NETHD.txt)")
            meta['tracker_status'][self.tracker]['status_message'] = "Missing cookie file."
            return False

        cookies = await common.parseCookieFile(cookiefile)
        try:
            async with httpx.AsyncClient(cookies=cookies, timeout=30.0, follow_redirects=True) as client:
                response = await client.post(url=self.upload_url, data=data, files=files)

                # NexusPHP redirects to details.php?id=XXX (or SEO friendly URL) on success
                response_url = str(response.url)
                if 'details.php?id=' in response_url or '/torrent-' in response_url:
                    clean_url = response_url.replace('&uploaded=1', '')
                    console.print(f"[green]{self.tracker}: Uploaded to: [yellow]{clean_url}[/yellow][/green]")

                    # Try standard NexusPHP ID extraction
                    id_match = re.search(r'id=(\d+)', urlparse(response_url).query)
                    if not id_match:
                        # Try SEO URL ID extraction (e.g., /torrent-206664-slug.html)
                        id_match = re.search(r'torrent-(\d+)-', response_url)

                    if id_match:
                        torrent_id = id_match.group(1)
                        meta['tracker_status'][self.tracker]['torrent_id'] = torrent_id
                        meta['tracker_status'][self.tracker]['status_message'] = clean_url

                        # Download the new torrent with passkey
                        await self.download_new_torrent(meta, torrent_id, torrent_path)
                    else:
                        meta['tracker_status'][self.tracker]['status_message'] = clean_url
                    return True
                else:
                    error_msg = f"Upload failed. Response URL: {response_url} (status {response.status_code})"
                    console.print(f"[bold red]{self.tracker}: {error_msg}")
                    failure_path = await common.save_html_file(meta, self.tracker, response.text, "Failed_Upload")
                    console.print(
                        f"The web page has been saved to [yellow]{failure_path}[/yellow] for analysis.\n"
                        "[red]Do not share this file publicly[/red], as it may contain confidential information.\n"
                    )
                    meta['tracker_status'][self.tracker]['status_message'] = error_msg
                    return False

        except httpx.TimeoutException:
            meta['tracker_status'][self.tracker]['status_message'] = "Connection timed out"
            console.print(f"[bold red]{self.tracker}: Connection timed out during upload.")
            return False
        except httpx.RequestError as e:
            meta['tracker_status'][self.tracker]['status_message'] = f"Request error: {e}"
            console.print(f"[bold red]{self.tracker}: Request error: {e}")
            return False
        except Exception as e:
            meta['tracker_status'][self.tracker]['status_message'] = f"Unexpected error: {e}"
            console.print(f"[bold red]{self.tracker}: Unexpected error: {e}")
            return False

    async def download_new_torrent(self, meta: Meta, torrent_id: str, torrent_path: str) -> None:
        """Download the newly uploaded torrent to get the one with passkey."""
        common = COMMON(config=self.config)
        cookiefile = f"{meta['base_dir']}/data/cookies/NETHD.txt"
        if not os.path.exists(cookiefile):
            return
        cookies = await common.parseCookieFile(cookiefile)
        download_url = f"{self.base_url}/download.php?id={torrent_id}"
        if self.passkey:
            download_url += f"&passkey={self.passkey}"

        try:
            async with httpx.AsyncClient(cookies=cookies, timeout=30.0, follow_redirects=True) as client:
                r = await client.get(url=download_url)
            if r.status_code == 200:
                async with aiofiles.open(torrent_path, "wb") as tor:
                    await tor.write(r.content)
            else:
                console.print(f"[red]{self.tracker}: Issue downloading the new .torrent (HTTP {r.status_code})")
        except Exception as e:
            console.print(f"[red]{self.tracker}: Error downloading new torrent: {e}")
