import os
import sys
import requests

USERNAME = "Mihichx"
TOKEN = os.environ.get("GH_TOKEN")

HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
API = "https://api.github.com"


def get_repos():
    repos, page = [], 1
    while True:
        try:
            r = requests.get(
                f"{API}/users/{USERNAME}/repos",
                headers=HEADERS,
                params={"per_page": 100, "page": page, "type": "owner"},
                timeout=20,
            )
            r.raise_for_status()
            data = r.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        except requests.exceptions.RequestException:
            sys.exit(1)
    return repos


def get_languages(repos):
    langs = {}
    for repo in repos:
        if repo.get("fork"):
            continue

        main_lang = repo.get("language")
        if main_lang:
            langs[main_lang] = langs.get(main_lang, 0) + 1

    return dict(sorted(langs.items(), key=lambda x: -x[1]))


def make_svg(langs):
    top = list(langs.items())[:6]
    total = sum(s for _, s in top) or 1

    colors = ["#f1e05a", "#3572A5", "#e34c26", "#563d7c", "#2b7489", "#89e051"]
    rows = ""
    y = 75 # Сместили начальную координату выше, так как шапка стала меньше
    
    for i, (lang, size) in enumerate(top):
        pct = size / total * 100
        width = int(pct * 3.2)
        color = colors[i % len(colors)]
        rows += f'''
        <text x="30" y="{y}" fill="#c9d1d9" font-size="15" font-family="Segoe UI, sans-serif">{lang}</text>
        <rect x="170" y="{y-13}" width="320" height="14" fill="#21262d" rx="7"/>
        <rect x="170" y="{y-13}" width="{width}" height="14" fill="{color}" rx="7"/>
        <text x="510" y="{y}" fill="#8b949e" font-size="13" font-family="Segoe UI, sans-serif">{pct:.1f}%</text>
        '''
        y += 28

    height = y + 15

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="{height}" viewBox="0 0 600 {height}">
    <rect width="600" height="{height}" fill="#0d1117" rx="12"/>
    <text x="30" y="35" fill="#58a6ff" font-size="18" font-weight="bold" font-family="Segoe UI, sans-serif">Топ языков профиля (по проектам)</text>
    {rows}
    </svg>'''
    return svg


if __name__ == "__main__":
    repos = get_repos()
    langs = get_languages(repos)
    
    svg = make_svg(langs)
    
    with open("stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)
