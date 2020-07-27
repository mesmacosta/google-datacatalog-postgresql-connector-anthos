# PostgreSQL Connector Service

This depends on the environment: [bank-of-anthos](https://github.com/GoogleCloudPlatform/bank-of-anthos).

The PostgreSQL connector pulls metadata from the accounts database and pushes in Google Data Catalog.

Implemented in Python with Flask.

![Architecture Diagram](./docs/architecture.png)

### Endpoints

| Endpoint                | Type  | Auth? | Description                                                        |
| ----------------------- | ----- | ----- | ------------------------------------------------------------------ |
| `/sync`                 | POST  | 🔒    |  Synchronize PostgreSQL metadata into Google Data Catalog.         |
| `/ready`                | GET   |       |  Readiness probe endpoint.                                         |
| `/version`              | GET   |       |  Returns the contents of `$VERSION`                                |


### Environment Variables

- `VERSION`
  - a version string for the service
- `PORT`
  - the port for the webserver
- `LOG_LEVEL`
  - the service-wide [logging level](https://docs.python.org/3/library/logging.html#levels) (default: INFO)

- ConfigMap `environment-config`:
  - `LOCAL_ROUTING_NUM`
    - the routing number for our bank
  - `PUB_KEY_PATH`
    - the path to the JWT signer's public key, mounted as a secret

- ConfigMap `accounts-db-config`:
  - `POSTGRES_DB`
    - name of `accounts-db` database
  - `POSTGRES_USER`
    - user of `accounts-db` database
  - `POSTGRES_PASSWORD`
    - pasword of `accounts-db` database

### Kubernetes Resources

- [deployments/postgresql-connector](postgresql-connector.yaml)
- [service/postgresql-connector](postgresql-connector.yaml)

### Development Resources

- [development.md](development.md)
