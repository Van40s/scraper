FROM python:3.12-slim-bookworm

WORKDIR /app/app

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["gunicorn", "requests_scrape:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "5", "--threads", "5", "--bind", "0.0.0.0:8000"]