# Upload Assistant © 2025 Audionut & wastaken7 — Licensed under UAPL v1.0
from typing import Any, Optional, cast

import cli_ui
import pycountry

from src.console import console
from src.get_desc import DescriptionBuilder
from src.languages import languages_manager
from src.tmdb import TmdbManager, get_tmdb_localized_data
from src.trackers.UNIT3D import UNIT3D


class DP(UNIT3D):
    # Nordic languages as DP's DUB matrix uses them (English is handled separately).
    NORDIC_CODES = frozenset({'da', 'sv', 'no', 'is', 'fi'})

    def __init__(self, config: dict[str, Any]):
        super().__init__(config, tracker_name='DP')
        self.config = config
        self.tmdb_manager = TmdbManager(config)
        self.tracker = 'DP'
        self.base_url = 'https://darkpeers.org'
        self.id_url = f'{self.base_url}/api/torrents/'
        self.upload_url = f'{self.base_url}/api/torrents/upload'
        self.requests_url = f'{self.base_url}/api/requests/filter'
        self.search_url = f'{self.base_url}/api/torrents/filter'
        self.torrent_url = f'{self.base_url}/torrents/'
        self.banned_groups = [
            'ARCADE', 'aXXo', 'BANDOLEROS', 'BONE', 'BRrip', 'CM8', 'CrEwSaDe', 'CTFOH', 'dAV1nci', 'DNL',
            'eranger2', 'FaNGDiNG0', 'FGT', 'FiSTER', 'flower', 'GalaxyTV', 'Goki', 'H4XO', 'HD2DVD', 'HDTime',
            'HorribleSubs', 'iHYTECH', 'ION10', 'iPlanet', 'KiNGDOM', 'LAMA', 'MeGusta', 'mHD', 'mSD', 'NaNi',
            'NhaNc3', 'nHD', 'nikt0', 'nSD', 'OFT', 'PiTBULL', 'PRODJi', 'PSA', 'RARBG', 'Rifftrax',
            'ROCKETRACCOON', 'SANTi', 'SARTRE', 'SasukeducK', 'SEEDSTER', 'ShAaNiG', 'Sicario', 'STUTTERSHIT',
            'Subsplease', 'SyncUp', 'TAoE', 'TGALAXY', 'TGx', 'TORRENTGALAXY', 'ToVaR', 'Trix', 'TSP', 'TSPxL',
            'ViSION', 'VXT', 'WAF', 'WKS', 'X0r', 'YIFY', 'YTS',
            ['EVO', 'WEB-DLs are allowed'],
            ['HDT', 'Remuxes or similar automated remuxes are allowed'],
        ]
        pass

    async def get_additional_checks(self, meta: dict[str, Any]) -> bool:
        should_continue = True
        if meta.get('keep_folder'):
            if not meta['unattended'] or (meta['unattended'] and meta.get('unattended_confirm', False)):
                console.print(f'[bold red]{self.tracker} does not allow single files in a folder.')
                if cli_ui.ask_yes_no("Do you want to upload anyway?", default=False):
                    pass
                else:
                    return False
            else:
                return False

        nordic_languages = ['danish', 'swedish', 'norwegian', 'icelandic', 'finnish', 'english']
        if not await self.common.check_language_requirements(
            meta, self.tracker, languages_to_check=nordic_languages, check_audio=True, check_subtitle=True
        ):
            return False

        if meta['type'] not in ['WEBDL'] and meta.get('tag', "") in ['EVO']:
            if not meta['unattended']:
                console.print(f"[bold red]{self.tracker} does not allow EVO for non-WEBDL types, skipping upload.")
            return False

        if meta.get('hardcoded_subs', False) and not meta['unattended']:
            console.print(f"[bold red]{self.tracker} does not allow hardcoded subtitles.")
            return False

        return should_continue

    async def get_description(self, meta: dict[str, Any]) -> dict[str, str]:
        if meta.get('logo', "") == "":
            TMDB_API_KEY = self.config['DEFAULT'].get('tmdb_api')
            TMDB_BASE_URL = "https://api.themoviedb.org/3"
            tmdb_id_raw = meta.get('tmdb')
            tmdb_id = int(tmdb_id_raw) if isinstance(tmdb_id_raw, (int, str)) and str(tmdb_id_raw).isdigit() else 0
            category = str(meta.get('category', ''))
            debug = bool(meta.get('debug'))
            logo_languages = ['da', 'sv', 'no', 'fi', 'is', 'en']
            tmdb_api_key = str(TMDB_API_KEY) if TMDB_API_KEY else ''
            if tmdb_id and category:
                logo_path = await self.tmdb_manager.get_logo(
                    tmdb_id,
                    category,
                    debug,
                    logo_languages=logo_languages,
                    TMDB_API_KEY=tmdb_api_key,
                    TMDB_BASE_URL=TMDB_BASE_URL,
                )
                if logo_path:
                    meta['logo'] = logo_path

        return {'description': await DescriptionBuilder(self.tracker, self.config).unit3d_edit_desc(meta)}

    async def get_additional_data(self, meta: dict[str, Any]) -> dict[str, Any]:
        data = {
            'mod_queue_opt_in': await self.get_flag(meta, 'modq'),
        }

        return data

    @staticmethod
    def _language_code(value: str) -> str:
        """Normalize a language name or code ('Japanese', 'ja', 'en-US') to alpha-2."""
        lang = str(value or '').strip().lower()
        if not lang:
            return ''
        # languages_manager uses langcodes display names, which carry a region
        # in parentheses ('Portuguese (Brazil)'); DP tags the language only.
        if '(' in lang:
            lang = lang.split('(')[0].strip()
        if '-' in lang:
            lang = lang.split('-')[0].strip()
        if len(lang) != 2:
            try:
                lang_obj = pycountry.languages.lookup(lang)
            except (AttributeError, KeyError, LookupError):
                lang_obj = pycountry.languages.get(name=lang.title()) or pycountry.languages.get(alpha_3=lang)
            # Languages with no alpha-2 (e.g. Filipino) keep their name and
            # simply match nothing, which leaves the core tag untouched.
            if lang_obj is not None and getattr(lang_obj, 'alpha_2', None):
                lang = str(lang_obj.alpha_2).lower()
        # Collapse variant spellings onto a single code.
        if lang in ('nb', 'nn'):
            return 'no'
        if lang in ('cmn', 'cn'):
            return 'zh'
        return lang

    @classmethod
    def _language_name(cls, code: str, detected: str) -> str:
        """Display name to use in the tag.

        Regional specification is kept for non-Nordic languages, so a Brazilian
        Portuguese track tags as 'Portuguese (Brazil) MULTi'. Nordic variants
        are the exception and collapse to the canonical language, so both
        'Norwegian Bokmal' and 'Swedish (Finland)' tag as plain 'Norwegian' /
        'Swedish'.
        """
        if code not in cls.NORDIC_CODES:
            return detected
        try:
            lang_obj = pycountry.languages.get(alpha_2=code)
            if lang_obj is not None and getattr(lang_obj, 'name', None):
                return str(lang_obj.name)
        except (AttributeError, KeyError, LookupError):
            pass
        return detected.split('(')[0].strip() or detected

    async def get_audio(self, meta: dict[str, Any]) -> Optional[str]:
        """Return DP's DUB element, per the site's decision matrix.

        Returns the tag to use, '' where the matrix calls for no tag, or None
        when the combination isn't covered by the matrix -- in which case the
        core's own tag is left alone rather than guessed at.
        """
        # 'Any / Disc release / (No tag)' -- DP only tags non-discs. Checked
        # here because --dual-audio forces a tag past audio.py's is_disc guard.
        if meta.get('is_disc'):
            return ''

        if not meta.get('language_checked', False):
            await languages_manager.process_desc_language(meta, tracker=self.tracker)

        audio_languages = meta.get('audio_languages')
        if not isinstance(audio_languages, list):
            return None
        audio_languages_list = cast(list[Any], audio_languages)

        # De-duplicate by code; see _language_name for how the tag text keeps
        # regional specification everywhere except Nordic variants.
        names_by_code: dict[str, str] = {}
        for entry in audio_languages_list:
            name = str(entry).strip()
            code = self._language_code(name)
            if code:
                names_by_code.setdefault(code, self._language_name(code, name))

        original = self._language_code(str(meta.get('original_language', '') or ''))
        if not names_by_code or not original:
            # Every row keys on the original language; without it, don't guess.
            return None

        codes = set(names_by_code)
        has_english = 'en' in codes
        has_original = original in codes
        has_nordic = bool(codes & self.NORDIC_CODES)

        # 'Any / Original language only / (No tag)'
        if codes == {original}:
            return ''

        if original != 'en':
            if codes == {'en'}:
                return 'Dubbed'
            # Nordic dub of non-English, non-Nordic content -> 'Swedish Dubbed'.
            if len(codes) == 1 and codes <= self.NORDIC_CODES and original not in self.NORDIC_CODES:
                return f'{names_by_code[next(iter(codes))]} Dubbed'
            if has_original and has_english:
                # Original + English is Dual-Audio; anything further is MULTi.
                return 'Dual-Audio' if len(codes) == 2 else 'MULTi'
            if has_original and len(codes - {original}) >= 2:
                return 'MULTi'
            # 'Original or English or Nordic + 1 other' -- name the language that
            # isn't acting as the base.
            others = codes - {original, 'en'}
            if has_original or has_english:
                candidates = sorted(others)
            elif has_nordic:
                # No original/English track, so a Nordic one is the base; name
                # whatever accompanies it.
                candidates = sorted(others - self.NORDIC_CODES)
            else:
                candidates = []
            if len(candidates) == 1 and len(codes) >= 2:
                return f'{names_by_code[candidates[0]]} MULTi'
            return None

        # English-original content: everything besides English is an 'other'.
        if has_english:
            extras = sorted(codes - {'en'})
            if len(extras) == 1:
                return f'{names_by_code[extras[0]]} MULTi'
            if len(extras) >= 2:
                return 'MULTi'
        return None

    @staticmethod
    def _apply_dub_tag(name: str, meta: dict[str, Any], tag: str) -> str:
        """Swap the core's DUB tag for DP's, inserting or removing as needed.

        audio.py builds meta['audio'] with the dub tag as its leading token
        (audio.py L499), so rewriting that substring covers all three cases.
        """
        core_audio = ' '.join(str(meta.get('audio', '')).split())
        if core_audio and core_audio in name:
            bare_audio = core_audio
            for existing in ('Dual-Audio', 'Dubbed'):
                if bare_audio.startswith(f'{existing} '):
                    bare_audio = bare_audio[len(existing) + 1:]
                    break
            replacement = f'{tag} {bare_audio}' if tag else bare_audio
            return ' '.join(name.replace(core_audio, replacement, 1).split())

        # Fallback if meta['audio'] can't be located: rewrite the tag in place.
        for existing in ('Dual-Audio', 'Dubbed'):
            if existing in name:
                return ' '.join(name.replace(existing, tag, 1).split())
        return name

    async def get_name(self, meta: dict[str, Any]) -> dict[str, str]:
        dp_name = str(meta.get('name', ''))

        # --- DP title/order fix (DP-local, not global) --------------------
        # 1) Title: canonical TMDB (en-US) name. The core overwrites
        #    meta['title'] with the TVDB series name for non-English-origin TV
        #    (see prep.py); DP requires the TMDB title.
        # 2) AKA: source from IMDb's aka field (imdb_info['aka']), NOT the IMDb
        #    title and NOT meta['aka'] (which can be TMDB-derived). Note
        #    imdb_info['aka'] itself falls back to the IMDb title when IMDb has
        #    no distinct alternate title (imdb.py L309) -- that fallback is the
        #    situation for releases like this one.
        # 3) Order: DP wants title, AKA, year. Rebuild only the pre-episode
        #    head; leave the season/episode marker and everything after it
        #    exactly as the core built it.
        try:
            tmdb_main = await get_tmdb_localized_data(
                meta, data_type='main', language='en-US', append_to_response=''
            )
            tmdb_title = str((tmdb_main or {}).get('name') or (tmdb_main or {}).get('title') or '').strip()
        except Exception:
            tmdb_title = ''
        if not tmdb_title:
            tmdb_title = str(meta.get('title', '')).strip()

        season = str(meta.get('season', '') or '').strip()
        episode = str(meta.get('episode', '') or '').strip()
        marker = f"{season}{episode}".strip()

        if meta.get('category') == 'TV' and marker and marker in dp_name:
            year = str(meta.get('year', '') or '').strip()
            aka = ''
            if not meta.get('no_aka', False):
                imdb_aka = str((meta.get('imdb_info') or {}).get('aka', '') or '').strip()
                if imdb_aka and imdb_aka.lower() != tmdb_title.lower() \
                        and imdb_aka.lower() not in tmdb_title.lower():
                    aka = f"AKA {imdb_aka}"
            tail = dp_name.partition(marker)[2]
            lead = ' '.join(p for p in (tmdb_title, aka, year) if p)
            dp_name = ' '.join(f"{lead} {marker}{tail}".split())
        # ------------------------------------------------------------------

        dub_tag = await self.get_audio(meta)
        if dub_tag is not None:
            dp_name = self._apply_dub_tag(dp_name, meta, dub_tag)

        return {'name': dp_name}
