# Stage 1: Builder
FROM python:3.12 AS builder
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Final Image
FROM python:3.12-slim
LABEL maintainer="kirankp.jan2@gmail.com" \
      version="1.0" \
      description="API service for notes built with Uvicorn and FastAPI"
ENV PORT=8080
RUN adduser note_api
USER note_api
ENV PATH="/home/note_api/.local/bin:${PATH}"
WORKDIR /home/note_api/app
COPY --from=builder /home/note_api/.local /home/note_api/.local
COPY ./note_api /home/note_api/app/note_api

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl --fail http://localhost:${PORT} || exit 1

ENTRYPOINT ["uvicorn", "note_api.main:app", "--host", "0.0.0.0"]
CMD ["--port", "${PORT}"]
