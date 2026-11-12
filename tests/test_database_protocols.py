import unittest
from unittest.mock import patch, MagicMock

from mailcow_doctor.protocols import check_redis, check_mariadb


class TestDatabaseProtocols(unittest.TestCase):

    @patch("mailcow_doctor.protocols.socket.create_connection")
    def test_redis_ping(self, mock_connect):
        conn = MagicMock()
        conn.recv.return_value = b"+PONG\r\n"
        mock_connect.return_value.__enter__.return_value = conn

        result = check_redis()
        self.assertEqual(result.status, "PASS")
        conn.sendall.assert_called_once_with(
            b"*1\r\n$4\r\nPING\r\n"
        )

    @patch("mailcow_doctor.protocols.socket.create_connection")
    def test_redis_auth_required(self, mock_connect):
        conn = MagicMock()
        conn.recv.return_value = b"-NOAUTH Authentication required\r\n"
        mock_connect.return_value.__enter__.return_value = conn

        result = check_redis()
        self.assertEqual(result.status, "WARN")

    @patch("mailcow_doctor.protocols.socket.create_connection")
    def test_mariadb_handshake(self, mock_connect):
        conn = MagicMock()

        # MySQL packet: 3-byte payload length, sequence 0,
        # protocol version 10 followed by a server version string.
        payload = b"\x0aMariaDB-10.11"
        packet = (
            len(payload).to_bytes(3, "little")
            + b"\x00"
            + payload
        )

        conn.recv.side_effect = [
            packet[:4],
            packet[4:],
        ]
        mock_connect.return_value.__enter__.return_value = conn

        result = check_mariadb()
        self.assertEqual(result.status, "PASS")

    @patch("mailcow_doctor.protocols.socket.create_connection")
    def test_mariadb_connection_refused(self, mock_connect):
        mock_connect.side_effect = ConnectionRefusedError(
            "Connection refused"
        )

        result = check_mariadb()
        self.assertEqual(result.status, "FAIL")


if __name__ == "__main__":
    unittest.main()
