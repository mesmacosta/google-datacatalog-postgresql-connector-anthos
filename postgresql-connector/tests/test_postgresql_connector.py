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


"""
Tests for contacts
"""

import random
import unittest
from unittest.mock import patch, mock_open

from postgresql_connector import create_app
from .constants import (
    EXAMPLE_PUBLIC_KEY,
    EXAMPLE_HEADERS,
)


class TestPostgreSQLConnector(unittest.TestCase):
    """
    Tests cases for PostgreSQL connector
    """

    def setUp(self):
        """Setup Flask TestClient and mock contacts_db"""
        # mock opening files
        with patch("postgresql_connector.open", mock_open(read_data="foo")):
            # mock env vars
            with patch(
                "os.environ",
                {
                    "VERSION": "1",
                    "LOCAL_ROUTING": "123456789",
                    "PUBLIC_KEY": "1",
                },
            ):
                # get create flask app
                self.flask_app = create_app()
                # set testing config
                self.flask_app.config["TESTING"] = True
                # create test client
                self.test_app = self.flask_app.test_client()
                # set public key
                self.flask_app.config["PUBLIC_KEY"] = EXAMPLE_PUBLIC_KEY

    def test_version_endpoint_returns_200_status_code_correct_version(self):
        """test if correct version is returned"""
        # generate a version
        version = str(random.randint(1, 9))
        # set version in Flask config
        self.flask_app.config["VERSION"] = version
        # send get request to test client
        response = self.test_app.get("/version")
        # assert 200 response code
        self.assertEqual(response.status_code, 200)
        # assert both versions are equal
        self.assertEqual(response.data, version.encode())

    def test_ready_endpoint_200_status_code_ok_string(self):
        """test if correct response is returned from readiness probe"""
        response = self.test_app.get("/ready")
        # assert 200 response code
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"ok")

    def test_run_sync_200_status_code(self):
        """test running sync"""
        # send request to test client
        response = self.test_app.post(
            "/sync",
            headers=EXAMPLE_HEADERS
        )
        # assert 201 response code
        self.assertEqual(response.status_code, 200)

    def test_get_contacts_401_get_contacts_invalid_auth(self):
        """test invalid auth"""
        # mock return value of get_contacts to return empty list
        # modify header token to be incorrect
        invalid_token_header = EXAMPLE_HEADERS.copy()
        invalid_token_header["Authorization"] = "foo"
        # send request to test client
        response = self.test_app.get(
            "/sync", headers=invalid_token_header
        )
        # assert 200 response code
        self.assertEqual(response.status_code, 401)
        # assert we get correct error message
        self.assertEqual(response.data, b"authentication denied")

