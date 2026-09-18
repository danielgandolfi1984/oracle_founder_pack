# syntax=docker/dockerfile:1

# An immutable multi-architecture manifest reference is intentionally required.
# Example shape: python:3.12-slim@sha256:<verified-manifest-digest>
ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
COPY --chown=65532:65532 app.py /app/app.py

USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["python", "/app/app.py"]
