import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from pythonanywhere_manager import PythonAnywhereClient, Settings


class FakeResponse:
    status_code = 200
    content = b"{}"
    text = "{}"
    ok = True

    def json(self):
        return {"source_directory": "/home/Kbnb/ember-signal-backend-staging"}


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.session.headers = {}
        self.session.request.return_value = FakeResponse()
        self.settings = Settings("Kbnb", "kbnb.pythonanywhere.com", "test-token")
        self.client = PythonAnywhereClient(self.settings, self.session)

    def test_auth_header_is_token_scheme(self):
        self.assertEqual(self.session.headers["Authorization"], "Token test-token")

    def test_reload_uses_expected_endpoint(self):
        self.client.reload()
        call = self.session.request.call_args
        self.assertEqual(call.args[:2], ("POST", "https://www.pythonanywhere.com/api/v0/user/Kbnb/webapps/kbnb.pythonanywhere.com/reload/"))

    def test_dry_run_does_not_upload_runtime_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("print('ok')")
            (root / "ember_signal.db").write_text("runtime")
            uploaded = self.client.deploy_directory(root, "/home/Kbnb/app", dry_run=True)
        self.assertEqual(uploaded, ["/home/Kbnb/app/app.py"])
        self.assertEqual(self.session.request.call_count, 0)


if __name__ == "__main__":
    unittest.main()
