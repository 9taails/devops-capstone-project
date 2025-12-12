"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"

HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}

######################################################################
#  T E S T   C A S E S
######################################################################


class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        talisman.force_https = False
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                f"Created test Account for {account.name}",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # Test case for listing all accounts

    def test_list_all_accounts(self):
        """It should return an object of type list"""

        self._create_accounts(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(len(data), 5)

    # Test case for getting an account by ID

    def test_get_account_by_id(self):
        """It should return an account with
        a given ID number.
        """

        test_list = self._create_accounts(1)
        test_account = test_list[0]

        resp = self.client.get(f"{BASE_URL}/{test_account.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        account = resp.get_json()
        self.assertEqual(account['name'], test_account.name)

    # Test case for updating account info

    def test_update_account(self):
        """It should update a value in the account details."""

        test_list = self._create_accounts(3)
        test_account = test_list[0]

        resp = self.client.get(f"{BASE_URL}/{test_account.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        account_data = resp.get_json()
        account_data['name'] = 'French Fries'
        account_id = account_data['id']

        response = self.client.put(f"{BASE_URL}/{account_id}", json=account_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        check = self.client.get(f"{BASE_URL}/{account_id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        check_data = check.get_json()
        check_name = check_data['name']
        self.assertEqual(check_name, 'French Fries')

    # Test case for updating account info with missing account

    def test_update_missing_account(self):
        """It should return 404_NOT_FOUND."""

        resp = self.client.put(f"{BASE_URL}/5")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # Test case for deleting an account

    def test_delete_an_account(self):
        """It should remove an account from the database."""

        test_list = self._create_accounts(1)
        test_account = test_list[0]

        resp = self.client.get(f"{BASE_URL}/{test_account.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        response = self.client.delete(f"{BASE_URL}/{test_account.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        resp = self.client.get(f"{BASE_URL}/{test_account.id}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        accounts = self.client.get(BASE_URL)
        accounts_data = accounts.get_json()
        self.assertEqual(len(accounts_data), 0)

    # Test case for deleting account info with missing account

    def test_delete_missing_account(self):
        """It should return 404_NOT_FOUND."""

        resp = self.client.delete(f"{BASE_URL}/5")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # Test case for trying to use POST method on an existing

    def test_post_to_existing_account(self):
        """It should return 405_METHOD_NOT_ALLOWED."""

        test_list = self._create_accounts(1)
        test_account = test_list[0]

        resp = self.client.post(f"{BASE_URL}/{test_account.id}")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Test case for security headers

    def test_security_headers(self):
        """It should return the following header values:
        'X-Frame-Options': 'SAMEORIGIN'
        'X-Content-Type-Options': 'nosniff'
        'Content-Security-Policy': 'default-src \'self\'; object-src \'none\''
        'Referrer-Policy': 'strict-origin-when-cross-origin'
        """

        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        headers = {
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src \'self\'; object-src \'none\'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)

    # Test case for adding CORS policies

    def test_add_cors_policies(self):
        """It should return the header
            'Access-Control-Allow-Origin': '*'
        """

        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        headers = {
            "Access-Control-Allow-Origin": "*",
        }

        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)
