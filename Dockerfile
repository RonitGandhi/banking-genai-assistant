FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Train the Rasa model at build-time (optional; you can also do at runtime)
RUN rasa train

EXPOSE 5005 8000
# Start both action server and Rasa via a simple script; use a process manager if preferred
CMD bash -lc "rasa run actions & rasa run --enable-api & uvicorn app.main:app --host 0.0.0.0 --port 8000 && wait"
