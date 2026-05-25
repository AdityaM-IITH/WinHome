# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "tomlkit",
# ]
# ///
import sys
import json
import os
import shutil
import tomlkit

def log(msg):
    sys.stderr.write(f"[topgrade-plugin] {msg}\n")
    sys.stderr.flush()

def get_config_path():
    appdata = os.getenv("APPDATA")
    if not appdata:
        raise Exception("APPDATA environment variable not found")

    fallback_path = os.path.join(appdata, "topgrade", "topgrade.toml")
    primary_path = os.path.join(appdata, "topgrade.toml")

    if os.path.exists(fallback_path) and not os.path.exists(primary_path):
        return fallback_path
    return primary_path

def read_toml(file_path: str):
    if not os.path.exists(file_path):
        return tomlkit.document()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return tomlkit.load(f)
    except Exception as e:
        log(f"Warning: could not parse {file_path}: {e}")
        return tomlkit.document()

def write_toml(file_path: str, doc) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        tomlkit.dump(doc, f)

def merge_settings(target, source: dict) -> bool:
    changed = False
    for key, value in source.items():
        if isinstance(value, dict):
            if key not in target:
                target[key] = tomlkit.table()
                changed = True
            if isinstance(target.get(key), (dict, tomlkit.items.Table)):
                if merge_settings(target[key], value):
                    changed = True
        else:
            # Handle arrays since tomlkit Arrays are slightly different
            if isinstance(value, list):
                if key not in target or list(target[key]) != value:
                    a = tomlkit.array()
                    for item in value:
                        a.append(item)
                    target[key] = a
                    changed = True
            else:
                if key not in target or target[key] != value:
                    target[key] = value
                    changed = True
    return changed

def check_installed(args: dict, request_id: str) -> dict:
    installed = shutil.which("topgrade.exe") is not None or shutil.which("topgrade") is not None
    return {
        "requestId": request_id,
        "success": True,
        "changed": False,
        "data": { "installed": installed },
    }

def apply_config(args: dict, context: dict, request_id: str) -> dict:
    dry_run = context.get("dryRun", False)
    settings = args.get("settings", {})

    try:
        config_path = get_config_path()
        current_config = read_toml(config_path)
        
        changed = merge_settings(current_config, settings)

        if not changed:
            return {
                "requestId": request_id,
                "success": True,
                "changed": False,
            }

        if dry_run:
            log(f"Would update {config_path} with: {json.dumps(settings)}")
            return {
                "requestId": request_id,
                "success": True,
                "changed": False,
            }

        write_toml(config_path, current_config)
        log(f"Updated topgrade config: {config_path}")

        return {
            "requestId": request_id,
            "success": True,
            "changed": True,
        }

    except Exception as e:
        log(f"Failed to apply config: {e}")
        return {
            "requestId": request_id,
            "success": False,
            "changed": False,
            "error": str(e),
        }

def main():
    input_data = sys.stdin.read()
    if not input_data:
        return

    try:
        request = json.loads(input_data)
    except Exception as e:
        log(f"Failed to parse request: {e}")
        sys.exit(1)

    request_id = request.get("requestId", "unknown")
    command = request.get("command")
    args = request.get("args", {})
    context = request.get("context", {})

    response = {
        "requestId": request_id,
        "success": False,
        "changed": False,
    }

    try:
        if command == "check_installed":
            response = check_installed(args, request_id)
        elif command == "apply":
            response = apply_config(args, context, request_id)
        else:
            response["error"] = f"Unknown command: {command}"
    except Exception as fatal_err:
        response["error"] = f"Internal Script Error: {str(fatal_err)}"

    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
