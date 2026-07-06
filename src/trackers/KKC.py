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


class KKC:

    def __init__(self, config: Config) -> None:
        self.config: Config = config
        self.tracker = 'KKC'
        self.source_flag = 'kokocon.net'
        self.banned_groups: list[str] = []

        tracker_config = self.config.get('TRACKERS', {}).get(self.tracker, {})
        tracker_config_dict = cast(dict[str, Any], tracker_config) if isinstance(tracker_config, dict) else {}
        url_from_config = str(tracker_config_dict.get('url', 'https://tracker.kokocon.net'))
        parsed_url = urlparse(url_from_config)
        self.config_url = parsed_url.netloc or 'tracker.kokocon.net'
        self.base_url = f'https://{self.config_url}'

        self.torrent_url = f'{self.base_url}/torrent/'
        self.announce_url = str(tracker_config_dict.get('announce_url', f'{self.base_url}/announce.php'))
        
        self.upload_url = f'{self.base_url}/create'

        self.session = httpx.AsyncClient(headers={
            'User-Agent': f'Upload Assistant ({platform.system()} {platform.release()})'
        }, timeout=60.0)

    async def validate_credentials(self, meta: Meta) -> bool:
        common = COMMON(config=self.config)
        cookiefile = f"{meta['base_dir']}/data/cookies/KKC.txt"
        if os.path.exists(cookiefile):
            cookies = await common.parseCookieFile(cookiefile)
            async with httpx.AsyncClient(cookies=cookies, timeout=30.0, follow_redirects=True) as client:
                # Use /profile instead of /create — /create requires upload permission
                resp = await client.get(f'{self.base_url}/profile')
                resp_lower = resp.text.lower()
                # XBTIT shows "Yo!: Guest" for unauthenticated users
                if 'yo!: guest' in resp_lower or ('name="uid"' in resp_lower and 'name="pwd"' in resp_lower):
                    console.print(f'[bold red]{self.tracker}: Cookie validation failed. Please re-export your cookies.')
                    failure_path = await common.save_html_file(meta, self.tracker, resp.text, "Cookie_Validation")
                    console.print(f'{self.tracker}: Response saved to [yellow]{failure_path}[/yellow] for debugging.')
                    return False
                else:
                    return True
        else:
            console.print(
                f"{self.tracker}: [red]Cookie file not found.[/red]\n"
                f"{self.tracker}: Please export your cookies to: [yellow]{cookiefile}[/yellow]\n"
            )
            return False

    async def get_category_id(self, meta: Meta) -> int:
        """
        KKC categories:
            Manga: 13
            Visual Novel: 25
            Light novel: 32
            New Releases: 31
            Vietsub Anime: 17
            Anime Music Video: 30
            J-Rock Vietsub: 21
            J-Pop Vietsub: 38
            So Nyuh Shi Dae: 22
            Idol 48: 14
            Music - Other: 15
            Tokusatsu Vietsub: 24
            Japanese Drama: 28
            Japanese Movie: 29
            Vocaloid Live: 33
            Vocaloid Video: 34
            Vocaloid Mp3: 35
            Live: 39
            Artbook: 37
            Drama CD: 40
            Game: 36
            Other: 4
            Incomplete: 27
        """
        category = str(meta.get('category', ''))
        genres_value = meta.get('genres', '')
        # meta['genres'] from TMDB is a comma-separated string like "Action, Animation, Adventure"
        if isinstance(genres_value, list):
            genres = [str(g).strip().lower() for g in genres_value]
        else:
            genres = [g.strip().lower() for g in str(genres_value).split(',') if g.strip()]
        
        # Individual episodes go to "New Releases"
        if meta.get('category') in ['TV', 'Anime'] and int(meta.get('tv_pack', 0) or 0) == 0:
            return 31 # New Releases

        # Anime logic
        if category == 'Anime' or 'anime' in genres or 'animation' in genres:
            return 17  # Vietsub Anime
        
        # Manga logic
        if 'manga' in genres:
            return 13
            
        # Music logic
        if category == 'Music' or 'music' in genres:
            if 'j-pop' in genres:
                return 38
            if 'j-rock' in genres:
                return 21
            return 15 # Music - Other
            
        # Game/VN logic
        if category == 'Games' or 'game' in genres:
            if 'visual novel' in genres:
                return 25
            return 36 # Game
            
        # Movie/Drama logic
        if category == 'Movie':
            return 29 # Japanese Movie
        if category == 'TV':
            return 28 # Japanese Drama

        return 4  # Other

    async def edit_name(self, meta: Meta) -> str:
        # 1. Extract Group (Priority: Service > Release Group)
        service = str(meta.get('service', ''))
        tag = str(meta.get('tag', ''))
        
        if service:
            group = service
        else:
            group = tag[1:] if tag.startswith('-') else tag
            
        group_prefix = f"[{group}] " if group else ""

        # 2. Construct Title (English AKA Romaji)
        primary_title = str(meta.get('title', ''))
        aka_title = str(meta.get('aka', ''))
        
        full_title = primary_title
        if aka_title and aka_title.strip():
            full_title = f"{primary_title} AKA {aka_title}"
            
        # 3. Add Season and Episode
        season = str(meta.get('season', ''))
        episode = str(meta.get('episode', ''))
        if season or episode:
            full_title = f"{full_title} {season}{episode}"

        # 4. Extract Year
        year = str(meta.get('year', ''))
        year_bracket = f" [{year}]" if year else ""

        # 5. Extract Technical Metadata
        source = str(meta.get('source', ''))
        resolution = str(meta.get('resolution', ''))
        
        # Clean up source (e.g. Blu-ray -> BluRay)
        source = source.replace("Blu-ray", "BluRay")
        
        # Only add service to tech_meta if it's NOT already used as the group prefix
        tech_meta = []
        if service and group != service:
            tech_meta.append(service)
        tech_meta.extend([source, resolution])
        
        tech_meta = [x for x in tech_meta if x and x.strip()]
        tech_suffix = f" [{' '.join(tech_meta)}]" if tech_meta else ""

        # 6. Construct Final Name: [Group] Title AKA AltTitle SxxExx [Year] [Metadata]
        final_name = f"{group_prefix}{full_title}{year_bracket}{tech_suffix}"
        return ' '.join(final_name.split())

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

        # Screenshots
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

        # XBTIT BBCode Cleanups (matching HDT.py)
        bbcode = BBCODE()
        description = description.replace('[user]', '').replace('[/user]', '')
        description = description.replace('[align=left]', '').replace('[/align]', '')
        description = description.replace('[align=right]', '').replace('[/align]', '')
        description = bbcode.remove_sub(description)
        description = bbcode.remove_sup(description)
        description = description.replace('[alert]', '').replace('[/alert]', '')
        description = description.replace('[note]', '').replace('[/note]', '')
        description = description.replace('[hr]', '').replace('[/hr]', '')
        description = description.replace('[h1]', '[u][b]').replace('[/h1]', '[/b][/u]')
        description = description.replace('[h2]', '[u][b]').replace('[/h2]', '[/b][/u]')
        description = description.replace('[h3]', '[u][b]').replace('[/h3]', '[/b][/u]')
        description = description.replace('[ul]', '').replace('[/ul]', '')
        description = description.replace('[ol]', '').replace('[/ol]', '')
        description = bbcode.convert_spoiler_to_hide(description)
        description = bbcode.remove_img_resize(description)
        description = bbcode.convert_comparison_to_centered(description, 1000)
        description = bbcode.remove_spoiler(description)
        description = bbcode.remove_list(description)
        description = bbcode.remove_extra_lines(description)

        async with aiofiles.open(f"{meta['base_dir']}/tmp/{meta['uuid']}/[{self.tracker}]DESCRIPTION.txt", 'w', encoding='utf-8') as description_file:
            await description_file.write(description)

        return description

    async def search_existing(self, meta: Meta, _disctype: str) -> list[dict[str, Optional[str]]]:
        common = COMMON(config=self.config)
        cookiefile = f"{meta['base_dir']}/data/cookies/KKC.txt"
        if not os.path.exists(cookiefile):
            return []
        cookies = await common.parseCookieFile(cookiefile)

        search_term = str(meta.get('title', ''))
        search_url = f'{self.base_url}/torrents'
        params = {
            'search': search_term,
            'active': '0'
        }

        results: list[dict[str, Optional[str]]] = []
        try:
            async with httpx.AsyncClient(cookies=cookies, timeout=30.0, follow_redirects=True) as client:
                response = await client.get(search_url, params=params)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # The table selector derived from subagent
                    table = soup.find('table', class_='stable') or soup.find('table', border=True)
                    if table:
                        rows = table.find_all('tr')[1:] # Skip header
                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= 5:
                                name_tag = cells[1].find('a', href=re.compile(r'^/torrent/'))
                                if name_tag:
                                    name = name_tag.text.strip()
                                    link = f"{self.base_url}{name_tag['href']}"
                                    size = cells[4].text.strip()
                                    results.append({
                                        'name': name,
                                        'size': size,
                                        'link': link
                                    })
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
            kkc_desc = await f.read()

        # Prepare torrent file
        torrent_path = f"{meta['base_dir']}/tmp/{meta['uuid']}/[{self.tracker}].torrent"
        async with aiofiles.open(torrent_path, 'rb') as torrent_file:
            torrent_bytes = await torrent_file.read()

        kkc_name = await self.edit_name(meta)

        # Form data matching KKC (XBTIT) upload form
        # anonymous: false, editor_mode: wys (hidden)
        data: dict[str, Any] = {
            'filename': kkc_name,
            'category': await self.get_category_id(meta),
            'info': kkc_desc,
            'anonymous': 'true' if (int(meta.get('anon', 0) or 0) != 0 or self.config['TRACKERS'].get(self.tracker, {}).get('anon', False)) else 'false',
            'editor_mode': 'wys'
        }

        files = {
            'torrent': (f"{self.tracker}.torrent", torrent_bytes, "application/x-bittorrent"),
        }

        # Debug mode
        if meta.get('debug'):
            console.print(f"[cyan]{self.tracker} Upload URL: {self.upload_url}")
            console.print(f"[cyan]{self.tracker} Form Data: {data}")
            meta['tracker_status'][self.tracker]['status_message'] = "Debug mode enabled, not uploading."
            return True

        # Upload
        cookiefile = f"{meta['base_dir']}/data/cookies/KKC.txt"
        cookies = await common.parseCookieFile(cookiefile)
        
        try:
            async with httpx.AsyncClient(cookies=cookies, timeout=60.0, follow_redirects=True) as client:
                response = await client.post(url=self.upload_url, data=data, files=files)
                
                response_url = str(response.url)
                response_text = response.text

                # XBTIT KKC does NOT redirect on success — it stays on /create
                # and shows a success page with a download link: download.php?id={hash}
                download_match = re.search(r'download\.php\?id=([a-fA-F0-9]+)', response_text)

                if download_match:
                    torrent_hash = download_match.group(1)
                    torrent_page = f'{self.base_url}/torrent/{torrent_hash}'
                    console.print(f"[green]{self.tracker}: Upload successful! Torrent: [yellow]{torrent_page}[/yellow][/green]")
                    meta['tracker_status'][self.tracker]['status_message'] = torrent_page
                    return True
                elif '/torrent/' in response_url:
                    # Fallback: some XBTIT versions do redirect
                    console.print(f"[green]{self.tracker}: Uploaded to: [yellow]{response_url}[/yellow][/green]")
                    meta['tracker_status'][self.tracker]['status_message'] = response_url
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
