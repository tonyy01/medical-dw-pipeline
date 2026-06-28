"""ETL Pipeline 主入口

执行完整的 Extract → Transform → Load 流程：
  1. 从 Synthea CSV 读取原始数据
  2. 数据清洗与标准化
  3. 写入 PostgreSQL ODS 层
  4. （可选）调用 dbt 执行维度建模
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

from etl.config import etl_config
from etl.extract import extract_all
from etl.load import create_db_engine, load_all
from etl.transform import transform_all

logger = logging.getLogger(__name__)

# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def run_dbt(target: str = "dev") -> bool:
    """运行 dbt 模型"""
    dbt_dir = etl_config.dbt_project_dir
    if not (dbt_dir / "dbt_project.yml").exists():
        logger.warning("dbt 项目不存在，跳过")
        return False

    logger.info("运行 dbt models (target=%s)...", target)
    result = subprocess.run(
        ["dbt", "run", "--target", target],
        cwd=str(dbt_dir),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("dbt run 失败:\n%s", result.stderr)
        return False

    # 运行 dbt test
    logger.info("运行 dbt tests...")
    test_result = subprocess.run(
        ["dbt", "test", "--target", target],
        cwd=str(dbt_dir),
        capture_output=True,
        text=True,
    )
    if test_result.returncode != 0:
        logger.warning("dbt test 有失败:\n%s", test_result.stderr)

    logger.info("dbt 完成")
    return True


@click.command()
@click.option("--csv-dir", default=None, help="Synthea CSV 目录路径")
@click.option("--no-load", is_flag=True, help="只做 ETL 不写入数据库")
@click.option("--truncate/--no-truncate", default=True, help="写入前是否清空目标表")
@click.option("--run-dbt", "run_dbt_flag", is_flag=True, help="ETL 完成后自动运行 dbt")
@click.option("--verbose", "-v", is_flag=True, help="详细日志")
def main(csv_dir, no_load, truncate, run_dbt_flag, verbose):
    """医疗数据仓库 ETL Pipeline

    执行 Extract → Transform → Load 全流程。
    """
    setup_logging(verbose)
    logger.info("=" * 50)
    logger.info("医疗数据仓库 ETL Pipeline 启动")
    logger.info("=" * 50)

    # --- Phase 1: Extract ---
    logger.info("[Phase 1/3] 数据提取 (Extract)")
    raw_data = extract_all(Path(csv_dir) if csv_dir else None)
    if not raw_data:
        logger.error("没有数据可处理，退出")
        sys.exit(1)

    # --- Phase 2: Transform ---
    logger.info("[Phase 2/3] 数据清洗 (Transform)")
    cleaned_data = transform_all(raw_data)

    # 打印统计
    for table_name, df in cleaned_data.items():
        logger.debug("  %s: %d 行", table_name, len(df))

    # --- Phase 3: Load ---
    logger.info("[Phase 3/3] 数据加载 (Load)")
    if no_load:
        logger.info("--no-load 模式，跳过数据库写入")
    else:
        engine = create_db_engine()
        try:
            results = load_all(cleaned_data, engine=engine, truncate_first=truncate)
            total_rows = sum(results.values())
            logger.info("成功写入 %d 行数据到 ODS 层", total_rows)
        finally:
            engine.dispose()

    # --- Optional: dbt ---
    if run_dbt_flag:
        logger.info("[Extra] 运行 dbt 维度建模...")
        run_dbt()

    logger.info("=" * 50)
    logger.info("ETL Pipeline 完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
