# Upload Assistant — MidnightScene (UNIT3D based)
from typing import Any, Optional, cast

from src.get_desc import DescriptionBuilder
from src.languages import languages_manager
from src.trackers.COMMON import COMMON
from src.trackers.UNIT3D import UNIT3D

Meta = dict[str, Any]
Config = dict[str, Any]


class MNS(UNIT3D):
    def __init__(self, config: Config) -> None:
        super().__init__(config, tracker_name='MNS')
        self.config = config
        self.common = COMMON(config)
        self.tracker = 'MNS'
        self.base_url = 'https://midnightscene.cc'
        self.id_url = f'{self.base_url}/api/torrents/'
        self.upload_url = f'{self.base_url}/api/torrents/upload'
        self.search_url = f'{self.base_url}/api/torrents/filter'
        self.torrent_url = f'{self.base_url}/torrents/'
        self.banned_groups = [""]

    async def get_name(self, meta: Meta) -> dict[str, str]:
        mns_name = str(meta.get('name', ''))
        resolution = str(meta.get('resolution', ''))

        # Ensure audio language detection has run.
        if not meta.get('audio_languages'):
            await languages_manager.process_desc_language(meta, tracker=self.tracker)

        # Prepend the spoken language (before the resolution) for non-English
        # releases, mirroring OE. Skipped for full BDMV discs.
        audio_languages_value = meta.get('audio_languages', [])
        audio_languages = cast(list[str], audio_languages_value) if isinstance(audio_languages_value, list) else []
        if audio_languages and not await languages_manager.has_english_language(audio_languages) and meta.get('is_disc') != "BDMV":
            foreign_lang = str(audio_languages[0]).upper()
            mns_name = mns_name.replace(f"{resolution}", f"{foreign_lang} {resolution}", 1)

        return {'name': mns_name}

    async def get_description(self, meta: Meta) -> dict[str, str]:
        signature = f"[right][url=https://github.com/bioidaika/Upload-Assistant][size=4]{meta['ua_signature']}[/size][/url][/right]"
        return {
            "description": await DescriptionBuilder(self.tracker, self.config).unit3d_edit_desc(
                meta, comparison=True, signature=signature
            )
        }

    async def get_additional_data(self, meta: Meta) -> dict[str, str]:
        return {
            'mod_queue_opt_in': await self.get_flag(meta, 'modq'),
        }

    async def get_category_id(
        self,
        meta: Meta,
        category: Optional[str] = None,
        reverse: bool = False,
        mapping_only: bool = False,
    ) -> dict[str, str]:
        _ = (category, reverse, mapping_only)
        category_id = {
            'MOVIE': '1',
            'TV': '2',
        }.get(meta['category'], '0')
        return {'category_id': category_id}

    async def get_type_id(
        self,
        meta: Meta,
        type: Optional[str] = None,
        reverse: bool = False,
        mapping_only: bool = False,
    ) -> dict[str, str]:
        _ = (type, reverse, mapping_only)
        type_id = {
            'DISC': '1',
            'REMUX': '2',
            'ENCODE': '3',
            'WEBDL': '4',
            'WEBRIP': '5',
            'HDTV': '6',
        }.get(meta['type'], '0')
        return {'type_id': type_id}

    async def get_resolution_id(
        self,
        meta: Meta,
        resolution: Optional[str] = None,
        reverse: bool = False,
        mapping_only: bool = False,
    ) -> dict[str, str]:
        _ = (resolution, reverse, mapping_only)
        resolution_id = {
            '4320p': '1',
            '2160p': '2',
            '1080p': '3',
            '1080i': '4',
            '720p': '5',
        }.get(meta['resolution'], '10')
        return {'resolution_id': resolution_id}
