"""
医疗数据仓库 ETL Pipeline — Airflow DAG

调度流程：
  1. check_data_ready → 确认 Synthea 数据已生成
  2. run_etl → 执行 Python ETL（extract → transform → load）
  3. run_dbt_ods → dbt: ODS 层（view 验证）
  4. run_dbt_dwd → dbt: DWD 维度表
  5. run_dbt_dws → dbt: DWS 汇总表
  6. run_dbt_ads → dbt: ADS 应用层
  7. run_dbt_test → dbt test
  8. data_quality_report → 数据质量报告（后续扩展）

运行频率：每天 06:00（可在 DAG 参数中调整）
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator

# ============================================================
# 配置
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
ETL_DIR = PROJECT_DIR / "etl"
DBT_DIR = PROJECT_DIR / "dbt"
SYNTHEA_DIR = PROJECT_DIR / "synthea" / "output" / "csv"

default_args = {
    "owner": "data_team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

# ============================================================
# DAG 定义
# ============================================================

dag = DAG(
    dag_id="medical_etl_pipeline",
    description="医疗数据仓库 ETL Pipeline — 从 Synthea 到 ODS/DWD/DWS/ADS 的全自动调度",
    default_args=default_args,
    schedule_interval="0 6 * * *",         # 每天 06:00 运行
    start_date=datetime(2024, 6, 1),
    catchup=False,
    tags=["medical", "etl", "data-warehouse"],
    doc_md=__doc__,
)


# ============================================================
# Task: 检查数据
# ============================================================

CHECK_DATA_SCRIPT = f"""
echo "检查 Synthea 数据目录..."
if [ -d "{SYNTHEA_DIR}" ] && [ "$(ls -A {SYNTHEA_DIR}/*.csv 2>/dev/null)" ]; then
    echo "数据就绪：{SYNTHEA_DIR}"
    echo "CSV 文件列表："
    ls -lh {SYNTHEA_DIR}/*.csv 2>/dev/null | head -20
    exit 0
else
    echo "数据未就绪：{SYNTHEA_DIR} 中无 CSV 文件"
    echo "请先运行：make generate-data"
    exit 1
fi
"""

check_data_ready = BashOperator(
    task_id="check_data_ready",
    bash_command=CHECK_DATA_SCRIPT,
    dag=dag,
)


# ============================================================
# Task: Python ETL（Extract → Transform → Load ODS）
# ============================================================

run_etl = BashOperator(
    task_id="run_etl",
    bash_command=(
        f"cd {PROJECT_DIR} && "
        f"python -m etl.pipeline --csv-dir {SYNTHEA_DIR} --verbose"
    ),
    dag=dag,
)


# ============================================================
# Task: dbt — ODS 层 (view 验证)
# ============================================================

run_dbt_ods = BashOperator(
    task_id="run_dbt_ods",
    bash_command=f"cd {DBT_DIR} && dbt run --models tag:ods --target dev",
    dag=dag,
)


# ============================================================
# Task: dbt — DWD 层（维度建模）
# ============================================================

run_dbt_dwd = BashOperator(
    task_id="run_dbt_dwd",
    bash_command=f"cd {DBT_DIR} && dbt run --models tag:dwd --target dev",
    dag=dag,
)


# ============================================================
# Task: dbt — DWS 层（汇总）
# ============================================================

run_dbt_dws = BashOperator(
    task_id="run_dbt_dws",
    bash_command=f"cd {DBT_DIR} && dbt run --models tag:dws --target dev",
    dag=dag,
)


# ============================================================
# Task: dbt — ADS 层（应用层）
# ============================================================

run_dbt_ads = BashOperator(
    task_id="run_dbt_ads",
    bash_command=f"cd {DBT_DIR} && dbt run --models tag:ads --target dev",
    dag=dag,
)


# ============================================================
# Task: dbt test — 数据质量测试
# ============================================================

run_dbt_test = BashOperator(
    task_id="run_dbt_test",
    bash_command=f"cd {DBT_DIR} && dbt test --target dev",
    dag=dag,
)


# ============================================================
# Task: 数据质量报告
# ============================================================

def generate_quality_report(**context) -> None:
    """生成简单的数据质量报告（后续可扩展为完整报告系统）"""
    from sqlalchemy import create_engine, text

    engine = create_engine(
        f"postgresql://{os.getenv('PGUSER', 'postgres')}"
        f":{os.getenv('PGPASSWORD', 'postgres')}"
        f"@{os.getenv('PGHOST', 'localhost')}"
        f":{os.getenv('PGPORT', '5432')}"
        f"/{os.getenv('PGDATABASE', 'medical_dw')}"
    )

    report = {"timestamp": datetime.now().isoformat(), "checks": []}

    with engine.connect() as conn:
        for schema in ["ods", "dwd", "dws", "ads"]:
            result = conn.execute(
                text("""
                    SELECT table_name,
                           (SELECT reltuples::bigint
                            FROM pg_class
                            WHERE oid = (quote_ident(:schema) || '.' || quote_ident(table_name))::regclass
                           ) AS row_count
                    FROM information_schema.tables
                    WHERE table_schema = :schema
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """),
                {"schema": schema},
            )
            for row in result:
                report["checks"].append({
                    "schema": schema,
                    "table": row.table_name,
                    "estimated_rows": row.row_count,
                })

    # 写入报告文件
    report_dir = PROJECT_DIR / "reports"
    report_dir.mkdir(exist_ok=True)
    report_file = report_dir / f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"数据质量报告已生成：{report_file}")


data_quality_report = PythonOperator(
    task_id="data_quality_report",
    python_callable=generate_quality_report,
    dag=dag,
)


# ============================================================
# 完成标记
# ============================================================

etl_complete = DummyOperator(task_id="etl_complete", dag=dag)


# ============================================================
# 依赖关系
# ============================================================

check_data_ready >> run_etl >> run_dbt_ods >> run_dbt_dwd >> run_dbt_dws >> run_dbt_ads
run_dbt_ads >> run_dbt_test >> data_quality_report >> etl_complete
