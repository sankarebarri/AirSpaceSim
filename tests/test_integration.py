import os
import sys

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from airspacesim.hello import say_hello


def test_say_hello_returns_expected_greeting():
    expected = "Hello, world from AirSpaceSim!"
    assert say_hello() == expected
