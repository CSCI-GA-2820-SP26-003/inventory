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
        // Clear filter range fields and errors
        $("#filter_condition").val("");
        $("#filter_quantity_min").val("");
        $("#filter_quantity_max").val("");
        $("#filter_restock_level_min").val("");
        $("#filter_restock_level_max").val("");
        $("#filter_restock_amount_min").val("");
        $("#filter_restock_amount_max").val("");
        $(".filter-error").text("");
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
    // Search for Inventory Items in results table
    // ****************************************

    $("#search-btn").click(function () {

        let product_id = $("#item_product_id").val();
        let condition = $("#filter_condition").val();

        let qty_min_str = $("#filter_quantity_min").val();
        let qty_max_str = $("#filter_quantity_max").val();
        let rl_min_str = $("#filter_restock_level_min").val();
        let rl_max_str = $("#filter_restock_level_max").val();
        let ra_min_str = $("#filter_restock_amount_min").val();
        let ra_max_str = $("#filter_restock_amount_max").val();

        // Clear previous filter errors
        $(".filter-error").text("");

        // Validate and parse filter range inputs
        let valid = true;

        function validateRangeField(minStr, maxStr, minErrId, maxErrId) {
            let minVal = minStr !== "" ? parseInt(minStr, 10) : null;
            let maxVal = maxStr !== "" ? parseInt(maxStr, 10) : null;

            if (minStr !== "" && (isNaN(minVal) || minVal < 0 || String(minVal) !== minStr.trim())) {
                $(minErrId).text("Must be a non-negative integer");
                valid = false;
                minVal = null;
            }
            if (maxStr !== "" && (isNaN(maxVal) || maxVal < 0 || String(maxVal) !== maxStr.trim())) {
                $(maxErrId).text("Must be a non-negative integer");
                valid = false;
                maxVal = null;
            }
            if (minVal !== null && maxVal !== null && minVal > maxVal) {
                $(minErrId).text("Min must not be greater than max");
                valid = false;
            }
            return { minVal, maxVal };
        }

        let qty = validateRangeField(qty_min_str, qty_max_str,
            "#err_filter_quantity_min", "#err_filter_quantity_max");
        let rl = validateRangeField(rl_min_str, rl_max_str,
            "#err_filter_restock_level_min", "#err_filter_restock_level_max");
        let ra = validateRangeField(ra_min_str, ra_max_str,
            "#err_filter_restock_amount_min", "#err_filter_restock_amount_max");

        if (!valid) return;

        let queryParts = [];
        if (product_id) queryParts.push('product_id=' + product_id);
        if (condition) queryParts.push('condition=' + condition);

        let queryString = queryParts.join('&');

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/inventory?${queryString}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            // Apply numeric range filters client-side
            res = res.filter(function(item) {
                if (qty.minVal !== null && item.quantity < qty.minVal) return false;
                if (qty.maxVal !== null && item.quantity > qty.maxVal) return false;
                if (rl.minVal !== null && item.restock_level < rl.minVal) return false;
                if (rl.maxVal !== null && item.restock_level > rl.maxVal) return false;
                if (ra.minVal !== null && item.restock_amount < ra.minVal) return false;
                if (ra.maxVal !== null && item.restock_amount > ra.maxVal) return false;
                return true;
            });

            $("#search_results").empty();
            let table = '<table class="table table-striped" cellpadding="10">'
            table += '<thead><tr>'
            table += '<th class="col-md-2">ID</th>'
            table += '<th class="col-md-2">Product ID</th>'
            table += '<th class="col-md-2">Condition</th>'
            table += '<th class="col-md-2">Quantity</th>'
            table += '<th class="col-md-2">Restock Level</th>'
            table += '<th class="col-md-2">Restock Amount</th>'
            table += '<th class="col-md-2">Update</th>'
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
                // Empty state handler
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
})