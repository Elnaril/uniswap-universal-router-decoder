"""Guard against version and registry-name drift.

The library version is written in more than one file: ``pyproject.toml`` is the source of truth, but ``server.json``
(the MCP Registry metadata) must repeat it, and the README carries the registry name as an ``mcp-name:`` marker. These
tests fail the build if any of them drift.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from packaging.version import Version


_ROOT = Path(__file__).resolve().parent.parent


def _pyproject_version() -> str:
    text = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project_table = re.search(r"^\[project\]$(.*?)(?=^\[)", text, re.MULTILINE | re.DOTALL)
    assert project_table is not None, "no [project] table found in pyproject.toml"
    version = re.search(r'^version\s*=\s*"([^"]+)"', project_table.group(1), re.MULTILINE)
    assert version is not None, "no version declared in the [project] table"
    return version.group(1)


def _server_json() -> dict[str, Any]:
    return json.loads((_ROOT / "server.json").read_text(encoding="utf-8"))


def test_server_json_tracks_the_packaging_version() -> None:
    expected = Version(_pyproject_version())
    server_json = _server_json()
    assert Version(server_json["version"]) == expected
    for package in server_json["packages"]:
        assert Version(package["version"]) == expected


def test_readme_mcp_name_matches_the_registry_name() -> None:
    registry_name = _server_json()["name"]
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    assert f"mcp-name: {registry_name}" in readme
