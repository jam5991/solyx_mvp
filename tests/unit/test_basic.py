def test_basic():
    """Basic test to verify test setup is working"""
    assert True


def test_python_version():
    """Test to verify we're running the correct Python version"""
    import sys

    assert sys.version_info >= (3, 10)
