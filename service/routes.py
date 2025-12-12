"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            # paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based the data
    in the body that is posted.
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    location_url = url_for("get_account_by_id", account_id=account.id, _external=True)
    return make_response(
        jsonify(message),
        status.HTTP_201_CREATED,
        {"Location": location_url}
    )

######################################################################
# LIST ALL ACCOUNTS
######################################################################


@app.route("/accounts", methods=['GET'])
def list_all_accounts():
    """
    List all accounts.
    This endpoint will return a list of all accounts
    currently in the database.
    """

    app.logger.info("Request to get all Accounts")
    accounts_in_db = Account.all()

    account_list = [account.serialize() for account in accounts_in_db]

    return jsonify(account_list), status.HTTP_200_OK

######################################################################
# READ AN ACCOUNT
######################################################################


@app.route("/accounts/<int:account_id>", methods=['GET'])
def get_account_by_id(account_id):
    """
    This endpoint will return an account with given id number.
    """
    app.logger.debug("Retrieving an account with %s", account_id)

    account = Account.find(account_id)

    if account and account_id is not None:
        return account.serialize(), status.HTTP_200_OK

    return jsonify({"message": "No account found."}), status.HTTP_404_NOT_FOUND

######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################


@app.route("/accounts/<int:account_id>", methods=['PUT'])
def update_account(account_id):
    """
    This endpoint will update information in an existing account.
    """
    app.logger.debug("Request to update an account with account_id: %s", account_id)

    account = Account.find(account_id)

    if account and account_id is not None:

        data = request.get_json()
        account.deserialize(data)
        account.update()

        return jsonify(account.serialize()), status.HTTP_200_OK

    return jsonify({"error": "Account not found."}), status.HTTP_404_NOT_FOUND

######################################################################
# DELETE AN ACCOUNT
######################################################################


@app.route("/accounts/<int:account_id>", methods=['DELETE'])
def delete_an_account(account_id):
    """
    This endpoint will delete an account with the given account_id.
    """
    app.logger.debug("Request to remove an account with account_id: %s", account_id)

    account = Account.find(account_id)

    if account and account_id is not None:

        account.delete()

        return jsonify({}), status.HTTP_204_NO_CONTENT

    return jsonify({"error": "Account not found."}), status.HTTP_404_NOT_FOUND

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )
