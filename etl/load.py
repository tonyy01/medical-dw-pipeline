"""数据加载模块 — 将清洗后的 DataFrame 写入 PostgreSQL ODS 层"""

from __future__ import annotations

import logging
from typing import Dict, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from etl.config import DatabaseConfig, ETLConfig, db_config, etl_config

logger = logging.getLogger(__name__)


def create_db_engine(config: Optional[DatabaseConfig] = None):
    """创建数据库引擎"""
    cfg = config or db_config
    engine = create_engine(
        cfg.connection_string,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
    logger.info("数据库连接: %s@%s:%d/%s", cfg.user, cfg.host, cfg.port, cfg.database)
    return engine


def truncate_table(engine, table_name: str) -> None:
    """清空表（确保幂等）"""
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        conn.commit()
    logger.info("清空表: %s", table_name)


def load_dataframe(
    engine,
    df: pd.DataFrame,
    table_name: str,
    batch_size: Optional[int] = None,
    if_exists: str = "append",
) -> int:
    """将 DataFrame 写入数据库表。

    Args:
        engine: SQLAlchemy 引擎
        df: 要写入的数据
        table_name: 目标表名（含 schema，如 ods.patients）
        batch_size: 每批写入行数
        if_exists: 'append' | 'replace' | 'fail'

    Returns:
        写入的行数
    """
    bs = batch_size or etl_config.batch_size

    try:
        # 分批写入，避免大数据量时内存溢出
        rows = df.to_sql(
            name=table_name.split(".")[1] if "." in table_name else table_name,
            schema=table_name.split(".")[0] if "." in table_name else None,
            con=engine,
            if_exists=if_exists,
            index=False,
            method=None,
            chunksize=bs,
        )
        logger.info("写入 %s: %d 行", table_name, rows)
        return rows
    except SQLAlchemyError as e:
        logger.error("写入 %s 失败: %s", table_name, e)
        raise


def load_all(
    dataframes: Dict[str, pd.DataFrame],
    engine=None,
    truncate_first: bool = True,
) -> Dict[str, int]:
    """将清洗后的数据全部加载到 ODS 表。

    Args:
        dataframes: {表名: 清洗后的 DataFrame}
        engine: 数据库引擎（默认创建新连接）
        truncate_first: 是否先清空目标表（确保幂等）

    Returns:
        {表名: 写入行数}
    """
    engine = engine or create_db_engine()
    results = {}

    for table_name, df in dataframes.items():
        target_table = etl_config.csv_to_table.get(table_name)
        if not target_table:
            logger.warning("表 %s 无目标映射，跳过", table_name)
            continue

        if df.empty:
            logger.warning("表 %s 数据为空，跳过", table_name)
            continue

        try:
            if truncate_first:
                truncate_table(engine, target_table)
            rows = load_dataframe(engine, df, target_table)
            results[table_name] = rows
        except Exception as e:
            logger.error("加载 %s → %s 失败: %s", table_name, target_table, e)
            raise

    logger.info("ODS 层加载完成，共写入 %d 张表", len(results))
    return results
