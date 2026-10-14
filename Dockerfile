FROM python:3.12-slim
ARG APP_VERSION=1.0.0
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_VERSION=${APP_VERSION}
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home appuser
COPY --chown=10001:10001 app.py ./
COPY --chown=10001:10001 templates ./templates
COPY --chown=10001:10001 static ./static
USER 10001:10001
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)"
# One worker is essential: separate workers would have separate task dictionaries.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--worker-tmp-dir", "/tmp", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
