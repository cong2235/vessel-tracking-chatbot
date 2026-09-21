"""Tool: tìm kiếm và lấy thông tin tĩnh của tàu."""

from __future__ import annotations

from typing import Any

from src.db import get_cursor

DEFAULT_LIMIT = 10

# pg_trgm mac dinh 0.3 qua long (chuoi vo nghia van trung trigram ngau
# nhien voi ten that). 0.4 loc bot false-positive, van giu duoc loi go sai
# nhe nhu "KOTA GAIA" -> "KOTA GAYA".
MIN_SIMILARITY_SCORE = 0.4


def search_vessel(query: str, limit: int = DEFAULT_LIMIT) -> list[dict[str, Any]]:
    # Luon tra ve list (ke ca rong/1 ket qua) de tang goi (LLM) tu quyet
    # dinh khi trung ten hoac khong tim thay.
    query = query.strip()
    if not query:
        return []

    if query.isdigit():
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT vessel_id, mmsi, imo, shipname, flag, ship_type_summary
                FROM vessels
                WHERE mmsi = %(q)s::integer OR imo = %(q)s
                LIMIT %(limit)s
                """,
                {"q": query, "limit": limit},
            )
            rows = cur.fetchall()
        if rows:
            return rows

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT vessel_id, mmsi, imo, shipname, flag, ship_type_summary, match_score
            FROM (
                SELECT vessel_id, mmsi, imo, shipname, flag, ship_type_summary,
                       GREATEST(
                           similarity(shipname, %(q)s),
                           CASE WHEN shipname ILIKE %(like)s THEN 1.0 ELSE 0.0 END
                       ) AS match_score
                FROM vessels
                WHERE shipname IS NOT NULL
                  AND (shipname ILIKE %(like)s OR shipname %% %(q)s)
            ) scored
            WHERE match_score >= %(min_score)s
            ORDER BY match_score DESC, shipname
            LIMIT %(limit)s
            """,
            {
                "q": query,
                "like": f"%{query}%",
                "min_score": MIN_SIMILARITY_SCORE,
                "limit": limit,
            },
        )
        return cur.fetchall()


def list_vessels_by_type(ship_type_substring: str, limit: int = 500) -> list[dict[str, Any]]:
    # ship_type_substring la tieng Anh (vd. "Tanker", "Cargo", "Fishing") -
    # khop ILIKE voi ship_type_summary. LLM tu anh xa tu tieng Viet nguoi
    # dung dung sang tu khoa nay (huong dan trong tool description).
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT vessel_id, mmsi, shipname, ship_type_summary
            FROM vessels
            WHERE ship_type_summary ILIKE %(pattern)s
            ORDER BY shipname
            LIMIT %(limit)s
            """,
            {"pattern": f"%{ship_type_substring}%", "limit": limit},
        )
        return cur.fetchall()


def get_vessel_info(vessel_id: str) -> dict[str, Any] | None:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT vessel_id, mmsi, imo, shipname, callsign, flag_code, flag,
                   ship_type_summary, ship_type_detail_name,
                   length_m, width_m, dwt, grt, year_built
            FROM vessels
            WHERE vessel_id = %(vid)s
            """,
            {"vid": vessel_id},
        )
        vessel = cur.fetchone()
        if vessel is None:
            return None

        cur.execute(
            """
            SELECT role, company_name, company_country, start_date
            FROM ownership
            WHERE vessel_id = %(vid)s
            ORDER BY role
            """,
            {"vid": vessel_id},
        )
        vessel["ownership"] = cur.fetchall()

    return vessel
