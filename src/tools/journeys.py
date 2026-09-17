"""Tool: tính hành trình (đường đi) của tàu trong một khoảng thời gian."""

from __future__ import annotations

from typing import Any

from src.db import get_cursor


def get_journey(vessel_id: str, start_ts: str, end_ts: str) -> dict[str, Any]:
    # Diem dau/cuoi truy van RIENG (khong lay tu list co LIMIT) - neu ghep
    # chung, so diem thuc te > LIMIT se cat nham "diem cuoi" thanh 1 diem
    # giua duong, sai lech quang duong/toc do.
    range_params = {"vid": vessel_id, "start": start_ts, "end": end_ts}

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT
                count(*) AS num_points,
                min(event_ts) AS first_ts,
                max(event_ts) AS last_ts,
                ST_Length(ST_MakeLine(geom ORDER BY event_ts)::geography) / 1852.0
                    AS distance_nm,
                ST_AsGeoJSON(ST_MakeLine(geom ORDER BY event_ts))::json AS geojson
            FROM ais_positions
            WHERE vessel_id = %(vid)s AND event_ts BETWEEN %(start)s AND %(end)s
            """,
            range_params,
        )
        agg = cur.fetchone()

        if not agg or agg["num_points"] == 0:
            return {
                "vessel_id": vessel_id,
                "num_points": 0,
                "distance_nm": 0.0,
                "avg_speed_knots": None,
                "start_point": None,
                "end_point": None,
                "geojson": None,
            }

        cur.execute(
            """
            SELECT event_ts, lat, lon, speed_knots
            FROM ais_positions
            WHERE vessel_id = %(vid)s AND event_ts BETWEEN %(start)s AND %(end)s
            ORDER BY event_ts ASC
            LIMIT 1
            """,
            range_params,
        )
        start_point = cur.fetchone()

        cur.execute(
            """
            SELECT event_ts, lat, lon, speed_knots
            FROM ais_positions
            WHERE vessel_id = %(vid)s AND event_ts BETWEEN %(start)s AND %(end)s
            ORDER BY event_ts DESC
            LIMIT 1
            """,
            range_params,
        )
        end_point = cur.fetchone()

    avg_speed_knots = None
    if agg["num_points"] >= 2:
        duration_hours = (agg["last_ts"] - agg["first_ts"]).total_seconds() / 3600
        if duration_hours > 0:
            avg_speed_knots = agg["distance_nm"] / duration_hours

    return {
        "vessel_id": vessel_id,
        "num_points": agg["num_points"],
        "distance_nm": agg["distance_nm"],
        "avg_speed_knots": avg_speed_knots,
        "start_point": start_point,
        "end_point": end_point,
        "geojson": agg["geojson"],
    }
