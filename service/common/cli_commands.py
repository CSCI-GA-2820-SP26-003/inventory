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
Flask CLI Command Extensions
"""
from flask import current_app as app  # Import Flask application
import uuid
from service.models import db, InventoryItem, Condition


######################################################################
# Command to force tables to be rebuilt
# Usage:
#   flask db-create
######################################################################
@app.cli.command("db-create")
def db_create():
    """
    Recreates a local database. You probably should not use this on
    production. ;-)
    """
    db.drop_all()
    db.create_all()
    db.session.commit()


######################################################################
# Command to seed the database with sample data
# Usage:
#   flask seed-db
######################################################################
@app.cli.command("seed-db")
def seed_db():
    """Seeds the database with sample inventory items for development."""
    pid1 = f"PROD-{uuid.uuid4().hex[:6].upper()}"
    pid2 = f"PROD-{uuid.uuid4().hex[:6].upper()}"
    pid3 = f"PROD-{uuid.uuid4().hex[:6].upper()}"
    items = [
        InventoryItem(product_id=pid1, quantity=10, restock_level=5, restock_amount=20, condition=Condition.NEW),
        InventoryItem(product_id=pid2, quantity=25, restock_level=10, restock_amount=30, condition=Condition.NEW),
        InventoryItem(product_id=pid1, quantity=3, restock_level=2, restock_amount=10, condition=Condition.OPEN_BOX),
        InventoryItem(product_id=pid3, quantity=0, restock_level=5, restock_amount=15, condition=Condition.USED),
    ]
    for item in items:
        item.create()
        app.logger.info("Created: %s", item.serialize())
    app.logger.info("Seeded %d inventory items.", len(items))
