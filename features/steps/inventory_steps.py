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
Inventory Steps

Steps file for inventory.feature

For information on Waiting until elements are present in the HTML see:
    https://selenium-python.readthedocs.io/waits.html
"""
import requests
from compare3 import expect
from behave import given  # pylint: disable=no-name-in-module

# HTTP Return Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204

WAIT_TIMEOUT = 60


def _load_inventory_items(context):
    """ Delete all Inventory Items and load new ones from context.table """
    rest_endpoint = f"{context.base_url}/inventory"
    context.resp = requests.get(rest_endpoint, timeout=WAIT_TIMEOUT)
    expect(context.resp.status_code).equal_to(HTTP_200_OK)
    for item in context.resp.json():
        context.resp = requests.delete(
            f"{rest_endpoint}/{item['public_id']}", timeout=WAIT_TIMEOUT
        )
        expect(context.resp.status_code).equal_to(HTTP_204_NO_CONTENT)

    for row in context.table:
        payload = {
            "product_id": row['product_id'],
            "condition": row['condition'],
            "quantity": int(row.get('quantity', 0)),
            "restock_level": int(row.get('restock_level', 0)),
            "restock_amount": int(row.get('restock_amount', 0)),
        }
        context.resp = requests.post(rest_endpoint, json=payload, timeout=WAIT_TIMEOUT)
        expect(context.resp.status_code).equal_to(HTTP_201_CREATED)


@given('the following inventory items')
def step_impl(context):
    """ Delete all Inventory Items and load new ones """
    _load_inventory_items(context)


@given('the following inventory items exist')
def step_impl(context):
    """ Delete all Inventory Items and load new ones (alias) """
    _load_inventory_items(context)


@given('the server returns an error on "GET /inventory"')
def step_impl(context):
    """Inject a JS mock so the next GET /inventory call returns a server error"""
    # Store flag; actual injection happens after page load in the When step
    context.inject_server_error = True
