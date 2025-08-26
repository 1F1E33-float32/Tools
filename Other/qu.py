import os
import json
import time
import requests


def query_vndb(name):
    payload = {
        "filters": ["search", "=", name],
        "fields": "id,title,alttitle",
        "sort": "title",
        "reverse": True,
        "page": 1,
        "results": 50
    }
    url = "https://api.vndb.org/kana/vn"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload)
    # Retry indefinitely on network errors
    while True:
        try:
            response = requests.post(url, headers=headers, data=data, timeout=15)
            response.raise_for_status()
            return response.json().get("results", [])
        except requests.exceptions.RequestException as e:
            print(f"Network error querying VNDB for '{name}': {e}. Retrying...")
            time.sleep(2)


def prompt_user_choice(results, folder_name):
    print(f"Multiple VNDB entries found for '{folder_name}':")
    for idx, res in enumerate(results):
        title = res.get("title", "")
        alt = res.get("alttitle", "")
        vn_id = res.get("id", "")
        print(f"[{idx}] ID: {vn_id}, Title: '{title}', Alt: '{alt}'")

    while True:
        choice = input(f"Enter the index of the correct entry (0-{len(results)-1}), or 's' to skip: ")
        if choice.lower() == 's':
            return None
        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(results):
                return results[idx]
        print("Invalid selection, please try again.")


def generate_metadata_for_folder(folder_path):
    folder_name = os.path.basename(folder_path)
    parts = folder_name.split('_', 1)
    if len(parts) == 2:
        developer_name, search_name = parts
    else:
        developer_name = ''
        search_name = folder_name

    results = query_vndb(search_name)
    if not results:
        print(f"No results found for '{search_name}'. Skipping '{folder_name}'.")
        return

    if len(results) > 1:
        selected = prompt_user_choice(results, folder_name)
        if selected is None:
            print(f"Skipped '{folder_name}'.")
            return
        result = selected
    else:
        result = results[0]

    vn_id = result.get("id", "")
    title = result.get("title") or ""
    alttitle = result.get("alttitle") or ""

    if not alttitle:
        game_name = title
        game_name_romaji = None
    else:
        game_name = alttitle
        game_name_romaji = title or None

    metadata = {
        "game_name": game_name,
        "game_name_romaji": game_name_romaji,
        "game_developer": developer_name,
        "game_category": "galgame",
        "game_link": f"https://vndb.org/{vn_id}"
    }

    metadata_path = os.path.join(folder_path, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
    print(f"Saved metadata for '{folder_name}' to {metadata_path}")


def main(root_path):
    for entry in os.scandir(root_path):
        if entry.is_dir():
            generate_metadata_for_folder(entry.path)


if __name__ == "__main__":
    # Update this to your root folder path
    root_path = r"D:\Dataset_VN_NoScene\#OK_20250821"
    main(root_path)