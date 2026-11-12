import unittest

from mailcow_doctor.checks import (
    parse_compose_ps,
    evaluate_services,
)


class TestMalformedComposeOutput(unittest.TestCase):

    def test_json_number_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_compose_ps("42")

    def test_json_string_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_compose_ps('"unexpected"')

    def test_array_with_non_object_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_compose_ps('[{"Service":"redis-mailcow"}, 42]')


if __name__ == "__main__":
    unittest.main()
