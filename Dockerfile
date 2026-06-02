FROM python:3.11-slim

WORKDIR /code

# Cài đặt các thư viện hệ thống cần thiết cho việc networking/scraping nếu có
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/list/apt/lists/*

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

ENV PYTHONPATH=/code