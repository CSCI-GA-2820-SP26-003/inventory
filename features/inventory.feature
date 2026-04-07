Feature: The inventory service back-end
    As an Inventory Manager
    I need a RESTful inventory service
    So that I can keep track of all my inventory items

Background:
    Given the following inventory items
        | product_id | condition | quantity | restock_level | restock_amount |
        | PROD001    | NEW       | 100      | 20            | 50             |
        | PROD002    | OPEN_BOX  | 30       | 10            | 25             |
        | PROD003    | USED      | 5        | 15            | 40             |
        | PROD004    | NEW       | 50       | 25            | 30             |

Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Inventory Service" in the title
    And I should not see "404 Not Found"

Scenario: Create an Inventory Item
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD_NEW"
    And I select "New" in the "Condition" dropdown
    And I set the "Quantity" to "100"
    And I set the "Restock Level" to "20"
    And I set the "Restock Amount" to "50"
    And I press the "Create" button
    Then I should see the message "Success"
    When I copy the "Id" field
    And I press the "Clear" button
    Then the "Id" field should be empty
    And the "Product Id" field should be empty
    When I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "PROD_NEW" in the "Product Id" field
    And I should see "New" in the "Condition" dropdown
    And I should see "100" in the "Quantity" field
    And I should see "20" in the "Restock Level" field
    And I should see "50" in the "Restock Amount" field

Scenario: Create a duplicate Inventory Item
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD001"
    And I select "New" in the "Condition" dropdown
    And I set the "Quantity" to "10"
    And I set the "Restock Level" to "5"
    And I set the "Restock Amount" to "15"
    And I press the "Create" button
    Then I should see the message "already exists"

Scenario: Create an Inventory Item with Open Box condition
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD_OPENBOX"
    And I select "Open Box" in the "Condition" dropdown
    And I set the "Quantity" to "30"
    And I set the "Restock Level" to "10"
    And I set the "Restock Amount" to "25"
    And I press the "Create" button
    Then I should see the message "Success"
    And I should see "PROD_OPENBOX" in the "Product Id" field
    And I should see "Open Box" in the "Condition" dropdown

Scenario: Create an Inventory Item with Used condition
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD_USED"
    And I select "Used" in the "Condition" dropdown
    And I set the "Quantity" to "5"
    And I set the "Restock Level" to "15"
    And I set the "Restock Amount" to "40"
    And I press the "Create" button
    Then I should see the message "Success"
    And I should see "PROD_USED" in the "Product Id" field
    And I should see "Used" in the "Condition" dropdown

Scenario: Create an Inventory Item with zero quantity
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD_ZERO"
    And I select "New" in the "Condition" dropdown
    And I set the "Quantity" to "0"
    And I set the "Restock Level" to "10"
    And I set the "Restock Amount" to "20"
    And I press the "Create" button
    Then I should see the message "Success"
    And I should see "0" in the "Quantity" field

Scenario: Create an Inventory Item with empty product id
    When I visit the "Home Page"
    And I set the "Quantity" to "10"
    And I set the "Restock Level" to "5"
    And I set the "Restock Amount" to "15"
    And I press the "Create" button
    Then I should see the message "product_id must not be empty"

Scenario: Create an Inventory Item with negative quantity
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD_NEG"
    And I select "New" in the "Condition" dropdown
    And I set the "Quantity" to "-5"
    And I set the "Restock Level" to "10"
    And I set the "Restock Amount" to "20"
    And I press the "Create" button
    Then I should see the message "ck_quantity_non_negative"

Scenario: Read an Inventory Item
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD001"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "PROD001" in the "Product Id" field
    When I copy the "Id" field
    And I press the "Clear" button
    And I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "PROD001" in the "Product Id" field
    And I should see "New" in the "Condition" dropdown
    And I should see "100" in the "Quantity" field
    And I should see "20" in the "Restock Level" field
    And I should see "50" in the "Restock Amount" field

Scenario: Read an Inventory Item that does not exist
    When I visit the "Home Page"
    And I set the "Id" to "00000000-0000-0000-0000-000000000000"
    And I press the "Retrieve" button
    Then I should see the message "was not found"

Scenario: Delete an Inventory Item
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD001"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "PROD001" in the "Product Id" field
    When I press the "Delete" button
    Then I should see the message "Item has been Deleted!"
    When I press the "Clear" button
    And I set the "Product Id" to "PROD001"
    And I press the "Search" button
    Then I should see the message "No items found" 
    And I should not see "PROD001" in the results

Scenario: Query by Product Id
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD001"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "PROD001" in the results
    And I should not see "PROD002" in the results

Scenario: Query by Condition
    When I visit the "Home Page"
    And I select "USED" from the "condition" filter dropdown
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "PROD003" in the results
    And I should not see "PROD001" in the results

Scenario: Query by both Product Id and Condition
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD001"
    And I select "NEW" from the "condition" filter dropdown
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "PROD001" in the results
    And I should see "NEW" in the results

Scenario: No Query Results Found
    When I visit the "Home Page"
    And I set the "Product Id" to "nonexistent"
    And I press the "Search" button
    Then I should see "No items found" in the results

# update
Scenario: Update an Inventory Item via inline edit
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD001"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "PROD001" in the results
    When I click the "Edit" button in the results table
    And I set the row "Quantity" field to "200"
    And I press the "Save" button in the results table
    Then I should see the message "Success"
    And I should see "200" in the results

Scenario: Update an Inventory Item with invalid quantity
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD001"
    And I press the "Search" button
    Then I should see the message "Success"
    When I click the "Edit" button in the results table
    And I set the row "Quantity" field to "-10"
    And I press the "Save" button in the results table
    Then I should see an error for the row "Quantity" field

Scenario: Cancel editing an Inventory Item
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD001"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "100" in the results
    When I click the "Edit" button in the results table
    And I set the row "Quantity" field to "999"
    And I press the "Cancel" button in the results table
    Then I should see "100" in the results
    And I should not see "999" in the results

Scenario: Update an Inventory Item that does not exist
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD001"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "PROD001" in the results
    When I click the "Edit" button in the results table
    And I press the "Delete" button
    And I set the row "Quantity" field to "999"
    And I press the "Save" button in the results table
    Then I should see the message "was not found"

Scenario: Update an Inventory Item condition via inline edit
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD002"
    And I select "OPEN_BOX" from the "condition" filter dropdown
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "PROD002" in the results
    When I click the "Edit" button in the results table
    And I select "Used" in the row "Condition" dropdown
    And I press the "Save" button in the results table
    Then I should see the message "Success"
    And I should see "USED" in the results

Scenario: Update restock_level and restock_amount via inline edit
    When I visit the "Home Page"
    And I set the "Product Id" to "PROD004"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "PROD004" in the results
    When I click the "Edit" button in the results table
    And I set the row "Restock Level" field to "35"
    And I set the row "Restock Amount" field to "45"
    And I press the "Save" button in the results table
    Then I should see the message "Success"
    And I should see "35" in the results
    And I should see "45" in the results

# UI - Filter Inventory Items (#41)

Scenario: filter by condition
    Given the following inventory items exist
        | product_id | quantity | condition | restock_level | restock_amount |
        | product1   | 100      | NEW       | 0             | 0              |
        | product2   | 50       | USED      | 0             | 0              |
        | product3   | 30       | NEW       | 0             | 0              |
    When I visit the "Home Page"
    And I select "NEW" from the "condition" filter dropdown
    And I press the "Search" button
    Then I should see "product1" in the result
    And I should see "product3" in the result
    And I should not see "product2" in the result

Scenario: filter by quantity range
    Given the following inventory items exist
        | product_id | quantity | condition | restock_level | restock_amount |
        | product1   | 100      | NEW       | 0             | 0              |
        | product2   | 50       | USED      | 0             | 0              |
        | product3   | 10       | NEW       | 0             | 0              |
    When I visit the "Home Page"
    And I enter "20" in the "quantity min" filter field
    And I enter "80" in the "quantity max" filter field
    And I press the "Search" button
    Then I should see "product2" in the result
    And I should not see "product1" in the result
    And I should not see "product3" in the result

Scenario: filter by restock_level range
    Given the following inventory items exist
        | product_id | quantity | condition | restock_level | restock_amount |
        | product1   | 0        | NEW       | 10            | 0              |
        | product2   | 0        | USED      | 30            | 0              |
        | product3   | 0        | NEW       | 50            | 0              |
    When I visit the "Home Page"
    And I enter "20" in the "restock_level min" filter field
    And I enter "40" in the "restock_level max" filter field
    And I press the "Search" button
    Then I should see "product2" in the result
    And I should not see "product1" in the result
    And I should not see "product3" in the result

Scenario: filter by restock_amount range
    Given the following inventory items exist
        | product_id | quantity | condition | restock_level | restock_amount |
        | product1   | 0        | NEW       | 0             | 100            |
        | product2   | 0        | USED      | 0             | 200            |
        | product3   | 0        | NEW       | 0             | 300            |
    When I visit the "Home Page"
    And I enter "150" in the "restock_amount min" filter field
    And I enter "250" in the "restock_amount max" filter field
    And I press the "Search" button
    Then I should see "product2" in the result
    And I should not see "product1" in the result
    And I should not see "product3" in the result

Scenario: filter with multiple fields combined
    Given the following inventory items exist
        | product_id | quantity | condition | restock_level | restock_amount |
        | product1   | 100      | NEW       | 0             | 0              |
        | product2   | 100      | USED      | 0             | 0              |
        | product3   | 50       | NEW       | 0             | 0              |
    When I visit the "Home Page"
    And I select "NEW" from the "condition" filter dropdown
    And I enter "80" in the "quantity min" filter field
    And I press the "Search" button
    Then I should see "product1" in the result
    And I should not see "product2" in the result
    And I should not see "product3" in the result

Scenario: no items match the filter
    Given the following inventory items exist
        | product_id | quantity | condition | restock_level | restock_amount |
        | product1   | 100      | NEW       | 0             | 0              |
    When I visit the "Home Page"
    And I select "OPEN_BOX" from the "condition" filter dropdown
    And I press the "Search" button
    Then I should see an empty state message
    And the result shows nothing

Scenario: API error
    Given the following inventory items exist
        | product_id | quantity | condition | restock_level | restock_amount |
        | product1   | 100      | NEW       | 0             | 0              |
    And the server returns an error on "GET /inventory"
    When I visit the "Home Page"
    And I select "NEW" from the "condition" filter dropdown
    And I press the "Search" button
    Then I should see an error message from the server response
    And the result shows nothing

Scenario: invalid numeric filter input
    When I visit the "Home Page"
    And I enter "-10" in the "quantity min" filter field
    And I press the "Search" button
    Then I should see an input error message for the "quantity min" field
    And no API call should be made

Scenario: min value greater than max value
    When I visit the "Home Page"
    And I enter "100" in the "quantity min" filter field
    And I enter "50" in the "quantity max" filter field
    And I press the "Search" button
    Then I should see an input error message indicating "Min must not be greater than max"
    And no API call should be made
