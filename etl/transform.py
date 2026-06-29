"""数据清洗与转换模块

Synthea 原始 CSV → 清洗后的 DataFrame（可加载到 ODS 层）
"""

from __future__ import annotations

import logging
import uuid

import pandas as pd

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────


def _generate_id(n: int) -> list[str]:
    """为没有自然主键的表生成合成 ID"""
    return [str(uuid.uuid4()) for _ in range(n)]


def _coerce_dates(df: pd.DataFrame, cols: list[str]) -> None:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")


def _coerce_numeric(df: pd.DataFrame, cols: list[str]) -> None:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")


def _rename_and_select(df: pd.DataFrame, rename_map: dict[str, str], expected_cols: list[str]) -> pd.DataFrame:
    df = df.rename(columns=rename_map)
    existing = [c for c in expected_cols if c in df.columns]
    return df[existing]


# ──────────────────────────────────────────────
# 各表清洗函数
# ──────────────────────────────────────────────


def clean_patients(df: pd.DataFrame) -> pd.DataFrame:
    """清洗病人数据"""
    df = df.copy()
    _coerce_dates(df, ["BIRTHDATE", "DEATHDATE"])
    _coerce_numeric(df, ["INCOME", "HEALTHCARE_EXPENSES", "HEALTHCARE_COVERAGE"])

    if "GENDER" in df.columns:
        df["GENDER"] = df["GENDER"].str.upper().str.strip()

    rename_map = {
        "Id": "patient_id", "BIRTHDATE": "birth_date", "DEATHDATE": "death_date",
        "GENDER": "gender", "RACE": "race", "ETHNICITY": "ethnicity",
        "MARITAL": "marital_status", "BLOODTYPE": "blood_type",
        "CITY": "address_city", "STATE": "address_state", "COUNTY": "address_county",
        "ZIP": "address_zip", "INCOME": "income",
        "HEALTHCARE_EXPENSES": "healthcare_expenses",
        "HEALTHCARE_COVERAGE": "healthcare_coverage",
    }
    expected = [
        "patient_id", "birth_date", "death_date", "gender", "race",
        "ethnicity", "marital_status", "blood_type",
        "address_city", "address_state", "address_county", "address_zip",
        "income", "healthcare_expenses", "healthcare_coverage",
    ]
    logger.info("  patients: %d 行 → %d 列", len(df), len(expected))
    return _rename_and_select(df, rename_map, expected)


def clean_encounters(df: pd.DataFrame) -> pd.DataFrame:
    """清洗就诊数据"""
    df = df.copy()
    _coerce_dates(df, ["START", "STOP"])
    _coerce_numeric(df, ["BASE_ENCOUNTER_COST", "TOTAL_CLAIM_COST", "PAYER_COVERAGE"])

    rename_map = {
        "Id": "encounter_id", "PATIENT": "patient_id",
        "START": "encounter_start", "STOP": "encounter_stop",
        "ENCOUNTERCLASS": "encounter_class", "DESCRIPTION": "description",
        "BASE_ENCOUNTER_COST": "base_encounter_cost",
        "TOTAL_CLAIM_COST": "total_claim_cost",
        "PAYER_COVERAGE": "payer_coverage",
        "REASONCODE": "reasoncode", "REASONDESCRIPTION": "reasondescription",
        "PROVIDER": "provider_id", "ORGANIZATION": "organization_id",
    }
    expected = [
        "encounter_id", "patient_id", "encounter_start", "encounter_stop",
        "encounter_class", "description", "base_encounter_cost",
        "total_claim_cost", "payer_coverage", "reasondescription",
        "provider_id", "organization_id",
    ]
    logger.info("  encounters: %d 行 → %d 列", len(df), len(expected))
    return _rename_and_select(df, rename_map, expected)


def clean_conditions(df: pd.DataFrame) -> pd.DataFrame:
    """清洗诊断数据（无 Id 列，生成合成主键）"""
    df = df.copy()
    _coerce_dates(df, ["START", "STOP"])

    df["condition_id"] = _generate_id(len(df))
    rename_map = {
        "PATIENT": "patient_id", "ENCOUNTER": "encounter_id",
        "CODE": "code", "DESCRIPTION": "description",
        "START": "condition_start", "STOP": "condition_stop",
    }
    expected = [
        "condition_id", "patient_id", "encounter_id", "code",
        "description", "condition_start", "condition_stop",
    ]
    logger.info("  conditions: %d 行 → %d 列", len(df), len(expected))
    return _rename_and_select(df, rename_map, expected)


def clean_medications(df: pd.DataFrame) -> pd.DataFrame:
    """清洗用药数据（无 Id 列，生成合成主键）"""
    df = df.copy()
    _coerce_dates(df, ["START", "STOP"])
    _coerce_numeric(df, ["BASE_COST", "PAYER_COVERAGE", "TOTALCOST", "DISPENSES"])

    if "DISPENSES" in df.columns:
        df["DISPENSES"] = df["DISPENSES"].fillna(0).astype(int)

    df["medication_id"] = _generate_id(len(df))
    rename_map = {
        "PATIENT": "patient_id", "ENCOUNTER": "encounter_id",
        "CODE": "code", "DESCRIPTION": "description",
        "BASE_COST": "base_cost", "PAYER_COVERAGE": "payer_coverage",
        "DISPENSES": "dispenses", "TOTALCOST": "total_cost",
        "REASONCODE": "reasoncode", "REASONDESCRIPTION": "reasondescription",
        "START": "start_date", "STOP": "stop_date",
    }
    expected = [
        "medication_id", "patient_id", "encounter_id", "code",
        "description", "base_cost", "payer_coverage", "dispenses",
        "total_cost", "reasondescription", "start_date", "stop_date",
    ]
    logger.info("  medications: %d 行 → %d 列", len(df), len(expected))
    return _rename_and_select(df, rename_map, expected)


def clean_observations(df: pd.DataFrame) -> pd.DataFrame:
    """清洗检验检查数据（无 Id 列，生成合成主键）"""
    df = df.copy()
    _coerce_dates(df, ["DATE"])

    # VALUE 列可能是文本或数值，保持原样
    df["observation_id"] = _generate_id(len(df))
    rename_map = {
        "PATIENT": "patient_id", "ENCOUNTER": "encounter_id",
        "CATEGORY": "category", "CODE": "code",
        "DESCRIPTION": "description", "VALUE": "value",
        "UNITS": "units", "DATE": "observation_date",
    }
    expected = [
        "observation_id", "patient_id", "encounter_id", "category",
        "code", "description", "value", "units", "observation_date",
    ]
    logger.info("  observations: %d 行 → %d 列", len(df), len(expected))
    return _rename_and_select(df, rename_map, expected)


def clean_imaging_studies(df: pd.DataFrame) -> pd.DataFrame:
    """清洗影像数据（Synthea Id 可能有重复，覆盖为合成主键）"""
    df = df.copy()
    _coerce_dates(df, ["DATE"])

    df["imaging_id"] = _generate_id(len(df))
    rename_map = {
        "PATIENT": "patient_id", "ENCOUNTER": "encounter_id",
        "BODYSITE_CODE": "bodysite_code",
        "BODYSITE_DESCRIPTION": "bodysite_description",
        "MODALITY_CODE": "modality_code",
        "MODALITY_DESCRIPTION": "modality_description",
        "SOP_CODE": "sop_code", "SOP_DESCRIPTION": "sop_description",
        "DATE": "imaging_date",
    }
    expected = [
        "imaging_id", "patient_id", "encounter_id",
        "bodysite_code", "bodysite_description",
        "modality_code", "modality_description",
        "sop_code", "sop_description", "imaging_date",
    ]
    logger.info("  imaging_studies: %d 行 → %d 列", len(df), len(expected))
    return _rename_and_select(df, rename_map, expected)


def clean_procedures(df: pd.DataFrame) -> pd.DataFrame:
    """清洗手术/操作数据（无 Id 列，生成合成主键）"""
    df = df.copy()
    _coerce_dates(df, ["START", "STOP"])
    _coerce_numeric(df, ["BASE_COST"])

    df["procedure_id"] = _generate_id(len(df))
    rename_map = {
        "PATIENT": "patient_id", "ENCOUNTER": "encounter_id",
        "CODE": "code", "DESCRIPTION": "description",
        "BASE_COST": "base_cost",
    }
    expected = [
        "procedure_id", "patient_id", "encounter_id",
        "code", "description", "base_cost",
    ]
    logger.info("  procedures: %d 行 → %d 列", len(df), len(expected))
    return _rename_and_select(df, rename_map, expected)


def clean_organizations(df: pd.DataFrame) -> pd.DataFrame:
    """清洗机构数据"""
    rename_map = {
        "Id": "organization_id", "NAME": "name",
        "CITY": "address_city", "STATE": "address_state",
        "ZIP": "address_zip", "PHONE": "phone",
    }
    expected = ["organization_id", "name", "address_city", "address_state", "address_zip", "phone"]
    logger.info("  organizations: %d 行 → %d 列", len(df), len(expected))
    return _rename_and_select(df, rename_map, expected)


def clean_providers(df: pd.DataFrame) -> pd.DataFrame:
    """清洗医护人员数据"""
    if "GENDER" in df.columns:
        df["GENDER"] = df["GENDER"].str.upper().str.strip()

    rename_map = {
        "Id": "provider_id", "ORGANIZATION": "organization_id",
        "NAME": "name", "GENDER": "gender",
        "SPECIALITY": "specialty",  # 注意：Synthea 列名是 SPECIALITY（少个 L ？实际是 SPECIALITY）
        "CITY": "address_city", "STATE": "address_state", "ZIP": "address_zip",
    }
    expected = [
        "provider_id", "organization_id", "name", "gender", "specialty",
        "address_city", "address_state", "address_zip",
    ]
    logger.info("  providers: %d 行 → %d 列", len(df), len(expected))
    return _rename_and_select(df, rename_map, expected)


def clean_payer_transitions(df: pd.DataFrame) -> pd.DataFrame:
    """清洗支付方变更数据（无 Id 列，生成合成主键）"""
    df = df.copy()
    for col in ["START_DATE", "END_DATE"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    df["transition_id"] = _generate_id(len(df))
    rename_map = {
        "PATIENT": "patient_id", "MEMBERID": "member_id",
        "PAYER": "payer_id",
        "START_DATE": "ownership_start", "END_DATE": "ownership_end",
    }
    expected = [
        "transition_id", "patient_id", "member_id", "payer_id",
        "ownership_start", "ownership_end",
    ]
    logger.info("  payer_transitions: %d 行 → %d 列", len(df), len(expected))
    return _rename_and_select(df, rename_map, expected)


def clean_payers(df: pd.DataFrame) -> pd.DataFrame:
    """清洗支付方数据"""
    _coerce_numeric(df, ["AMOUNT_COVERED", "AMOUNT_UNCOVERED", "REVENUE"])
    count_cols = [
        "COVERED_ENCOUNTERS", "UNCOVERED_ENCOUNTERS",
        "COVERED_MEDICATIONS", "UNCOVERED_MEDICATIONS",
        "COVERED_PROCEDURES", "UNCOVERED_PROCEDURES",
        "COVERED_IMMUNIZATIONS", "UNCOVERED_IMMUNIZATIONS",
    ]
    for col in count_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    rename_map = {
        "Id": "payer_id", "NAME": "name",
        "AMOUNT_COVERED": "amount_covered", "AMOUNT_UNCOVERED": "amount_uncovered",
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
    expected = [
        "payer_id", "name", "amount_covered", "amount_uncovered", "revenue",
        "covered_encounters", "uncovered_encounters",
        "covered_medications", "uncovered_medications",
        "covered_procedures", "uncovered_procedures",
        "covered_immunizations", "uncovered_immunizations",
    ]
    logger.info("  payers: %d 行 → %d 列", len(df), len(expected))
    return _rename_and_select(df, rename_map, expected)


# ──────────────────────────────────────────────
# 调度
# ──────────────────────────────────────────────

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
