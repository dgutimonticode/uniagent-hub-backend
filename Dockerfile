FROM python:3.14-slim

WORKDIR /app

ENV FLASK_APP=run.py
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--debug"]
