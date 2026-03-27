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
