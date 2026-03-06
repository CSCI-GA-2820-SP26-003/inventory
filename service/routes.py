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
Inventory Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Inventory Items
"""

from flask import (
    request,
    jsonify,
    url_for,
    abort,
    current_app as app,
)
from service.common import status  # HTTP Status Codes
from service.models import InventoryItem, Condition, DataValidationError

######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


@app.route("/")
def index():
    """Root URL response with service URL and available resources"""
    app.logger.info("Request for root URL")
    return (
        jsonify(
            url=url_for("index", _external=True),
            resources={"inventory": url_for("inventory_index", _external=True)},
        ),
        status.HTTP_200_OK,
    )


######################################################################
# GET INDEX
######################################################################
@app.route("/inventory")
def inventory_index():
    """Inventory Root URL response or restock query"""
    app.logger.info("Request for inventory URL")

    return (
        jsonify(
            name="Inventory RESTful Service",
            version="1.0",
            description="The inventory service tracks product stock levels and conditions.",
        ),
        status.HTTP_200_OK,
    )


######################################################################
# LIST ALL INVENTORY ITEMS
######################################################################
@app.route("/inventory/items", methods=["GET"])
def list_inventory_items():
    """
    List all Inventory Items
    This endpoint will return all Inventory Items ordered by id ascending
    It can also filter by items needing restock: /inventory/items?restock=true
    """
    app.logger.info("Request to List all Inventory Items...")

    # Initialize the query
    query = InventoryItem.query

    # Check for restock query parameter
    restock = request.args.get("restock")
    if restock is not None:
        if restock.lower() not in ["true", "false"]:
            app.logger.error("Invalid restock value: %s", restock)
            return (
                jsonify(
                    status=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Invalid value for 'restock'. Must be 'true' or 'false'.",
                ),
                status.HTTP_400_BAD_REQUEST,
            )
        if restock and restock.lower() == "true":
            app.logger.info(
                "Filtering for items needing restock (quantity <= restock_level)"
            )
            query = query.filter(InventoryItem.quantity <= InventoryItem.restock_level)

    items = query.order_by(InventoryItem.id).all()
    results = [item.serialize() for item in items]
    app.logger.info("Returning %d inventory items", len(results))
    return jsonify(results), status.HTTP_200_OK


######################################################################
# CREATE A NEW Inventory
######################################################################
@app.route("/inventory/items", methods=["POST"])
def create_inventory_items():
    """
    Create a Inventory Item
    This endpoint will create a Inventory Item based the data in the body that is posted
    """
    app.logger.info("Request to Create a Inventory Item...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    if data is None:
        return (
            jsonify(
                status=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message="Invalid JSON or request body",
            ),
            status.HTTP_400_BAD_REQUEST,
        )

    # Reject negative quantity
    quantity = data.get("quantity", 0)
    if not isinstance(quantity, int) or quantity < 0:
        return (
            jsonify(
                status=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message="quantity must be non-negative",
            ),
            status.HTTP_400_BAD_REQUEST,
        )

    inventory_item = InventoryItem()
    try:
        inventory_item.deserialize(data)
    except DataValidationError as err:
        msg = str(err)
        if "Condition" in msg or "condition" in msg.lower():
            valid_values = ", ".join(c.value for c in Condition)
            return (
                jsonify(
                    status=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message=f"Invalid condition. Valid values: {valid_values}",
                ),
                status.HTTP_400_BAD_REQUEST,
            )
        return (
            jsonify(
                status=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message=msg,
            ),
            status.HTTP_400_BAD_REQUEST,
        )

    # Prevent duplicate (product_id + condition) -> 409 CONFLICT
    # query the database for the inventory item
    existing = InventoryItem.query.filter_by(
        product_id=inventory_item.product_id,
        condition=inventory_item.condition,
    ).first()
    if existing is not None:
        return (
            jsonify(
                status=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=(
                    f"An inventory item already exists for product_id={inventory_item.product_id} "
                    f"with condition={inventory_item.condition.value}"
                ),
            ),
            status.HTTP_409_CONFLICT,
        )

    inventory_item.create()
    app.logger.info("Inventory Item with new id [%s] saved!", inventory_item.id)
    location_url = url_for(
        "get_inventory_items", public_id=inventory_item.public_id, _external=True
    )
    return (
        jsonify(inventory_item.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


######################################################################
# READ A SPECIFIC INVENTORY ITEM
######################################################################
@app.route("/inventory/items/<public_id>", methods=["GET"])
def get_inventory_items(public_id):
    """
    Retrieve a single Inventory Item
    This endpoint will return an Item based on its id
    """
    app.logger.info("Request to Retrieve inventory item with public_id: %s", public_id)
    inventory_item = InventoryItem.find_by_public_id(public_id)
    if not inventory_item:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Inventory item with public_id '{public_id}' was not found.",
        )

    app.logger.info("Returning inventory item: %s", inventory_item.public_id)
    return jsonify(inventory_item.serialize()), status.HTTP_200_OK


######################################################################
# DELETE AN INVENTORY ITEM
######################################################################
@app.route("/inventory/items/<public_id>", methods=["DELETE"])
def delete_inventory_items(public_id):
    """
    Delete an Inventory Item

    This endpoint will delete an Inventory Item based on the public_id specified in the path
    """
    app.logger.info(
        "Request to Delete an inventory item with public_id [%s]", public_id
    )

    item = InventoryItem.find_by_public_id(public_id)
    if item:
        app.logger.info("Inventory Item with public_id: %s found.", item.public_id)
        item.delete()

    app.logger.info("Inventory Item with public_id: %s delete complete.", public_id)
    return {}, status.HTTP_204_NO_CONTENT


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


######################################################################
# Checks the ContentType of a request
######################################################################
def check_content_type(content_type) -> None:
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# UPDATE AN EXISTING INVENTORY ITEM
######################################################################
@app.route("/inventory/items/<string:public_id>", methods=["PUT"])
def update_inventory_item(public_id):
    """
    Update a inventory item

    This endpoint will update a inventory item based the body that is posted
    """
    app.logger.info("Request to Update a inventory item with id [%s]", public_id)
    check_content_type("application/json")

    # Attempt to find the inventory item and abort if not found
    inventory_item = InventoryItem.find_by_public_id(public_id)
    if not inventory_item:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"inventory item with id '{public_id}' was not found.",
        )

    # Update the inventory item with the new data
    data = request.get_json()
    app.logger.info("Processing: %s", data)

    # Null body check
    if data is None:
        return (
            jsonify(
                status=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message="Invalid JSON or request body",
            ),
            status.HTTP_400_BAD_REQUEST,
        )

    # Empty body check
    if not data:
        return (
            jsonify(
                status=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message="Invalid InventoryItem: missing data",
            ),
            status.HTTP_400_BAD_REQUEST,
        )

    # Reject negative quantity
    if "quantity" in data:
        quantity = data.get("quantity")
        if not isinstance(quantity, int) or quantity < 0:
            return (
                jsonify(
                    status=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="quantity must be non-negative",
                ),
                status.HTTP_400_BAD_REQUEST,
            )

    # Reject invalid condition
    if "condition" in data:
        condition = data.get("condition")
        valid_values = ", ".join(c.value for c in Condition)
        if condition not in [c.value for c in Condition]:
            return (
                jsonify(
                    status=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message=f"Invalid condition. Valid values: {valid_values}",
                ),
                status.HTTP_400_BAD_REQUEST,
            )

    # Perform update
    try:
        inventory_item.deserialize(data)
    except DataValidationError as err:
        return (
            jsonify(
                status=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message=str(err),
            ),
            status.HTTP_400_BAD_REQUEST,
        )

    # Save the updates to the database
    inventory_item.update()

    app.logger.info("inventory item with ID: %d updated.", inventory_item.id)
    return jsonify(inventory_item.serialize()), status.HTTP_200_OK
