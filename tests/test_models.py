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
Test cases for InventoryItem Model
"""

# pylint: disable=duplicate-code
import os
import logging
import uuid
from unittest import TestCase
from unittest.mock import patch
from wsgi import app
from service.models import InventoryItem, Condition, DataValidationError, db
from tests.factories import InventoryItemFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  InventoryItem   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestInventoryItem(TestCase):
    """Test Cases for InventoryItem Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(InventoryItem).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_an_inventory_item(self):
        """It should create an InventoryItem and assert that it exists"""
        item = InventoryItemFactory()
        item.create()
        self.assertIsNotNone(item.id)
        found = InventoryItem.find(item.id)
        self.assertEqual(found.product_id, item.product_id)
        self.assertEqual(found.condition, item.condition)

    def test_create_sets_public_id(self):
        """It should auto-generate a UUID public_id on create"""
        item = InventoryItemFactory()
        item.create()
        self.assertIsNotNone(item.public_id)
        # Validate it's a proper UUID
        uuid.UUID(item.public_id, version=4)

    def test_create_sets_timestamps(self):
        """It should auto-set created_at and updated_at on create"""
        item = InventoryItemFactory()
        item.create()
        self.assertIsNotNone(item.created_at)
        self.assertIsNotNone(item.updated_at)
        # Both timestamps are set independently, so allow a small delta
        delta = abs((item.updated_at - item.created_at).total_seconds())
        self.assertLess(delta, 1.0)

    def test_update_an_inventory_item(self):
        """It should update an InventoryItem"""
        item = InventoryItemFactory()
        item.create()
        original_id = item.id
        item.quantity = 99
        item.update()
        self.assertEqual(item.id, original_id)
        found = InventoryItem.find(item.id)
        self.assertEqual(found.quantity, 99)

    def test_delete_an_inventory_item(self):
        """It should delete an InventoryItem"""
        item = InventoryItemFactory()
        item.create()
        self.assertEqual(len(InventoryItem.all()), 1)
        item.delete()
        self.assertEqual(len(InventoryItem.all()), 0)

    def test_list_all_inventory_items(self):
        """It should list all InventoryItems in the database"""
        items = InventoryItem.all()
        self.assertEqual(len(items), 0)
        for _ in range(5):
            item = InventoryItemFactory()
            item.create()
        items = InventoryItem.all()
        self.assertEqual(len(items), 5)

    def test_find_by_product_id(self):
        """It should find InventoryItems by product_id"""
        item = InventoryItemFactory(product_id="PROD-TEST")
        item.create()
        # Create another item with a different product_id
        other = InventoryItemFactory(product_id="PROD-OTHER")
        other.create()
        results = InventoryItem.find_by_name("PROD-TEST")
        self.assertEqual(results.count(), 1)
        self.assertEqual(results[0].product_id, "PROD-TEST")

    def test_find_by_condition(self):
        """It should find InventoryItems by condition"""
        item = InventoryItemFactory(condition=Condition.NEW, product_id="COND-1")
        item.create()
        item2 = InventoryItemFactory(condition=Condition.USED, product_id="COND-2")
        item2.create()
        results = InventoryItem.find_by_condition(Condition.NEW)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results[0].condition, Condition.NEW)

    def test_serialize_an_inventory_item(self):
        """It should serialize an InventoryItem"""
        item = InventoryItemFactory()
        item.create()
        data = item.serialize()
        self.assertEqual(data["product_id"], item.product_id)
        self.assertEqual(data["quantity"], item.quantity)
        self.assertEqual(data["restock_level"], item.restock_level)
        self.assertEqual(data["restock_amount"], item.restock_amount)
        self.assertEqual(data["condition"], item.condition.value)
        self.assertIn("public_id", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_deserialize_an_inventory_item(self):
        """It should deserialize an InventoryItem"""
        data = {
            "product_id": "PROD-123",
            "quantity": 10,
            "restock_level": 5,
            "restock_amount": 20,
            "condition": "NEW",
        }
        item = InventoryItem()
        item.deserialize(data)
        self.assertEqual(item.product_id, "PROD-123")
        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.restock_level, 5)
        self.assertEqual(item.restock_amount, 20)
        self.assertEqual(item.condition, Condition.NEW)

    def test_deserialize_missing_product_id(self):
        """It should raise DataValidationError when product_id is missing"""
        data = {
            "quantity": 10,
            "restock_level": 5,
            "restock_amount": 20,
            "condition": "NEW",
        }
        item = InventoryItem()
        self.assertRaises(DataValidationError, item.deserialize, data)

    def test_deserialize_missing_condition(self):
        """It should raise DataValidationError when condition is missing"""
        data = {
            "product_id": "PROD-123",
            "quantity": 10,
            "restock_level": 5,
            "restock_amount": 20,
        }
        item = InventoryItem()
        self.assertRaises(DataValidationError, item.deserialize, data)

    def test_deserialize_invalid_condition(self):
        """It should raise DataValidationError for an invalid condition"""
        data = {
            "product_id": "PROD-123",
            "quantity": 10,
            "restock_level": 5,
            "restock_amount": 20,
            "condition": "DAMAGED",
        }
        item = InventoryItem()
        self.assertRaises(DataValidationError, item.deserialize, data)

    def test_deserialize_bad_data(self):
        """It should raise DataValidationError for bad data"""
        item = InventoryItem()
        self.assertRaises(DataValidationError, item.deserialize, "not a dict")

    def test_deserialize_defaults_quantity_to_zero(self):
        """It should default quantity to 0 when not provided"""
        data = {
            "product_id": "PROD-123",
            "restock_level": 5,
            "restock_amount": 20,
            "condition": "NEW",
        }
        item = InventoryItem()
        item.deserialize(data)
        self.assertEqual(item.quantity, 0)

    def test_unique_public_id_constraint(self):
        """It should enforce unique public_id"""
        item1 = InventoryItemFactory()
        item1.create()
        item2 = InventoryItemFactory()
        item2.public_id = item1.public_id
        self.assertRaises(DataValidationError, item2.create)

    def test_unique_product_condition_constraint(self):
        """It should enforce unique (product_id, condition) constraint"""
        item1 = InventoryItemFactory(product_id="PROD-DUP", condition=Condition.NEW)
        item1.create()
        item2 = InventoryItemFactory(product_id="PROD-DUP", condition=Condition.NEW)
        self.assertRaises(DataValidationError, item2.create)

    def test_same_product_different_condition_allowed(self):
        """It should allow same product_id with different conditions"""
        item1 = InventoryItemFactory(product_id="PROD-MULTI", condition=Condition.NEW)
        item1.create()
        item2 = InventoryItemFactory(product_id="PROD-MULTI", condition=Condition.OPEN_BOX)
        item2.create()
        self.assertEqual(len(InventoryItem.all()), 2)

    def test_quantity_cannot_be_negative(self):
        """It should reject negative quantity via check constraint"""
        item = InventoryItemFactory(quantity=-5)
        self.assertRaises(DataValidationError, item.create)

    def test_repr(self):
        """It should have a string representation"""
        item = InventoryItemFactory(product_id="PROD-REPR", condition=Condition.USED)
        self.assertIn("PROD-REPR", repr(item))
        self.assertIn("USED", repr(item))

    def test_update_with_invalid_data(self):
        """It should raise DataValidationError on update error"""
        item = InventoryItemFactory()
        item.create()
        item.product_id = None  # violates NOT NULL
        self.assertRaises(DataValidationError, item.update)

    def test_delete_with_invalid_item(self):
        """It should raise DataValidationError on delete error"""
        item = InventoryItemFactory()
        item.create()
        with patch("service.models.db.session.commit", side_effect=Exception("delete error")):
            self.assertRaises(DataValidationError, item.delete)

    def test_deserialize_with_attribute_error(self):
        """It should raise DataValidationError on attribute error"""
        item = InventoryItem()
        data = {
            "product_id": "PROD-123",
            "quantity": 10,
            "restock_level": 5,
            "restock_amount": 20,
            "condition": "NEW",
        }
        with patch.object(
            InventoryItem, "__setattr__",
            side_effect=AttributeError("bad attribute"),
        ):
            self.assertRaises(DataValidationError, item.deserialize, data)
