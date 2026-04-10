import requests
import json
import base64
import os
from datetime import datetime
import re

# CONFIG
Tokengithub = os.getenv("GITHUB_TOKEN")

SOURCE_URL = "https://raw.githubusercontent.com/MrNico98/PhoenixPlay/refs/heads/main/IDapp/steamrip.json"

REPO_OWNER = "MrNico98"
REPO_NAME = "PhoenixPlay-Resources"
FILE_PATH = "Navigatore/Catalogo.json"
BRANCH = "main"


def get_source_data():
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    return response.json()


def clean_title(title):
    """
    Rimuove la parte tra parentesi (versione)
    es: "Abiotic Factor Free Download (v1.2.0)" -> "Abiotic Factor Free Download"
    """
    return re.sub(r"\s*\(.*?\)", "", title).strip()


def filter_and_keep_latest(data):
    latest_games = {}

    for item in data.get("downloads", []):
        # Filtra buzzheavier
        buzz_links = [u for u in item.get("uris", []) if "buzzheavier" in u.lower()]
        if not buzz_links:
            continue

        base_title = clean_title(item.get("title", ""))

        # Parse data
        upload_date = datetime.fromisoformat(item.get("uploadDate").replace("Z", "+00:00"))

        # Se non esiste o è più recente → sostituisci
        if (base_title not in latest_games or 
            upload_date > latest_games[base_title]["date"]):

            latest_games[base_title] = {
                "date": upload_date,
                "data": {
                    "title": item.get("title"),
                    "uploadDate": item.get("uploadDate"),
                    "fileSize": item.get("fileSize"),
                    "uris": buzz_links
                }
            }

    # Estrai solo i dati finali
    result = [v["data"] for v in latest_games.values()]

    # Ordina per data (più recenti prima)
    result.sort(key=lambda x: x["uploadDate"], reverse=True)

    return {"downloads": result}


def get_file_sha():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {Tokengithub}"}

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()["sha"]


def update_github_file(content_json):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"

    headers = {
        "Authorization": f"token {Tokengithub}",
        "Content-Type": "application/json"
    }

    sha = get_file_sha()

    content_str = json.dumps(content_json, indent=2, ensure_ascii=False)
    content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

    data = {
        "message": "Aggiornamento automatico Catalogo.json (latest only)",
        "content": content_b64,
        "sha": sha,
        "branch": BRANCH
    }

    r = requests.put(url, headers=headers, data=json.dumps(data))
    r.raise_for_status()

    print("✅ File aggiornato su GitHub (solo versioni più recenti)!")


def main():
    source_data = get_source_data()
    filtered_data = filter_and_keep_latest(source_data)
    update_github_file(filtered_data)


if __name__ == "__main__":
    main()
