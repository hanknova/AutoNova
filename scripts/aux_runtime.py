import os
import json
import requests

SOURCE_URL = os.environ.get("SOURCE_JSON_URL", "")
TARGET_DIR = os.environ.get("TARGET_DIR", ".")
TARGET_FILE_NAME = os.environ.get("TARGET_FILE_NAME", "")
MAPPING_JSON_STR = os.environ.get("CHANNEL_MAPPING_JSON", "{}")

def main():
    if not SOURCE_URL or not TARGET_FILE_NAME:
        print("No hay cambios")
        return

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"}
        res = requests.get(SOURCE_URL, headers=headers, timeout=30)
        res.raise_for_status()
        source_data = res.json()
    except Exception:
        print("No hay cambios")
        return

    try:
        MAPPING = json.loads(MAPPING_JSON_STR)
    except Exception:
        print("No hay cambios")
        return

    source_items = []
    def extract_items(obj):
        if isinstance(obj, list):
            for entry in obj:
                extract_items(entry)
        elif isinstance(obj, dict):
            for key in ["items", "samples", "stations", "channels", "categories", "groups"]:
                if key in obj and isinstance(obj[key], list):
                    extract_items(obj[key])
            if "name" in obj and ("url" in obj or "stream_url" in obj):
                source_items.append(obj)

    extract_items(source_data)

    new_urls = {}
    for item in source_items:
        name = item.get("name", "").strip()
        url = item.get("url", "") or item.get("stream_url", "")
        if name in MAPPING and url:
            new_urls[MAPPING[name]] = url

    if not new_urls:
        print("No hay cambios")
        return

    target_path = None
    if os.path.exists(TARGET_DIR):
        for root, dirs, files in os.walk(TARGET_DIR):
            if TARGET_FILE_NAME in files:
                target_path = os.path.join(root, TARGET_FILE_NAME)
                break
    if not target_path:
        for root, dirs, files in os.walk('.'):
            if TARGET_FILE_NAME in files:
                target_path = os.path.join(root, TARGET_FILE_NAME)
                break

    if not target_path or not os.path.exists(target_path):
        print("No hay cambios")
        return

    with open(target_path, "r", encoding="utf-8") as f:
        target_data = json.load(f)

    changes_made = False

    def update_channels(node):
        nonlocal changes_made
        if isinstance(node, list):
            for sub in node:
                update_channels(sub)
        elif isinstance(node, dict):
            name = node.get("name")
            if name in new_urls:
                expected_url = new_urls[name]
                if node.get("url") != expected_url:
                    node["url"] = expected_url
                    changes_made = True
            for k, v in node.items():
                if k != "name":
                    update_channels(v)

    update_channels(target_data)

    if changes_made:
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(target_data, f, indent=2, ensure_ascii=False)
        print("Actualizado con exito")
    else:
        print("No hay cambios")

if __name__ == "__main__":
    main()
