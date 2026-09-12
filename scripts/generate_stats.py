import os
import sys
import requests

USERNAME = "Mihichx"
TOKEN = os.environ.get("GH_TOKEN")

HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
API = "https://api.github.com"


def get_user():
    try:
        r = requests.get(f"{API}/users/{USERNAME}", headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException:
        sys.exit(1)


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


def get_total_commits():
    commits = 0
    try:
        r = requests.get(f"{API}/users/{USERNAME}/events/public", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            for event in r.json():
                if event.get("type") == "PushEvent":
                    commits += len(event.get("payload", {}).get("commits", []))
    except Exception:
        pass
    return commits if commits > 0 else "Активен"


def get_starred_count():
    try:
        r = requests.get(f"{API}/users/{USERNAME}/starred", headers=HEADERS, params={"per_page": 1}, timeout=20)
        if "Link" in r.headers:
            links = r.headers["Link"]
            if 'rel="last"' in links:
                last_page_url = links.split('fill="#58a6ff"').split('<')[-1].split('>')
                r_last = requests.get(last_page_url, headers=HEADERS, timeout=20)
                page_num = int(last_page_url.split("page=")[-1].split("&"))
                return (page_num - 1) * 1 + len(r_last.json())
        return len(r.json())
    except Exception:
        return 0


def get_languages(repos):
    langs = {}
    for repo in repos:
        if repo.get("fork"):
            continue

        main_lang = repo.get("language")
        if main_lang:
            langs[main_lang] = langs.get(main_lang, 0) + 1

    return dict(sorted(langs.items(), key=lambda x: -x))


def make_svg(user, repos, langs, total_commits, starred_count):
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
    <text x="240" y="95" fill="#c9d1d9" font-size="15" font-family="Segoe UI, sans-serif">👥 Подписчиков: <tspan fill="#58a6ff">{followers}</tspan></text>
    
    <text x="30" y="125" fill="#c9d1d9" font-size="15" font-family="Segoe UI, sans-serif">🔥 Новые коммиты: <tspan fill="#58a6ff">{total_commits}</tspan></text>
    <text x="240" y="125" fill="#c9d1d9" font-size="15" font-family="Segoe UI, sans-serif">⭐ Вы лайкнули: <tspan fill="#58a6ff">{starred_count}</tspan></text>
    
    <text x="30" y="175" fill="#58a6ff" font-size="17" font-weight="bold" font-family="Segoe UI, sans-serif">Топ языков (по проектам)</text>
    {rows}
    </svg>'''
    return svg


if __name__ == "__main__":
    user = get_user()
    repos = get_repos()
    langs = get_languages(repos)
    commits = get_total_commits()
    starred = get_starred_count()
    
    svg = make_svg(user, repos, langs, commits, starred)
    
    with open("stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)
