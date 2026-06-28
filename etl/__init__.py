"""
medical-dw-pipeline — 医疗数据仓库 ETL Pipeline

基于 Synthea 合成医疗数据，完整实现：
  - Extract: CSV → Pandas DataFrame
  - Transform: 数据清洗、标准化、类型转换
  - Load: 写入 PostgreSQL ODS 层
  - dbt: 维度建模 (ODS → DWD → DWS → ADS)
  - Airflow: 全流程编排
"""
