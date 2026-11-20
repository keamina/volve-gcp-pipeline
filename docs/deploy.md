# Deploy as a scheduled Cloud Run job

Needs a project with billing enabled (the free trial credit is enough; this
pipeline costs cents per run).

```bash
PROJECT=your-project-id
REGION=europe-west1
BUCKET=$PROJECT-volve-landing

gcloud config set project $PROJECT
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com bigquery.googleapis.com storage.googleapis.com \
  cloudscheduler.googleapis.com

# Landing bucket (EU, same location as the BigQuery datasets)
gcloud storage buckets create gs://$BUCKET --location=EU --uniform-bucket-level-access

# Service account the job runs as, with only the roles it needs
gcloud iam service-accounts create volve-pipeline --display-name="Volve pipeline"
SA=volve-pipeline@$PROJECT.iam.gserviceaccount.com
for ROLE in roles/bigquery.dataEditor roles/bigquery.jobUser; do
  gcloud projects add-iam-policy-binding $PROJECT --member=serviceAccount:$SA --role=$ROLE
done
gcloud storage buckets add-iam-policy-binding gs://$BUCKET \
  --member=serviceAccount:$SA --role=roles/storage.objectAdmin

# Build the container from the Dockerfile and create the job
gcloud run jobs deploy volve-pipeline --source . --region $REGION \
  --service-account $SA \
  --set-env-vars GCP_PROJECT=$PROJECT,BQ_LOCATION=EU,GCS_BUCKET=$BUCKET,DATASET_PREFIX=volve

# Run once now
gcloud run jobs execute volve-pipeline --region $REGION --wait

# Run every day at 06:00 (Dakar time)
gcloud scheduler jobs create http volve-pipeline-daily --location $REGION \
  --schedule "0 6 * * *" --time-zone "Africa/Dakar" \
  --uri "https://run.googleapis.com/v2/projects/$PROJECT/locations/$REGION/jobs/volve-pipeline:run" \
  --http-method POST --oauth-service-account-email $SA
```

The scheduler's service account also needs `roles/run.invoker` on the job:

```bash
gcloud run jobs add-iam-policy-binding volve-pipeline --region $REGION \
  --member=serviceAccount:$SA --role=roles/run.invoker
```

Logs: Cloud Run → Jobs → volve-pipeline → Logs. Every run prints the row
counts and the quality results, and the quality results also go to
`volve_marts.data_quality_log`.
