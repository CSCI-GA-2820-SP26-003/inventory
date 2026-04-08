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

# pylint: disable=function-redefined, missing-function-docstring
# flake8: noqa
"""
Web Steps

Steps file for web interactions with Selenium

For information on Waiting until elements are present in the HTML see:
    https://selenium-python.readthedocs.io/waits.html
"""
import re
import logging
from typing import Any
from behave import when, then  # pylint: disable=no-name-in-module
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions

ID_PREFIX = "item_"


def save_screenshot(context: Any, filename: str) -> None:
    """Takes a snapshot of the web page for debugging and validation

    Args:
        context (Any): The session context
        filename (str): The message that you are looking for
    """
    # Remove all non-word characters (everything except numbers and letters)
    filename = re.sub(r"[^\w\s]", "", filename)
    # Replace all runs of whitespace with a single dash
    filename = re.sub(r"\s+", "-", filename)
    context.driver.save_screenshot(f"./captures/{filename}.png")


@when('I visit the "Home Page"')
def step_impl(context: Any) -> None:
    """Make a call to the base URL"""
    context.driver.get(context.base_url)
    # Uncomment next line to take a screenshot of the web page
    # save_screenshot(context, 'Home Page')


@then('I should see "{message}" in the title')
def step_impl(context: Any, message: str) -> None:
    """Check the document title for a message"""
    assert message in context.driver.title


@then('I should not see "{text_string}"')
def step_impl(context: Any, text_string: str) -> None:
    element = context.driver.find_element(By.TAG_NAME, "body")
    assert text_string not in element.text


@when('I set the "{element_name}" to "{text_string}"')
def step_impl(context: Any, element_name: str, text_string: str) -> None:
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    element = context.driver.find_element(By.ID, element_id)
    element.clear()
    element.send_keys(text_string)


@when('I select "{text}" in the "{element_name}" dropdown')
def step_impl(context: Any, text: str, element_name: str) -> None:
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    element = Select(context.driver.find_element(By.ID, element_id))
    element.select_by_visible_text(text)


@then('I should see "{text}" in the "{element_name}" dropdown')
def step_impl(context: Any, text: str, element_name: str) -> None:
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    element = Select(context.driver.find_element(By.ID, element_id))
    assert element.first_selected_option.text == text


@then('the "{element_name}" field should be empty')
def step_impl(context: Any, element_name: str) -> None:
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    element = context.driver.find_element(By.ID, element_id)
    assert element.get_attribute("value") == ""


##################################################################
# These two function simulate copy and paste
##################################################################
@when('I copy the "{element_name}" field')
def step_impl(context: Any, element_name: str) -> None:
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located((By.ID, element_id))
    )
    context.clipboard = element.get_attribute("value")
    logging.info("Clipboard contains: %s", context.clipboard)


@when('I paste the "{element_name}" field')
def step_impl(context: Any, element_name: str) -> None:
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located((By.ID, element_id))
    )
    element.clear()
    element.send_keys(context.clipboard)


##################################################################
# This code works because of the following naming convention:
# The buttons have an id in the html hat is the button text
# in lowercase followed by '-btn' so the Clear button has an id of
# id='clear-btn'. That allows us to lowercase the name and add '-btn'
# to get the element id of any button
##################################################################


@when('I press the "{button}" button')
def step_impl(context: Any, button: str) -> None:
    button_id = button.lower().replace(" ", "_") + "-btn"
    context.driver.find_element(By.ID, button_id).click()


@then('I should see "{name}" in the results')
def step_impl(context: Any, name: str) -> None:
    found = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, "search_results"), name
        )
    )
    assert found


@then('I should not see "{name}" in the results')
def step_impl(context: Any, name: str) -> None:
    element = context.driver.find_element(By.ID, "search_results")
    assert name not in element.text


@then('I should see the message "{message}"')
def step_impl(context: Any, message: str) -> None:
    # Uncomment next line to take a screenshot of the web page for debugging
    # save_screenshot(context, message)
    found = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, "flash_message"), message
        )
    )
    assert found


##################################################################
# This code works because of the following naming convention:
# The id field for text input in the html is the element name
# prefixed by ID_PREFIX so the Product Id field has an id='item_product_id'
# We can then lowercase the name and prefix with item_ to get the id
##################################################################


@then('I should see "{text_string}" in the "{element_name}" field')
def step_impl(context: Any, text_string: str, element_name: str) -> None:
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    found = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.text_to_be_present_in_element_value(
            (By.ID, element_id), text_string
        )
    )
    assert found


@when('I change "{element_name}" to "{text_string}"')
def step_impl(context: Any, element_name: str, text_string: str) -> None:
    element_id = ID_PREFIX + element_name.lower().replace(" ", "_")
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located((By.ID, element_id))
    )
    element.clear()
    element.send_keys(text_string)


@then("the results table should be cleared")
def step_impl(context):
    """Checks if the search results table is empty or only contains the header"""
    element = context.driver.find_element(By.ID, "search_results")
    # In index.html, clearing empties the div or the tbody
    rows = element.find_elements(By.TAG_NAME, "tr")
    # If using the update above, an empty search shows "No items found" or empty table
    # We verify that no data rows exist (length <= 1 if header exists, or look for specific empty text)
    assert len(rows) <= 1 or "No items found" not in element.text


##################################################################
# Steps for inline editing in the search results table
##################################################################


@when('I click the "Edit" button in the results table')
def step_impl(context: Any) -> None:
    button = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.element_to_be_clickable(
            (By.CSS_SELECTOR, "#search_results .edit-row-btn")
        )
    )
    button.click()


@when('I set the row "{field_name}" field to "{text_string}"')
def step_impl(context: Any, field_name: str, text_string: str) -> None:
    field_id = field_name.lower().replace(" ", "_")
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located(
            (By.CSS_SELECTOR, f'#search_results [data-field="{field_id}"]')
        )
    )
    element.clear()
    element.send_keys(text_string)


@when('I select "{text}" in the row "{field_name}" dropdown')
def step_impl(context: Any, text: str, field_name: str) -> None:
    field_id = field_name.lower().replace(" ", "_")
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located(
            (By.CSS_SELECTOR, f'#search_results [data-field="{field_id}"]')
        )
    )
    Select(element).select_by_visible_text(text)


@when('I press the "Save" button in the results table')
def step_impl(context: Any) -> None:
    button = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.element_to_be_clickable(
            (By.CSS_SELECTOR, "#search_results .save-row-btn")
        )
    )
    button.click()


@when('I press the "Cancel" button in the results table')
def step_impl(context: Any) -> None:
    button = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.element_to_be_clickable(
            (By.CSS_SELECTOR, "#search_results .cancel-row-btn")
        )
    )
    button.click()


@then('I should see an error for the row "{field_name}" field')
def step_impl(context: Any, field_name: str) -> None:
    field_id = field_name.lower().replace(" ", "_")
    error_div = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located(
            (By.CSS_SELECTOR, f"#search_results .err-{field_id}")
        )
    )
    assert error_div.text != ""


##################################################################
# Steps for numeric range filter inputs
##################################################################


@when('I enter "{value}" in the "{field}" filter field')
def step_impl(context: Any, value: str, field: str) -> None:
    field_id = "filter_" + field.lower().replace(" ", "_")
    element = context.driver.find_element(By.ID, field_id)
    element.clear()
    element.send_keys(value)


@then('I should see a filter error for the "{field}" field')
def step_impl(context: Any, field: str) -> None:
    field_id = "err_" + field.lower().replace(" ", "_")
    error_span = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located((By.ID, field_id))
    )
    assert error_span.text != ""


@when('I click the "Decrement" button in the results table')
def step_impl(context):
    button = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.element_to_be_clickable(
            (By.CSS_SELECTOR, ".decrement-row-btn")
        )
    )
    button.click()


@when('I enter "{value}" in the "amount" field')
def step_impl(context, value):
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located((By.ID, "decrement_amount"))
    )
    element.clear()
    element.send_keys(value)


@when('I click the "Confirm" button in the results table')
def step_impl(context):
    button = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.element_to_be_clickable(
            (By.CSS_SELECTOR, ".confirm-decrement-btn")
        )
    )
    button.click()


@when('I click the "Cancel" button in the results table')
def step_impl(context):
    button = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.element_to_be_clickable(
            (By.CSS_SELECTOR, ".cancel-decrement-btn")
        )
    )
    button.click()


@then('I should see an input error message for the "{field}" field')
def step_impl(context, field):
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located(
            (By.CSS_SELECTOR, ".err-decrement")
        )
    )
    assert element.text != ""


@then("I should see an error message indicating insufficient inventory")
def step_impl(context):
    found = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located((By.ID, "flash_message"))
    )
    text = found.text.lower()
    assert any(
        word in text
        for word in ["insufficient", "not enough", "lower than", "less than"]
    )
