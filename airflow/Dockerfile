FROM apache/airflow:2.9.1-python3.11

USER root

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# 安装 Python 依赖
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY dags /opt/airflow/dags
