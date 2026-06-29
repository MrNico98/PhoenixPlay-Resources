import os
import requests
import json
import re
import base64
from bs4 import BeautifulSoup

def get_github_token():
    """Recupera il token GitHub dalle variabili d'ambiente"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN non trovato nelle variabili d'ambiente")
    return token

def get_file_from_github(owner, repo, path, token):
    """Recupera un file da GitHub e restituisce il contenuto e lo SHA"""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Decodifica il contenuto base64
        content = base64.b64decode(data['content']).decode('utf-8')
        return content, data['sha']
    except requests.exceptions.RequestException as e:
        print(f"Errore nel recupero del file: {e}")
        return None, None

def update_file_on_github(owner, repo, path, content, sha, token, message="Aggiornato Catalogo.json con tag HV"):
    """Aggiorna un file su GitHub"""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Codifica il contenuto in base64
    content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    data = {
        "message": message,
        "content": content_base64,
        "sha": sha
    }
    
    try:
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        print("✅ File aggiornato con successo su GitHub!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore nell'aggiornamento del file: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Dettagli: {e.response.text}")
        return False

def fetch_fitgirl_titles():
    """Recupera i titoli dalla pagina FitGirl"""
    url = "https://fitgirl-repacks.site/all-hypervisor-bypassed-repacks-a-z/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        ul_element = soup.find('ul', class_='lcp_catlist')
        
        if not ul_element:
            print("❌ Lista non trovata nella pagina")
            return []
        
        titles = []
        for li in ul_element.find_all('li'):
            link = li.find('a')
            if link:
                title_text = link.text.strip()
                titles.append(title_text)
        
        return titles
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore nel recupero della pagina FitGirl: {e}")
        return []

def normalize_title(title):
    """Normalizza il titolo per un confronto più accurato"""
    title = title.lower()
    
    # Rimuovi "free download" e "download"
    title = re.sub(r'\bfree download\b', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\bdownload\b', '', title, flags=re.IGNORECASE)
    
    # Rimuovi versioni tra parentesi
    title = re.sub(r'\s*\([^)]*\)\s*', ' ', title)
    
    # Rimuovi spazi multipli
    title = ' '.join(title.split())
    
    return title.strip()

def clean_fitgirl_title(title):
    """Pulisce il titolo di FitGirl per un confronto migliore"""
    title = title.lower()
    
    # Rimuovi informazioni sulla versione e DLC
    title = re.sub(r'\s*[-:]\s*v[0-9.]+.*$', '', title)
    title = re.sub(r'\s*[-:]\s*build [0-9.]+.*$', '', title)
    title = re.sub(r'\s*[–-]\s*.*', '', title)
    title = re.sub(r'\([^)]*\)', '', title)
    title = re.sub(r'\+.*$', '', title)
    
    # Rimuovi spazi multipli
    title = ' '.join(title.split())
    
    return title.strip()

def title_matches(json_title, fitgirl_title):
    """Verifica se un titolo JSON corrisponde a un titolo FitGirl"""
    if not json_title or not fitgirl_title:
        return False
    
    json_normalized = normalize_title(json_title)
    fitgirl_cleaned = clean_fitgirl_title(fitgirl_title)
    
    # Verifica se il titolo JSON è contenuto nel titolo FitGirl o viceversa
    if json_normalized in fitgirl_cleaned:
        return True
    
    if fitgirl_cleaned in json_normalized:
        return True
    
    # Verifica le parole principali
    json_words = set(json_normalized.split())
    fitgirl_words = set(fitgirl_cleaned.split())
    
    common_words = {'the', 'of', 'and', 'for', 'with', 'in', 'on', 'at', 'to', 'by', 'from', 'up', 'off'}
    
    json_words = {w for w in json_words if w not in common_words and len(w) > 2}
    fitgirl_words = {w for w in fitgirl_words if w not in common_words and len(w) > 2}
    
    if json_words and fitgirl_words:
        common = json_words.intersection(fitgirl_words)
        match_ratio = len(common) / max(len(json_words), len(fitgirl_words))
        return match_ratio >= 0.7
    
    return False

def update_json_with_hv_tags(json_data, fitgirl_titles):
    """Confronta i titoli e aggiunge il tag HV dove corrispondono"""
    if not json_data or not fitgirl_titles:
        return json_data, 0
    
    updated_count = 0
    
    for item in json_data.get('downloads', []):
        json_title = item.get('title', '')
        
        # Salta se ha già il tag HV
        if 'tag' in item and item['tag'] == 'HV':
            continue
        
        for fitgirl_title in fitgirl_titles:
            if title_matches(json_title, fitgirl_title):
                item['tag'] = 'HV'
                updated_count += 1
                print(f"✅ Trovata corrispondenza: '{json_title}'")
                print(f"   → '{fitgirl_title}'")
                break
    
    return json_data, updated_count

def main():
    # Configurazione repository
    owner = "MrNico98"
    repo = "PhoenixPlay-Resources"
    path = "Navigatore/Catalogo.json"
    
    try:
        # 1. Recupera il token GitHub
        token = get_github_token()
        print("✅ Token GitHub recuperato con successo")
        
        # 2. Recupera il file da GitHub
        print(f"\n📥 Recuperando {path} da {owner}/{repo}...")
        content, sha = get_file_from_github(owner, repo, path, token)
        
        if not content or not sha:
            print("❌ Impossibile recuperare il file")
            return
        
        # 3. Parsing del JSON
        json_data = json.loads(content)
        print(f"✅ Recuperati {len(json_data.get('downloads', []))} elementi dal JSON")
        
        # 4. Recupera i titoli da FitGirl
        print("\n🌐 Recuperando titoli da FitGirl...")
        fitgirl_titles = fetch_fitgirl_titles()
        
        if not fitgirl_titles:
            print("❌ Impossibile recuperare i titoli FitGirl")
            return
        
        print(f"✅ Recuperati {len(fitgirl_titles)} titoli da FitGirl")
        
        # 5. Controlla quanti hanno già il tag HV
        existing_hv = sum(1 for item in json_data.get('downloads', []) if item.get('tag') == 'HV')
        print(f"\n📊 Elementi già con tag HV: {existing_hv}")
        
        # 6. Aggiorna il JSON con i nuovi tag HV
        print("\n🔍 Confrontando titoli...")
        updated_json, new_hv_count = update_json_with_hv_tags(json_data, fitgirl_titles)
        
        if new_hv_count == 0:
            print("\nℹ️ Nessuna nuova corrispondenza trovata. Il file rimane invariato.")
            return
        
        # 7. Salva il file aggiornato su GitHub
        print(f"\n📤 Aggiornando {path} su GitHub con {new_hv_count} nuovi tag HV...")
        updated_content = json.dumps(updated_json, indent=2, ensure_ascii=False)
        
        message = f"Aggiunti {new_hv_count} tag HV a Catalogo.json"
        success = update_file_on_github(owner, repo, path, updated_content, sha, token, message)
        
        if success:
            total_hv = existing_hv + new_hv_count
            print(f"\n📊 Statistiche finali:")
            print(f"   - Totale elementi: {len(updated_json.get('downloads', []))}")
            print(f"   - Elementi con tag HV: {total_hv}")
            print(f"   - Nuovi tag aggiunti: {new_hv_count}")
        
    except json.JSONDecodeError as e:
        print(f"❌ Errore nel parsing del JSON: {e}")
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    main()
