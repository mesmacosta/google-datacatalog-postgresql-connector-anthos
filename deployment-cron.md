# Deployment Cron Guide

# Create Cron Job for PostgreSQL Connector
> run inside cron-job folder
```
kubectl create configmap trigger --from-file=trigger-sync.sh
kubectl apply -f postgresql-connector-cron-job.yaml
```

# Test call
> `{TOKEN_PLACEHOLDER}` should be generated with the jwt key at `deployment.md`

```
kubectl run -it \
  --image busybox \
  --serviceaccount ${KSA_NAME} \
  --namespace ${K8S_NAMESPACE} \
  test-sync

export WEBHOOK=http://postgresql-connector:8080/sync
wget \
 --header="Authorization: Bearer {TOKEN_PLACEHOLDER}" \
 --post-data="{}" \
 $WEBHOOK
```  