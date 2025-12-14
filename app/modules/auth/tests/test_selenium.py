import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from app import create_app, db
from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def create_test_user():
    """Create test user in the database if it doesn't exist."""
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email="user1@example.com").first()
        if user is None:
            user = User(email="user1@example.com", password="1234")
            db.session.add(user)
            db.session.commit()

            # Create profile for the user
            profile = UserProfile(user_id=user.id, orcid="", affiliation="Test University", name="John", surname="Doe")
            db.session.add(profile)
            db.session.commit()
            print("✓ Test user created")


def test_login_and_check_element():

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f"{host}/login")

        # Wait a little while to make sure the page has loaded completely
        time.sleep(4)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        # Send the form
        password_field.send_keys(Keys.RETURN)

        # Wait a little while to ensure that the action has been completed
        time.sleep(4)

        try:

            driver.find_element(By.XPATH, "//h1[contains(@class, 'h2 mb-3') and contains(., 'Latest datasets')]")
            print("Test passed!")

        except NoSuchElementException:
            raise AssertionError("Test failed!")

    finally:

        # Close the browser
        close_driver(driver)


# Setup test data and call the test function
create_test_user()
test_login_and_check_element()
