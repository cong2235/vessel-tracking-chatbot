"""Tool: truy vấn các sự kiện tàu mất tín hiệu AIS (dark gap)."""

from __future__ import annotations

from typing import Any

from src.db import get_cursor

DEFAULT_LIMIT = 20

_ORDER_COLUMNS = {
    "duration_desc": "g.gap_duration_seconds DESC",
    "start_ts": "g.gap_start_ts",
}


def get_dark_gaps(
    vessel_id: str | None = None,
    order_by: str = "start_ts",
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    if order_by not in _ORDER_COLUMNS:
        raise ValueError(f"order_by khong hop le: {order_by!r}, chi nhan {list(_ORDER_COLUMNS)}")

    where_clause = "WHERE g.vessel_id = %(vid)s" if vessel_id else ""
    order_clause = _ORDER_COLUMNS[order_by]

    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT g.gap_id, g.vessel_id, v.shipname, g.gap_start_ts, g.gap_end_ts,
                   g.gap_duration_seconds, g.distance_nm, g.implied_speed_knots,
                   g.start_lat, g.start_lon, g.end_lat, g.end_lon,
                   ST_AsGeoJSON(g.gap_line)::json AS line_geojson
            FROM dark_gaps g
            JOIN vessels v ON v.vessel_id = g.vessel_id
            {where_clause}
            ORDER BY {order_clause}
            LIMIT %(limit)s
            """,
            {"vid": vessel_id, "limit": limit},
        )
        rows = cur.fetchall()

    features = []
    for row in rows:
        line_geojson = row.pop("line_geojson")
        features.append(
            {
                "type": "Feature",
                "geometry": line_geojson,
                "properties": {
                    "gap_id": str(row["gap_id"]),
                    "vessel_id": str(row["vessel_id"]),
                    "shipname": row["shipname"],
                },
            }
        )

    return {
        "gaps": rows,
        "geojson": {"type": "FeatureCollection", "features": features} if features else None,
    }
