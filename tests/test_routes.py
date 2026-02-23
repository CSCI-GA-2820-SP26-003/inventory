######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
TestInventoryItem API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, InventoryItem, Condition
from tests.factories import InventoryItemFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)

BASE_URL = "/inventory/items"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestInventoryService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(InventoryItem).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # Todo: Add your test cases here...

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_inventory_item(self):
        """It should Create a new InventoryItem"""
        test_item = InventoryItemFactory.build()
        logging.debug("Test InventoryItem: %s", test_item.serialize())
        response = self.client.post(BASE_URL, json=test_item.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check that the data is correct
        new_item = response.get_json()
        self.assertEqual(new_item["product_id"], test_item.product_id)
        self.assertEqual(new_item["quantity"], test_item.quantity)
        self.assertEqual(new_item["condition"], test_item.condition.name)
        self.assertEqual(new_item["restock_level"], test_item.restock_level)
        self.assertEqual(new_item["restock_amount"], test_item.restock_amount)

        # uncomment when we have the get_inventory_items endpoint
        # # Check that the location header was correct
        # response = self.client.get(location)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # new_item = response.get_json()
        # self.assertEqual(new_item["product_id"], test_item.product_id)
        # self.assertEqual(new_item["quantity"], test_item.quantity)
        # self.assertEqual(new_item["condition"], test_item.condition.value)
        # self.assertEqual(new_item["restock_level"], test_item.restock_level)
        # self.assertEqual(new_item["restock_amount"], test_item.restock_amount)

    def test_create_inventory_item_reject_negative_quantity(self):
        """It should reject request with negative quantity and return 400"""
        test_item = InventoryItemFactory.build()
        payload = test_item.serialize()
        payload["quantity"] = -5
        response = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("message", data)
        self.assertIn("non-negative", data["message"].lower())

    def test_create_inventory_item_reject_invalid_condition(self):
        """It should reject request with invalid condition and return 400 with valid values"""
        test_item = InventoryItemFactory.build()
        payload = test_item.serialize()
        payload["condition"] = "DAMAGED"
        response = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("message", data)
        msg = data["message"]
        self.assertIn("NEW", msg)
        self.assertIn("OPEN_BOX", msg)
        self.assertIn("USED", msg)

    def test_create_inventory_item_duplicate_409_conflict(self):
        """It should return 409 CONFLICT when same product_id and condition already exists"""
        test_item = InventoryItemFactory.build(
            product_id="prod_456",
            condition=Condition.NEW,
        )
        payload = test_item.serialize()
        response1 = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        response2 = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response2.status_code, status.HTTP_409_CONFLICT)
