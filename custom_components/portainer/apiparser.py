"""API parser for JSON APIs."""

from datetime import datetime
import re
from logging import getLogger
from pytz import utc
from typing import Any


from homeassistant.components.diagnostics import async_redact_data

from .const import TO_REDACT

_LOGGER = getLogger(__name__)


# ---------------------------
#   utc_from_timestamp
# ---------------------------
def utc_from_timestamp(timestamp: float) -> datetime:
    """Return a UTC time from a timestamp."""
    return utc.localize(datetime.utcfromtimestamp(timestamp))


# ---------------------------
#   utc_from_iso_string
# ---------------------------
def utc_from_iso_string(iso_string: str) -> datetime | None:
    """Return a UTC time from an ISO 8601 string."""
    if not iso_string or iso_string.startswith("0001-01-01"):
        return None
    try:
        # Truncate to 6 decimal places for microseconds, fromisoformat can't handle more
        iso_string = re.sub(r"(\.\d{6})\d*([Zz]|\+.*)?", r"\1\2", iso_string)
        if iso_string.endswith("Z"):
            iso_string = iso_string[:-1] + "+00:00"
        return datetime.fromisoformat(iso_string)
    except (ValueError, TypeError):
        _LOGGER.warning("Could not parse ISO string: %s", iso_string)
        return None


# ---------------------------
#   _get_nested_value
# ---------------------------
def _get_nested_value(data: Any, path: str, default: Any = None) -> Any:
    """Safely get a nested value from a dictionary using a slash-separated path."""
    parts = path.split("/")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


# ---------------------------
#   from_entry
# ---------------------------
def from_entry(entry, param, default="") -> str:
    """Validate and return str value an API dict."""
    if "/" in param:
        ret = _get_nested_value(entry, param, default)
    else:
        ret = entry.get(param, default)

    if isinstance(ret, str) and len(ret) > 255:
        return ret[:255]
    return ret


# ---------------------------
#   from_entry_bool
# ---------------------------
def from_entry_bool(entry, param, default=False, reverse=False) -> bool:
    """Validate and return a bool value from an API dict."""
    if "/" in param:
        ret = _get_nested_value(entry, param, default)
    else:
        ret = entry.get(param, default)
    if isinstance(ret, str):
        if ret.lower() in ("on", "yes", "up"):
            ret = True
        elif ret.lower() in ("off", "no", "down"):
            ret = False

    if not isinstance(ret, bool):
        ret = default

    if reverse:
        return not ret

    return ret


# ---------------------------
#   _process_value_definition
# ---------------------------
def _process_value_definition(
    target_dict: dict, source_entry: dict, val_def: dict
) -> None:
    """Process a single value definition and fill it into the target dictionary."""
    _name = val_def["name"]
    _type = val_def.get("type", "str")
    _source_path = val_def.get("source", _name)
    _convert = val_def.get("convert")

    if _type == "str":
        _default = val_def.get("default", "")
        if "default_val" in val_def and val_def["default_val"] in val_def:
            _default = val_def[val_def["default_val"]]
        target_dict[_name] = from_entry(source_entry, _source_path, default=_default)
    elif _type == "bool":
        _default = val_def.get("default", False)
        _reverse = val_def.get("reverse", False)
        target_dict[_name] = from_entry_bool(
            source_entry, _source_path, default=_default, reverse=_reverse
        )
    else:
        # Handle other types or raise error if unsupported
        _LOGGER.warning("Unsupported value type: %s for %s", _type, _name)
        return

    if _convert == "utc_from_timestamp":
        val = target_dict[_name]
        if isinstance(val, (int, float)) and val > 0:
            if val > 100000000000:  # Heuristic for milliseconds vs seconds
                val /= 1000
            target_dict[_name] = utc_from_timestamp(val)
    elif _convert == "utc_from_iso_string":
        val = target_dict[_name]
        if isinstance(val, str):
            target_dict[_name] = utc_from_iso_string(val)


# ---------------------------
#   parse_api
# ---------------------------
def parse_api(
    data: dict | None = None,
    source: Any = None,
    key: str | None = None,
    vals: list | None = None,
    val_proc: list | None = None,
    ensure_vals: list | None = None,
    only: list | None = None,
    skip: list | None = None,
) -> dict:
    """Get data from API."""
    if data is None:
        data = {}

    if isinstance(source, dict):
        source = [source]

    if not source:
        # If no source, and no key for list processing, fill defaults if vals are provided
        if not key and vals:
            for val_def in vals:
                if val_def.get("name") not in data:
                    _process_value_definition(
                        data, {}, val_def
                    )  # Pass empty dict for source_entry
        return data

    for entry in source:
        if only and not matches_only(entry, only):
            continue

        if skip and can_skip(entry, skip):
            continue

        uid = None
        if key:
            uid = _get_nested_value(entry, key)
            if uid is None:  # UID must not be None
                continue

            if uid not in data:
                data[uid] = {}

            target_data = data[uid]
        else:
            target_data = data  # If no UID, operate directly on the passed data dict

        _LOGGER.debug("Processing entry %s", async_redact_data(entry, TO_REDACT))

        if vals:
            for val_def in vals:
                _process_value_definition(target_data, entry, val_def)

        if ensure_vals:
            for val_def in ensure_vals:
                if val_def.get("name") not in target_data:
                    target_data[val_def["name"]] = val_def.get("default", "")

        if val_proc:
            fill_vals_proc(data, uid, val_proc)

    return data


# ---------------------------
#   matches_only
# ---------------------------
def matches_only(entry, only) -> bool:
    """Return True if all variables are matched."""
    ret = False
    for val in only:
        if val["key"] in entry and entry[val["key"]] == val["value"]:
            ret = True
        else:
            ret = False
            break

    return ret


# ---------------------------
#   can_skip
# ---------------------------
def can_skip(entry, skip) -> bool:
    """Return True if at least one variable matches."""
    ret = False
    for val in skip:
        if val["name"] in entry and entry[val["name"]] == val["value"]:
            ret = True
            break

        if val["value"] == "" and val["name"] not in entry:
            ret = True
            break

    return ret


# ---------------------------
#   fill_vals_proc
# ---------------------------
def fill_vals_proc(data, uid, vals_proc) -> dict:
    """Add custom keys."""
    _data = data[uid] if uid else data
    for val_sub in vals_proc:
        _name = None
        _action = None
        _value = None
        for val in val_sub:
            if "name" in val:
                _name = val["name"]
                continue

            if "action" in val:
                _action = val["action"]
                continue

            if not _name and not _action:
                break

            if _action == "combine":
                if "key" in val:
                    tmp = _data[val["key"]] if val["key"] in _data else "unknown"
                    _value = f"{_value}{tmp}" if _value else tmp

                if "text" in val:
                    tmp = val["text"]
                    _value = f"{_value}{tmp}" if _value else tmp

        if _name and _value:
            if uid:
                data[uid][_name] = _value
            else:
                data[_name] = _value

    return data
