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
        payload["quantity"] = -5    # negative quantity
        response = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("message", data)
        msg = data["message"]
        self.assertIn("quantity must be non-negative", msg)

    def test_create_inventory_item_reject_invalid_condition(self):
        """It should reject request with invalid condition and return 400 with valid values"""
        test_item = InventoryItemFactory.build()
        payload = test_item.serialize()
        payload["condition"] = "DAMAGED"    # invalid condition
        response = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("message", data)
        msg = data["message"]
        self.assertIn("Invalid condition. Valid values: NEW, OPEN_BOX, USED", msg)

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

    def test_create_inventory_item_null_body_returns_400(self):
        """It should return 400 when request body is null (get_json() returns None)"""
        response = self.client.post(
            BASE_URL,
            data="null",    # null body
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_inventory_item_deserialize_error_missing_condition(self):
        """It should return 400 with valid condition values when condition is missing"""
        test_item = InventoryItemFactory.build()
        payload = test_item.serialize()
        payload.pop("condition")    # remove the condition field
        response = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("message", data)
        msg = data["message"]
        self.assertIn("Invalid condition. Valid values: NEW, OPEN_BOX, USED", msg)

    def test_create_inventory_item_deserialize_error_missing_required_field(self):
        """It should return 400 with error message when a required field is missing"""
        test_item = InventoryItemFactory.build()
        payload = test_item.serialize()
        payload.pop("product_id")    # remove the product_id field
        response = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("message", data)
        self.assertIn("product_id", data["message"].lower())

    def test_create_inventory_item_no_content_type_returns_415(self):
        """It should return 415 when Content-Type header is missing"""
        response = self.client.post(
            BASE_URL,
            data='{"product_id":"p1","quantity":0,"condition":"NEW","restock_level":1,"restock_amount":2}',
            # remove the content_type header
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_inventory_item_wrong_content_type_returns_415(self):
            """It should return 415 when Content-Type is not application/json"""
            test_item = InventoryItemFactory.build()
            payload = test_item.serialize()
            response = self.client.post(
                BASE_URL,
                data=payload,
                content_type="text/plain", # wrong content type
            )
            self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_update_item(self):
        """It should Update an existing Inventory item"""
        # create a item to update
        test_item = InventoryItemFactory()
        response = self.client.post(BASE_URL, json=test_item.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the item
        new_item = response.get_json()
        logging.debug(new_item)

        #replace required fields
        #new_item["category"] = "unknown"
        new_item["productId"] = "PROD123"
        new_item["quantity"] = 75
        new_item["restockLevel"] = 30
        new_item["restockAmount"] = 150
        new_item["condition"] = "NEW"

        #send PUT request
        response = self.client.put(f"{BASE_URL}/{new_item['id']}", json=new_item)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_item = response.get_json()
        self.assertEqual(updated_item["quantity"], 75)
        self.assertEqual(updated_item["condition"], "NEW")
    
    def test_update_nonexistent_item(self):
        """It should return 404 when updating an item that doesn't exist"""
        payload = {
            "productId": "PROD999",
            "quantity": 10,
            "restockLevel": 5,
            "restockAmount": 50,
            "condition": "NEW",
        }
        response = self.client.put(f"{BASE_URL}/9999", json=payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("message", data)
        self.assertIn("not found", data["message"].lower())

    def test_update_item_empty_body(self):
        """It should return 400 when PUT body is empty"""
        test_item = InventoryItemFactory()
        response = self.client.post(BASE_URL, json=test_item.serialize())
        item = response.get_json()

        response = self.client.put(f"{BASE_URL}/{item['id']}", json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("missing", response.get_json()["message"].lower())
    
    def test_update_item_post_method_not_allowed(self):
        """It should return 405 when POST is used on the update endpoint"""
        test_item = InventoryItemFactory()
        response = self.client.post(BASE_URL, json=test_item.serialize())
        item = response.get_json()

        payload = test_item.serialize()
        # Send POST to the PUT endpoint
        response = self.client.post(f"{BASE_URL}/{item['id']}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)