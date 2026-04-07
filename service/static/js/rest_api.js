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
        let condition = $("#item_condition").val() || "NEW";
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
        $("#filter_quantity_min").val("");
        $("#filter_quantity_max").val("");
        $("#filter_restock_level_min").val("");
        $("#filter_restock_level_max").val("");
        $("#filter_restock_amount_min").val("");
        $("#filter_restock_amount_max").val("");
        $("#err_quantity").text("");
        $("#err_restock_level").text("");
        $("#err_restock_amount").text("");
        clear_form_data()
    });

    // ****************************************
    // Search for Inventory Items in results table
    // ****************************************

    function validateRangeFilter(minVal, maxVal, errorId) {
        let min = minVal.trim();
        let max = maxVal.trim();
        let minNum = min === "" ? NaN : Number(min);
        let maxNum = max === "" ? NaN : Number(max);

        if (min !== "" && (minNum < 0 || !Number.isInteger(minNum))) {
            $(errorId).text("Min must be a non-negative integer");
            return false;
        }
        if (max !== "" && (maxNum < 0 || !Number.isInteger(maxNum))) {
            $(errorId).text("Max must be a non-negative integer");
            return false;
        }
        if (min !== "" && max !== "" && minNum > maxNum) {
            $(errorId).text("Min must not be greater than max");
            return false;
        }
        $(errorId).text("");
        return true;
    }

    $("#search-btn").click(function () {

        // Clear previous filter errors
        $("#err_quantity").text("");
        $("#err_restock_level").text("");
        $("#err_restock_amount").text("");

        // Validate numeric range filters
        let qMinVal = $("#filter_quantity_min").val();
        let qMaxVal = $("#filter_quantity_max").val();
        let rlMinVal = $("#filter_restock_level_min").val();
        let rlMaxVal = $("#filter_restock_level_max").val();
        let raMinVal = $("#filter_restock_amount_min").val();
        let raMaxVal = $("#filter_restock_amount_max").val();

        let valid = true;
        if (!validateRangeFilter(qMinVal, qMaxVal, "#err_quantity")) valid = false;
        if (!validateRangeFilter(rlMinVal, rlMaxVal, "#err_restock_level")) valid = false;
        if (!validateRangeFilter(raMinVal, raMaxVal, "#err_restock_amount")) valid = false;
        if (!valid) return;

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
            let qMin = qMinVal.trim() === "" ? NaN : Number(qMinVal);
            let qMax = qMaxVal.trim() === "" ? NaN : Number(qMaxVal);
            let rlMin = rlMinVal.trim() === "" ? NaN : Number(rlMinVal);
            let rlMax = rlMaxVal.trim() === "" ? NaN : Number(rlMaxVal);
            let raMin = raMinVal.trim() === "" ? NaN : Number(raMinVal);
            let raMax = raMaxVal.trim() === "" ? NaN : Number(raMaxVal);

            res = res.filter(function(item) {
                if (!isNaN(qMin) && item.quantity < qMin) return false;
                if (!isNaN(qMax) && item.quantity > qMax) return false;
                if (!isNaN(rlMin) && item.restock_level < rlMin) return false;
                if (!isNaN(rlMax) && item.restock_level > rlMax) return false;
                if (!isNaN(raMin) && item.restock_amount < raMin) return false;
                if (!isNaN(raMax) && item.restock_amount > raMax) return false;
                return true;
            });

            $("#search_results").empty();
            let table = '<table class="table table-striped" cellpadding="10">'
            table += '<thead><tr>'
            table += '<th class="col-md-1">ID</th>'
            table += '<th class="col-md-2">Product ID</th>'
            table += '<th class="col-md-2">Condition</th>'
            table += '<th class="col-md-1">Quantity</th>'
            table += '<th class="col-md-2">Restock Level</th>'
            table += '<th class="col-md-2">Restock Amount</th>'
            table += '<th class="col-md-1">Update</th>'
            table += '<th class="col-md-1">Decrement</th>'
            table += '</tr></thead><tbody>'

            let firstItem = "";
            if (res.length > 0) {
                for(let i = 0; i < res.length; i++) {
                    let item = res[i];
                    table += `<tr id="row_${i}" data-public-id="${item.public_id}">` +
                        `<td>${item.public_id}</td>` +
                        `<td>${item.product_id}</td>` +
                        `<td>${item.condition}</td>` +
                        `<td>${item.quantity}</td>` +
                        `<td>${item.restock_level}</td>` +
                        `<td>${item.restock_amount}</td>` +
                        `<td><button class="btn btn-xs btn-warning edit-row-btn">Edit</button></td>` +
                        `<td><button class="btn btn-xs btn-info decrement-row-btn">Decrement</button></td>` +
                        `</tr>`;
                    if (i == 0) {
                        firstItem = item;
                    }
                }
                table += '</tbody></table>';
                $("#search_results").append(table);

                if (firstItem != "") {
                    update_form_data(firstItem);
                }
                flash_message("Success");
            } else {
                $("#search_results").append('<div class="text-center">No items found</div>');
                flash_message("No items found");
            }
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Edit button in search results row
    // ****************************************

    $("#search_results").on("click", ".edit-row-btn", function () {
        let $row = $(this).closest("tr");
        let cells = $row.find("td");

        let orig = {
            product_id: cells.eq(1).text(),
            condition: cells.eq(2).text(),
            quantity: cells.eq(3).text(),
            restock_level: cells.eq(4).text(),
            restock_amount: cells.eq(5).text()
        };
        $row.data("orig", orig);

        cells.eq(1).empty().append(
            $('<input type="text" class="form-control input-sm" data-field="product_id">').val(orig.product_id)
        );
        cells.eq(2).empty().append(
            $('<select class="form-control input-sm" data-field="condition">' +
              '<option value="NEW">New</option>' +
              '<option value="OPEN_BOX">Open Box</option>' +
              '<option value="USED">Used</option>' +
              '</select>').val(orig.condition)
        );
        cells.eq(3).empty().append(
            $('<input type="number" class="form-control input-sm" data-field="quantity">').val(orig.quantity),
            $('<div class="text-danger small err-quantity"></div>')
        );
        cells.eq(4).empty().append(
            $('<input type="number" class="form-control input-sm" data-field="restock_level">').val(orig.restock_level),
            $('<div class="text-danger small err-restock_level"></div>')
        );
        cells.eq(5).empty().append(
            $('<input type="number" class="form-control input-sm" data-field="restock_amount">').val(orig.restock_amount),
            $('<div class="text-danger small err-restock_amount"></div>')
        );
        cells.eq(6).html(
            `<button class="btn btn-xs btn-success save-row-btn">Save</button> ` +
            `<button class="btn btn-xs btn-default cancel-row-btn">Cancel</button>`
        );
    });

    // ****************************************
    // Cancel button in search results row
    // ****************************************

    $("#search_results").on("click", ".cancel-row-btn", function () {
        let $row = $(this).closest("tr");
        let orig = $row.data("orig");
        let cells = $row.find("td");

        cells.eq(1).text(orig.product_id);
        cells.eq(2).text(orig.condition);
        cells.eq(3).text(orig.quantity);
        cells.eq(4).text(orig.restock_level);
        cells.eq(5).text(orig.restock_amount);
        cells.eq(6).html(`<button class="btn btn-xs btn-warning edit-row-btn">Edit</button>`);
    });

    // ****************************************
    // Save button in search results row
    // ****************************************

    $("#search_results").on("click", ".save-row-btn", function () {
        let $row = $(this).closest("tr");
        let cells = $row.find("td");
        let public_id = $row.data("public-id");

        let product_id = cells.eq(1).find("input").val();
        let condition = cells.eq(2).find("select").val();
        let quantity = parseInt(cells.eq(3).find("input").val());
        let restock_level = parseInt(cells.eq(4).find("input").val());
        let restock_amount = parseInt(cells.eq(5).find("input").val());

        // Client-side validation
        let valid = true;
        $row.find(".err-quantity").text("");
        $row.find(".err-restock_level").text("");
        $row.find(".err-restock_amount").text("");

        if (isNaN(quantity) || quantity < 0) {
            $row.find(".err-quantity").text("Must be a non-negative integer");
            valid = false;
        }
        if (isNaN(restock_level) || restock_level < 0) {
            $row.find(".err-restock_level").text("Must be a non-negative integer");
            valid = false;
        }
        if (isNaN(restock_amount) || restock_amount < 0) {
            $row.find(".err-restock_amount").text("Must be a non-negative integer");
            valid = false;
        }
        if (!valid) return;

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
            url: `/inventory/${public_id}`,
            contentType: "application/json",
            data: JSON.stringify(data)
        });

        ajax.done(function (res) {
            cells.eq(1).text(res.product_id);
            cells.eq(2).text(res.condition);
            cells.eq(3).text(res.quantity);
            cells.eq(4).text(res.restock_level);
            cells.eq(5).text(res.restock_amount);
            cells.eq(6).html(`<button class="btn btn-xs btn-warning edit-row-btn">Edit</button>`);
            flash_message("Success");
        });

        ajax.fail(function (res) {
            flash_message(res.responseJSON.message);
        });
    });

    $("#search_results").on("click", ".decrement-row-btn", function () {
        let $row = $(this).closest("tr");
        let $qtyCell = $row.find("td").eq(3);
        let currentQty = $qtyCell.text();
        $("#flash_message").empty();
        $row.data("orig-qty", currentQty);
        $qtyCell.html(
            `<input type="number" class="form-control input-sm" id="decrement_amount" placeholder="Amount">` +
            `<div class="text-danger small err-decrement"></div>`
        );
        $row.find("td").eq(7).html(
            `<button class="btn btn-xs btn-success confirm-decrement-btn">Confirm</button> ` +
            `<button class="btn btn-xs btn-default cancel-decrement-btn">Cancel</button>`
        );
    });

    $("#search_results").on("click", ".cancel-decrement-btn", function () {
        let $row = $(this).closest("tr");
        let origQty = $row.data("orig-qty");
        $row.find("td").eq(3).text(origQty);
        $row.find("td").eq(7).html(`<button class="btn btn-xs btn-info decrement-row-btn">Decrement</button>`);
    });

    $("#search_results").on("click", ".confirm-decrement-btn", function () {
        let $row = $(this).closest("tr");
        let public_id = $row.data("public-id");
        let amountVal = $row.find("#decrement_amount").val();
        let amount = parseInt(amountVal);
        let $errorDiv = $row.find(".err-decrement");
        $("#flash_message").empty();
        if (isNaN(amount) || amount <= 0) {
            $errorDiv.text("Must be a positive integer");
            return;
        }
        $.ajax({
            type: "POST",
            url: `/inventory/${public_id}/decrement`,
            contentType: "application/json",
            data: JSON.stringify({ "amount": amount })
        }).done(function (res) {
            $row.find("td").eq(3).text(res.quantity);
            $row.find("td").eq(7).html(`<button class="btn btn-xs btn-info decrement-row-btn">Decrement</button>`);
            flash_message("Success");
        }).fail(function (res) {
            let msg = res.responseJSON ? res.responseJSON.message : "Server error!";
            $errorDiv.text(msg);
            flash_message(msg);
        });
    });
})