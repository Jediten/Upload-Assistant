# Upload Assistant — NordicQuality (UNIT3D based)
from typing import Any

from src.trackers.COMMON import COMMON
from src.trackers.UNIT3D import UNIT3D

Config = dict[str, Any]


class NQ(UNIT3D):
    def __init__(self, config: Config) -> None:
        super().__init__(config, tracker_name='NQ')
        self.config = config
        self.common = COMMON(config)
        self.tracker = 'NQ'
        self.base_url = 'https://nordicq.org'
        self.id_url = f'{self.base_url}/api/torrents/'
        self.upload_url = f'{self.base_url}/api/torrents/upload'
        self.search_url = f'{self.base_url}/api/torrents/filter'
        self.torrent_url = f'{self.base_url}/torrents/'
        self.banned_groups = ['']
