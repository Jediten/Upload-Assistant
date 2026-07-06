# Upload Assistant — Zenith (UNIT3D based)
from typing import Any

from src.trackers.COMMON import COMMON
from src.trackers.UNIT3D import UNIT3D

Config = dict[str, Any]


class ZNTH(UNIT3D):
    def __init__(self, config: Config) -> None:
        super().__init__(config, tracker_name='ZNTH')
        self.config = config
        self.common = COMMON(config)
        self.tracker = 'ZNTH'
        self.base_url = 'https://znth.cx'
        self.id_url = f'{self.base_url}/api/torrents/'
        self.upload_url = f'{self.base_url}/api/torrents/upload'
        self.search_url = f'{self.base_url}/api/torrents/filter'
        self.requests_url = f'{self.base_url}/api/requests/filter'
        self.torrent_url = f'{self.base_url}/torrents/'
        self.banned_groups = [
            '4K4U', 'Alcaide_Kira', 'AROMA', 'aXXo', 'BiTOR', 'BRrip', 'CM8', 'CrEwSaDe', 'd3g', 'DNL',
            'EVO', 'FaNGDiNG0', 'FGT', 'FRDS', 'GalaxyTV', 'HD2DVD', 'HDTime', 'Hi10', 'ION10', 'iPlanet',
            'KiNGDOM', 'LAMA', 'MeGusta', 'mHD', 'mSD', 'NhaNc3', 'nHD', 'nikt0', 'nSD', 'OFT', 'PRODJi',
            'RARBG', 'SANTi', 'SPDVD', 'STUTTERSHIT', 'Telly', 'TGx', 'TSP', 'TSPxL', 'WAF', 'x0r',
            'YIFY', 'YTS',
        ]
