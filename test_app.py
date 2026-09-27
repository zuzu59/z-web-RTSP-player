import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

import app


class CameraUrlTests(unittest.TestCase):
    def test_accepts_requested_camera_url_format(self):
        url = "rtsp://admin:example-password@192.168.1.50:554/user=admin_password=example-password_channel=1_stream=0.sdp"
        self.assertIsNone(app.validate_rtsp_url(url))

    def test_rejects_non_rtsp_url(self):
        self.assertIn("rtsp://", app.validate_rtsp_url("http://camera.local/live"))

    def test_rejects_missing_host_and_bad_port(self):
        self.assertIsNotNone(app.validate_rtsp_url("rtsp:///live"))
        self.assertIsNotNone(app.validate_rtsp_url("rtsp://camera.local:99999/live"))


class HttpAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_home_page_and_status(self):
        with urlopen(self.base_url + "/") as response:
            self.assertEqual(response.status, 200)
            self.assertIn("Caméra en direct", response.read().decode())
        with urlopen(self.base_url + "/status?fresh=1") as response:
            self.assertEqual(json.load(response), {"configured": False})

    def test_connect_rejects_invalid_url(self):
        request = Request(self.base_url + "/connect", data=json.dumps({"url": "not a URL"}).encode(), headers={"Content-Type": "application/json"})
        with self.assertRaises(Exception) as caught:
            urlopen(request)
        self.assertEqual(caught.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
