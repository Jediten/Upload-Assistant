# Upload Assistant — PeerGarden (custom, UNIT3D-compatible API)
from typing import Any, Optional

from src.trackers.COMMON import COMMON
from src.trackers.UNIT3D import UNIT3D

Meta = dict[str, Any]
Config = dict[str, Any]


class PG(UNIT3D):
    def __init__(self, config: Config) -> None:
        super().__init__(config, tracker_name='PG')
        self.config = config
        self.common = COMMON(config)
        self.tracker = 'PG'
        self.base_url = 'https://peergarden.org'
        self.id_url = f'{self.base_url}/api/torrents/'
        self.upload_url = f'{self.base_url}/api/torrents/upload'
        self.search_url = f'{self.base_url}/api/torrents/filter'
        self.torrent_url = f'{self.base_url}/torrents/'
        self.banned_groups = [""]

    async def get_additional_data(self, meta: Meta) -> dict[str, Any]:
        return {
            'mod_queue_opt_in': await self.get_flag(meta, 'modq'),
        }

    # PG prohibits the staff-only flags outright rather than ignoring them: sending
    # featured/free/doubleup/sticky without torrents:moderate fails validation and
    # rejects the whole upload. The UNIT3D base sends all four unconditionally, so
    # they are suppressed here.
    async def get_featured(self, _meta: Meta) -> dict[str, str]:
        return {}

    async def get_free(self, _meta: Meta) -> dict[str, str]:
        return {}

    async def get_doubleup(self, _meta: Meta) -> dict[str, str]:
        return {}

    async def get_sticky(self, _meta: Meta) -> dict[str, str]:
        return {}

    async def get_category_id(
        self,
        meta: Meta,
        category: Optional[str] = None,
        reverse: bool = False,
        mapping_only: bool = False,
    ) -> dict[str, str]:
        category_id = {
            'MOVIE': '1',
            'TV': '2',
        }
        if mapping_only:
            return category_id
        elif reverse:
            return {v: k for k, v in category_id.items()}
        elif category:
            return {'category_id': category_id.get(category, '0')}
        else:
            return {'category_id': category_id.get(str(meta.get('category', '')), '0')}

    async def get_type_id(
        self,
        meta: Meta,
        type: Optional[str] = None,
        reverse: bool = False,
        mapping_only: bool = False,
    ) -> dict[str, str]:
        type_id = {
            'DISC': '1',
            'REMUX': '2',
            'ENCODE': '3',
            'WEBDL': '4',
            'WEBRIP': '5',
            'HDTV': '6',
            'DVDRIP': '3',
        }
        if mapping_only:
            return type_id
        elif reverse:
            return {v: k for k, v in type_id.items()}
        elif type:
            return {'type_id': type_id.get(type, '0')}
        else:
            return {'type_id': type_id.get(str(meta.get('type', '')), '0')}

    async def get_resolution_id(
        self,
        meta: Meta,
        resolution: Optional[str] = None,
        reverse: bool = False,
        mapping_only: bool = False,
    ) -> dict[str, str]:
        # PG's table is not the UNIT3D one - it has no 4320p row, so everything
        # sits one lower. Anchored on the API reference, which documents 1080p as 2.
        resolution_id = {
            '8640p': '9',
            '4320p': '1',
            '2160p': '1',
            '1440p': '2',
            '1080p': '2',
            '1080i': '3',
            '720p': '4',
            '576p': '5',
            '576i': '6',
            '480p': '7',
            '480i': '8',
        }
        if mapping_only:
            return resolution_id
        elif reverse:
            return {v: k for k, v in resolution_id.items()}
        elif resolution:
            return {'resolution_id': resolution_id.get(resolution, '9')}
        else:
            return {'resolution_id': resolution_id.get(str(meta.get('resolution', '')), '9')}
