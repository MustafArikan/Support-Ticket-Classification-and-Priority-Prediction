from pathlib import Path
from unittest.mock import patch

import requests
from streamlit.testing.v1 import AppTest


def test_streamlit_demo_initializes_without_model_server():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
    with patch("requests.get", side_effect=requests.ConnectionError("offline")):
        app.run(timeout=10)
    assert len(app.exception) == 0
