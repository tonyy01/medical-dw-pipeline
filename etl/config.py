"""ETL 配置管理"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

load_dotenv()


# --- 项目路径 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SYNTHEA_OUTPUT_DIR = PROJECT_ROOT / "synthea" / "output" / "csv"
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class DatabaseConfig:
    """PostgreSQL 连接配置"""

    host: str = os.getenv("PGHOST", "localhost")
    port: int = int(os.getenv("PGPORT", "5432"))
    database: str = os.getenv("PGDATABASE", "medical_dw")
    user: str = os.getenv("PGUSER", "postgres")
    password: str = os.getenv("PGPASSWORD", "postgres")

    @property
    def connection_string(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass
class ETLConfig:
    """ETL 流程配置"""

    # Synthea CSV 文件与对应 ODS 表的映射
    csv_to_table: Dict[str, str] = field(default_factory=lambda: {
        "patients": "ods.patients",
        "encounters": "ods.encounters",
        "conditions": "ods.conditions",
        "medications": "ods.medications",
        "observations": "ods.observations",
        "imaging_studies": "ods.imaging_studies",
        "procedures": "ods.procedures",
        "organizations": "ods.organizations",
        "providers": "ods.providers",
        "payer_transitions": "ods.payer_transitions",
        "payers": "ods.payers",
    })

    # 批量写入大小
    batch_size: int = 10000

    # dbt 项目路径
    dbt_project_dir: Path = PROJECT_ROOT / "dbt"

    # Synthea CSV 输出目录
    synthea_csv_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("SYNTHEA_CSV_DIR", str(SYNTHEA_OUTPUT_DIR))
        )
    )


# 全局配置实例
db_config = DatabaseConfig()
etl_config = ETLConfig()
