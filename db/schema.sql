CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE UNLOGGED TABLE IF NOT EXISTS staging_vessels (
    vessel_id text, mmsi text, imo text, shipname text, callsign text,
    flag_code text, flag text, ship_type_summary text, ship_type_detail_name text,
    length_m text, width_m text, dwt text, grt text, year_built text
);

CREATE UNLOGGED TABLE IF NOT EXISTS staging_ais_positions (
    vessel_id text, mmsi text, event_ts text, lat text, lon text,
    speed_knots text, course_deg text, heading_deg text, nav_status text,
    reported_dest text, draught_m text
);

CREATE UNLOGGED TABLE IF NOT EXISTS staging_dark_gaps (
    gap_id text, vessel_id text, mmsi text, gap_start_ts text, gap_end_ts text,
    gap_duration_seconds text, distance_nm text, implied_speed_knots text,
    start_lat text, start_lon text, end_lat text, end_lon text
);

CREATE UNLOGGED TABLE IF NOT EXISTS staging_ownership (
    vessel_id text, role text, company_name text, company_country text, start_date text
);

CREATE TABLE IF NOT EXISTS vessels (
    vessel_id              uuid PRIMARY KEY,
    mmsi                   integer,
    imo                    text,
    shipname               text,
    callsign               text,
    flag_code              text,
    flag                   text,
    ship_type_summary      text,
    ship_type_detail_name  text,
    length_m               double precision,
    width_m                double precision,
    dwt                    double precision,
    grt                    double precision,
    year_built             integer
);

CREATE TABLE IF NOT EXISTS ais_positions (
    id              bigserial PRIMARY KEY,
    vessel_id       uuid NOT NULL REFERENCES vessels(vessel_id),
    mmsi            integer,
    event_ts        timestamptz NOT NULL,
    lat             double precision NOT NULL,
    lon             double precision NOT NULL,
    speed_knots     double precision,
    course_deg      double precision,
    heading_deg     double precision,
    nav_status      text,
    reported_dest   text,
    draught_m       double precision,
    geom geometry(Point, 4326)
        GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(lon, lat), 4326)) STORED
);

CREATE TABLE IF NOT EXISTS dark_gaps (
    gap_id                  uuid PRIMARY KEY,
    vessel_id               uuid NOT NULL REFERENCES vessels(vessel_id),
    mmsi                    integer,
    gap_start_ts             timestamptz NOT NULL,
    gap_end_ts               timestamptz NOT NULL,
    gap_duration_seconds     integer NOT NULL,
    distance_nm              double precision,
    implied_speed_knots      double precision,
    start_lat                double precision,
    start_lon                double precision,
    end_lat                  double precision,
    end_lon                  double precision,
    start_geom geometry(Point, 4326)
        GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(start_lon, start_lat), 4326)) STORED,
    end_geom geometry(Point, 4326)
        GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(end_lon, end_lat), 4326)) STORED,
    gap_line geometry(LineString, 4326)
        GENERATED ALWAYS AS (
            ST_MakeLine(
                ST_SetSRID(ST_MakePoint(start_lon, start_lat), 4326),
                ST_SetSRID(ST_MakePoint(end_lon, end_lat), 4326)
            )
        ) STORED
);

CREATE TABLE IF NOT EXISTS ownership (
    id                bigserial PRIMARY KEY,
    vessel_id         uuid NOT NULL REFERENCES vessels(vessel_id),
    role              text NOT NULL,
    company_name      text NOT NULL,
    company_country   text,
    start_date        date
);

CREATE INDEX IF NOT EXISTS idx_vessels_shipname_trgm
    ON vessels USING gin (shipname gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_vessels_mmsi ON vessels (mmsi);
CREATE INDEX IF NOT EXISTS idx_vessels_imo ON vessels (imo);

CREATE INDEX IF NOT EXISTS idx_ais_vessel_ts ON ais_positions (vessel_id, event_ts);
CREATE INDEX IF NOT EXISTS idx_ais_geom ON ais_positions USING gist (geom);

CREATE INDEX IF NOT EXISTS idx_gaps_vessel ON dark_gaps (vessel_id);
CREATE INDEX IF NOT EXISTS idx_gaps_duration ON dark_gaps (gap_duration_seconds DESC);
CREATE INDEX IF NOT EXISTS idx_gaps_start_geom ON dark_gaps USING gist (start_geom);
CREATE INDEX IF NOT EXISTS idx_gaps_end_geom ON dark_gaps USING gist (end_geom);

CREATE INDEX IF NOT EXISTS idx_ownership_vessel ON ownership (vessel_id);
CREATE INDEX IF NOT EXISTS idx_ownership_company_trgm
    ON ownership USING gin (company_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_ownership_role ON ownership (role);

CREATE TABLE IF NOT EXISTS conversations (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title       text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id                bigserial PRIMARY KEY,
    conversation_id   uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role              text NOT NULL,
    content           text,
    tool_call_id      text,
    tool_calls_json   jsonb,
    created_at        timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE messages ADD COLUMN IF NOT EXISTS tool_call_id text;

CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages (conversation_id, created_at);

CREATE TABLE IF NOT EXISTS memory_chunks (
    id                  bigserial PRIMARY KEY,
    conversation_id     uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    content_summary     text NOT NULL,
    source_msg_from_id  bigint,
    source_msg_to_id    bigint,
    embedding           vector(1024),
    is_pinned           boolean NOT NULL DEFAULT false,
    created_at          timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE memory_chunks ADD COLUMN IF NOT EXISTS is_pinned boolean NOT NULL DEFAULT false;

DROP INDEX IF EXISTS idx_memory_chunks_embedding;
TRUNCATE memory_chunks;
ALTER TABLE memory_chunks ALTER COLUMN embedding TYPE vector(1024);

CREATE INDEX IF NOT EXISTS idx_memory_chunks_conversation
    ON memory_chunks (conversation_id);
CREATE INDEX IF NOT EXISTS idx_memory_chunks_embedding
    ON memory_chunks USING hnsw (embedding vector_cosine_ops);
