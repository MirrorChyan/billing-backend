FROM python:3.12-alpine3.20

WORKDIR /app

COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt --no-cache-dir

COPY . .

EXPOSE 8000

ENTRYPOINT ["python3", "-m", "uvicorn", "main:app"]

