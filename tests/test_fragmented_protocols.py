import unittest
from unittest.mock import patch

from mailcow_doctor.protocols import check_smtp, check_redis


class FragmentedSocket:
    """Simulate a TCP response arriving in multiple chunks."""

    def __init__(self, chunks):
        self.chunks = list(chunks)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def settimeout(self, timeout):
        pass

    def recv(self, size):
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

    def sendall(self, data):
        pass


class TestFragmentedResponses(unittest.TestCase):

    def test_smtp_greeting_arrives_in_multiple_chunks(self):
        fake = FragmentedSocket([
            b"2",
            b"20 mail.example.test ESMTP",
            b"\r\n",
        ])

        with patch(
            "mailcow_doctor.protocols.socket.create_connection",
            return_value=fake,
        ):
            result = check_smtp()

        self.assertEqual(result.status, "PASS")

    def test_redis_response_arrives_in_multiple_chunks(self):
        fake = FragmentedSocket([
            b"+P",
            b"ON",
            b"G\r\n",
        ])

        with patch(
            "mailcow_doctor.protocols.socket.create_connection",
            return_value=fake,
        ):
            result = check_redis()

        self.assertEqual(result.status, "PASS")


if __name__ == "__main__":
    unittest.main()
