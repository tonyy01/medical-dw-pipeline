# Medical Data Warehouse ETL Pipeline 🏥

**A production-grade data engineering pipeline: from synthetic medical data to a layered data warehouse**

## Overview

This project demonstrates a **complete production-level data engineering pipeline**, covering data ingestion, cleansing/transformation, dimensional modeling, task orchestration, and quality monitoring.

It uses **Synthea** (an open-source synthetic patient generator) to simulate healthcare data and builds a layered data warehouse (ODS → DWD → DWS → ADS) via **dbt**, with the entire workflow orchestrated by **Apache Airflow**.

### Core Capabilities

| Area | Stack |
|------|-------|
| **Data Source** | Synthea — open-source synthetic healthcare data (CSV) |
| **ETL Engine** | Python (pandas, SQLAlchemy) |
| **Data Modeling** | dbt-core (dimensional modeling, Star Schema) |
| **Storage** | PostgreSQL 16 |
| **Orchestration** | Apache Airflow |
| **Infrastructure** | Docker Compose |
| **Code Quality** | Ruff, pytest |

---

## Architecture

```
         ┌──────────────────────────────┐
         │           Synthea            │
         │   (Synthetic Patient Data)   │
         └─────── ──────┬───────────────┘
                        │ CSV files
                        ▼
┌─────────────────────────────────────────────────┐
│       Phase 1: Extract (Python / pandas)        │
│    Read CSVs, type inference, null handling     │
└───────────────────────┬─────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────┐
│          Phase 2: Transform (Python)            │
│    Cleanse, standardize, column mapping, type   │
│        casting, synthetic ID generation         │
└───────────────────────┬─────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────┐
│    Phase 3: Load (SQLAlchemy → PostgreSQL)      │ 
│   Write to ODS layer (raw, type-converted data) │
└───────────────────────┬─────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────┐
│             dbt Dimensional Modeling            │
├─────────────────────────────────────────────────┤
│ ODS (Operation Data Store) — 11 raw tables      │
│   ↓                                             │
│ DWD (Detail Warehouse) — Star Schema            │
│   ↓                                             │
│ DWS (Summary Warehouse) — Daily/Dept/Segment    │
│   ↓                                             │
│ ADS (Application Data Store) — DRG, Readmission │
└───────────────────────┬─────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────┐
│     Airflow Auto-Scheduling (daily @ 06:00)     │
│   check → etl → dbt(ods→dwd→dws→ads) → test     │
└─────────────────────────────────────────────────┘
```

### Data Layering

| Layer | Schema | Description | Materialization |
|-------|--------|-------------|----------------|
| **ODS** | `ods.*` | Raw data mirroring Synthea CSV structure | - |
| **DWD** | `public_dwd.*` | Dimensional star schema (5 dimensions + 3 facts) | Table |
| **DWS** | `public_dws.*` | Lightweight business process aggregations | Table |
| **ADS** | `public_ads.*` | Application layer — DRG analysis, readmission risk | Table |

### Dimensional Model

```
dim_patient ────────────┐
                        │
dim_provider ───────────┤── fact_encounter ── fact_diagnosis
                        │       │                 │
dim_organization ───────┘       │                 │
                        │       │                 │
dim_date ───────────────┘       │                 │
                                │                 │
dim_diagnosis ──────────────────┘                 │
                                                  │
                              fact_medication ────┘
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional, for containerized PostgreSQL)
- Java 8+ (for Synthea)
- 2 GB free RAM

### 1. Clone & Configure

```bash
git clone <your-repo-url>
cd medical-dw-pipeline

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
```

### 2. Start Database

```bash
# Using Docker (recommended)
docker compose up -d

# Or use a local PostgreSQL instance
# Ensure a `medical_dw` database exists and run:
# psql -d medical_dw -f sql/init_db.sql
```

### 3. Generate Synthetic Data

```bash
# Generate 1,000 patients' healthcare data
bash scripts/download_synthea.sh 1000
```

### 4. Run ETL Pipeline

```bash
# One command: Extract → Transform → Load
python -m etl.pipeline --verbose
```

### 5. Run dbt Dimensional Modeling

```bash
cd dbt
dbt run
dbt test
```

### One-shot Full Pipeline

```bash
make reset  # Stop → rebuild → init → ETL → dbt
```

---

## Project Structure

```
medical-dw-pipeline/
│
├── etl/                        # Python ETL core
│   ├── config.py               # Configuration (DB, paths)
│   ├── extract.py              # Phase 1: CSV data extraction
│   ├── transform.py            # Phase 2: Data cleansing & standardization
│   ├── load.py                 # Phase 3: Write to PostgreSQL ODS
│   └── pipeline.py             # CLI entry point
│
├── dbt/                        # dbt dimensional modeling
│   ├── dbt_project.yml         # dbt project configuration
│   ├── profiles.yml            # Database connection config
│   ├── models/
│   │   ├── ods/                # ODS source definitions
│   │   ├── dwd/                # DWD dimension + fact tables
│   │   ├── dws/                # DWS aggregation tables
│   │   └── ads/                # ADS application layer
│   └── tests/                  # Data quality tests
│
├── airflow/                    # Airflow orchestration
│   ├── Dockerfile
│   └── dags/
│       └── medical_etl_pipeline.py
│
├── sql/                        # SQL scripts
│   └── init_db.sql             # Database initialization
│
├── scripts/
│   └── download_synthea.sh     # Data generation script
│
├── synthea/                    # Synthea output directory
├── docker-compose.yml          # Infrastructure
├── pyproject.toml              # Python project config
├── Makefile                    # Common commands
└── README.md                   # This file
```

---

## Technical Highlights

### 1. Traceable ETL Design
- Each phase independently runnable and debuggable
- Idempotent writes (TRUNCATE + INSERT) for safe re-runs
- Batch processing (10,000 rows/chunk) for memory control

### 2. Standard Dimensional Modeling
- Star Schema design following Kimball methodology
- Surrogate key + natural key separation
- SCD Type 1 support for slowly changing dimensions
- Date dimension covering 2010–2030

### 3. Data Quality Assurance
- dbt source freshness and null/unique tests
- Custom assertion tests (non-negative costs, valid ages, etc.)
- Airflow retry mechanism (1 retry, 5-minute interval)

### 4. Engineering Best Practices
- Full type annotations
- Configuration separated from code (env vars + dataclasses)
- Makefile one-command operations
- Docker Compose for dev/prod parity

---

## Business Analysis Scenarios

| Scenario | Model | Value |
|----------|-------|-------|
| **DRG Cost Analysis** | `ads.drg_analysis` | Medical cost control, procedure-standardized costing |
| **Readmission Risk** | `ads.readmission_risk` | Quality management, reducing 30-day readmissions |
| **Department Load** | `dws.agg_department_load` | Resource allocation optimization |
| **Patient Profiling** | `dws.agg_patient_segment` | Precision health management |
| **Visit Trends** | `dws.agg_daily_admissions` | Volume forecasting |

---

## Example Queries

```sql
-- Which age group costs the most per encounter?
SELECT age_group, round(avg(total_claim_cost), 2) AS avg_cost
FROM public_dwd.fact_encounter fe
JOIN public_dwd.dim_patient dp ON fe.patient_sk = dp.patient_sk
GROUP BY age_group
ORDER BY avg_cost DESC;

-- What are the most expensive diagnoses?
SELECT diagnosis_desc, avg_total_cost, median_total_cost
FROM public_ads.drg_analysis
ORDER BY avg_total_cost DESC
LIMIT 10;

-- High readmission risk patients
SELECT patient_id, total_admissions, risk_level
FROM public_ads.readmission_risk
WHERE risk_level = '高风险'
ORDER BY total_admissions DESC;
```

---

MIT
