import os
import sys
import json
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import plugin

class TestLazydockerPlugin(unittest.TestCase):
    @patch('shutil.which')
    def test_check_installed_true(self, mock_which):
        mock_which.return_value = '/path/to/lazydocker.exe'
        res = plugin.check_installed({}, "req-1")
        self.assertTrue(res["success"])
        self.assertTrue(res["data"]["installed"])

    @patch('shutil.which')
    def test_check_installed_false(self, mock_which):
        mock_which.return_value = None
        res = plugin.check_installed({}, "req-1")
        self.assertTrue(res["success"])
        self.assertFalse(res["data"]["installed"])

    def test_merge_settings(self):
        target = {
            "gui": {
                "theme": { "activeBorderColor": ["red"] }
            }
        }
        source = {
            "gui": {
                "theme": { "activeBorderColor": ["green"] },
                "language": "en"
            }
        }
        changed = plugin.merge_settings(target, source)
        self.assertTrue(changed)
        self.assertEqual(target["gui"]["theme"]["activeBorderColor"], ["green"])
        self.assertEqual(target["gui"]["language"], "en")

if __name__ == '__main__':
    unittest.main()
