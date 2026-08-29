# Upload Assistant © 2025 Audionut & wastaken7 — Licensed under UAPL v1.0
from collections.abc import Iterable, Mapping
from typing import Any


# PTPImg has shut down permanently. Imgbox remains disabled by default while
# its outage is unresolved. Users can override this with disabled_image_hosts.
DEFAULT_DISABLED_IMAGE_HOSTS = frozenset({"ptpimg", "imgbox"})


def get_disabled_image_hosts(default_config: Mapping[str, Any]) -> set[str]:
    """Return normalized image hosts that must not be selected or retried."""
    if "disabled_image_hosts" not in default_config:
        return set(DEFAULT_DISABLED_IMAGE_HOSTS)

    raw_value = default_config.get("disabled_image_hosts")
    if isinstance(raw_value, str):
        values: Iterable[Any] = raw_value.split(',')
    elif isinstance(raw_value, (list, tuple, set, frozenset)):
        values = raw_value
    else:
        return set(DEFAULT_DISABLED_IMAGE_HOSTS)

    return {str(value).strip().lower() for value in values if str(value).strip()}
