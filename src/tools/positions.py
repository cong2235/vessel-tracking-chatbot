"""Tool: tìm vị trí AIS của tàu tại một thời điểm cụ thể."""

from __future__ import annotations

from typing import Any

from src.db import get_cursor

DEFAULT_STALE_THRESHOLD_HOURS = 6.0


def get_position_at_time(
    vessel_id: str,
    at_ts: str,
    stale_threshold_hours: float = DEFAULT_STALE_THRESHOLD_HOURS,
) -> dict[str, Any] | None:
    # delta_seconds > 0: diem du lieu o sau at_ts. is_stale=True khi diem
    # gan nhat van cach qua xa - de tang chat bao "khong co du lieu gan do"
    # thay vi ngam coi la chinh xac (R4).
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT vessel_id, event_ts, lat, lon, speed_knots, course_deg,
                   heading_deg, nav_status,
                   EXTRACT(EPOCH FROM (event_ts - %(at_ts)s::timestamptz))
                       AS delta_seconds,
                   ST_AsGeoJSON(geom)::json AS point_geojson
            FROM ais_positions
            WHERE vessel_id = %(vid)s
            ORDER BY ABS(EXTRACT(EPOCH FROM (event_ts - %(at_ts)s::timestamptz)))
            LIMIT 1
            """,
            {"vid": vessel_id, "at_ts": at_ts},
        )
        row = cur.fetchone()

    if row is None:
        return None

    row["is_stale"] = abs(row["delta_seconds"]) > stale_threshold_hours * 3600
    point_geojson = row.pop("point_geojson")
    row["geojson"] = {
        "type": "Feature",
        "geometry": point_geojson,
        "properties": {"vessel_id": row["vessel_id"], "event_ts": str(row["event_ts"])},
    }
    return row
