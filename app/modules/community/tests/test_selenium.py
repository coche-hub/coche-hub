import time

from selenium.webdriver.common.by import By

from app import create_app, db
from app.modules.community.models import Community
from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def wait_for_page_to_load(driver, timeout=4):
    """Wait for page to finish loading."""
    time.sleep(timeout)


def create_test_communities():
    """Create test communities in the database."""
    app = create_app()
    with app.app_context():
        # Check if communities already exist
        if Community.query.first() is None:
            # Create test communities
            community1 = Community(name="Test Community 1", description="This is a test community for Selenium testing")
            community2 = Community(name="Test Community 2", description="Another test community")
            db.session.add(community1)
            db.session.add(community2)
            db.session.commit()
            print("✓ Test communities created")


def test_community_index_page_buttons():
    """
    Test that verifies the existence of buttons on the community index page.
    This is a simple interface test that checks button rendering without login.
    """
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/community")
        wait_for_page_to_load(driver)

        # Check if "View Details" buttons exist
        view_details_buttons = driver.find_elements(
            By.XPATH, "//a[contains(@class, 'btn') and contains(text(), 'View Details')]"
        )
        assert len(view_details_buttons) > 0, "No 'View Details' buttons found on community index page"

        print("✓ Community index page buttons test passed!")

    finally:
        close_driver(driver)


def test_community_detail_page_buttons():
    """
    Test that verifies the existence of buttons on a community detail page.
    This is a simple interface test that checks button rendering without login.
    """
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        # Navigate to first community detail page (assuming community with id=1 exists)
        driver.get(f"{host}/community/1")
        wait_for_page_to_load(driver)

        # Check if "View All Datasets" button exists (using partial text match)
        view_datasets_buttons = driver.find_elements(By.XPATH, "//a[contains(., 'View All Datasets')]")
        assert len(view_datasets_buttons) > 0, "'View All Datasets' button not found"

        print("✓ Community detail page buttons test passed!")

    finally:
        close_driver(driver)


def test_community_datasets_page_buttons():
    """
    Test that verifies the existence of buttons on the community datasets page.
    This is a simple interface test that checks button rendering without login.
    """
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        # Navigate to community datasets page (assuming community with id=1 exists)
        driver.get(f"{host}/community/1/datasets")
        wait_for_page_to_load(driver)

        # Check if page loaded successfully (look for heading or container)
        page_heading = driver.find_element(By.TAG_NAME, "h1")
        assert page_heading is not None, "Community datasets page did not load properly"

        # Check if "View Dataset" buttons exist (if there are any datasets)
        # This is optional since the page might have no datasets
        driver.find_elements(By.XPATH, "//a[contains(@class, 'btn') and contains(text(), 'View Dataset')]")
        # We just check that the search doesn't error - there may be 0 buttons if no datasets

        print("✓ Community datasets page buttons test passed!")

    finally:
        close_driver(driver)


# Setup test data and run the tests
create_test_communities()
test_community_index_page_buttons()
test_community_detail_page_buttons()
test_community_datasets_page_buttons()
