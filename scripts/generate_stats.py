import os
import requests

USERNAME = "Mihichx"
TOKEN = os.environ.get("GH_TOKEN")

HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
API = "https://api.github.com"


def get_user():
    r = requests.get(f"{API}/users/{USERNAME}", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def get_repos():
    repos, page = [], 1
    while True:
        r = requests.get(
            f"{API}/users/{USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "owner"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos


def get_languages(repos):
    langs = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        try:
            r = requests.get(repo["languages_url"], headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            for lang, size in r.json().items():
                langs[lang] = langs.get(lang, 0) + size
        except Exception:
            continue
    return dict(sorted(langs.items(), key=lambda x: -x[1]))


def make_svg(user, repos, langs):
    stars = sum(r["stargazers_count"] for r in repos)
    forks = sum(r["forks_count"] for r in repos)
    repos_count = user["public_repos"]
    followers = user["followers"]

    top = list(langs.items())[:6]
    total = sum(s for _, s in top) or 1

    colors = ["#f1e05a", "#3572A5", "#e34c26", "#563d7c", "#2b7489", "#89e051"]
    rows = ""
    y = 210
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

    height = y + 20

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="{height}" viewBox="0 0 600 {height}">
    <rect width="600" height="{height}" fill="#0d1117" rx="12"/>
    <text x="30" y="50" fill="#58a6ff" font-size="22" font-weight="bold" font-family="Segoe UI, sans-serif">GitHub Stats — {USERNAME}</text>
    <text x="30" y="95" fill="#c9d1d9" font-size="15" font-family="Segoe UI, sans-serif">📦 Репозиториев: <tspan fill="#58a6ff">{repos_count}</tspan></text>
    <text x="250" y="95" fill="#c9d1d9" font-size="15" font-family="Segoe UI, sans-serif">⭐ Звёзд: <tspan fill="#58a6ff">{stars}</tspan></text>
    <text x="420" y="95" fill="#c9d1d9" font-size="15" font-family="Segoe UI, sans-serif">👥 Подписчиков: <tspan fill="#58a6ff">{followers}</tspan></text>
    <text x="30" y="125" fill="#c9d1d9" font-size="15" font-family="Segoe UI, sans-serif">🍴 Форков: <tspan fill="#58a6ff">{forks}</tspan></text>
    <text x="30" y="175" fill="#58a6ff" font-size="17" font-weight="bold" font-family="Segoe UI, sans-serif">Топ языков</text>
    {rows}
    </svg>'''
    return svg


if __name__ == "__main__":
    user = get_user()
    repos = get_repos()
    langs = get_languages(repos)
    svg = make_svg(user, repos, langs)
    with open("stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("✅ stats.svg обновлён")
