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
Error handlers
Handles all of the HTTP Error Codes returning JSON messages
"""
from flask import current_app as app
from werkzeug.exceptions import MethodNotAllowed
from service.routes import api
from service.models import DataValidationError
from . import status


######################################################################
# Error Handlers
######################################################################
@app.errorhandler(DataValidationError)
def request_validation_error(error):
    """Handles DataValidationError from bad data - Flask-RESTX does not handle this automatically"""
    message = str(error)
    app.logger.warning(message)
    return {
        "status": status.HTTP_400_BAD_REQUEST,
        "error": "Bad Request",
        "message": message,
    }, status.HTTP_400_BAD_REQUEST


@api.errorhandler(MethodNotAllowed)
def api_method_not_allowed(error):
    """Handles 405 errors raised inside Flask-RESTX API routes"""
    message = str(error)
    app.logger.warning(message)
    return {
        "status": status.HTTP_405_METHOD_NOT_ALLOWED,
        "error": "Method not Allowed",
        "message": message,
    }, status.HTTP_405_METHOD_NOT_ALLOWED


@api.errorhandler
def default_error_handler(error):
    """Default error handler for unhandled exceptions in API routes"""
    message = str(error)
    app.logger.error(message)
    return {
        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "error": "Internal Server Error",
        "message": message,
    }, status.HTTP_500_INTERNAL_SERVER_ERROR
