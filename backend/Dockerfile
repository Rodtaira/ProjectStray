FROM python:3.12-slim

ARG HOST_UID=1000
ARG HOST_GID=1000

RUN groupadd -g "${HOST_GID}" appuser \
    && useradd -m -u "${HOST_UID}" -g "${HOST_GID}" appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
