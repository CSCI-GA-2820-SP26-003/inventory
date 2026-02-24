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
YourResourceModel Service

This service implements a REST API that allows you to Create, Read, Update
and Delete YourResourceModel
"""

from flask import current_app as app  # Import Flask application
from flask import request, jsonify, url_for, abort  # Import Flask request, jsonify, url_for, abort
from service.common import status  # HTTP Status Codes
from service.models import InventoryItem, Condition, DataValidationError


######################################################################
# GET INDEX
######################################################################
@app.route("/inventory")
def index():
    """Root URL response"""
    # app.logger.info("Request for root URL")
    return (
        jsonify(
            name="Inventory RESTful Service",
            version="1.0",
            description="The inventory service tracks product stock levels and conditions.",
        ),
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################

# Todo: Place your REST API code here ...

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
    if not type(quantity) == int or quantity < 0:
        return (
            jsonify(
                status=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message="quantity must be non-negative",
            ),
            status.HTTP_400_BAD_REQUEST,
        )

    # Reject invalid condition and list valid values
    if "condition" in data:
        condition = data.get("condition")
        if condition not in Condition:
            return (
                jsonify(
                    status=status.HTTP_400_BAD_REQUEST, 
                    error="Bad Request", 
                    message=f"Invalid condition. Valid values: {', '.join(c.value for c in Condition)}",
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
    # uncomment to replace the location_url when we have the get_inventory_items endpoint
    # location_url = url_for("get_inventory_items", inventory_item_public_id=inventory_item.public_id, _external=True)
    location_url = "unknown"
    return jsonify(inventory_item.serialize()), status.HTTP_201_CREATED, {"Location": location_url}



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