FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# You can change main:app to the actual Python file and app name if different!
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
