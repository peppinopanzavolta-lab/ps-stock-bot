FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY products.json telegram_bot.py ./

CMD ["python", "telegram_bot.py"]
