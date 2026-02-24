FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txte_web_sm
COPY . .
#ENV PYTHONPATH=/app
# Gunicorn binds to internal port 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app", "--log-level", "debug"]
