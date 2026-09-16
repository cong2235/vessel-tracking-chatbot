"""Pipeline nạp dữ liệu tàu biển (4 file CSV) vào PostgreSQL/PostGIS.

Idempotent: chạy lại bao nhiêu lần cũng ra cùng một kết quả (không nhân đôi
dữ liệu) vì luôn TRUNCATE bảng đích trước khi nạp lại từ staging.

Cách dùng:
    python scripts/load_data.py

Cấu hình qua biến môi trường (xem .env.example):
    DATABASE_URL  - chuỗi kết nối Postgres
    DATA_DIR      - thư mục chứa 4 file CSV (mặc định: <project_root>/data)
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Cột kỳ vọng theo ĐÚNG thứ tự cho từng file — dùng để xác thực header trước
# khi COPY. COPY của Postgres map dữ liệu theo VỊ TRÍ cột, không theo tên
# trong dòng header, nên nếu thứ tự cột trong CSV thay đổi mà không kiểm tra
# trước, dữ liệu sẽ bị nạp sai cột một cách âm thầm (không lỗi). Việc này
# chặn đứng rủi ro đó bằng cách so khớp header thực tế với danh sách dưới
# đây, dừng ngay và báo lỗi rõ ràng nếu lệch.
CSV_COLUMNS: dict[str, list[str]] = {
    "staging_vessels": [
        "vessel_id", "mmsi", "imo", "shipname", "callsign", "flag_code", "flag",
        "ship_type_summary", "ship_type_detail_name",
        "length_m", "width_m", "dwt", "grt", "year_built",
    ],
    "staging_ais_positions": [
        "vessel_id", "mmsi", "event_ts", "lat", "lon", "speed_knots",
        "course_deg", "heading_deg", "nav_status", "reported_dest", "draught_m",
    ],
    "staging_dark_gaps": [
        "gap_id", "vessel_id", "mmsi", "gap_start_ts", "gap_end_ts",
        "gap_duration_seconds", "distance_nm", "implied_speed_knots",
        "start_lat", "start_lon", "end_lat", "end_lon",
    ],
    "staging_ownership": [
        "vessel_id", "role", "company_name", "company_country", "start_date",
    ],
}

# Mỗi entry: (tên bảng staging, tên file csv, danh sách cột theo đúng thứ tự CSV)
CSV_FILES = [
    ("staging_vessels", "vessels.csv"),
    ("staging_ais_positions", "ais_positions.csv"),
    ("staging_dark_gaps", "dark_gaps.csv"),
    ("staging_ownership", "ownership.csv"),
]

# Số dòng kỳ vọng (theo mô tả đề bài) — dùng để cảnh báo nếu lệch, không chặn.
EXPECTED_ROW_COUNTS = {
    "vessels": 1000,
    "ais_positions": 171073,
    "dark_gaps": 880,
    "ownership": 4127,
}

# Cast + làm sạch từ staging (toàn TEXT) sang bảng chính, xử lý các trường hợp
# nhiễu đã biết: số dạng "9605047.0", cột rỗng -> NULL.
INSERT_VESSELS = """
INSERT INTO vessels (
    vessel_id, mmsi, imo, shipname, callsign, flag_code, flag,
    ship_type_summary, ship_type_detail_name,
    length_m, width_m, dwt, grt, year_built
)
SELECT
    vessel_id::uuid,
    NULLIF(mmsi, '')::double precision::integer,
    NULLIF(imo, '')::double precision::bigint::text,  -- "9605047.0" -> "9605047"
    NULLIF(trim(shipname), ''),                        -- tên rỗng -> NULL, không phải chuỗi rỗng
    NULLIF(callsign, ''),
    NULLIF(flag_code, ''),
    NULLIF(flag, ''),
    NULLIF(ship_type_summary, ''),
    NULLIF(ship_type_detail_name, ''),
    NULLIF(length_m, '')::double precision,
    NULLIF(width_m, '')::double precision,
    NULLIF(dwt, '')::double precision,
    NULLIF(grt, '')::double precision,
    NULLIF(year_built, '')::double precision::integer
FROM staging_vessels;
"""

INSERT_AIS_POSITIONS = """
INSERT INTO ais_positions (
    vessel_id, mmsi, event_ts, lat, lon, speed_knots, course_deg,
    heading_deg, nav_status, reported_dest, draught_m
)
SELECT
    vessel_id::uuid,
    NULLIF(mmsi, '')::double precision::integer,
    event_ts::timestamptz,
    lat::double precision,
    lon::double precision,
    NULLIF(speed_knots, '')::double precision,
    NULLIF(course_deg, '')::double precision,
    NULLIF(heading_deg, '')::double precision,
    NULLIF(nav_status, ''),
    NULLIF(reported_dest, ''),
    NULLIF(draught_m, '')::double precision
FROM staging_ais_positions;
"""

INSERT_DARK_GAPS = """
INSERT INTO dark_gaps (
    gap_id, vessel_id, mmsi, gap_start_ts, gap_end_ts, gap_duration_seconds,
    distance_nm, implied_speed_knots, start_lat, start_lon, end_lat, end_lon
)
SELECT
    gap_id::uuid,
    vessel_id::uuid,
    NULLIF(mmsi, '')::double precision::integer,
    gap_start_ts::timestamptz,
    gap_end_ts::timestamptz,
    NULLIF(gap_duration_seconds, '')::double precision::integer,
    NULLIF(distance_nm, '')::double precision,
    NULLIF(implied_speed_knots, '')::double precision,
    start_lat::double precision,
    start_lon::double precision,
    end_lat::double precision,
    end_lon::double precision
FROM staging_dark_gaps;
"""

INSERT_OWNERSHIP = """
INSERT INTO ownership (vessel_id, role, company_name, company_country, start_date)
SELECT
    vessel_id::uuid,
    role,
    trim(company_name),
    NULLIF(company_country, ''),
    NULLIF(start_date, '')::date
FROM staging_ownership;
"""

INSERT_STATEMENTS = {
    "staging_vessels": ("vessels", INSERT_VESSELS),
    "staging_ais_positions": ("ais_positions", INSERT_AIS_POSITIONS),
    "staging_dark_gaps": ("dark_gaps", INSERT_DARK_GAPS),
    "staging_ownership": ("ownership", INSERT_OWNERSHIP),
}


def get_data_dir() -> Path:
    raw = os.environ.get("DATA_DIR", str(PROJECT_ROOT / "data"))
    return Path(raw)


def apply_schema(conn) -> None:
    schema_path = PROJECT_ROOT / "db" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    print(f"[schema] applied {schema_path}")


def read_csv_header(csv_path: Path) -> list[str]:
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f))


def validate_header(staging_table: str, csv_path: Path) -> None:
    expected = CSV_COLUMNS[staging_table]
    actual = read_csv_header(csv_path)
    if actual != expected:
        raise ValueError(
            f"Header cua {csv_path.name} khong khop thu tu cot ky vong.\n"
            f"  Ky vong: {expected}\n"
            f"  Thuc te : {actual}\n"
            "Dung lai truoc khi nap de tranh COPY gan sai du lieu vao sai cot."
        )


def copy_csv_into_staging(conn, staging_table: str, csv_path: Path) -> int:
    validate_header(staging_table, csv_path)
    columns = ", ".join(CSV_COLUMNS[staging_table])
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE {staging_table};")
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            cur.copy_expert(
                f"COPY {staging_table} ({columns}) FROM STDIN WITH (FORMAT csv, HEADER true)",
                f,
            )
        cur.execute(f"SELECT count(*) FROM {staging_table};")
        (count,) = cur.fetchone()
    print(f"[staging] {staging_table}: {count} dong nap tu {csv_path.name} (header da xac thuc)")
    return count


def reload_target_tables(conn) -> None:
    with conn.cursor() as cur:
        # vessels la bang cha; CASCADE se don sach ca 3 bang con tham chieu no
        cur.execute("TRUNCATE vessels RESTART IDENTITY CASCADE;")
        # vessels phai nap truoc vi cac bang khac co FK vessel_id
        cur.execute(INSERT_VESSELS)
        cur.execute(INSERT_AIS_POSITIONS)
        cur.execute(INSERT_DARK_GAPS)
        cur.execute(INSERT_OWNERSHIP)
    print("[load] da nap du lieu tu staging sang bang chinh")


def verify_row_counts(conn) -> bool:
    ok = True
    with conn.cursor() as cur:
        for table, expected in EXPECTED_ROW_COUNTS.items():
            cur.execute(f"SELECT count(*) FROM {table};")
            (actual,) = cur.fetchone()
            status = "OK" if actual == expected else "CHECK"
            if actual != expected:
                ok = False
            print(f"[verify] {table}: {actual} dong (ky vong {expected}) -> {status}")
    return ok


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: bien moi truong DATABASE_URL chua duoc thiet lap "
              "(xem .env.example).", file=sys.stderr)
        return 1

    data_dir = get_data_dir()
    for _, filename in CSV_FILES:
        if not (data_dir / filename).exists():
            print(f"ERROR: khong tim thay {data_dir / filename}", file=sys.stderr)
            return 1

    conn = psycopg2.connect(database_url)
    try:
        apply_schema(conn)
        for staging_table, filename in CSV_FILES:
            copy_csv_into_staging(conn, staging_table, data_dir / filename)
        reload_target_tables(conn)
        all_ok = verify_row_counts(conn)
        conn.commit()
        print("[done] pipeline hoan tat, da commit.")
        return 0 if all_ok else 0  # lech so dong chi la canh bao, khong fail pipeline
    except Exception:
        conn.rollback()
        print("[error] pipeline that bai, da rollback toan bo thay doi.", file=sys.stderr)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
