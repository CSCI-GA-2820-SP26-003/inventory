$(function () {

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#item_id").val(res.public_id);
        $("#item_product_id").val(res.product_id);
        $("#item_condition").val(res.condition);
        $("#item_quantity").val(res.quantity);
        $("#item_restock_level").val(res.restock_level);
        $("#item_restock_amount").val(res.restock_amount);
    }

    /// Clears all form fields
    function clear_form_data() {
        $("#item_product_id").val("");
        $("#item_condition").val("");
        $("#item_quantity").val("");
        $("#item_restock_level").val("");
        $("#item_restock_amount").val("");
    }

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    // ****************************************
    // Create an Inventory Item
    // ****************************************

    $("#create-btn").click(function () {

        let product_id = $("#item_product_id").val();
        let condition = $("#item_condition").val();
        let quantity = parseInt($("#item_quantity").val());
        let restock_level = parseInt($("#item_restock_level").val());
        let restock_amount = parseInt($("#item_restock_amount").val());

        let data = {
            "product_id": product_id,
            "condition": condition,
            "quantity": quantity,
            "restock_level": restock_level,
            "restock_amount": restock_amount
        };

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "POST",
            url: "/inventory",
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });
    });


    // ****************************************
    // Update an Inventory Item
    // ****************************************

    $("#update-btn").click(function () {

        let item_id = $("#item_id").val();
        let product_id = $("#item_product_id").val();
        let condition = $("#item_condition").val();
        let quantity = parseInt($("#item_quantity").val());
        let restock_level = parseInt($("#item_restock_level").val());
        let restock_amount = parseInt($("#item_restock_amount").val());

        let data = {
            "product_id": product_id,
            "condition": condition,
            "quantity": quantity,
            "restock_level": restock_level,
            "restock_amount": restock_amount
        };

        $("#flash_message").empty();

        let ajax = $.ajax({
                type: "PUT",
                url: `/inventory/${item_id}`,
                contentType: "application/json",
                data: JSON.stringify(data)
            })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Retrieve an Inventory Item
    // ****************************************

    $("#retrieve-btn").click(function () {

        let item_id = $("#item_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/inventory/${item_id}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Delete an Inventory Item
    // ****************************************

    $("#delete-btn").click(function () {

        let item_id = $("#item_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "DELETE",
            url: `/inventory/${item_id}`,
            contentType: "application/json",
            data: '',
        })

        ajax.done(function(res){
            clear_form_data()
            flash_message("Item has been Deleted!")
        });

        ajax.fail(function(res){
            flash_message("Server error!")
        });
    });

    // ****************************************
    // Clear the form
    // ****************************************

    $("#clear-btn").click(function () {
        $("#item_id").val("");
        $("#flash_message").empty();
        clear_form_data()
    });

    // ****************************************
    // Search for Inventory Items
    // ****************************************

    $("#search-btn").click(function () {

        let product_id = $("#item_product_id").val();
        let condition = $("#item_condition").val();

        let queryString = ""

        if (product_id) {
            queryString += 'product_id=' + product_id
        }
        if (condition) {
            if (queryString.length > 0) {
                queryString += '&condition=' + condition
            } else {
                queryString += 'condition=' + condition
            }
        }

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/inventory?${queryString}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            $("#search_results").empty();
            let table = '<table class="table table-striped" cellpadding="10">'
            table += '<thead><tr>'
            table += '<th class="col-md-2">ID</th>'
            table += '<th class="col-md-2">Product ID</th>'
            table += '<th class="col-md-2">Condition</th>'
            table += '<th class="col-md-2">Quantity</th>'
            table += '<th class="col-md-2">Restock Level</th>'
            table += '<th class="col-md-2">Restock Amount</th>'
            table += '</tr></thead><tbody>'
            let firstItem = "";
            for(let i = 0; i < res.length; i++) {
                let item = res[i];
                table +=  `<tr id="row_${i}"><td>${item.public_id}</td><td>${item.product_id}</td><td>${item.condition}</td><td>${item.quantity}</td><td>${item.restock_level}</td><td>${item.restock_amount}</td></tr>`;
                if (i == 0) {
                    firstItem = item;
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // copy the first result to the form
            if (firstItem != "") {
                update_form_data(firstItem)
            }

            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

})
