FROM docker.io/library/python:3.14-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py llm.py main.py ./
CMD ["python", "-u", "main.py", "--watch"]
