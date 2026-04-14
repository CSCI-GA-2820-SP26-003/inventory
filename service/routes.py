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

# spell: ignore Rofrano jsonify restx dbname
"""
Inventory Service with Swagger

Paths:
------
GET / - Displays a UI for Selenium testing
GET /health - Returns the health status
GET /api/inventory - Returns a list all of the Inventory Items
GET /api/inventory/{id} - Returns the Inventory Item with a given id
POST /api/inventory - Creates a new Inventory Item record in the database
PUT /api/inventory/{id} - Updates an Inventory Item record in the database
DELETE /api/inventory/{id} - Deletes an Inventory Item record in the database
POST /api/inventory/{id}/restock - Restocks an Inventory Item
POST /api/inventory/{id}/decrement - Decrements an Inventory Item quantity
"""

from flask import request
from flask import current_app as app  # Import Flask application
from flask_restx import Api, Resource, fields
from service.models import InventoryItem, Condition, DataValidationError
from service.common import status  # HTTP Status Codes


######################################################################
# Configure Swagger before initializing it
######################################################################
api = Api(
    app,
    version="1.0.0",
    title="Inventory REST API Service",
    description="This is the Inventory store service.",
    default="inventory",
    default_label="Inventory operations",
    doc="/apidocs",
    prefix="/api",
)


######################################################################
# Configure the Root route before OpenAPI
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
# HEALTH CHECK
######################################################################
@app.route("/health")
def health_check():
    """Health check endpoint for Kubernetes probes"""
    return {"status": "OK"}, status.HTTP_200_OK


# Define the model so that the docs reflect what can be sent
create_model = api.model(
    "InventoryItem",
    {
        "product_id": fields.String(
            required=True, description="The product ID of the Inventory Item"
        ),
        "condition": fields.String(
            required=True,
            # pylint: disable=protected-access
            enum=Condition._member_names_,
            description="The condition of the Inventory Item (NEW, OPEN_BOX, USED)",
        ),
        "quantity": fields.Integer(
            required=True, description="The quantity of the Inventory Item"
        ),
        "restock_level": fields.Integer(
            required=True, description="The restock level of the Inventory Item"
        ),
        "restock_amount": fields.Integer(
            required=True, description="The restock amount of the Inventory Item"
        ),
    },
)

inventory_model = api.inherit(
    "InventoryItemModel",
    create_model,
    {
        "id": fields.Integer(
            readOnly=True,
            description="The unique id assigned internally by service",
        ),
        "public_id": fields.String(
            readOnly=True,
            description="The unique public id assigned internally by service",
        ),
        "created_at": fields.String(
            readOnly=True,
            description="The date the Inventory Item was created",
        ),
        "updated_at": fields.String(
            readOnly=True,
            description="The date the Inventory Item was last updated",
        ),
    },
)


######################################################################
#  PATH: /inventory/{id}
######################################################################
@api.route("/inventory/<public_id>")
@api.param("public_id", "The Inventory Item identifier")
class InventoryResource(Resource):
    """
    InventoryResource class

    Allows the manipulation of a single Inventory Item
    GET /inventory/{id} - Returns an Inventory Item with the id
    PUT /inventory/{id} - Update an Inventory Item with the id
    DELETE /inventory/{id} - Deletes an Inventory Item with the id
    """

    # ------------------------------------------------------------------
    # RETRIEVE AN INVENTORY ITEM
    # ------------------------------------------------------------------
    @api.doc("get_inventory_items")
    @api.response(404, "Inventory Item not found")
    @api.marshal_with(inventory_model)
    def get(self, public_id):
        """
        Retrieve a single Inventory Item

        This endpoint will return an Inventory Item based on its id
        """
        app.logger.info(
            "Request to Retrieve inventory item with public_id: %s", public_id
        )
        inventory_item = InventoryItem.find_by_public_id(public_id)
        if not inventory_item:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Inventory item with public_id '{public_id}' was not found.",
            )
        app.logger.info(
            "Returning inventory item: %s", inventory_item.public_id
        )
        return inventory_item.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # UPDATE AN EXISTING INVENTORY ITEM
    # ------------------------------------------------------------------
    @api.doc("update_inventory_items")
    @api.response(404, "Inventory Item not found")
    @api.response(400, "The posted Inventory Item data was not valid")
    @api.expect(create_model)
    @api.marshal_with(inventory_model)
    def put(self, public_id):
        """
        Update an Inventory Item

        This endpoint will update an Inventory Item based the body that is posted
        """
        app.logger.info(
            "Request to Update a inventory item with id [%s]", public_id
        )
        check_content_type("application/json")

        # Attempt to find the inventory item and abort if not found
        inventory_item = InventoryItem.find_by_public_id(public_id)
        if not inventory_item:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"inventory item with id '{public_id}' was not found.",
            )

        # Update the inventory item with the new data
        data = api.payload
        app.logger.info("Processing: %s", data)

        # Null body check
        if data is None:
            abort(
                status.HTTP_400_BAD_REQUEST,
                "Invalid JSON or request body",
            )

        # Empty body check
        if not data:
            abort(
                status.HTTP_400_BAD_REQUEST,
                "Invalid InventoryItem: missing data",
            )

        # Reject negative quantity
        if "quantity" in data:
            quantity = data.get("quantity")
            if not isinstance(quantity, int) or quantity < 0:
                abort(
                    status.HTTP_400_BAD_REQUEST,
                    "quantity must be non-negative",
                )

        # Reject invalid condition
        if "condition" in data:
            condition = data.get("condition")
            valid_values = ", ".join(c.value for c in Condition)
            if condition not in [c.value for c in Condition]:
                abort(
                    status.HTTP_400_BAD_REQUEST,
                    f"Invalid condition. Valid values: {valid_values}",
                )

        # Perform update
        try:
            inventory_item.deserialize(data)
        except DataValidationError as err:
            abort(status.HTTP_400_BAD_REQUEST, str(err))

        # Save the updates to the database
        inventory_item.update()

        app.logger.info(
            "inventory item with ID: %d updated.", inventory_item.id
        )
        return inventory_item.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # DELETE AN INVENTORY ITEM
    # ------------------------------------------------------------------
    @api.doc("delete_inventory_items")
    @api.response(204, "Inventory Item deleted")
    def delete(self, public_id):
        """
        Delete an Inventory Item

        This endpoint will delete an Inventory Item based on the public_id
        specified in the path
        """
        app.logger.info(
            "Request to Delete an inventory item with public_id [%s]",
            public_id,
        )

        item = InventoryItem.find_by_public_id(public_id)
        if item:
            app.logger.info(
                "Inventory Item with public_id: %s found.", item.public_id
            )
            item.delete()

        app.logger.info(
            "Inventory Item with public_id: %s delete complete.", public_id
        )
        return "", status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /inventory
######################################################################
@api.route("/inventory", strict_slashes=False)
class InventoryCollection(Resource):
    """Handles all interactions with collections of Inventory Items"""

    # ------------------------------------------------------------------
    # LIST ALL INVENTORY ITEMS
    # ------------------------------------------------------------------
    @api.doc("list_inventory_items")
    @api.marshal_list_with(inventory_model)
    def get(self):
        """Returns all of the Inventory Items"""
        app.logger.info("Request to List all Inventory Items...")

        items = []

        # Parse any arguments from the query string
        product_id = request.args.get("product_id")
        condition = request.args.get("condition")
        restock = request.args.get("restock")

        query = InventoryItem.query

        if product_id:
            app.logger.info("Find by product_id: %s", product_id)
            query = query.filter(InventoryItem.product_id == product_id)
        if condition:
            app.logger.info("Find by condition: %s", condition)
            try:
                query = query.filter(
                    InventoryItem.condition == Condition[condition.upper()]
                )
            except KeyError:
                valid_values = ", ".join(c.value for c in Condition)
                abort(
                    status.HTTP_400_BAD_REQUEST,
                    f"Invalid condition. Valid values: {valid_values}",
                )
        if restock is not None:
            if restock.lower() not in ["true", "false"]:
                app.logger.error("Invalid restock value: %s", restock)
                abort(
                    status.HTTP_400_BAD_REQUEST,
                    "Invalid value for 'restock'. Must be 'true' or 'false'.",
                )
            if restock.lower() == "true":
                app.logger.info(
                    "Filtering for items needing restock (quantity <= restock_level)"
                )
                query = query.filter(
                    InventoryItem.quantity <= InventoryItem.restock_level
                )

        items = query.all()

        results = [item.serialize() for item in items]
        app.logger.info("Returning %d inventory items", len(results))
        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # ADD A NEW INVENTORY ITEM
    # ------------------------------------------------------------------
    @api.doc("create_inventory_items")
    @api.response(400, "The posted data was not valid")
    @api.expect(create_model)
    @api.marshal_with(inventory_model, code=201)
    def post(self):
        """
        Creates an Inventory Item

        This endpoint will create an Inventory Item based the data in the body
        that is posted
        """
        app.logger.info("Request to Create a Inventory Item...")
        check_content_type("application/json")

        data = api.payload
        app.logger.info("Processing: %s", data)
        if data is None:
            abort(
                status.HTTP_400_BAD_REQUEST,
                "Invalid JSON or request body",
            )

        inventory_item = InventoryItem()
        try:
            inventory_item.deserialize(data)
        except DataValidationError as err:
            abort(status.HTTP_400_BAD_REQUEST, str(err))

        # Validate product_id is not empty
        if not inventory_item.product_id or not inventory_item.product_id.strip():
            abort(
                status.HTTP_400_BAD_REQUEST,
                "Invalid InventoryItem: product_id must not be empty",
            )

        # Prevent duplicate (product_id + condition) -> 409 CONFLICT
        existing = InventoryItem.query.filter_by(
            product_id=inventory_item.product_id,
            condition=inventory_item.condition,
        ).first()
        if existing is not None:
            abort(
                status.HTTP_409_CONFLICT,
                f"An inventory item already exists for "
                f"product_id={inventory_item.product_id} "
                f"with condition={inventory_item.condition.value}",
            )

        inventory_item.create()
        app.logger.info(
            "Inventory Item with new id [%s] saved!", inventory_item.id
        )
        location_url = api.url_for(
            InventoryResource,
            public_id=inventory_item.public_id,
            _external=True,
        )
        return (
            inventory_item.serialize(),
            status.HTTP_201_CREATED,
            {"Location": location_url},
        )


######################################################################
#  PATH: /inventory/{id}/restock
######################################################################
@api.route("/inventory/<public_id>/restock")
@api.param("public_id", "The Inventory Item identifier")
class RestockResource(Resource):
    """Restock actions on an Inventory Item"""

    @api.doc("restock_inventory_item")
    @api.response(404, "Inventory Item not found")
    @api.marshal_with(inventory_model)
    def post(self, public_id):
        """
        Restock an Inventory Item

        This endpoint will increase the quantity of an item by its
        restock_amount
        """
        app.logger.info(
            "Request to Restock inventory item with id [%s]", public_id
        )

        # Find Inventory Item by public id
        inventory_item = InventoryItem.find_by_public_id(public_id)
        if not inventory_item:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Inventory item with id '{public_id}' was not found.",
            )

        # Restock: add restock_amount to quantity
        inventory_item.quantity += inventory_item.restock_amount
        inventory_item.update()

        app.logger.info(
            "Inventory item [%s] restocked by [%d]",
            public_id,
            inventory_item.restock_amount,
        )
        return inventory_item.serialize(), status.HTTP_200_OK


######################################################################
#  PATH: /inventory/{id}/decrement
######################################################################
@api.route("/inventory/<public_id>/decrement")
@api.param("public_id", "The Inventory Item identifier")
class DecrementResource(Resource):
    """Decrement actions on an Inventory Item"""

    @api.doc("decrement_inventory_item")
    @api.response(404, "Inventory Item not found")
    @api.response(400, "Invalid decrement request")
    @api.marshal_with(inventory_model)
    def post(self, public_id):
        """
        Decrement the quantity of an Inventory Item

        This endpoint will decrement the quantity of an item by a specific
        amount
        """
        app.logger.info(
            "Request to Decrement inventory item with id [%s]", public_id
        )
        check_content_type("application/json")

        # Find Inventory Item by public id
        inventory_item = InventoryItem.find_by_public_id(public_id)
        if not inventory_item:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Inventory item with id '{public_id}' was not found.",
            )

        data = api.payload
        if data is None or "amount" not in data:
            abort(
                status.HTTP_400_BAD_REQUEST,
                "Missing 'amount' in request body",
            )

        amount = data.get("amount")

        # Verify amount is non-negative
        if not isinstance(amount, int) or amount < 0:
            abort(
                status.HTTP_400_BAD_REQUEST,
                "quantity must be non-negative",
            )

        # Check storage
        if inventory_item.quantity < amount:
            abort(
                status.HTTP_400_BAD_REQUEST,
                "INSUFFICIENT INVENTORY",
            )

        # Decrement
        inventory_item.quantity -= amount
        inventory_item.update()

        app.logger.info(
            "Inventory item [%s] decremented by [%d]", public_id, amount
        )
        return inventory_item.serialize(), status.HTTP_200_OK


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


######################################################################
# HTTP error code to error name mapping
######################################################################
ERROR_NAMES = {
    400: "Bad Request",
    404: "Not Found",
    405: "Method not Allowed",
    409: "Conflict",
    415: "Unsupported media type",
    500: "Internal Server Error",
}


def abort(error_code: int, message: str):
    """Logs errors before aborting"""
    app.logger.error(message)
    api.abort(
        error_code,
        message,
        error=ERROR_NAMES.get(error_code, "Error"),
        status=error_code,
    )


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
