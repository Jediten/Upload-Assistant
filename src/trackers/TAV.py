# Upload Assistant — TorrentAvenue (UNIT3D based)
from typing import Any

from src.trackers.COMMON import COMMON
from src.trackers.UNIT3D import UNIT3D

Meta = dict[str, Any]
Config = dict[str, Any]


class TAV(UNIT3D):
    def __init__(self, config: Config) -> None:
        super().__init__(config, tracker_name='TAV')
        self.config = config
        self.common = COMMON(config)
        self.tracker = 'TAV'
        self.base_url = 'https://torrentavenue.online'
        self.id_url = f'{self.base_url}/api/torrents/'
        self.upload_url = f'{self.base_url}/api/torrents/upload'
        self.search_url = f'{self.base_url}/api/torrents/filter'
        self.torrent_url = f'{self.base_url}/torrents/'
        self.banned_groups = [""]

    async def get_additional_data(self, meta: Meta) -> dict[str, Any]:
        return {
            'mod_queue_opt_in': await self.get_flag(meta, 'modq'),
        }
