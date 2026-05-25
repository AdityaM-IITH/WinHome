import os
import sys
import json
import unittest
from unittest.mock import patch, mock_open

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import plugin

class TestJoplinPlugin(unittest.TestCase):
    @patch('shutil.which')
    def test_check_installed_true(self, mock_which):
        mock_which.return_value = '/path/to/joplin-desktop.exe'
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
        target = {"editor.codeView": False, "theme": 2}
        source = {"editor.codeView": True, "locale": "en-GB"}
        changed = plugin.merge_settings(target, source)
        self.assertTrue(changed)
        self.assertEqual(target["editor.codeView"], True)
        self.assertEqual(target["locale"], "en-GB")
        self.assertEqual(target["theme"], 2)

if __name__ == '__main__':
    unittest.main()
