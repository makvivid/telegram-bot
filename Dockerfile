FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render сам подставит PORT
ENV PORT=10000

CMD ["python", "bot.py"]
