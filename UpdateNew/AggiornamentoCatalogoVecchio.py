import requests
import base64
import json
import os

# ===== CONFIG =====
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "MrNico98/PhoenixPlay-Resources"
BRANCH = "main"

FILE_NEW = "Navigatore/Catalogo.json"
FILE_OLD = "Navigatore/CatalogoOld.json"

BASE_URL = "https://api.github.com/repos"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ===== FUNZIONI =====

def get_file_content(path):
    url = f"{BASE_URL}/{REPO}/contents/{path}?ref={BRANCH}"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()

    content = base64.b64decode(data["content"]).decode("utf-8")
    return json.loads(content), data["sha"]

def update_file(path, new_content, sha):
    url = f"{BASE_URL}/{REPO}/contents/{path}"

    encoded_content = base64.b64encode(
        json.dumps(new_content, indent=2).encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": "Auto update CatalogoOld.json (aggiunti mancanti)",
        "content": encoded_content,
        "sha": sha,
        "branch": BRANCH
    }

    r = requests.put(url, headers=headers, json=payload)
    r.raise_for_status()
    print("✅ File aggiornato su GitHub!")

# ===== LOGICA =====

def main():
    print("📥 Scarico file...")

    new_data, _ = get_file_content(FILE_NEW)
    old_data, old_sha = get_file_content(FILE_OLD)

    new_downloads = new_data.get("downloads", [])
    old_downloads = old_data.get("downloads", [])

    print(f"Nuovi: {len(new_downloads)}")
    print(f"Vecchi: {len(old_downloads)}")

    # Crea set titoli esistenti
    old_titles = {d["title"] for d in old_downloads}

    # Trova mancanti
    missing = [d for d in new_downloads if d["title"] not in old_titles]

    print(f"🆕 Mancanti trovati: {len(missing)}")

    if not missing:
        print("✔ Nessun aggiornamento necessario.")
        return

    # Aggiungi mancanti
    old_downloads.extend(missing)

    # Aggiorna JSON finale
    updated_data = {
        "downloads": old_downloads
    }

    print("🚀 Aggiorno GitHub...")
    update_file(FILE_OLD, updated_data, old_sha)


if __name__ == "__main__":
    main()
