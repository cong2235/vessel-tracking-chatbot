"""Tool: tìm vị trí AIS của tàu tại một thời điểm cụ thể, hoặc vị trí mới
nhất hiện có nếu không truyền thời điểm."""

from __future__ import annotations

from typing import Any

from src.db import get_cursor

DEFAULT_STALE_THRESHOLD_HOURS = 6.0

_SELECT_FIELDS = """
    vessel_id, event_ts, lat, lon, speed_knots, course_deg, heading_deg, nav_status,
    EXTRACT(EPOCH FROM (event_ts - %(at_ts)s::timestamptz)) AS delta_seconds
"""

_SELECT_FIELDS_LATEST = """
    vessel_id, event_ts, lat, lon, speed_knots, course_deg, heading_deg, nav_status
"""


def get_position_at_time(
    vessel_id: str,
    at_ts: str | None = None,
    stale_threshold_hours: float = DEFAULT_STALE_THRESHOLD_HOURS,
) -> dict[str, Any] | None:
    if at_ts is None:
        return _get_latest_position(vessel_id)

    params = {"vid": vessel_id, "at_ts": at_ts}
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT {_SELECT_FIELDS}
            FROM ais_positions
            WHERE vessel_id = %(vid)s AND event_ts <= %(at_ts)s::timestamptz
            ORDER BY event_ts DESC
            LIMIT 1
            """,
            params,
        )
        before = cur.fetchone()

        cur.execute(
            f"""
            SELECT {_SELECT_FIELDS}
            FROM ais_positions
            WHERE vessel_id = %(vid)s AND event_ts >= %(at_ts)s::timestamptz
            ORDER BY event_ts ASC
            LIMIT 1
            """,
            params,
        )
        after = cur.fetchone()

    if before is None and after is None:
        return None

    nearest = _nearest(before, after)
    delta_seconds = nearest["delta_seconds"]
    is_stale = abs(delta_seconds) > stale_threshold_hours * 3600

    interpolated = _interpolate(before, after)
    source = interpolated or nearest
    result_ts = str(at_ts) if interpolated else str(source["event_ts"])

    result = {
        "vessel_id": vessel_id,
        "event_ts": result_ts,
        "lat": source["lat"],
        "lon": source["lon"],
        "speed_knots": source["speed_knots"],
        "course_deg": source["course_deg"],
        "heading_deg": source["heading_deg"],
        "nav_status": source["nav_status"],
        "delta_seconds": delta_seconds,
        "is_stale": is_stale,
        "is_interpolated": interpolated is not None,
        "geojson": {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [source["lon"], source["lat"]]},
            "properties": {"vessel_id": vessel_id, "event_ts": result_ts},
        },
    }
    if interpolated:
        result["interpolated_between"] = {
            "before_ts": str(before["event_ts"]),
            "after_ts": str(after["event_ts"]),
        }
    return result


def _nearest(before: dict[str, Any] | None, after: dict[str, Any] | None) -> dict[str, Any]:
    if before is None:
        return after
    if after is None:
        return before
    return before if abs(before["delta_seconds"]) <= after["delta_seconds"] else after


def _interpolate(before: dict[str, Any] | None, after: dict[str, Any] | None) -> dict[str, Any] | None:
    if before is None or after is None:
        return None
    if before["delta_seconds"] == 0 or after["delta_seconds"] == 0:
        return None

    total_seconds = after["delta_seconds"] - before["delta_seconds"]
    if total_seconds <= 0:
        return None
    fraction = float(-before["delta_seconds"] / total_seconds)

    speed_knots = None
    if before["speed_knots"] is not None and after["speed_knots"] is not None:
        before_speed, after_speed = float(before["speed_knots"]), float(after["speed_knots"])
        speed_knots = before_speed + fraction * (after_speed - before_speed)

    nearer = before if fraction < 0.5 else after

    return {
        "event_ts": None,
        "lat": before["lat"] + fraction * (after["lat"] - before["lat"]),
        "lon": before["lon"] + fraction * (after["lon"] - before["lon"]),
        "speed_knots": speed_knots,
        "course_deg": nearer["course_deg"],
        "heading_deg": nearer["heading_deg"],
        "nav_status": nearer["nav_status"],
    }


def _get_latest_position(vessel_id: str) -> dict[str, Any] | None:
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT {_SELECT_FIELDS_LATEST}
            FROM ais_positions
            WHERE vessel_id = %(vid)s
            ORDER BY event_ts DESC
            LIMIT 1
            """,
            {"vid": vessel_id},
        )
        row = cur.fetchone()

    if row is None:
        return None

    return {
        "vessel_id": vessel_id,
        "event_ts": str(row["event_ts"]),
        "lat": row["lat"],
        "lon": row["lon"],
        "speed_knots": row["speed_knots"],
        "course_deg": row["course_deg"],
        "heading_deg": row["heading_deg"],
        "nav_status": row["nav_status"],
        "delta_seconds": 0,
        "is_stale": False,
        "is_interpolated": False,
        "geojson": {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row["lon"], row["lat"]]},
            "properties": {"vessel_id": vessel_id, "event_ts": str(row["event_ts"])},
        },
    }
