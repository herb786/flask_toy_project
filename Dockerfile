FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Optimization: Pre-warm the transformer cache
# This prevents the bot from downloading the RoBERTa weights on the first request
RUN python -c "import spacy; spacy.load('en_core_web_trf')"
#ENV PYTHONPATH=/app
# Gunicorn binds to internal port 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app", "--log-level", "debug"]
