import json
import os
import subprocess
import sys
import tempfile

PLUGIN = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "plugin.py"))

def run_plugin(payload: dict, env=None) -> dict:
    if env is None:
        env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, PLUGIN],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        print(f"Error output: {result.stderr}")
    try:
        return json.loads(result.stdout.strip())
    except Exception as e:
        print(f"Failed to parse stdout: {result.stdout}")
        raise e

def test_check_installed():
    res = run_plugin(
        {
            "requestId": "1",
            "command": "check_installed",
            "args": {},
            "context": {},
        }
    )
    assert res["requestId"] == "1"
    assert res["success"] is True
    assert "installed" in res["data"]

def test_apply_config_dry_run():
    with tempfile.TemporaryDirectory() as temp_dir:
        env = os.environ.copy()
        env["APPDATA"] = temp_dir
        
        # Test dry-run
        res = run_plugin(
            {
                "requestId": "2",
                "command": "apply",
                "args": {
                    "settings": {
                        "set_title": True,
                        "disable": ["pip", "npm"]
                    }
                },
                "context": {
                    "dryRun": True
                },
            },
            env=env
        )
        assert res["requestId"] == "2"
        assert res["success"] is True
        assert res["changed"] is True
        
        # Ensure file was not created
        config_path = os.path.join(temp_dir, "topgrade.toml")
        assert not os.path.exists(config_path)

def test_apply_config_real():
    with tempfile.TemporaryDirectory() as temp_dir:
        env = os.environ.copy()
        env["APPDATA"] = temp_dir
        
        res = run_plugin(
            {
                "requestId": "3",
                "command": "apply",
                "args": {
                    "settings": {
                        "set_title": True,
                        "disable": ["pip", "npm"],
                        "git_repos": {
                            "~/Projects/dotfiles": "main"
                        }
                    }
                },
                "context": {},
            },
            env=env
        )
        assert res["requestId"] == "3"
        assert res["success"] is True
        assert res["changed"] is True
        
        config_path = os.path.join(temp_dir, "topgrade.toml")
        assert os.path.exists(config_path)
        
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "set_title = true" in content
            assert "disable = [\"pip\", \"npm\"]" in content
            assert "[git_repos]" in content
            assert "\"~/Projects/dotfiles\" = \"main\"" in content

        # Test idempotency
        res_idem = run_plugin(
            {
                "requestId": "4",
                "command": "apply",
                "args": {
                    "settings": {
                        "set_title": True,
                        "disable": ["pip", "npm"],
                        "git_repos": {
                            "~/Projects/dotfiles": "main"
                        }
                    }
                },
                "context": {},
            },
            env=env
        )
        assert res_idem["requestId"] == "4"
        assert res_idem["success"] is True
        assert res_idem["changed"] is False

def test_apply_config_merge():
    with tempfile.TemporaryDirectory() as temp_dir:
        env = os.environ.copy()
        env["APPDATA"] = temp_dir
        
        config_path = os.path.join(temp_dir, "topgrade.toml")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("existing_key = \"value\"\n[git_repos]\n\"existing/repo\" = \"master\"\n")
            
        res = run_plugin(
            {
                "requestId": "5",
                "command": "apply",
                "args": {
                    "settings": {
                        "set_title": True,
                        "git_repos": {
                            "new/repo": "main"
                        }
                    }
                },
                "context": {},
            },
            env=env
        )
        
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "existing_key = \"value\"" in content
            assert "set_title = true" in content
            assert "[git_repos]" in content
            assert "\"existing/repo\" = \"master\"" in content
            assert "\"new/repo\" = \"main\"" in content

