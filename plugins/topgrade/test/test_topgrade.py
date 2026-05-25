import os
import sys
import json
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import plugin
import tomlkit

class TestTopgradePlugin(unittest.TestCase):
    @patch('shutil.which')
    def test_check_installed_true(self, mock_which):
        mock_which.return_value = '/path/to/topgrade.exe'
        res = plugin.check_installed({}, "req-1")
        self.assertTrue(res["success"])
        self.assertTrue(res["data"]["installed"])

    def test_merge_settings(self):
        doc = tomlkit.document()
        doc["disable"] = ["pip"]
        doc["set_title"] = False

        source = {
            "disable": ["npm", "pip"],
            "set_title": True,
            "git_repos": {
                "~/Projects/dotfiles": "main"
            }
        }
        changed = plugin.merge_settings(doc, source)
        self.assertTrue(changed)
        self.assertEqual(list(doc["disable"]), ["npm", "pip"])
        self.assertEqual(doc["set_title"], True)
        self.assertEqual(doc["git_repos"]["~/Projects/dotfiles"], "main")

if __name__ == '__main__':
    unittest.main()
