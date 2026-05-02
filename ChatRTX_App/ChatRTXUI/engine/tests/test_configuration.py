import json
import os
import tempfile
import unittest
from unittest.mock import patch

from configuration import Configuration

class TestConfiguration(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory and a temporary config file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_config_path = os.path.join(self.temp_dir.name, "config.json")
        self.temp_other_config_path = os.path.join(self.temp_dir.name, "other_config.json")

        self.initial_config = {
            "app": {
                "name": "ChatRTX",
                "version": "1.0"
            },
            "models": {
                "llama2": {"path": "/path/to/llama2"},
                "mistral": {"path": "/path/to/mistral"}
            }
        }

        with open(self.temp_config_path, 'w') as f:
            json.dump(self.initial_config, f)

        self.other_config = {
            "test_key": "test_value"
        }
        with open(self.temp_other_config_path, 'w') as f:
            json.dump(self.other_config, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('configuration.Configuration.expand_programdata_path')
    def test_init_and_get_config(self, mock_expand):
        mock_expand.return_value = self.temp_config_path

        config_obj = Configuration()

        # Test getting root config
        self.assertEqual(config_obj.get_config(""), self.initial_config)
        self.assertEqual(config_obj.get_config(None), self.initial_config)

        # Test getting specific keys
        self.assertEqual(config_obj.get_config("app/name"), "ChatRTX")
        self.assertEqual(config_obj.get_config("models/llama2/path"), "/path/to/llama2")

        # Test getting missing key
        self.assertIsNone(config_obj.get_config("app/missing_key"))
        self.assertIsNone(config_obj.get_config("missing_root/key"))

    @patch('configuration.Configuration.expand_programdata_path')
    def test_get_config_from_file(self, mock_expand):
        mock_expand.return_value = self.temp_config_path
        config_obj = Configuration()

        # Test invalid file
        self.assertIsNone(config_obj.get_config_from_file("app", None))
        self.assertIsNone(config_obj.get_config_from_file("app", ""))

        # Test getting from another file
        self.assertEqual(config_obj.get_config_from_file("test_key", self.temp_other_config_path), "test_value")
        self.assertIsNone(config_obj.get_config_from_file("missing_key", self.temp_other_config_path))

        # Test invalid key
        self.assertIsNone(config_obj.get_config_from_file(None, self.temp_other_config_path))
        self.assertIsNone(config_obj.get_config_from_file("", self.temp_other_config_path))

    @patch('configuration.Configuration.expand_programdata_path')
    def test_merge_objects(self, mock_expand):
        mock_expand.return_value = self.temp_config_path
        config_obj = Configuration()

        obj1 = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3
            }
        }
        obj2 = {
            "b": {
                "c": 4,
                "e": 5
            },
            "f": 6
        }

        merged = config_obj._merge_objects(obj1, obj2)

        expected = {
            "a": 1,
            "b": {
                "c": 4,
                "d": 3,
                "e": 5
            },
            "f": 6
        }

        self.assertEqual(merged, expected)

        # Test non-dict inputs
        self.assertEqual(config_obj._merge_objects(obj1, "not_dict"), "not_dict")

    @patch('configuration.Configuration.expand_programdata_path')
    def test_write_default_config(self, mock_expand):
        mock_expand.return_value = self.temp_config_path
        config_obj = Configuration()

        # Write new nested value
        config_obj.write_default_config("app/settings/theme", "dark")

        # Check internal state was updated
        self.assertEqual(config_obj._default_config["app"]["settings"]["theme"], "dark")

        # Check file was updated
        with open(self.temp_config_path, 'r') as f:
            saved_config = json.load(f)
            self.assertEqual(saved_config["app"]["settings"]["theme"], "dark")

        # Write root value
        new_root_config = {"new": "root"}
        config_obj.write_default_config("", new_root_config)
        with open(self.temp_config_path, 'r') as f:
            saved_config = json.load(f)
            self.assertEqual(saved_config, new_root_config)

    @patch('configuration.Configuration.expand_programdata_path')
    def test_read_json_file_errors(self, mock_expand):
        mock_expand.return_value = self.temp_config_path
        config_obj = Configuration()

        # Test non-existent file
        result = config_obj._read_json_file("non_existent_file.json")
        self.assertEqual(result, {})

        # Test invalid JSON file
        invalid_json_path = os.path.join(self.temp_dir.name, "invalid.json")
        with open(invalid_json_path, 'w') as f:
            f.write("not valid json")

        result = config_obj._read_json_file(invalid_json_path)
        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()
