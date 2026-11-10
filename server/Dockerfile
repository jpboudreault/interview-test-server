FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY fixtures fixtures
COPY static static
EXPOSE 5001
CMD ["gunicorn", "app:app", "-w", "2", "--threads", "8", "-b", ":5001"]
