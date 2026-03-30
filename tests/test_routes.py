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
from unittest.mock import patch
from urllib.parse import quote_plus
from wsgi import app
from service.common import status
from service.common.cli_commands import db_create
from service.models import db, InventoryItem, Condition, DataValidationError
from tests.factories import InventoryItemFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)

BASE_URL = "/inventory"


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

    def test_root_url(self):
        """It should return the UI page on root URL"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(b"Inventory REST API Service", resp.data)

    # ----------------------------------------------------------
    # TEST HEALTH CHECK
    # ----------------------------------------------------------
    def test_health_check(self):
        """It should return 200 OK on health check"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["status"], "OK")

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
        self.assertEqual(new_item["condition"], test_item.condition.value)
        self.assertEqual(new_item["restock_level"], test_item.restock_level)
        self.assertEqual(new_item["restock_amount"], test_item.restock_amount)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_item = response.get_json()
        self.assertEqual(new_item["product_id"], test_item.product_id)
        self.assertEqual(new_item["quantity"], test_item.quantity)
        self.assertEqual(new_item["condition"], test_item.condition.value)
        self.assertEqual(new_item["restock_level"], test_item.restock_level)
        self.assertEqual(new_item["restock_amount"], test_item.restock_amount)

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
            data="null",  # null body
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_inventory_item_deserialize_error_missing_required_field(self):
        """It should return 400 with error message when a required field is missing"""
        test_item = InventoryItemFactory.build()
        payload = test_item.serialize()
        payload.pop("product_id")  # remove the product_id field
        response = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("message", data)
        self.assertIn("product_id", data["message"].lower())

    def test_create_inventory_item_empty_product_id(self):
        """It should return 400 when product_id is empty string"""
        test_item = InventoryItemFactory.build()
        payload = test_item.serialize()
        payload["product_id"] = ""
        response = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("product_id", data["message"].lower())

    def test_create_inventory_item_negative_quantity(self):
        """It should reject request with negative quantity and return 400"""
        test_item = InventoryItemFactory.build()
        payload = test_item.serialize()
        payload["quantity"] = -5
        response = self.client.post(BASE_URL, json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("quantity", data["message"].lower())

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
            content_type="text/plain",  # wrong content type
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ----------------------------------------------------------
    # TEST READ
    # ----------------------------------------------------------
    def test_get_inventory_item(self):
        """It should Get a single InventoryItem"""
        test_item = InventoryItemFactory()
        test_item.create()

        response = self.client.get(f"{BASE_URL}/{test_item.public_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(data["public_id"], test_item.public_id)
        self.assertEqual(data["product_id"], test_item.product_id)

    def test_get_inventory_item_not_found(self):
        """It should not Get an InventoryItem that's not found"""
        response = self.client.get(f"{BASE_URL}/non-existent-id")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_method_not_allowed(self):
        """It should not allow unsupported HTTP methods"""
        response = self.client.put("/inventory")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_method_not_allowed_on_items(self):
        """It should return 405 Method Not Allowed when calling an unsupported method on items"""
        response = self.client.put(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.delete(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_inventory_item_data_validation_error(self):
        """It should return 400 Bad Request on DataValidationError"""
        with patch("service.models.InventoryItem.deserialize") as mocked_deser:
            mocked_deser.side_effect = DataValidationError("Custom Validation Error")

            test_item = InventoryItemFactory()
            response = self.client.post(BASE_URL, json=test_item.serialize())

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            data = response.get_json()
            self.assertEqual(data["error"], "Bad Request")

    def test_get_inventory_item_500_error(self):
        """It should return 500 Internal Server Error when the database fails"""
        original = app.config.get("PROPAGATE_EXCEPTIONS")
        try:
            app.config["PROPAGATE_EXCEPTIONS"] = False
            with patch("service.models.InventoryItem.find_by_public_id") as mocked_find:
                mocked_find.side_effect = Exception("Database connection failed")
                response = self.client.get(f"{BASE_URL}/any-id")
                self.assertEqual(
                    response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                data = response.get_json()
                self.assertEqual(data["error"], "Internal Server Error")
        finally:
            app.config["PROPAGATE_EXCEPTIONS"] = original

    # ----------------------------------------------------------
    # TEST UPDATE
    # ----------------------------------------------------------
    def test_update_item(self):
        """It should Update an existing Inventory item"""
        # create a item to update
        test_item = InventoryItemFactory()
        response = self.client.post(BASE_URL, json=test_item.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the item
        new_item = response.get_json()
        logging.debug(new_item)

        new_item["product_id"] = "PROD123"
        new_item["quantity"] = 75
        new_item["restock_level"] = 30
        new_item["restock_amount"] = 150
        new_item["condition"] = "NEW"

        # send PUT request
        response = self.client.put(f"{BASE_URL}/{new_item['public_id']}", json=new_item)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_item = response.get_json()
        self.assertEqual(updated_item["quantity"], 75)
        self.assertEqual(updated_item["condition"], "NEW")

    def test_update_nonexistent_item(self):
        """It should return 404 when updating an item that doesn't exist"""
        payload = {
            "product_id": "PROD999",
            "quantity": 10,
            "restock_level": 5,
            "restock_amount": 50,
            "condition": "NEW",
        }
        response = self.client.put(f"{BASE_URL}/fake-public-id-9999", json=payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("message", data)
        self.assertIn("not found", data["message"].lower())

    def test_update_item_empty_body(self):
        """It should return 400 when PUT body is empty"""
        test_item = InventoryItemFactory()
        response = self.client.post(BASE_URL, json=test_item.serialize())
        item = response.get_json()

        response = self.client.put(f"{BASE_URL}/{item['public_id']}", json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("missing", response.get_json()["message"].lower())

    def test_update_item_post_method_not_allowed(self):
        """It should return 405 when POST is used on the update endpoint"""
        test_item = InventoryItemFactory()
        response = self.client.post(BASE_URL, json=test_item.serialize())
        item = response.get_json()

        payload = test_item.serialize()
        # Send POST to the PUT endpoint
        response = self.client.post(f"{BASE_URL}/{item['public_id']}", json=payload)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_bad_json(self):
        """It should hit the 400 bad_request error handler"""

        response = self.client.post(
            BASE_URL,
            data="this is not json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_data_validation_error(self):
        """It should trigger DataValidationError handler on update"""
        test_item = InventoryItemFactory()
        response = self.client.post(BASE_URL, json=test_item.serialize())
        item = response.get_json()

        payload = {
            "product_id": "PROD123",
            "quantity": 10,
            "restock_level": 5,
            "restock_amount": 50,
            "condition": "NEW",
        }

        with patch("service.models.InventoryItem.deserialize") as mocked_deser:
            mocked_deser.side_effect = DataValidationError("Update validation error")
            response = self.client.put(
                f"{BASE_URL}/{item['public_id']}",
                json=payload,
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            data = response.get_json()
            self.assertEqual(data["error"], "Bad Request")

    def test_update_item_null_body(self):
        """It should return 400 when PUT body is null"""
        test_item = InventoryItemFactory()
        response = self.client.post(BASE_URL, json=test_item.serialize())
        item = response.get_json()

        response = self.client.put(
            f"{BASE_URL}/{item['public_id']}",
            data="null",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_item_negative_quantity(self):
        """It should return 400 when updating with negative quantity"""
        test_item = InventoryItemFactory()
        response = self.client.post(BASE_URL, json=test_item.serialize())
        item = response.get_json()

        item["quantity"] = -10
        response = self.client.put(f"{BASE_URL}/{item['public_id']}", json=item)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.get_json()["message"].lower())

    def test_update_item_invalid_condition(self):
        """It should return 400 when updating with invalid condition"""
        test_item = InventoryItemFactory()
        response = self.client.post(BASE_URL, json=test_item.serialize())
        item = response.get_json()

        item["condition"] = "DAMAGED"
        response = self.client.put(f"{BASE_URL}/{item['public_id']}", json=item)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid condition", response.get_json()["message"])

    def test_unsupported_method_on_item(self):
        """It should return 405 Method Not Allowed when sending POST to an item URL"""
        test_item = InventoryItemFactory()
        test_item.create()
        response = self.client.post(f"{BASE_URL}/{test_item.public_id}")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_method_not_allowed_global_handler(self):
        """It should trigger the global 405 error handler"""
        response = self.client.delete(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        data = response.get_json()
        self.assertEqual(data["error"], "Method not Allowed")

    # ----------------------------------------------------------
    # TEST DELETE
    # ----------------------------------------------------------
    def test_delete_inventory_item(self):
        """It should Delete an Inventory Item"""
        test_item = InventoryItemFactory()
        test_item.create()
        response = self.client.delete(f"{BASE_URL}/{test_item.public_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_item.public_id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_non_existing_inventory_item(self):
        """It should Delete an Inventory Item even if it doesn't exist"""
        response = self.client.delete(
            f"{BASE_URL}/00000000-0000-0000-0000-000000000000"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)

    def test_db_create_command(self):
        """It should execute the db-create command"""
        runner = app.test_cli_runner()
        result = runner.invoke(db_create)
        self.assertEqual(result.exit_code, 0)

    def test_data_validation_error_global_handler(self):
        """It should trigger the global 400 error handler for DataValidationError"""
        with patch("service.models.InventoryItem.find_by_public_id") as mocked_find:
            mocked_find.side_effect = DataValidationError("Global Validation Error")
            response = self.client.get(f"{BASE_URL}/some-id")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            data = response.get_json()
            self.assertEqual(data["error"], "Bad Request")
            self.assertEqual(data["message"], "Global Validation Error")

    # ----------------------------------------------------------
    # HELPER METHODS
    # ----------------------------------------------------------
    def _create_items(self, count):
        """Helper to create multiple inventory items via POST"""
        items = []
        for _ in range(count):
            test_item = InventoryItemFactory.build()
            response = self.client.post(BASE_URL, json=test_item.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            items.append(response.get_json())
        return items

    # ----------------------------------------------------------
    # TEST LIST ALL
    # ----------------------------------------------------------
    def test_list_all_inventory_items(self):
        """It should return all inventory items"""
        self._create_items(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_list_inventory_items_empty(self):
        """It should return an empty list when no items exist"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data, [])

    def test_list_inventory_items_fields(self):
        """It should return all required fields for each item"""
        self._create_items(1)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        item = data[0]
        required_fields = [
            "id",
            "public_id",
            "product_id",
            "quantity",
            "restock_level",
            "restock_amount",
            "condition",
            "created_at",
            "updated_at",
        ]
        for field in required_fields:
            self.assertIn(field, item)

    def test_list_inventory_items_order(self):
        """It should return items ordered by id ascending"""
        self._create_items(3)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        ids = [item["id"] for item in data]
        self.assertEqual(ids, sorted(ids))

    def test_list_inventory_items_content_type(self):
        """It should return application/json content type"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content_type, "application/json")

    def test_query_restock_items(self):
        """It should query inventory items that need restocking (quantity <= restock_level)"""
        # Create an item that definitely needs restocking (5 <= 10)
        item_need = InventoryItemFactory(quantity=5, restock_level=10)
        item_need.create()

        # Create an item that is exactly at the limit (10 <= 10)
        item_at_limit = InventoryItemFactory(quantity=10, restock_level=10)
        item_at_limit.create()

        # Create an item that does NOT need restocking (20 > 10)
        item_ok = InventoryItemFactory(quantity=20, restock_level=10)
        item_ok.create()

        # Send GET request with the restock query parameter
        response = self.client.get(BASE_URL, query_string="restock=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        # Only the first two items should be returned
        self.assertEqual(len(data), 2)

        # Verify that all returned items satisfy the restock condition
        for item in data:
            self.assertTrue(item["quantity"] <= item["restock_level"])

        # Verify specific IDs are present/absent
        returned_ids = [item["id"] for item in data]
        self.assertIn(item_need.id, returned_ids)
        self.assertIn(item_at_limit.id, returned_ids)
        self.assertNotIn(item_ok.id, returned_ids)

    def test_query_restock_with_false(self):
        """It should return all items when restock=false is passed"""
        self._create_items(3)
        response = self.client.get(BASE_URL, query_string="restock=false")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 3)

    def test_query_restock_invalid_value(self):
        """It should return 400 for invalid restock query value"""
        response = self.client.get(BASE_URL, query_string="restock=invalid")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("Invalid value for 'restock'", data["message"])

    def test_query_restock_items_from_correct_endpoint(self):
        """It should query restock items from /inventory endpoint"""
        item_need = InventoryItemFactory(quantity=5, restock_level=10)
        item_need.create()

        response = self.client.get(BASE_URL, query_string="restock=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)

    # ----------------------------------------------------------
    # TEST QUERY
    # ----------------------------------------------------------
    def test_query_by_product_id(self):
        """It should Query Inventory Items by product_id"""
        items = self._create_items(5)
        test_product_id = items[0]["product_id"]
        product_count = len(
            [item for item in items if item["product_id"] == test_product_id]
        )
        response = self.client.get(
            BASE_URL, query_string=f"product_id={quote_plus(test_product_id)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), product_count)
        for item in data:
            self.assertEqual(item["product_id"], test_product_id)

    def test_query_by_product_id_and_condition(self):
        """It should Query Inventory Items by both product_id and condition"""
        # Create items with known product_id and condition
        item1 = InventoryItemFactory(product_id="PROD_COMBO", condition=Condition.NEW)
        resp1 = self.client.post(BASE_URL, json=item1.serialize())
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        item2 = InventoryItemFactory(product_id="PROD_COMBO", condition=Condition.USED)
        resp2 = self.client.post(BASE_URL, json=item2.serialize())
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)

        item3 = InventoryItemFactory(product_id="PROD_OTHER", condition=Condition.NEW)
        resp3 = self.client.post(BASE_URL, json=item3.serialize())
        self.assertEqual(resp3.status_code, status.HTTP_201_CREATED)

        # Query by both product_id and condition
        response = self.client.get(
            BASE_URL, query_string="product_id=PROD_COMBO&condition=NEW"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["product_id"], "PROD_COMBO")
        self.assertEqual(data[0]["condition"], "NEW")

    def test_query_by_invalid_condition(self):
        """It should return 400 for invalid condition query value"""
        response = self.client.get(BASE_URL, query_string="condition=DAMAGED")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("Invalid condition", data["message"])

    def test_query_by_product_id_condition_and_restock(self):
        """It should Query Inventory Items by product_id, condition, and restock"""
        # Create item that matches all three filters
        item1 = InventoryItemFactory(
            product_id="PROD_ALL", condition=Condition.NEW, quantity=5, restock_level=10
        )
        resp1 = self.client.post(BASE_URL, json=item1.serialize())
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        # Same product_id, different condition, does NOT need restock
        item2 = InventoryItemFactory(
            product_id="PROD_ALL",
            condition=Condition.USED,
            quantity=20,
            restock_level=10,
        )
        resp2 = self.client.post(BASE_URL, json=item2.serialize())
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)

        # Different product_id, needs restock
        item3 = InventoryItemFactory(
            product_id="PROD_OTHER",
            condition=Condition.NEW,
            quantity=2,
            restock_level=10,
        )
        resp3 = self.client.post(BASE_URL, json=item3.serialize())
        self.assertEqual(resp3.status_code, status.HTTP_201_CREATED)

        # Query with all three params
        response = self.client.get(
            BASE_URL, query_string="product_id=PROD_ALL&condition=NEW&restock=true"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["product_id"], "PROD_ALL")
        self.assertEqual(data[0]["condition"], "NEW")

    def test_query_by_condition(self):
        """It should Query Inventory Items by condition"""
        items = self._create_items(10)
        test_condition = items[0]["condition"]
        condition_count = len(
            [item for item in items if item["condition"] == test_condition]
        )
        response = self.client.get(
            BASE_URL, query_string=f"condition={quote_plus(test_condition)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), condition_count)
        for item in data:
            self.assertEqual(item["condition"], test_condition)

    # ----------------------------------------------------------
    # TEST DECREMENT
    # ----------------------------------------------------------
    def test_decrement_inventory_success(self):
        """It should successfully decrement inventory quantity"""
        test_item = InventoryItemFactory(quantity=10)
        test_item.create()

        payload = {"amount": 2, "orderId": "order_123"}
        response = self.client.post(
            f"{BASE_URL}/{test_item.public_id}/decrement", json=payload
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_data = response.get_json()
        self.assertEqual(new_data["quantity"], 8)

    def test_decrement_negative_amount(self):
        """It should reject a negative decrement amount"""
        test_item = InventoryItemFactory(quantity=10)
        test_item.create()

        payload = {"amount": -5, "orderId": "order_123"}
        response = self.client.post(
            f"{BASE_URL}/{test_item.public_id}/decrement", json=payload
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity must be non-negative", response.get_json()["message"])

    def test_decrement_insufficient_inventory(self):
        """It should return 400 if inventory is insufficient"""
        test_item = InventoryItemFactory(quantity=5)
        test_item.create()

        payload = {"amount": 10, "orderId": "order_123"}
        response = self.client.post(
            f"{BASE_URL}/{test_item.public_id}/decrement", json=payload
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.get_json()["message"], "INSUFFICIENT INVENTORY")

    def test_decrement_item_not_found(self):
        """It should return 404 when decrementing a non-existent item"""
        payload = {"amount": 2, "orderId": "order_123"}
        response = self.client.post(
            f"{BASE_URL}/non-existent-id/decrement", json=payload
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
