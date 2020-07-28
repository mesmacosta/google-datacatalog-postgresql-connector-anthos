# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Web service for handling PostgreSQL metadata sync.

"""

import atexit
import logging
import os

import jwt
from flask import Flask, jsonify, request
from google.cloud import logging as gcp_logging
from google.cloud.logging.handlers import CloudLoggingHandler, ContainerEngineHandler, \
    AppEngineHandler
from google.datacatalog_connectors.postgresql import \
    datacatalog_cli
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.exporter.cloud_trace.cloud_trace_propagator import CloudTraceFormatPropagator
from opentelemetry.ext.flask import FlaskInstrumentor
from opentelemetry.propagators import set_global_httptextformat
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleExportSpanProcessor


def create_app():
    """Flask application factory to create instances
    of the Connector Service Flask App
    """
    app = Flask(__name__)

    # Set up tracing and export spans to Cloud Trace
    trace.set_tracer_provider(TracerProvider())
    cloud_trace_exporter = CloudTraceSpanExporter()
    trace.get_tracer_provider().add_span_processor(
        SimpleExportSpanProcessor(cloud_trace_exporter)
    )

    set_global_httptextformat(CloudTraceFormatPropagator())

    # Add Flask auto-instrumentation for tracing
    FlaskInstrumentor().instrument_app(app)

    # Disabling unused-variable for lines with route decorated functions
    # as pylint thinks they are unused
    # pylint: disable=unused-variable
    @app.route("/version", methods=["GET"])
    def version():
        """
        Service version endpoint
        """
        return app.config["VERSION"], 200

    @app.route("/ready", methods=["GET"])
    def ready():
        """Readiness probe."""
        return "ok", 200

    @app.route("/sync", methods=["POST"])
    def sync():
        """Sync PostgreSQL metadata with Google Data Catalog

        """
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[-1]
        else:
            token = ""

        try:
            auth_payload = jwt.decode(
                token, key=app.config["PUBLIC_KEY"], algorithms="RS256"
            )

            if auth_payload is None:
                raise PermissionError

            logging.info("Starting sync logic.")
            datacatalog_cli.PostgreSQL2DatacatalogCli().run(_get_connector_run_args())
            logging.info("Sync execution done.")
            return jsonify({}), 200

        except (PermissionError, jwt.exceptions.InvalidTokenError) as err:
            logging.error("Error executing sync: %s", str(err))
            return "authentication denied", 401
        except UserWarning as warn:
            logging.error("Error executing sync: %s", str(warn))
            return str(warn), 400
        except Exception as err:
            logging.error("Error executing sync: %s", str(err))
            return "failed to sync", 500

    @atexit.register
    def _shutdown():
        """Executed when web app is terminated."""
        logging.info("Stopping contacts service.")

    def _get_connector_run_args():
        return [
            '--datacatalog-project-id', os.environ.get('DATACATALOG_PROJECT_ID'),
            '--datacatalog-location-id', os.environ.get('DATACATALOG_LOCATION_ID'),
            '--postgresql-host', os.environ.get('POSTGRESQL_SERVER'),
            '--postgresql-user', os.environ.get('POSTGRES_USER'),
            '--postgresql-pas', os.environ.get('POSTGRES_PASSWORD'),
            '--postgresql-database', os.environ.get('POSTGRES_DB')
        ]

    logging_client = gcp_logging.Client()
    logging_client.setup_logging(log_level=logging.INFO)
    root_logger = logging.getLogger()
    # use the GCP handler ONLY in order to prevent logs from getting written to STDERR
    root_logger.handlers = [handler
                            for handler in root_logger.handlers
                            if isinstance(handler, (
                             CloudLoggingHandler,
                             ContainerEngineHandler,
                             AppEngineHandler))]

    logging.info("Service PostgreSQL connector created.")

    # setup global variables
    app.config["VERSION"] = os.environ.get("VERSION")
    app.config["PUBLIC_KEY"] = open(os.environ.get("PUB_KEY_PATH"), "r").read()

    return app


if __name__ == "__main__":
    # Create an instance of flask server when called directly
    CONNECTOR = create_app()
    CONNECTOR.run()
