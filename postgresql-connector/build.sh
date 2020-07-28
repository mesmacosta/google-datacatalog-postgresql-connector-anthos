#!/usr/bin/env bash
docker build -t bank-of-anthos-postgresql-connector .
docker tag bank-of-anthos-postgresql-connector gcr.io/my-project/bank-of-anthos-postgresql-connector:stable
docker push gcr.io/my-project/bank-of-anthos-postgresql-connector:stable
gcloud container images list-tags gcr.io/my-project/bank-of-anthos-postgresql-connector