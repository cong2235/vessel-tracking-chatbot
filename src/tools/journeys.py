"""Tool: tính hành trình (đường đi) của tàu trong một khoảng thời gian."""

from __future__ import annotations

from typing import Any

from src.db import get_cursor

MAX_VESSELS_PER_REQUEST = 50
# Do gian don duong (ST_Simplify) truoc khi tra ve - giu ban do muot voi
# hang chuc nghin diem ma khong gui het toa do tho cho FE/LLM.
SIMPLIFY_TOLERANCE_DEGREES = 0.0005


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


def get_multi_journey_geojson(
    vessel_ids: list[str],
    start_ts: str,
    end_ts: str,
    page: int = 1,
    page_size: int = MAX_VESSELS_PER_REQUEST,
) -> dict[str, Any]:
    """N3: hanh trinh cua nhieu tau cung luc. LLM chi nen doc cac truong
    ngoai "geojson" (num_vessels/total_points/bbox/vessel_names) - geojson
    day du duoc tach rieng sang su kien `data` cho FE, khong di qua model.

    Phan trang THAT tren danh sach vessel_ids dau vao (khong chi cat cung
    lay 50 tau dau): page/page_size chon 1 lat cat cua vessel_ids, has_more
    bao con trang tiep theo hay khong - LLM goi lai voi page+1 de lay het
    khi vessel_ids vuot MAX_VESSELS_PER_REQUEST (vd. 628 tau Cargo)."""
    page = max(1, page)
    page_size = min(max(1, page_size), MAX_VESSELS_PER_REQUEST)
    total_vessels_requested = len(vessel_ids)
    start_idx = (page - 1) * page_size
    page_vessel_ids = vessel_ids[start_idx : start_idx + page_size]
    has_more = start_idx + page_size < total_vessels_requested

    if not page_vessel_ids:
        return {
            "num_vessels": 0,
            "total_points": 0,
            "bbox": None,
            "vessel_names": [],
            "geojson": None,
            "page": page,
            "page_size": page_size,
            "total_vessels_requested": total_vessels_requested,
            "has_more": False,
        }

    params = {"vids": page_vessel_ids, "start": start_ts, "end": end_ts, "tol": SIMPLIFY_TOLERANCE_DEGREES}

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT a.vessel_id, v.shipname, count(*) AS num_points,
                   ST_AsGeoJSON(
                       ST_Simplify(ST_MakeLine(a.geom ORDER BY a.event_ts), %(tol)s)
                   )::json AS line_geojson
            FROM ais_positions a
            JOIN vessels v ON v.vessel_id = a.vessel_id
            WHERE a.vessel_id = ANY(%(vids)s::uuid[]) AND a.event_ts BETWEEN %(start)s AND %(end)s
            GROUP BY a.vessel_id, v.shipname
            HAVING count(*) >= 2
            """,
            params,
        )
        rows = cur.fetchall()

        cur.execute(
            """
            SELECT min(lon) AS min_lon, max(lon) AS max_lon, min(lat) AS min_lat, max(lat) AS max_lat
            FROM ais_positions
            WHERE vessel_id = ANY(%(vids)s::uuid[]) AND event_ts BETWEEN %(start)s AND %(end)s
            """,
            params,
        )
        bbox_row = cur.fetchone()

    features = [
        {
            "type": "Feature",
            "geometry": r["line_geojson"],
            "properties": {
                "vessel_id": str(r["vessel_id"]),
                "shipname": r["shipname"],
                "num_points": r["num_points"],
            },
        }
        for r in rows
    ]

    return {
        "num_vessels": len(rows),
        "total_points": sum(r["num_points"] for r in rows),
        "bbox": (
            [bbox_row["min_lon"], bbox_row["min_lat"], bbox_row["max_lon"], bbox_row["max_lat"]]
            if bbox_row and bbox_row["min_lon"] is not None
            else None
        ),
        "vessel_names": [r["shipname"] for r in rows],
        "geojson": {"type": "FeatureCollection", "features": features} if features else None,
        "page": page,
        "page_size": page_size,
        "total_vessels_requested": total_vessels_requested,
        "has_more": has_more,
    }


def compare_journeys(vessel_ids: list[str], start_ts: str, end_ts: str) -> dict[str, Any]:
    """So sanh quang duong/toc do nhieu tau trong 1 khoang thoi gian. Tinh va
    sap xep NGAY TRONG SQL (1 lan goi) - tranh LLM phai tu lap get_journey
    cho tung tau roi tu so sanh (vua cham MAX_TOOL_ITERATIONS voi nhieu tau,
    vua de tinh sai/quen tau khi so sanh thu cong qua nhieu luot)."""
    vessel_ids = vessel_ids[:MAX_VESSELS_PER_REQUEST]
    if not vessel_ids:
        return {"num_vessels": 0, "vessels": [], "farthest": None, "shortest": None}

    params = {"vids": vessel_ids, "start": start_ts, "end": end_ts}

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT a.vessel_id, v.shipname, count(*) AS num_points,
                   min(a.event_ts) AS first_ts, max(a.event_ts) AS last_ts,
                   ST_Length(ST_MakeLine(a.geom ORDER BY a.event_ts)::geography) / 1852.0
                       AS distance_nm
            FROM ais_positions a
            JOIN vessels v ON v.vessel_id = a.vessel_id
            WHERE a.vessel_id = ANY(%(vids)s::uuid[]) AND a.event_ts BETWEEN %(start)s AND %(end)s
            GROUP BY a.vessel_id, v.shipname
            HAVING count(*) >= 2
            ORDER BY distance_nm DESC
            """,
            params,
        )
        rows = cur.fetchall()

    vessels = []
    for r in rows:
        duration_hours = (r["last_ts"] - r["first_ts"]).total_seconds() / 3600
        avg_speed_knots = r["distance_nm"] / duration_hours if duration_hours > 0 else None
        vessels.append(
            {
                "vessel_id": str(r["vessel_id"]),
                "shipname": r["shipname"],
                "num_points": r["num_points"],
                "distance_nm": r["distance_nm"],
                "avg_speed_knots": avg_speed_knots,
            }
        )

    return {
        "num_vessels": len(vessels),
        "vessels": vessels,  # da sap xep distance_nm giam dan
        "farthest": vessels[0] if vessels else None,
        "shortest": vessels[-1] if vessels else None,
    }
