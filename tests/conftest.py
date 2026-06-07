import pytest

@pytest.fixture
def mock_hardware():
    return {"threads": 16, "refresh_rate": 144, "os": "Windows 10", "ram": "16GB", "gpu": "NVIDIA RTX 3060"}

@pytest.fixture
def sample_vdf_content():
    return '"730" { "LaunchOptions" "-novid" }'