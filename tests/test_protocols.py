import unittest
from unittest.mock import patch, MagicMock

from mailcow_doctor.protocols import check_greeting


class TestProtocolChecks(unittest.TestCase):

    @patch("mailcow_doctor.protocols.socket.create_connection")
    def test_valid_smtp_greeting(self, mock_connect):
        connection = MagicMock()
        connection.recv.return_value = b"220 mail.example ESMTP\r\n"
        mock_connect.return_value.__enter__.return_value = connection

        result = check_greeting(
            "SMTP", "127.0.0.1", 25, b"220"
        )

        self.assertEqual(result.status, "PASS")

    @patch("mailcow_doctor.protocols.socket.create_connection")
    def test_invalid_greeting(self, mock_connect):
        connection = MagicMock()
        connection.recv.return_value = b"500 Service unavailable\r\n"
        mock_connect.return_value.__enter__.return_value = connection

        result = check_greeting(
            "SMTP", "127.0.0.1", 25, b"220"
        )

        self.assertEqual(result.status, "FAIL")

    @patch("mailcow_doctor.protocols.socket.create_connection")
    def test_empty_greeting(self, mock_connect):
        connection = MagicMock()
        connection.recv.return_value = b""
        mock_connect.return_value.__enter__.return_value = connection

        result = check_greeting(
            "IMAP", "127.0.0.1", 143, b"* OK"
        )

        self.assertEqual(result.status, "FAIL")

    @patch("mailcow_doctor.protocols.socket.create_connection")
    def test_connection_error(self, mock_connect):
        mock_connect.side_effect = ConnectionRefusedError(
            "Connection refused"
        )

        result = check_greeting(
            "SMTP", "127.0.0.1", 25, b"220"
        )

        self.assertEqual(result.status, "FAIL")


if __name__ == "__main__":
    unittest.main()
