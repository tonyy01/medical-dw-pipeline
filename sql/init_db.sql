-- ============================================================
-- 医疗数据仓库 — 初始化数据库 Schema
-- 分层：ODS (操作数据层) → DWD (明细层) → DWS (汇总层) → ADS (应用层)
-- ============================================================

-- 创建分层的 schema
CREATE SCHEMA IF NOT EXISTS ods;
CREATE SCHEMA IF NOT EXISTS dwd;
CREATE SCHEMA IF NOT EXISTS dws;
CREATE SCHEMA IF NOT EXISTS ads;

-- ========================
-- ODS 层：原始数据导入区
-- 结构与 Synthea CSV 一致，仅做类型转换
-- ========================

CREATE TABLE IF NOT EXISTS ods.patients (
    patient_id          VARCHAR(64) PRIMARY KEY,
    birth_date          DATE,
    death_date          DATE,
    gender              VARCHAR(16),
    race                VARCHAR(64),
    ethnicity           VARCHAR(64),
    marital_status      VARCHAR(32),
    language            VARCHAR(32),
    blood_type          VARCHAR(8),
    address_city        VARCHAR(128),
    address_state       VARCHAR(64),
    address_county      VARCHAR(128),
    address_zip         VARCHAR(16),
    income              NUMERIC(12,2),
    healthcare_expenses NUMERIC(12,2),
    healthcare_coverage NUMERIC(12,2),
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.encounters (
    encounter_id        VARCHAR(64) PRIMARY KEY,
    patient_id          VARCHAR(64),
    encounter_start     TIMESTAMP,
    encounter_stop      TIMESTAMP,
    encounter_class     VARCHAR(64),
    description         TEXT,
    base_encounter_cost NUMERIC(12,2),
    total_claim_cost    NUMERIC(12,2),
    payer_coverage      NUMERIC(12,2),
    reasondescription   TEXT,
    provider_id         VARCHAR(64),
    organization_id     VARCHAR(64),
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.conditions (
    condition_id        VARCHAR(64) PRIMARY KEY,
    patient_id          VARCHAR(64),
    encounter_id        VARCHAR(64),
    code                VARCHAR(32),
    description         TEXT,
    condition_start     DATE,
    condition_stop      DATE,
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.medications (
    medication_id       VARCHAR(64) PRIMARY KEY,
    patient_id          VARCHAR(64),
    encounter_id        VARCHAR(64),
    code                VARCHAR(32),
    description         TEXT,
    base_cost           NUMERIC(12,2),
    payer_coverage      NUMERIC(12,2),
    dispenses           INTEGER,
    total_cost          NUMERIC(12,2),
    reasondescription   TEXT,
    start_date          TIMESTAMP,
    stop_date           TIMESTAMP,
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.observations (
    observation_id      VARCHAR(64) PRIMARY KEY,
    patient_id          VARCHAR(64),
    encounter_id        VARCHAR(64),
    category            VARCHAR(64),
    code                VARCHAR(32),
    description         TEXT,
    value               TEXT,
    units               VARCHAR(64),
    observation_date    TIMESTAMP,
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.imaging_studies (
    imaging_id          VARCHAR(64) PRIMARY KEY,
    patient_id          VARCHAR(64),
    encounter_id        VARCHAR(64),
    bodysite_code       VARCHAR(32),
    bodysite_description TEXT,
    modality_code       VARCHAR(32),
    modality_description TEXT,
    sop_code            VARCHAR(32),
    sop_description     TEXT,
    imaging_date        TIMESTAMP,
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.procedures (
    procedure_id        VARCHAR(64) PRIMARY KEY,
    patient_id          VARCHAR(64),
    encounter_id        VARCHAR(64),
    code                VARCHAR(32),
    description         TEXT,
    base_cost           NUMERIC(12,2),
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.organizations (
    organization_id     VARCHAR(64) PRIMARY KEY,
    name                VARCHAR(256),
    address_city        VARCHAR(128),
    address_state       VARCHAR(64),
    address_zip         VARCHAR(16),
    phone               VARCHAR(32),
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.providers (
    provider_id         VARCHAR(64) PRIMARY KEY,
    organization_id     VARCHAR(64),
    name                VARCHAR(256),
    gender              VARCHAR(16),
    specialty           VARCHAR(128),
    address_city        VARCHAR(128),
    address_state       VARCHAR(64),
    address_zip         VARCHAR(16),
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.payer_transitions (
    transition_id       VARCHAR(64) PRIMARY KEY,
    patient_id          VARCHAR(64),
    member_id           VARCHAR(64),
    payer_id            VARCHAR(64),
    ownership_start     DATE,
    ownership_end       DATE,
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.payers (
    payer_id            VARCHAR(64) PRIMARY KEY,
    name                VARCHAR(256),
    amount_covered      NUMERIC(12,2),
    amount_uncovered    NUMERIC(12,2),
    revenue             NUMERIC(12,2),
    covered_encounters  INTEGER,
    uncovered_encounters INTEGER,
    covered_medications  INTEGER,
    uncovered_medications INTEGER,
    covered_procedures   INTEGER,
    uncovered_procedures  INTEGER,
    covered_immunizations INTEGER,
    uncovered_immunizations INTEGER,
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================
-- DWD 层：维度建模
-- Star Schema
-- ========================

CREATE TABLE IF NOT EXISTS dwd.dim_patient (
    patient_sk          SERIAL PRIMARY KEY,
    patient_id          VARCHAR(64) NOT NULL,
    birth_date          DATE,
    age_years           INTEGER,
    age_group           VARCHAR(32),
    gender              VARCHAR(16),
    race                VARCHAR(64),
    ethnicity           VARCHAR(64),
    marital_status      VARCHAR(32),
    blood_type          VARCHAR(8),
    address_city        VARCHAR(128),
    address_state       VARCHAR(64),
    address_county      VARCHAR(128),
    income_bracket      VARCHAR(32),
    is_deceased         BOOLEAN DEFAULT FALSE,
    death_date          DATE,
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(patient_id)
);

CREATE TABLE IF NOT EXISTS dwd.dim_provider (
    provider_sk         SERIAL PRIMARY KEY,
    provider_id         VARCHAR(64) NOT NULL,
    name                VARCHAR(256),
    gender              VARCHAR(16),
    specialty           VARCHAR(128),
    organization_id     VARCHAR(64),
    organization_name   VARCHAR(256),
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id)
);

CREATE TABLE IF NOT EXISTS dwd.dim_date (
    date_sk             SERIAL PRIMARY KEY,
    full_date           DATE NOT NULL UNIQUE,
    year                INTEGER,
    quarter             INTEGER,
    month               INTEGER,
    month_name          VARCHAR(16),
    week                INTEGER,
    day_of_year         INTEGER,
    day_of_month        INTEGER,
    day_of_week         INTEGER,
    day_name            VARCHAR(16),
    is_weekend          BOOLEAN,
    is_holiday          BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dwd.dim_diagnosis (
    diagnosis_sk        SERIAL PRIMARY KEY,
    code                VARCHAR(32) NOT NULL,
    description         TEXT,
    code_system         VARCHAR(16) DEFAULT 'ICD-10-CM',
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code)
);

CREATE TABLE IF NOT EXISTS dwd.dim_organization (
    organization_sk     SERIAL PRIMARY KEY,
    organization_id     VARCHAR(64) NOT NULL,
    name                VARCHAR(256),
    address_city        VARCHAR(128),
    address_state       VARCHAR(64),
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id)
);

CREATE TABLE IF NOT EXISTS dwd.fact_encounter (
    encounter_sk        SERIAL PRIMARY KEY,
    encounter_id        VARCHAR(64) NOT NULL UNIQUE,
    patient_sk          INTEGER REFERENCES dwd.dim_patient(patient_sk),
    provider_sk         INTEGER REFERENCES dwd.dim_provider(provider_sk),
    organization_sk     INTEGER REFERENCES dwd.dim_organization(organization_sk),
    date_sk             INTEGER REFERENCES dwd.dim_date(date_sk),
    encounter_class     VARCHAR(64),
    description         TEXT,
    encounter_start     TIMESTAMP,
    encounter_stop      TIMESTAMP,
    encounter_duration_minutes INTEGER,
    base_encounter_cost NUMERIC(12,2),
    total_claim_cost    NUMERIC(12,2),
    payer_coverage      NUMERIC(12,2),
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dwd.fact_diagnosis (
    diagnosis_sk        SERIAL PRIMARY KEY,
    condition_id        VARCHAR(64) NOT NULL UNIQUE,
    patient_sk          INTEGER REFERENCES dwd.dim_patient(patient_sk),
    encounter_sk        INTEGER REFERENCES dwd.fact_encounter(encounter_sk),
    diagnosis_sk_ref    INTEGER REFERENCES dwd.dim_diagnosis(diagnosis_sk),
    date_sk             INTEGER REFERENCES dwd.dim_date(date_sk),
    condition_start     DATE,
    condition_stop      DATE,
    is_active           BOOLEAN DEFAULT TRUE,
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dwd.fact_medication (
    medication_sk       SERIAL PRIMARY KEY,
    medication_id       VARCHAR(64) NOT NULL UNIQUE,
    patient_sk          INTEGER REFERENCES dwd.dim_patient(patient_sk),
    encounter_sk        INTEGER REFERENCES dwd.fact_encounter(encounter_sk),
    date_sk             INTEGER REFERENCES dwd.dim_date(date_sk),
    code                VARCHAR(32),
    description         TEXT,
    base_cost           NUMERIC(12,2),
    payer_coverage      NUMERIC(12,2),
    total_cost          NUMERIC(12,2),
    dispenses           INTEGER,
    reasondescription   TEXT,
    start_date          TIMESTAMP,
    stop_date           TIMESTAMP,
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================
-- DWS 层：轻量汇总
-- 围绕业务过程的指标聚合
-- ========================

CREATE TABLE IF NOT EXISTS dws.agg_daily_admissions (
    date_sk             INTEGER PRIMARY KEY REFERENCES dwd.dim_date(date_sk),
    total_admissions    INTEGER,
    emergency_admissions INTEGER,
    inpatient_admissions INTEGER,
    outpatient_visits   INTEGER,
    unique_patients     INTEGER,
    avg_encounter_cost  NUMERIC(12,2),
    total_claim_cost    NUMERIC(14,2)
);

CREATE TABLE IF NOT EXISTS dws.agg_department_load (
    organization_sk     INTEGER REFERENCES dwd.dim_organization(organization_sk),
    date_sk             INTEGER REFERENCES dwd.dim_date(date_sk),
    total_encounters    INTEGER,
    unique_providers    INTEGER,
    total_claim_cost    NUMERIC(14,2),
    PRIMARY KEY (organization_sk, date_sk)
);

CREATE TABLE IF NOT EXISTS dws.agg_patient_segment (
    gender              VARCHAR(16),
    age_group           VARCHAR(32),
    year                INTEGER,
    patient_count       INTEGER,
    avg_annual_encounters NUMERIC(10,2),
    avg_annual_cost     NUMERIC(12,2),
    PRIMARY KEY (gender, age_group, year)
);

-- ========================
-- ADS 层：业务分析视图
-- ========================

CREATE TABLE IF NOT EXISTS ads.drg_analysis (
    diagnosis_code      VARCHAR(32),
    diagnosis_desc      TEXT,
    patient_count       INTEGER,
    avg_los_days        NUMERIC(10,2),
    avg_total_cost      NUMERIC(12,2),
    median_total_cost   NUMERIC(12,2),
    readmission_rate_30d NUMERIC(5,4),
    data_period         VARCHAR(16),
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ads.readmission_risk (
    patient_id          VARCHAR(64),
    total_admissions    INTEGER,
    first_admission     DATE,
    last_admission      DATE,
    days_between_admissions INTEGER,
    num_chronic_conditions INTEGER,
    risk_level          VARCHAR(16),
    _etl_loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
