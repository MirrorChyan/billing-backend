FROM python:3.12

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install -r requirements.txt --no-cache-dir

COPY ..

EXPOSE 8000

ENTRYPOINT ["python", "main.py"]
