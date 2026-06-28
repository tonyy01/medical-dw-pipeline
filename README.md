# 医疗数据仓库 ETL Pipeline 🏥

> **从合成医疗数据到分层数据仓库的完整工程化实现**
>
> 作者：南方医科大学珠江医院 · 大数据中心

---

## 项目概览

本项目展示了一个**生产级数据工程 Pipeline** 的完整构建过程，涵盖数据采集、清洗转换、维度建模、任务编排和质量监控。

使用 **Synthea**（开源医疗数据生成器）模拟病人数据，通过分层架构（ODS → DWD → DWS → ADS）构建医疗数据仓库，并用 Airflow 实现全流程自动化调度。

### 核心能力

| 领域 | 技术栈 |
|------|--------|
| **数据源** | Synthea 合成医疗数据（CSV） |
| **ETL 开发** | Python (pandas, SQLAlchemy) |
| **数据建模** | dbt-core (维度建模, Star Schema) |
| **数据存储** | PostgreSQL |
| **任务编排** | Apache Airflow |
| **基础设施** | Docker Compose |
| **代码质量** | Ruff, pre-commit, pytest |

---

## 架构设计

```
                   ┌─────────────────────┐
                   │    Synthea           │
                   │  (合成医疗数据生成器)   │
                   └──────────┬──────────┘
                              │ CSV 文件
                              ▼
┌─────────────────────────────────────────────────┐
│  Phase 1: Extract (Python / pandas)              │
│  → 读取 CSV, 数据类型推断, 空值处理              │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  Phase 2: Transform (Python)                     │
│  → 清洗, 标准化, 列映射, 类型转换                │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  Phase 3: Load (SQLAlchemy → PostgreSQL)         │
│  → 写入 ODS 层 (原始数据, 仅做类型转换)          │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│              dbt 维度建模                         │
├─────────────────────────────────────────────────┤
│  ODS (操作数据层) — 11 张原始表                   │
│    ↓                                              │
│  DWD (明细数据层) — 维度表 + 事实表 (Star Schema) │
│    ↓                                              │
│  DWS (汇总数据层) — 按天/科室/患者群汇总          │
│    ↓                                              │
│  ADS (应用数据层) — DRG 分析, 再入院风险           │
└─────────────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│          Airflow 自动调度 (每日 06:00)            │
│  check → etl → dbt(ods→dwd→dws→ads) → test     │
└─────────────────────────────────────────────────┘
```

### 数据分层说明

| 层级 | Schema | 说明 | 物化策略 |
|------|--------|------|----------|
| **ODS** | `ods.*` | 操作数据层，与 Synthea CSV 结构一致，仅做类型转换 | View |
| **DWD** | `dwd.*` | 明细数据层，星型维度建模（5 维 + 3 事实） | Table |
| **DWS** | `dws.*` | 汇总数据层，按业务过程轻量聚合 | Table |
| **ADS** | `ads.*` | 应用数据层，DRG 分析、再入院风险评估 | Table |

### 维度模型

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

## 快速开始

### 前置条件

- Python 3.11+
- Docker & Docker Compose
- Java 8+ (运行 Synthea 用)
- 2 GB 可用内存

### 1. 克隆并配置环境

```bash
git clone <your-repo-url>
cd medical-dw-pipeline

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
```

### 2. 启动数据库

```bash
docker compose up -d
# 等待 PostgreSQL 就绪
docker compose logs -f postgres  # 看到 "ready to accept connections" 即可
```

### 3. 生成模拟数据

```bash
# 生成 1000 个病人的医疗数据
bash scripts/download_synthea.sh 1000
```

### 4. 运行 ETL Pipeline

```bash
# 一键执行 Extract → Transform → Load
python -m etl.pipeline --verbose
```

### 5. 运行 dbt 维度建模

```bash
cd dbt
dbt run
dbt test
```

### 一键全流程

```bash
make reset  # 停服务 → 重建 → 初始化 → ETL → dbt
```

---

## 项目结构

```
medical-dw-pipeline/
│
├── etl/                        # Python ETL 核心
│   ├── config.py               # 配置管理（数据库、路径）
│   ├── extract.py              # Phase 1: CSV 数据提取
│   ├── transform.py            # Phase 2: 清洗与标准化
│   ├── load.py                 # Phase 3: 写入 PostgreSQL ODS
│   └── pipeline.py             # CLI 入口
│
├── dbt/                        # dbt 维度建模
│   ├── dbt_project.yml         # dbt 项目配置
│   ├── profiles.yml            # 数据库连接配置
│   ├── models/
│   │   ├── ods/                # ODS 源定义
│   │   ├── dwd/                # DWD 维度 + 事实表
│   │   ├── dws/                # DWS 汇总表
│   │   └── ads/                # ADS 应用层
│   └── tests/                  # 数据质量测试
│
├── airflow/                    # Airflow 编排
│   ├── Dockerfile
│   └── dags/
│       └── medical_etl_pipeline.py
│
├── sql/                        # SQL 脚本
│   └── init_db.sql             # 数据库初始化
│
├── scripts/
│   └── download_synthea.sh     # 数据生成脚本
│
├── synthea/                    # Synthea 输出目录
├── docker-compose.yml          # 基础设施
├── pyproject.toml              # Python 项目配置
├── Makefile                    # 常用命令
└── README.md                   # 本文件
```

---

## 技术亮点

### 1. 可追溯的 ETL 设计
- 每阶段独立日志，可单独运行/调试
- 幂等写入（TRUNCATE + INSERT），支持重跑
- 分批写入（默认 10,000 行/批），控制内存

### 2. 标准维度建模
- Star Schema 设计，符合 Kimball 方法论
- 代理键 + 自然键分离
- 缓慢变化维度（SCD Type 1）支持
- 日期维度表覆盖 2010-2030 年

### 3. 数据质量保障
- dbt source freshness 测试
- 自定义断言测试（费用非负、年龄不超限等）
- Airflow retry 机制（最多重试 1 次，5 分钟间隔）

### 4. 工程最佳实践
- 类型注解全覆盖
- 配置与代码分离（环境变量 + dataclass）
- Makefile 一键操作
- Docker Compose 开发/部署一体化

---

## 适用场景分析

本项目模拟的医疗数据仓库可以直接支撑以下业务分析：

| 分析场景 | 对应模型 | 价值 |
|----------|----------|------|
| **DRG 分组费用分析** | `ads.drg_analysis` | 医保控费，按病种标化费用 |
| **再入院风险评估** | `ads.readmission_risk` | 医疗质量管理，降低 30 天再入院率 |
| **科室负荷监控** | `dws.agg_department_load` | 资源配置优化 |
| **患者画像分析** | `dws.agg_patient_segment` | 精准健康管理 |
| **就诊趋势分析** | `dws.agg_daily_admissions` | 业务量预测 |

---

## 扩展方向

- [ ] **接入真实医疗数据**：替换 Synthea 数据源为 MIMIC-IV
- [ ] **实时流处理**：增加 Kafka + Flink 处理实时设备数据
- [ ] **数据可视化**：接入 Apache Superset / Evidence
- [ ] **数据血缘**：集成 dbt 文档 + 血缘图
- [ ] **CI/CD**：GitHub Actions 自动化测试
- [ ] **数据湖**：增加 Iceberg / Hudi 支持历史版本
- [ ] **数据治理**：增加元数据管理、数据字典

---

## License

MIT
