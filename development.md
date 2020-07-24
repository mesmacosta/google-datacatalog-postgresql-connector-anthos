# Development Guide

To develop the PostgreSQL connector locally, you will need:

- a GCP project
- the `PROJECT_ID` variable set to your project
- one GKE cluster (with at least 4 nodes, recommended machine type `n1-standard-4`)
- [skaffold](https://skaffold.dev/docs/install/) and [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) installed to your local environment

All commands needs to be executed inside `postgresql-connector` directory.

### Build images and deploy once

```
skaffold run --default-repo=gcr.io/${PROJECT_ID}/bank-of-anthos
```

### Build images and deploy continuously

Use `skaffold dev` to automatically propagate code changes to your cluster on file save.

```
skaffold dev --default-repo=gcr.io/${PROJECT_ID}/bank-of-anthos
```

### Adding Packages in the Python Services

The `requirements.txt` file is auto-generated by `pip-compile`, then used by the Dockerfile to install python packages in the container.
To add a package, first add the package name to `requirements.in` within the service (ex: frontend service).
Then run:

```
python3 -m pip install pip-tools
python3 -m piptools compile --output-file=requirements.txt requirements.in

# run skaffold or docker build using the generated requirements.txt
```

Alternatively, you can also run:

```
python3 -m venv .
source ./bin/activate
pip install pip-tools

pip-compile --output-file=requirements.txt requirements.in

# run skaffold or docker build using the generated requirements.txt