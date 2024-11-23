import datetime

from starlette.testclient import TestClient
from bs4 import BeautifulSoup
import pytest
import re
from main import app, state

@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_state():
    """Clear the global state before each test"""
    state.global_numbers.clear()
    state.websockets.clear()
    yield


def test_homepage_initial_state(client):
    """Test initial page load and structure"""
    response = client.get("/")
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, 'html.parser')

    # Check for main UI elements
    assert soup.find('h2', text='Local Generated Numbers')
    assert soup.find('h2', text='Global Numbers (All Instances)')

    # Check for empty lists initially
    local_list = soup.find('ul', id='local-numbers-list')
    assert len(local_list.find_all('li')) == 0

    global_list = soup.find('ul', id='global-numbers-list')
    assert len(global_list.find_all('li')) == 0


def test_add_manual_number(client):
    """Test adding a number manually"""

    # Record timestamp before making request
    timestamp_before = datetime.datetime.now()

    # Test data
    number = 42

    # Make request
    response = client.post("/add-number", data={"number": number})

    # Basic response checks
    assert response.status_code == 200

    # Parse response
    soup = BeautifulSoup(response.text, 'html.parser')
    li = soup.find('li')

    # Check list item structure
    assert li['class'] == ['number-item']
    assert str(number) in li.get_text()

    # Get timestamp from response
    timestamp_str = li.find('div', class_='timestamp').get_text()

    # Parse timestamp string to datetime object
    timestamp_client = datetime.datetime.strptime(timestamp_str, "%H:%M:%S").replace(
        year=timestamp_before.year,
        month=timestamp_before.month,
        day=timestamp_before.day
    )

    # Calculate time difference
    time_diff = abs((timestamp_client - timestamp_before).total_seconds())

    # Assert time difference is within acceptable range (5 seconds)
    assert time_diff < 5, f"Time difference too large: {time_diff} seconds"


def test_add_random_number(client):
    """Test adding a random number"""
    response = client.post("/add-random-number")
    assert response.status_code == 200

    # Check response structure
    soup = BeautifulSoup(response.text, 'html.parser')
    li = soup.find('li')
    assert li['class'] == ['number-item']

    # Extract number from text and verify it's a float
    number_text = li.find('div').get_text()
    number = float(re.search(r'Number: (-?\d+\.?\d*)', number_text).group(1))
    assert -10000 <= number <= 10000


def test_invalid_number_input(client):
    """Test invalid number inputs"""
    # Test with no number
    response = client.post("/add-number")
    soup = BeautifulSoup(response.text, 'html.parser')
    assert "Invalid input" in soup.get_text()

    # Test with non-numeric value
    # response = client.post("/add-number", data={"number": "not_a_number"})
    # soup2 = BeautifulSoup(response.text, 'html.parser')
    # assert "Invalid input" in soup2.get_text()


def test_global_list_updates(client):
    """Test that global list updates with new numbers"""
    # Add a number
    number = 42
    response = client.post("/add-number", data={"number": number})
    assert response.status_code == 200

    # Get homepage and check global list
    response = client.get("/")
    soup = BeautifulSoup(response.text, 'html.parser')
    global_list = soup.find('ul', id='global-numbers-list')
    assert str(number) in global_list.get_text()


def test_local_list_empty_on_reload(client):
    """Test that local list is empty on page reload"""
    # Add a number first
    response = client.post("/add-number", data={"number": 42})
    assert response.status_code == 200

    # Get homepage and verify local list is empty
    response = client.get("/")
    soup = BeautifulSoup(response.text, 'html.parser')
    local_list = soup.find('ul', id='local-numbers-list')
    assert len(local_list.find_all('li')) == 0


def test_number_formatting(client):
    """Test number formatting in the lists"""
    number = 42.123456
    response = client.post("/add-number", data={"number": number})
    soup = BeautifulSoup(response.text, 'html.parser')

    # Check number format
    number_text = soup.find('div').get_text()
    assert f"Number: {number}" in number_text

    # Check timestamp format
    timestamp = soup.find('div', class_='timestamp').get_text()
    assert re.match(r'\d{2}:\d{2}:\d{2}', timestamp)


def test_global_list_max_size(client):
    """Test that global list doesn't exceed max size"""
    # Add more than maxlen numbers
    for i in range(110):  # Add 110 numbers (max is 100)
        response = client.post("/add-number", data={"number": i})
        assert response.status_code == 200

    # Check global list size
    assert len(state.global_numbers) == 100


def test_multiple_random_numbers(client):
    """Test adding multiple random numbers"""
    numbers = []
    # Add several random numbers
    for _ in range(5):
        response = client.post("/add-random-number")
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, 'html.parser')
        number_text = soup.find('div').get_text()
        number = float(re.search(r'Number: (-?\d+\.?\d*)', number_text).group(1))
        numbers.append(number)

    # Verify all numbers are within range
    for num in numbers:
        assert -10000 <= num <= 10000

    # Verify numbers are different (very unlikely to get duplicates)
    assert len(set(numbers)) == len(numbers)