# Deployment

## Creating Secret Manually

```
  openssl genrsa -out jwtRS256.key 4096
  openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub
  kubectl create secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
```

## Set cluster environment variables
```
export PROJECT_ID=my-project
export ZONE=us-central1
```

## Create cluster
```
gcloud beta container clusters create bank-of-anthos \
    --project=${PROJECT_ID} --zone=${ZONE} \
    --workload-pool=${PROJECT_ID}.svc.id.goog \
    --machine-type=n1-standard-2 --num-nodes=4
```

## Set secret
```
kubectl create secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
```

## Create Bank of Anthos kubernetes resources
> Run this at the [bank-of-anthos](https://github.com/GoogleCloudPlatform/bank-of-anthos) github root dir.
```
kubectl apply -f ./kubernetes-manifests
```

## Set workload identity environment varibles
```
export K8S_NAMESPACE=default
export KSA_NAME=postgresql-connector-ksa
export GSA_NAME=postgresql-connector
```

## Add Cloud Trace role
```
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/cloudtrace.agent
```

## Add Metrics Writer role
```
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/monitoring.metricWriter
```

## Add DataCatalog admin role
```
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/datacatalog.admin
```

## Add Logs Writer role
```
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/logging.logWriter
```

## Add KSA as workload identity user
```
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[${K8S_NAMESPACE}/${KSA_NAME}]" \
  ${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
```

## Create KSA
```
kubectl create serviceaccount \
--namespace ${K8S_NAMESPACE} \
${KSA_NAME}
```

## Anotate KSA with GSA
```
kubectl annotate serviceaccount \
  --namespace ${K8S_NAMESPACE} \
  ${KSA_NAME} \
  iam.gke.io/gcp-service-account=${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
```  

## Test KSA
```
kubectl run -it \
  --image google/cloud-sdk:slim \
  --serviceaccount ${KSA_NAME} \
  --namespace ${K8S_NAMESPACE} \
  workload-identity-test
```  

## Update hardcoded values at postgresql-connector.yaml
set the placeholder "<SET-PROJECT>" with your project.

## Update hardcoded values at build.sh and run it.
Set the placeholder with the your project, and execute:
```
./build.sh
```
make sure `postgresql-connector.yaml` uses the container image name.

# Create PostgreSQL Connector kubernetes resources
> Run this at the `google-datacatalog-postgresql-connector-anthos` github root dir.
```
kubectl apply -f postgresql-connector.yaml
```

# Set serviceaccout
```
kubectl set serviceaccount deployment postgresql-connector ${KSA_NAME}
```

# Test Connector sync
> `{TOKEN_PLACEHOLDER}` should be generated with the jwt key.

```
kubectl exec $(kubectl get pod -l app=postgresql-connector -o jsonpath={.items..metadata.name}) -- curl \
-X POST \
  http://postgresql-connector:8080/sync \
  -H 'Accept: */*' \
  -H 'Accept-Encoding: gzip, deflate' \
  -H 'Authorization: Bearer {TOKEN_PLACEHOLDER}'
```  
