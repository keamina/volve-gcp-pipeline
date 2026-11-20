# Container for running the pipeline as a Cloud Run job.
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pipeline/ pipeline/
COPY sql/ sql/
COPY data/raw/ data/raw/
COPY run_pipeline.py .
ENTRYPOINT ["python", "run_pipeline.py"]
