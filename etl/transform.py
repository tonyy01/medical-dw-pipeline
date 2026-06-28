"""数据清洗与转换模块

Synthea 原始 CSV → 清洗后的 DataFrame（可加载到 ODS 层）
"""

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


def clean_patients(df: pd.DataFrame) -> pd.DataFrame:
    """清洗病人数据"""
    df = df.copy()

    # 日期列转换
    date_cols = ["BIRTHDATE", "DEATHDATE"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # 标准化性别
    if "GENDER" in df.columns:
        df["GENDER"] = df["GENDER"].str.upper().str.strip()

    # 收入列转为数值
    if "INCOME" in df.columns:
        df["INCOME"] = pd.to_numeric(df["INCOME"], errors="coerce")

    # 标准列名重命名（大写 → 小写 + 下划线）
    rename_map = {
        "Id": "patient_id",
        "BIRTHDATE": "birth_date",
        "DEATHDATE": "death_date",
        "GENDER": "gender",
        "RACE": "race",
        "ETHNICITY": "ethnicity",
        "MARITAL": "marital_status",
        "LANGUAGE": "language",
        "BLOODTYPE": "blood_type",
        "CITY": "address_city",
        "STATE": "address_state",
        "COUNTY": "address_county",
        "ZIP": "address_zip",
        "INCOME": "income",
        "HEALTHCARE_EXPENSES": "healthcare_expenses",
        "HEALTHCARE_COVERAGE": "healthcare_coverage",
    }
    df = df.rename(columns=rename_map)

    # 只保留我们定义了的列
    expected_cols = [
        "patient_id", "birth_date", "death_date", "gender", "race",
        "ethnicity", "marital_status", "language", "blood_type",
        "address_city", "address_state", "address_county", "address_zip",
        "income", "healthcare_expenses", "healthcare_coverage",
    ]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]

    logger.info("  patients: %d 行, %d 列", len(df), len(df.columns))
    return df


def clean_encounters(df: pd.DataFrame) -> pd.DataFrame:
    """清洗就诊数据"""
    df = df.copy()

    # 时间列转换
    for col in ["START", "STOP"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # 金额列
    for col in ["BASE_ENCOUNTER_COST", "TOTAL_CLAIM_COST", "PAYER_COVERAGE"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    rename_map = {
        "Id": "encounter_id",
        "PATIENT": "patient_id",
        "START": "encounter_start",
        "STOP": "encounter_stop",
        "ENCOUNTERCLASS": "encounter_class",
        "DESCRIPTION": "description",
        "BASE_ENCOUNTER_COST": "base_encounter_cost",
        "TOTAL_CLAIM_COST": "total_claim_cost",
        "PAYER_COVERAGE": "payer_coverage",
        "REASONCODE": "reasoncode",
        "REASONDESCRIPTION": "reasondescription",
        "PROVIDER": "provider_id",
        "ORGANIZATION": "organization_id",
    }
    df = df.rename(columns=rename_map)

    expected_cols = [
        "encounter_id", "patient_id", "encounter_start", "encounter_stop",
        "encounter_class", "description", "base_encounter_cost",
        "total_claim_cost", "payer_coverage", "reasondescription",
        "provider_id", "organization_id",
    ]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]

    logger.info("  encounters: %d 行, %d 列", len(df), len(df.columns))
    return df


def clean_conditions(df: pd.DataFrame) -> pd.DataFrame:
    """清洗诊断/条件数据"""
    df = df.copy()

    for col in ["START", "STOP"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    rename_map = {
        "Id": "condition_id",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "code",
        "DESCRIPTION": "description",
        "START": "condition_start",
        "STOP": "condition_stop",
    }
    df = df.rename(columns=rename_map)

    expected_cols = [
        "condition_id", "patient_id", "encounter_id", "code",
        "description", "condition_start", "condition_stop",
    ]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]

    logger.info("  conditions: %d 行, %d 列", len(df), len(df.columns))
    return df


def clean_medications(df: pd.DataFrame) -> pd.DataFrame:
    """清洗用药数据"""
    df = df.copy()

    for col in ["START", "STOP"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in ["BASE_COST", "PAYER_COVERAGE", "TOTALCOST"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "DISPENSES" in df.columns:
        df["DISPENSES"] = pd.to_numeric(df["DISPENSES"], errors="coerce").fillna(0).astype(int)

    rename_map = {
        "Id": "medication_id",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "code",
        "DESCRIPTION": "description",
        "BASE_COST": "base_cost",
        "PAYER_COVERAGE": "payer_coverage",
        "DISPENSES": "dispenses",
        "TOTALCOST": "total_cost",
        "REASONDESCRIPTION": "reasondescription",
        "START": "start_date",
        "STOP": "stop_date",
    }
    df = df.rename(columns=rename_map)

    expected_cols = [
        "medication_id", "patient_id", "encounter_id", "code",
        "description", "base_cost", "payer_coverage", "dispenses",
        "total_cost", "reasondescription", "start_date", "stop_date",
    ]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]

    logger.info("  medications: %d 行, %d 列", len(df), len(df.columns))
    return df


def clean_observations(df: pd.DataFrame) -> pd.DataFrame:
    """清洗检验检查数据"""
    df = df.copy()

    if "DATE" in df.columns:
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

    rename_map = {
        "Id": "observation_id",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CATEGORY": "category",
        "CODE": "code",
        "DESCRIPTION": "description",
        "VALUE": "value",
        "UNITS": "units",
        "DATE": "observation_date",
    }
    df = df.rename(columns=rename_map)

    expected_cols = [
        "observation_id", "patient_id", "encounter_id", "category",
        "code", "description", "value", "units", "observation_date",
    ]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]

    logger.info("  observations: %d 行, %d 列", len(df), len(df.columns))
    return df


def clean_imaging_studies(df: pd.DataFrame) -> pd.DataFrame:
    """清洗影像数据"""
    df = df.copy()

    if "DATE" in df.columns:
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

    rename_map = {
        "Id": "imaging_id",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "BODYSITE_CODE": "bodysite_code",
        "BODYSITE_DESCRIPTION": "bodysite_description",
        "MODALITY_CODE": "modality_code",
        "MODALITY_DESCRIPTION": "modality_description",
        "SOP_CODE": "sop_code",
        "SOP_DESCRIPTION": "sop_description",
        "DATE": "imaging_date",
    }
    df = df.rename(columns=rename_map)

    expected_cols = [
        "imaging_id", "patient_id", "encounter_id",
        "bodysite_code", "bodysite_description",
        "modality_code", "modality_description",
        "sop_code", "sop_description", "imaging_date",
    ]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]

    logger.info("  imaging_studies: %d 行, %d 列", len(df), len(df.columns))
    return df


def clean_procedures(df: pd.DataFrame) -> pd.DataFrame:
    """清洗手术/操作数据"""
    df = df.copy()

    if "BASE_COST" in df.columns:
        df["BASE_COST"] = pd.to_numeric(df["BASE_COST"], errors="coerce")

    rename_map = {
        "Id": "procedure_id",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "code",
        "DESCRIPTION": "description",
        "BASE_COST": "base_cost",
    }
    df = df.rename(columns=rename_map)

    expected_cols = [
        "procedure_id", "patient_id", "encounter_id",
        "code", "description", "base_cost",
    ]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]

    logger.info("  procedures: %d 行, %d 列", len(df), len(df.columns))
    return df


def clean_organizations(df: pd.DataFrame) -> pd.DataFrame:
    """清洗机构数据"""
    rename_map = {
        "Id": "organization_id",
        "NAME": "name",
        "CITY": "address_city",
        "STATE": "address_state",
        "ZIP": "address_zip",
        "PHONE": "phone",
    }
    df = df.rename(columns=rename_map)
    expected_cols = ["organization_id", "name", "address_city", "address_state", "address_zip", "phone"]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]
    logger.info("  organizations: %d 行", len(df))
    return df


def clean_providers(df: pd.DataFrame) -> pd.DataFrame:
    """清洗医生数据"""
    rename_map = {
        "Id": "provider_id",
        "ORGANIZATION": "organization_id",
        "NAME": "name",
        "GENDER": "gender",
        "SPECIALTY": "specialty",
        "CITY": "address_city",
        "STATE": "address_state",
        "ZIP": "address_zip",
    }
    df = df.rename(columns=rename_map)
    if "GENDER" in df.columns:
        df["GENDER"] = df["GENDER"].str.upper().str.strip()
    expected_cols = ["provider_id", "organization_id", "name", "gender", "specialty",
                     "address_city", "address_state", "address_zip"]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]
    logger.info("  providers: %d 行", len(df))
    return df


def clean_payer_transitions(df: pd.DataFrame) -> pd.DataFrame:
    """清洗支付方变更数据"""
    for col in ["OWNERSHIP_START", "OWNERSHIP_END"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    rename_map = {
        "Id": "transition_id",
        "PATIENT": "patient_id",
        "MEMBER_ID": "member_id",
        "PAYER": "payer_id",
        "OWNERSHIP_START": "ownership_start",
        "OWNERSHIP_END": "ownership_end",
    }
    df = df.rename(columns=rename_map)
    expected_cols = ["transition_id", "patient_id", "member_id", "payer_id",
                     "ownership_start", "ownership_end"]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]
    logger.info("  payer_transitions: %d 行", len(df))
    return df


def clean_payers(df: pd.DataFrame) -> pd.DataFrame:
    """清洗支付方数据"""
    for col in ["AMOUNT_COVERED", "AMOUNT_UNCOVERED", "REVENUE"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["COVERED_ENCOUNTERS", "UNCOVERED_ENCOUNTERS", "COVERED_MEDICATIONS",
                "UNCOVERED_MEDICATIONS", "COVERED_PROCEDURES", "UNCOVERED_PROCEDURES",
                "COVERED_IMMUNIZATIONS", "UNCOVERED_IMMUNIZATIONS"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    rename_map = {
        "Id": "payer_id",
        "NAME": "name",
        "AMOUNT_COVERED": "amount_covered",
        "AMOUNT_UNCOVERED": "amount_uncovered",
        "REVENUE": "revenue",
        "COVERED_ENCOUNTERS": "covered_encounters",
        "UNCOVERED_ENCOUNTERS": "uncovered_encounters",
        "COVERED_MEDICATIONS": "covered_medications",
        "UNCOVERED_MEDICATIONS": "uncovered_medications",
        "COVERED_PROCEDURES": "covered_procedures",
        "UNCOVERED_PROCEDURES": "uncovered_procedures",
        "COVERED_IMMUNIZATIONS": "covered_immunizations",
        "UNCOVERED_IMMUNIZATIONS": "uncovered_immunizations",
    }
    df = df.rename(columns=rename_map)
    expected_cols = ["payer_id", "name", "amount_covered", "amount_uncovered", "revenue",
                     "covered_encounters", "uncovered_encounters",
                     "covered_medications", "uncovered_medications",
                     "covered_procedures", "uncovered_procedures",
                     "covered_immunizations", "uncovered_immunizations"]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]
    logger.info("  payers: %d 行", len(df))
    return df


# 清洗函数映射表：表名 → 对应的清洗函数
CLEAN_FUNCTIONS = {
    "patients": clean_patients,
    "encounters": clean_encounters,
    "conditions": clean_conditions,
    "medications": clean_medications,
    "observations": clean_observations,
    "imaging_studies": clean_imaging_studies,
    "procedures": clean_procedures,
    "organizations": clean_organizations,
    "providers": clean_providers,
    "payer_transitions": clean_payer_transitions,
    "payers": clean_payers,
}


def transform_all(dataframes: dict) -> dict[str, pd.DataFrame]:
    """对所有提取的 DataFrame 执行清洗转换。"""
    cleaned = {}
    for table_name, df in dataframes.items():
        clean_func = CLEAN_FUNCTIONS.get(table_name)
        if clean_func:
            try:
                cleaned[table_name] = clean_func(df)
            except Exception as e:
                logger.error("清洗 %s 失败: %s", table_name, e)
                raise
        else:
            logger.warning("表 %s 没有对应的清洗函数，跳过", table_name)
    return cleaned
