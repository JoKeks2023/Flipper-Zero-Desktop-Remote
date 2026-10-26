"""Parse Momentum storage listings without losing spaces in file names."""
from dataclasses import dataclass
import posixpath
import re


@dataclass(frozen=True)
class StorageEntry:
    path: str
    is_dir: bool
    size: int | None = None


def quote_path(path: str) -> str:
    if not path.startswith("/") or ('"' in path or any(ord(c) < 32 or ord(c) == 127 for c in path)):
        raise ValueError("Expected an absolute device path without quotes or control characters")
    return f'"{path}"'


def parse_listing(directory: str, response: str) -> list[StorageEntry]:
    entries = []
    for line in response.splitlines():
        match = re.fullmatch(r"\s*\[([DF])\] (.+?)\s*", line)
        if not match:
            continue
        kind, name = match.groups()
        size = None
        if kind == "F":
            file_match = re.fullmatch(r"(.+) (\d+)b", name)
            if not file_match:
                continue
            name, raw_size = file_match.groups()
            size = int(raw_size)
        if name in {".", ".."} or "/" in name:
            continue
        entries.append(StorageEntry(posixpath.join(directory, name), kind == "D", size))
    return entries
