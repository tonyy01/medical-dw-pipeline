"""数据提取模块 — 从 Synthea CSV 读取原始数据"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from etl.config import etl_config

logger = logging.getLogger(__name__)


def find_csv_files(csv_dir: Optional[Path] = None) -> Dict[str, Path]:
    """扫描目录，查找 Synthea 输出的所有 CSV 文件。

    Returns:
        {表名: 文件路径} 的映射字典
    """
    csv_dir = csv_dir or etl_config.synthea_csv_dir

    if not csv_dir.exists():
        logger.warning("CSV 目录不存在: %s", csv_dir)
        return {}

    csv_files: Dict[str, Path] = {}
    for f in sorted(csv_dir.glob("*.csv")):
        table_name = f.stem  # 文件名（不含扩展名）
        if table_name in etl_config.csv_to_table:
            csv_files[table_name] = f
            logger.debug("发现 CSV: %s → %s", f.name, etl_config.csv_to_table[table_name])

    logger.info("在 %s 中找到 %d 个 CSV 文件", csv_dir, len(csv_files))
    return csv_files


def read_csv(file_path: Path, **kwargs) -> pd.DataFrame:
    """读取单个 CSV 文件为 DataFrame。

    自动处理 Synthea CSV 的常见问题：
      - 编码：UTF-8
      - 空字符串 → NaN
      - 低精度浮点数
    """
    logger.info("读取 CSV: %s", file_path.name)
    df = pd.read_csv(
        file_path,
        dtype_backend="numpy_nullable",
        low_memory=False,
        **kwargs,
    )
    # 去除列名首尾空格
    df.columns = df.columns.str.strip()
    logger.info("  行数: %d, 列数: %d", len(df), len(df.columns))
    return df


def extract_all(csv_dir: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    """提取所有 Synthea CSV 文件，返回 {表名: DataFrame}。"""
    csv_files = find_csv_files(csv_dir)
    if not csv_files:
        logger.warning("没有找到 CSV 文件，请先运行 scripts/download_synthea.sh")
        return {}

    dataframes: Dict[str, pd.DataFrame] = {}
    for table_name, file_path in csv_files.items():
        try:
            df = read_csv(file_path)
            dataframes[table_name] = df
        except Exception as e:
            logger.error("读取 %s 失败: %s", file_path.name, e)
            raise

    logger.info("成功提取 %d 个表的数据", len(dataframes))
    return dataframes
