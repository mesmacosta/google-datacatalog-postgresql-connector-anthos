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
import sys

import jwt
from flask import Flask, jsonify, request
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

            app.logger.debug("Starting sync logic.")
            datacatalog_cli.PostgreSQL2DatacatalogCli().run(sys.argv)
            app.logger.info("Sync execution done.")
            return jsonify({}), 200

        except (PermissionError, jwt.exceptions.InvalidTokenError) as err:
            app.logger.error("Error executing sync: %s", str(err))
            return "authentication denied", 401
        except UserWarning as warn:
            app.logger.error("Error executing sync: %s", str(warn))
            return str(warn), 400
        except Exception as err:
            app.logger.error("Error executing sync: %s", str(err))
            return "failed to sync", 500

    @atexit.register
    def _shutdown():
        """Executed when web app is terminated."""
        app.logger.info("Stopping contacts service.")

    # set up logger
    app.logger.handlers = logging.getLogger("gunicorn.error").handlers
    app.logger.setLevel(logging.getLogger("gunicorn.error").level)
    app.logger.info("Starting PostgreSQL connector service.")

    # setup global variables
    app.config["VERSION"] = os.environ.get("VERSION")
    app.config["PUBLIC_KEY"] = open(os.environ.get("PUB_KEY_PATH"), "r").read()

    __add_connector_env_variables()

    return app


def __add_connector_env_variables():
    sys.argv.extend(['datacatalog-project-id',
                     os.environ.get("POSTGRESQL2DC_DATACATALOG_PROJECT_ID")])
    sys.argv.extend(['datacatalog-location-id',
                     os.environ.get("POSTGRESQL2DC_DATACATALOG_LOCATION_ID")])
    sys.argv.extend(['postgresql-host',
                     os.environ.get("POSTGRESQL2DC_POSTGRESQL_SERVER")])
    sys.argv.extend(['postgresql-user',
                     os.environ.get("POSTGRESQL2DC_POSTGRESQL_USERNAME")])
    sys.argv.extend(['postgresql-pass',
                     os.environ.get("POSTGRESQL2DC_POSTGRESQL_PASSWORD")])
    sys.argv.extend(['postgresql-database',
                     os.environ.get("POSTGRESQL2DC_POSTGRESQL_DATABASE")])


if __name__ == "__main__":
    # Create an instance of flask server when called directly
    CONNECTOR = create_app()
    CONNECTOR.run()
