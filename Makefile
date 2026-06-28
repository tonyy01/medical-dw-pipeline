.PHONY: help setup install lint format test clean run-etl run-dbt up down reset generate-data

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## 初始化环境（创建 venv + 安装依赖）
	python3 -m venv .venv && \
	. .venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -e . && \
	pip install -e ".[dev]"

install: ## 安装依赖
	pip install -e .
	pip install -e ".[dev]"

lint: ## 代码检查
	ruff check etl/
	ruff format --check etl/

format: ## 代码格式化
	ruff format etl/

test: ## 运行测试
	pytest tests/ -v --cov=etl

generate-data: ## 用 Synthea 生成模拟医疗数据
	@echo "=== 生成 Synthea 模拟数据 ==="
	cd synthea && java -jar synthea.jar -p 1000 --exporter.fhir.export=false --exporter.practitioner.fhir.export=false

init-db: ## 初始化数据库 schema
	@echo "=== 初始化 PostgreSQL schema ==="
	psql -h localhost -U postgres -d medical_dw -f sql/init_db.sql

run-etl: ## 运行 ETL 全流程（extract → transform → load）
	@echo "=== 运行 ETL Pipeline ==="
	python -m etl.pipeline

run-dbt: ## 运行 dbt 模型（数据分层建模）
	@echo "=== 运行 dbt ==="
	cd dbt && dbt run
	cd dbt && dbt test

up: ## 启动 Docker 基础设施（PostgreSQL + Airflow）
	docker compose up -d

down: ## 停止 Docker 基础设施
	docker compose down

clean: ## 清理生成文件
	rm -rf .venv
	rm -rf synthea/output
	rm -rf dbt/logs dbt/target
	rm -rf __pycache__ */__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

reset: down ## 完全重置（停服务 + 删数据 + 重建）
	docker compose down -v
	make up
	sleep 3
	make init-db
	make run-etl
	make run-dbt
