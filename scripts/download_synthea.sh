#!/usr/bin/env bash
# ============================================================
# Synthea 下载与数据生成脚本
# 用于生成模拟的医疗数据，作为 ETL Pipeline 的数据源
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SYNTHEA_DIR="$PROJECT_DIR/synthea"
OUTPUT_DIR="$SYNTHEA_DIR/output"

SYNTHEA_VERSION="2.10.0"
SYNTHEA_JAR="$SYNTHEA_DIR/synthea.jar"
SYNTHEA_URL="https://github.com/synthetichealth/synthea/releases/download/v${SYNTHEA_VERSION}/synthea-${SYNTHEA_VERSION}.jar"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

# --- 1. 检查 Java ---
check_java() {
    if ! command -v java &>/dev/null; then
        error "需要 Java 8+，请先安装：sudo apt install openjdk-17-jre"
        exit 1
    fi
    java_version=$(java -version 2>&1 | head -1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [ "$java_version" -lt 8 ] && [ "$java_version" -ge 1 ]; then
        error "Java 版本过低（$java_version），需要 Java 8+"
        exit 1
    fi
    info "Java 就绪：$(java -version 2>&1 | head -1)"
}

# --- 2. 下载 Synthea Jar ---
download_synthea() {
    if [ -f "$SYNTHEA_JAR" ]; then
        warn "Synthea jar 已存在，跳过下载"
        return
    fi
    mkdir -p "$SYNTHEA_DIR"
    echo "下载 Synthea v${SYNTHEA_VERSION} ..."
    curl -L -o "$SYNTHEA_JAR" "$SYNTHEA_URL"
    info "Synthea 下载完成"
}

# --- 3. 生成数据 ---
generate_data() {
    local population="${1:-1000}"
    local seed="${2:-42}"

    mkdir -p "$OUTPUT_DIR"
    echo "生成 ${population} 个病人的模拟医疗数据（seed=${seed}）..."

    java -jar "$SYNTHEA_JAR" \
        -p "$population" \
        -s "$seed" \
        --exporter.fhir.export=false \
        --exporter.practitioner.fhir.export=false \
        --exporter.csv.export=true \
        --exporter.csv.folder.export=true \
        --exporter.baseDirectory="$OUTPUT_DIR"

    info "数据生成完成！输出目录：$OUTPUT_DIR"
}

# --- 4. 统计输出 ---
show_stats() {
    echo ""
    echo "========== 生成文件统计 =========="
    for f in "$OUTPUT_DIR"/csv/*.csv; do
        basename=$(basename "$f")
        lines=$(wc -l < "$f")
        printf "  %-35s %s 行\n" "$basename" "$lines"
    done
    echo "=================================="
}

# --- Main ---
main() {
    echo "=========================================="
    echo "  Synthea 医疗数据生成器"
    echo "=========================================="
    echo ""

    check_java
    download_synthea
    generate_data "$@"
    show_stats

    echo ""
    info "下一步：运行 ETL Pipeline"
    echo "  cd $PROJECT_DIR && make run-etl"
}

main "$@"
