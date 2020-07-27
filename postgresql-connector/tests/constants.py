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
Example constants used in tests
"""
import random
import string
from Crypto.PublicKey import RSA
import jwt


def generate_rsa_key():
    """Generate priv,pub key pair for test"""
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key


def get_random_string(length):
    """Generate random string of given length"""
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))


EXAMPLE_PRIVATE_KEY, EXAMPLE_PUBLIC_KEY = generate_rsa_key()

EXAMPLE_TOKEN = jwt.encode(
    {}, EXAMPLE_PRIVATE_KEY, algorithm="RS256"
)

EXAMPLE_HEADERS = {
    "Authorization": EXAMPLE_TOKEN,
    "content-type": "application/json",
}
