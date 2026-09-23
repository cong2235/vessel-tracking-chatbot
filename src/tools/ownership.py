"""Tool: tìm tàu theo công ty (chủ sở hữu / khai thác / quản lý)."""

from __future__ import annotations

from typing import Any

from src.db import get_cursor

DEFAULT_LIMIT = 200
MIN_SIMILARITY_SCORE = 0.45


def get_company_vessels(
    company_query: str,
    role: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    company_query = company_query.strip()
    if not company_query:
        return {"matched_companies": [], "vessels": []}

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT company_name, match_score
            FROM (
                SELECT company_name, similarity(company_name, %(q)s) AS match_score
                FROM (SELECT DISTINCT company_name FROM ownership) AS distinct_companies
                WHERE company_name %% %(q)s OR company_name ILIKE %(like)s
            ) scored
            WHERE match_score >= %(min_score)s
            ORDER BY match_score DESC
            LIMIT 10
            """,
            {"q": company_query, "like": f"%{company_query}%", "min_score": MIN_SIMILARITY_SCORE},
        )
        matched_companies = cur.fetchall()
        if not matched_companies:
            return {"matched_companies": [], "vessels": []}

        names = tuple(row["company_name"] for row in matched_companies)
        params: dict[str, Any] = {"names": names, "limit": limit}

        role_filter = ""
        if role:
            role_filter = "AND o.role = %(role)s"
            params["role"] = role

        cur.execute(
            f"""
            SELECT v.vessel_id, v.mmsi, v.shipname, v.ship_type_summary,
                   array_agg(DISTINCT o.role) AS roles,
                   array_agg(DISTINCT o.company_name) AS matched_company_names
            FROM ownership o
            JOIN vessels v ON v.vessel_id = o.vessel_id
            WHERE o.company_name IN %(names)s
            {role_filter}
            GROUP BY v.vessel_id, v.mmsi, v.shipname, v.ship_type_summary
            ORDER BY v.shipname
            LIMIT %(limit)s
            """,
            params,
        )
        vessels = cur.fetchall()

    return {"matched_companies": matched_companies, "vessels": vessels}
