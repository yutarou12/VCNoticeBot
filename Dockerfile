# 環境構築
FROM python:3.12-slim-bullseye AS builder
WORKDIR /app
COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# 稼働環境
FROM python:3.12-slim-bullseye AS runtime
WORKDIR /app

ENV TZ Asia/Tokyo

# builderから必要な内容をコピー
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENTRYPOINT ["python", "main.py"]