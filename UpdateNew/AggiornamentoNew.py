import os
import json
import random
import requests
from github import Github

def get_random_games():
    response = requests.get("https://raw.githubusercontent.com/MrNico98/PhoenixPlay-Resources/main/Navigatore/Catalogo.json")
    catalogo = response.json()
    tutti_giochi = catalogo["Catalogo"]
    return random.sample(tutti_giochi, min(4, len(tutti_giochi)))

def update_home_json(giochi):
    home_data = {"Home": []}
    for gioco in giochi:
        gioco_home = gioco.copy()
        home_data["Home"].append(gioco_home)
    return home_data

def update_github(home_data):
    g = Github(os.getenv('GITHUB_TOKEN'))
    repo = g.get_repo("MrNico98/PhoenixPlay-Resources")
    
    # Formattazione personalizzata per avere ogni gioco su una riga
    json_str = '{\n  "Home": [\n    '
    json_str += ',\n    '.join([json.dumps(game, ensure_ascii=False) for game in home_data["Home"]])
    json_str += '\n  ]\n}'
    
    try:
        contents = repo.get_contents("Navigatore/Home.json", ref="main")
        repo.update_file(
            path="Navigatore/Home.json",
            message="Aggiornamento casuale giochi in Home.json",
            content=json_str,
            sha=contents.sha,
            branch="main"
        )
    except:
        repo.create_file(
            path="Navigatore/Home.json",
            message="Creazione Home.json con giochi casuali",
            content=json_str,
            branch="main"
        )

def main():
    giochi = get_random_games()
    home_data = update_home_json(giochi)
    update_github(home_data)
    print("Home.json aggiornato con successo con i seguenti giochi:")
    for gioco in giochi:
        print(f"- {gioco['nome_gioco']}")

if __name__ == "__main__":
    main()
