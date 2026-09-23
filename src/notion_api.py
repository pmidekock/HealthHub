"""Ophalen van Notion data sources via de REST API (versie 2025-09-03)."""

import pandas as pd
import requests

from src.config import NOTION_VERSION

API_URL = "https://api.notion.com/v1/data_sources/{id}/query"


def _waarde(prop: dict):
    """Zet één Notion-property om naar een Python-waarde."""
    t = prop.get("type")
    v = prop.get(t)
    if v is None:
        return None
    if t in ("title", "rich_text"):
        return "".join(x.get("plain_text", "") for x in v) or None
    if t == "number":
        return v
    if t in ("select", "status"):
        return v.get("name")
    if t == "multi_select":
        return ", ".join(x["name"] for x in v) or None
    if t == "date":
        return v.get("start")
    if t == "checkbox":
        return bool(v)
    if t == "formula":
        return v.get(v.get("type"))
    if t in ("created_time", "last_edited_time"):
        return v
    return None


def query_data_source(token: str, data_source_id: str) -> pd.DataFrame:
    """Haal alle rijen van een data source op (met paginering)."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    rijen, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = requests.post(API_URL.format(id=data_source_id), headers=headers, json=body, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Notion API {r.status_code}: {r.text[:300]}")
        data = r.json()
        for page in data.get("results", []):
            rij = {naam: _waarde(p) for naam, p in page.get("properties", {}).items()}
            rij["_id"] = page.get("id")
            rijen.append(rij)
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return pd.DataFrame(rijen)
