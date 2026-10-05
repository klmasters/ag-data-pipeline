-- ag-data-pipeline: schema for the ag_data schema
-- Rebuilt on 2026-10-05 from the table definitions written in earlier chats.
--
-- PROVENANCE
--   Copied as written in chat (final working versions):
--     fred_series_meta, raw_fred_observations,
--     raw_mmn_3097_*, raw_mmn_2885_*, raw_usdm_kansas, all row_key expressions
--   RECONSTRUCTED (check against the live database if it comes back):
--     raw_mmn_1895 column list and types. The original create statement was not
--     found in chat. Columns come from the final fetch script's insert list, and
--     types are inferred (text for descriptive fields, numeric for prices/weights,
--     integer for head counts/receipts). offspring_weight_est is text because MMN
--     sends ranges like '150-300'.
--
-- row_key notes: generated columns must be immutable, so dates are split with
-- extract() instead of ::text or to_char(). avg_price is deliberately excluded
-- from the 1895 key because USDA revises it.

create schema if not exists ag_data;

-- ---------------------------------------------------------------- FRED

create table if not exists ag_data.fred_series_meta (
    series_id text primary key,
    title text not null,
    units text,
    frequency text,
    seasonally_adjusted boolean,
    source text,
    notes text
);

create table if not exists ag_data.raw_fred_observations (
    id bigint generated always as identity primary key,
    series_id text not null references ag_data.fred_series_meta(series_id),
    observation_date date not null,
    value numeric,
    ingested_at timestamptz not null default now(),
    unique (series_id, observation_date)
);

-- Series currently loaded (from chat; confirm titles/units against your meta rows)
-- PCU311119311119H  PPI: Complete Beef Cattle Feed
-- WPU0131           PPI by Commodity: Farm Products, Slaughter Cattle
-- WPU0134           PPI: Feeder and Replacement Cattle
insert into ag_data.fred_series_meta (series_id, title, units, frequency, seasonally_adjusted, source) values
('WPU0131', 'PPI by Commodity: Farm Products, Slaughter Cattle', 'Index 1982=100, Not Seasonally Adjusted', 'Monthly', false, 'BLS via FRED')
on conflict (series_id) do nothing;
-- The other two meta rows: add with the same shape (series_id, title, units, frequency,
-- seasonally_adjusted, source). The exact text you used is not in the chats I found.

-- ---------------------------------------------------------------- MMN 1895 (RECONSTRUCTED)

create table if not exists ag_data.raw_mmn_1895 (
    id bigint generated always as identity primary key,
    report_id text not null,
    slug_id text,
    slug_name text,
    report_title text,
    report_begin_date date,
    report_end_date date,
    report_date date,
    published_date timestamptz,
    final_ind text,
    "group" text,
    category text,
    commodity text,
    class text,
    frame text,
    age text,
    dressing text,
    muscle_grade text,
    yield_grade text,
    quality_grade_name text,
    pregnancy_stage text,
    lot_desc text,
    weight_collect text,
    weight_break_low numeric,
    weight_break_high numeric,
    avg_weight numeric,
    avg_weight_min numeric,
    avg_weight_max numeric,
    avg_price numeric,
    avg_price_min numeric,
    avg_price_max numeric,
    price_unit text,
    freight text,
    head_count integer,
    receipts integer,
    receipts_week_ago integer,
    receipts_year_ago integer,
    offspring_weight_est text,
    market_type text,
    market_type_category text,
    market_location_name text,
    market_location_city text,
    market_location_state text,
    office_code text,
    office_name text,
    office_city text,
    office_state text,
    comments_commodity text,
    report_narrative text,
    raw_data jsonb not null,
    ingested_at timestamptz not null default now(),
    row_key text generated always as (
        md5(
            coalesce(report_id, '') || '|' ||
            coalesce(extract(year from report_begin_date)::text, '') || '-' ||
            coalesce(extract(month from report_begin_date)::text, '') || '-' ||
            coalesce(extract(day from report_begin_date)::text, '') || '|' ||
            coalesce(commodity, '') || '|' ||
            coalesce(class, '') || '|' ||
            coalesce(frame, '') || '|' ||
            coalesce(age, '') || '|' ||
            coalesce(dressing, '') || '|' ||
            coalesce(muscle_grade, '') || '|' ||
            coalesce(yield_grade, '') || '|' ||
            coalesce(quality_grade_name, '') || '|' ||
            coalesce(pregnancy_stage, '') || '|' ||
            coalesce(lot_desc, '') || '|' ||
            coalesce(price_unit, '') || '|' ||
            coalesce(avg_weight::text, '') || '|' ||
            coalesce(head_count::text, '') || '|' ||
            coalesce(offspring_weight_est, '')
        )
    ) stored,
    constraint raw_mmn_1895_row_key_unique unique (row_key)
);

-- ---------------------------------------------------------------- MMN 3097 (Kansas Direct Cattle)

create table if not exists ag_data.raw_mmn_3097_header (
    id serial primary key,
    slug_id text,
    slug_name text,
    report_title text,
    report_begin_date date,
    report_end_date date,
    report_date date,
    published_date timestamp,
    final_ind text,
    report_narrative text,
    special_notes text,
    office_name text,
    office_code text,
    office_city text,
    office_state text,
    market_location_name text,
    market_location_city text,
    market_location_state text,
    geographical_indicator text,
    geographical_location text,
    raw_data jsonb,
    ingested_at timestamp default now()
);

create table if not exists ag_data.raw_mmn_3097_details (
    id serial primary key,
    category text,
    office_name text,
    office_code text,
    office_city text,
    office_state text,
    report_begin_date date,
    report_end_date date,
    published_date timestamp,
    market_location_name text,
    market_location_city text,
    market_location_state text,
    geographical_indicator text,
    geographical_location text,
    commodity text,
    market_type text,
    slug_id text,
    slug_name text,
    report_title text,
    final_ind text,
    report_date date,
    grp text,
    class text,
    purchase_type text,
    weight_collect text,
    freight text,
    price_unit text,
    frame text,
    muscle_grade text,
    quality_grade_name text,
    yield_grade text,
    dressing text,
    age text,
    pregnancy text,
    offspring_weight_estimate text,
    lot_desc text,
    current_ind text,
    basis_futures_month text,
    delivery_month text,
    head_count numeric,
    weight_min numeric,
    weight_max numeric,
    wtd_avg_wt numeric,
    price_min numeric,
    price_max numeric,
    wtd_avg_price numeric,
    weight_break_low numeric,
    weight_break_high numeric,
    raw_data jsonb,
    ingested_at timestamp default now(),
    row_key text generated always as (
        md5(
            coalesce(extract(year from report_begin_date)::text, '') || '-' ||
            coalesce(extract(month from report_begin_date)::text, '') || '-' ||
            coalesce(extract(day from report_begin_date)::text, '') || '|' ||
            coalesce(commodity, '') || '|' ||
            coalesce(class, '') || '|' ||
            coalesce(frame, '') || '|' ||
            coalesce(muscle_grade, '') || '|' ||
            coalesce(purchase_type, '') || '|' ||
            coalesce(delivery_month, '') || '|' ||
            coalesce(weight_break_low::text, '') || '|' ||
            coalesce(freight, '') || '|' ||
            coalesce(lot_desc, '') || '|' ||
            coalesce(price_unit, '') || '|' ||
            coalesce(quality_grade_name, '') || '|' ||
            coalesce(offspring_weight_estimate, '')
        )
    ) stored,
    constraint raw_mmn_3097_details_row_key_unique unique (row_key)
);

create table if not exists ag_data.raw_mmn_3097_receipts (
    id serial primary key,
    raw_data jsonb,
    ingested_at timestamp default now()
);

-- ---------------------------------------------------------------- MMN 2885 (Kansas Direct Hay)

create table if not exists ag_data.raw_mmn_2885_header (
    id serial primary key,
    slug_id text,
    slug_name text,
    report_title text,
    report_begin_date date,
    report_end_date date,
    published_date timestamp,
    office_name text,
    office_city text,
    office_state text,
    raw_data jsonb,
    ingested_at timestamp default now()
);

create table if not exists ag_data.raw_mmn_2885_details (
    id serial primary key,
    report_begin_date date,
    report_end_date date,
    published_date timestamp,
    office_name text,
    office_state text,
    office_city text,
    market_type text,
    market_type_category text,
    market_location_name text,
    market_location_state text,
    market_location_city text,
    slug_id text,
    slug_name text,
    report_title text,
    grp text,
    category text,
    commodity text,
    conventional text,
    region text,
    class text,
    quality text,
    sale_type text,
    price_unit text,
    package text,
    freight text,
    quantity numeric,
    price_min numeric,
    price_max numeric,
    wtd_avg_price numeric,
    use_desc text,
    desc_field text,
    crop_age text,
    raw_data jsonb,
    ingested_at timestamp default now(),
    row_key text generated always as (
        md5(
            coalesce(extract(year from report_begin_date)::text, '') || '-' ||
            coalesce(extract(month from report_begin_date)::text, '') || '-' ||
            coalesce(extract(day from report_begin_date)::text, '') || '|' ||
            coalesce(region, '') || '|' ||
            coalesce(class, '') || '|' ||
            coalesce(quality, '') || '|' ||
            coalesce(sale_type, '') || '|' ||
            coalesce(price_unit, '') || '|' ||
            coalesce(package, '') || '|' ||
            coalesce(freight, '') || '|' ||
            coalesce(conventional, '') || '|' ||
            coalesce(use_desc, '') || '|' ||
            coalesce(desc_field, '') || '|' ||
            coalesce(crop_age, '')
        )
    ) stored,
    constraint raw_mmn_2885_details_row_key_unique unique (row_key)
);

create table if not exists ag_data.raw_mmn_2885_receipts (
    id serial primary key,
    raw_data jsonb,
    ingested_at timestamp default now()
);

-- ---------------------------------------------------------------- USDM drought (Kansas)

create table if not exists ag_data.raw_usdm_kansas (
    id serial primary key,
    map_date date,
    state_abbreviation text,
    none_pct numeric,
    d0_pct numeric,
    d1_pct numeric,
    d2_pct numeric,
    d3_pct numeric,
    d4_pct numeric,
    valid_start date,
    valid_end date,
    statistic_format_id integer,
    row_key text generated always as (
        md5(
            coalesce(state_abbreviation, '') || '|' ||
            coalesce(extract(year from map_date)::text, '') || '-' ||
            coalesce(extract(month from map_date)::text, '') || '-' ||
            coalesce(extract(day from map_date)::text, '')
        )
    ) stored,
    raw_data jsonb,
    ingested_at timestamp default now(),
    constraint raw_usdm_kansas_row_key_unique unique (row_key)
);
