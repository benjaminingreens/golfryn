#!/usr/bin/env python3

from __future__ import annotations

import csv
import html
import shutil
from collections import defaultdict
from pathlib import Path


CSV_FILE = "delfryn_golf.csv"
DOCS_DIR = "docs"
SITE_TITLE = "Golfryn"

PLAYER_COLUMNS = ["Tom", "Jonny", "Ben"]


# ----------------------------
# HTML template
# ----------------------------

HTML_START = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&display=swap" rel="stylesheet">

    <style>
        html {
            height: 100%;
            box-sizing: border-box;
        }
        *, *::before, *::after {
            box-sizing: inherit;
        }

        body {
            font-family: "IBM Plex Mono",
                         ui-monospace,
                         SFMono-Regular,
                         Menlo,
                         Monaco,
                         Consolas,
                         "Liberation Mono",
                         "Courier New",
                         monospace;

            display: flex;
            justify-content: center;
            align-items: flex-start;

            min-height: 100%;
            margin: 0;
            padding: 14px 20px 20px 20px;

            background-color: black;
            color: white;

            font-size: 19px;
            line-height: 1.7;

            overflow-x: hidden;
        }

        @media (min-width: 768px) {
            body {
                padding: 28px 50px 50px 50px;
                font-size: 22px;
            }
        }

        .content {
            max-width: 600px;
            width: 100%;
            min-width: 0;
        }

        @media (min-width: 1024px) {
            .content {
                max-width: 900px;
                min-width: 0;
            }
        }

        .content,
        .content * {
            overflow-wrap: anywhere;
            word-break: break-word;
            hyphens: auto;
        }

        h1, h2, h3 {
            text-align: left;
            line-height: 1.2;
            margin: 0 0 0.45em 0;
        }

        h1 { font-size: 2em; font-weight: 700; }
        h2 { font-size: 1.5em; font-weight: 700; margin-top: 1.2em; }
        h3 { font-size: 1.25em; font-weight: 600; margin-top: 1em; }

        p {
            margin: 0 0 0.45em 0;
        }

        ul {
            list-style-type: none;
            padding: 0;
            margin: 0 0 0.45em 0;
        }

        li {
            margin: 0.5em 0;
            text-indent: -1em;
            padding-left: 1em;
        }

        li::before {
            content: "* ";
        }

        a {
            color: white;
            text-decoration: underline;
        }

        a:hover {
            text-decoration: none;
        }

        hr {
            border: none;
            border-top: 1px solid #444;
            margin: 0.9em 0;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 0.8em 0 1.2em 0;
            font-size: 0.9em;
        }

        th, td {
            border: 1px solid #444;
            padding: 0.35em 0.45em;
            text-align: left;
            vertical-align: top;
        }

        th {
            font-weight: 700;
        }

        .stat {
            border: 1px solid #444;
            border-radius: 10px;
            padding: 0.8em 1em;
            margin: 0.8em 0 1em 0;
        }

        .stat-label {
            font-size: 0.85em;
            color: #ccc;
            margin-bottom: 0.2em;
        }

        .big-number {
            font-size: 2.4em;
            line-height: 1.1;
            font-weight: 700;
        }

        .small-detail {
            color: #ccc;
            font-size: 0.9em;
        }

        .up {
            color: #ff6b6b;
            font-weight: 700;
        }

        .down {
            color: #51cf66;
            font-weight: 700;
        }

        .flat {
            color: #ccc;
            font-weight: 700;
        }

        .meta {
            color: #ccc;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="content">
"""

HTML_END = """    </div>
</body>
</html>
"""


# ----------------------------
# Data
# ----------------------------

def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_rows(filename: str = CSV_FILE) -> list[dict]:
    rows = []

    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            clean = {
                "Date": row["Date"],
                "Location": row["Location"],
                "Game": int(row["Game"]),
                "Hole": int(row["Hole"]),
                "Par": int(row["Par"]),
                "Starter": row["Starter"],
            }

            for player in PLAYER_COLUMNS:
                clean[player] = int(row[player]) if row[player] != "" else None

            rows.append(clean)

    return rows


def score_fmt(score: float | int) -> str:
    if isinstance(score, float):
        rounded = round(score, 2)
        if rounded > 0:
            return f"+{rounded:.2f}"
        return f"{rounded:.2f}"

    if score > 0:
        return f"+{score}"
    return str(score)


def strokes(score_vs_par: int, par: int) -> int:
    return par + score_vs_par


def group_by_game(rows: list[dict]) -> dict[int, list[dict]]:
    games = defaultdict(list)

    for row in rows:
        games[row["Game"]].append(row)

    return dict(sorted(games.items()))


# ----------------------------
# Stats
# ----------------------------

def player_summary(rows: list[dict]) -> dict[str, dict]:
    out = {}

    for player in PLAYER_COLUMNS:
        scores = [
            row[player]
            for row in rows
            if row[player] is not None
        ]

        total = sum(scores)
        count = len(scores)
        average = total / count if count else 0

        out[player] = {
            "total": total,
            "average": average,
            "shots": count,
        }

    return out


def collective_summary(rows: list[dict]) -> dict:
    scores = []

    for row in rows:
        for player in PLAYER_COLUMNS:
            if row[player] is not None:
                scores.append(row[player])

    total = sum(scores)
    count = len(scores)
    average = total / count if count else 0

    return {
        "total": total,
        "average": average,
        "shots": count,
    }


def ranking_by_average(rows: list[dict]) -> list[tuple[str, dict]]:
    summary = player_summary(rows)

    return sorted(
        summary.items(),
        key=lambda item: (item[1]["average"], item[1]["total"])
    )


def ranking_by_total(rows: list[dict]) -> list[tuple[str, dict]]:
    summary = player_summary(rows)

    return sorted(
        summary.items(),
        key=lambda item: (item[1]["total"], item[1]["average"])
    )


def shot_breakdown(rows: list[dict]) -> dict[str, dict]:
    out = {}

    for player in PLAYER_COLUMNS:
        over = 0
        par = 0
        under = 0

        for row in rows:
            score = row[player]

            if score is None:
                continue

            if score > 0:
                over += 1
            elif score == 0:
                par += 1
            else:
                under += 1

        out[player] = {
            "Over par": over,
            "Par": par,
            "Under par": under,
            "Total shots": over + par + under,
        }

    return out


def trend_arrow(current: float, previous: float) -> str:
    """
    For golf, lower is better:
      current > previous = worse = red up
      current < previous = better = green down
    """
    if current > previous:
        return '<span class="up">▲</span>'
    if current < previous:
        return '<span class="down">▼</span>'
    return '<span class="flat">■</span>'


def previous_collective_average(rows: list[dict], current_game: int | None = None) -> float:
    games = group_by_game(rows)

    if current_game is None:
        # Main page: compare latest game against previous game.
        game_numbers = sorted(games)

        if len(game_numbers) < 2:
            return 0

        previous_game = game_numbers[-2]
        return collective_summary(games[previous_game])["average"]

    # Game page: compare this game against the game immediately before it.
    previous_games = [g for g in sorted(games) if g < current_game]

    if not previous_games:
        return 0

    return collective_summary(games[previous_games[-1]])["average"]


# ----------------------------
# HTML chunks
# ----------------------------

def page(title: str, body: str) -> str:
    return (
        HTML_START
        + f"<h1>{esc(title)}</h1>\n"
        + body
        + HTML_END
    )


def link_list(items: list[tuple[str, str]]) -> str:
    lines = ["<ul>"]

    for href, label in items:
        lines.append(f'<li><a href="{esc(href)}">{esc(label)}</a></li>')

    lines.append("</ul>")
    return "\n".join(lines)


def average_par_stat(rows: list[dict], all_rows: list[dict]) -> str:
    ranking = ranking_by_average(rows)
    collective = collective_summary(rows)

    # Main page compares latest game with previous game.
    games = group_by_game(all_rows)
    latest_game = max(games) if games else None
    previous = previous_collective_average(all_rows, latest_game)
    arrow = trend_arrow(collective["average"], previous)

    rank_text = " / ".join(
        f"{player} {score_fmt(data['average'])} ({score_fmt(data['total'])})"
        for player, data in ranking
    )

    return f"""
<h2>Average Par</h2>

<div class="stat">
    <div class="stat-label">Ranking</div>
    <p>{rank_text}</p>

    <div class="stat-label">Collective average</div>
    <div class="big-number">{score_fmt(collective["average"])} {arrow}</div>
    <div class="small-detail">overall {score_fmt(collective["total"])} between all players</div>
</div>
"""


def game_par_stat(game_rows: list[dict], all_rows: list[dict], game_number: int) -> str:
    ranking = ranking_by_total(game_rows)
    collective = collective_summary(game_rows)
    previous = previous_collective_average(all_rows, game_number)
    arrow = trend_arrow(collective["average"], previous)

    rank_text = " / ".join(
        f"{player} {score_fmt(data['total'])} ({score_fmt(data['average'])})"
        for player, data in ranking
    )

    return f"""
<h2>Par Ranking</h2>

<div class="stat">
    <div class="stat-label">Ranking</div>
    <p>{rank_text}</p>

    <div class="stat-label">Collective score</div>
    <div class="big-number">{score_fmt(collective["total"])} {arrow}</div>
    <div class="small-detail">average {score_fmt(collective["average"])} between all players</div>
</div>
"""


def player_average_stat(player: str, rows: list[dict]) -> str:
    summary = player_summary(rows)[player]

    return f"""
<h2>Average Par</h2>

<div class="stat">
    <div class="stat-label">{esc(player)}</div>
    <div class="big-number">{score_fmt(summary["average"])}</div>
    <div class="small-detail">overall {score_fmt(summary["total"])}</div>
</div>
"""


def shot_breakdown_table(rows: list[dict], players: list[str] | None = None) -> str:
    players = players or PLAYER_COLUMNS
    breakdown = shot_breakdown(rows)

    lines = [
        "<h2>Shot Breakdown</h2>",
        "<table>",
        "<thead>",
        "<tr><th>Player</th><th>Over par</th><th>Par</th><th>Under par</th><th>Total shots</th></tr>",
        "</thead>",
        "<tbody>",
    ]

    for player in players:
        data = breakdown[player]
        lines.append(
            "<tr>"
            f"<td>{esc(player)}</td>"
            f"<td>{data['Over par']}</td>"
            f"<td>{data['Par']}</td>"
            f"<td>{data['Under par']}</td>"
            f"<td>{data['Total shots']}</td>"
            "</tr>"
        )

    lines += ["</tbody>", "</table>"]
    return "\n".join(lines)


def scorecard_table(rows: list[dict]) -> str:
    lines = [
        "<h2>Scorecard</h2>",
        "<table>",
        "<thead>",
        "<tr><th>Hole</th><th>Par</th><th>Tom</th><th>Jonny</th><th>Ben</th><th>Starter</th></tr>",
        "</thead>",
        "<tbody>",
    ]

    for row in sorted(rows, key=lambda r: r["Hole"]):
        lines.append(
            "<tr>"
            f"<td>{row['Hole']}</td>"
            f"<td>{row['Par']}</td>"
            f"<td>{score_fmt(row['Tom'])}</td>"
            f"<td>{score_fmt(row['Jonny'])}</td>"
            f"<td>{score_fmt(row['Ben'])}</td>"
            f"<td>{esc(row['Starter'])}</td>"
            "</tr>"
        )

    lines += ["</tbody>", "</table>"]
    return "\n".join(lines)


def full_data_table(rows: list[dict]) -> str:
    lines = [
        "<table>",
        "<thead>",
        "<tr><th>Date</th><th>Location</th><th>Game</th><th>Hole</th><th>Par</th><th>Tom</th><th>Jonny</th><th>Ben</th><th>Starter</th></tr>",
        "</thead>",
        "<tbody>",
    ]

    for row in rows:
        lines.append(
            "<tr>"
            f"<td>{esc(row['Date'])}</td>"
            f"<td>{esc(row['Location'])}</td>"
            f"<td>{row['Game']}</td>"
            f"<td>{row['Hole']}</td>"
            f"<td>{row['Par']}</td>"
            f"<td>{score_fmt(row['Tom'])}</td>"
            f"<td>{score_fmt(row['Jonny'])}</td>"
            f"<td>{score_fmt(row['Ben'])}</td>"
            f"<td>{esc(row['Starter'])}</td>"
            "</tr>"
        )

    lines += ["</tbody>", "</table>"]
    return "\n".join(lines)


# ----------------------------
# Pages
# ----------------------------

def write(path: Path, html_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8")


def build_home_page(rows: list[dict], docs: Path) -> None:
    body = ""

    body += average_par_stat(rows, rows)
    body += shot_breakdown_table(rows)

    body += "<h2>Links</h2>"
    body += link_list([
        ("games/index.html", "List of games"),
        ("players/index.html", "List of players"),
        ("data.html", "Underlying data"),
    ])

    write(docs / "index.html", page(SITE_TITLE, body))


def build_games_pages(rows: list[dict], docs: Path) -> None:
    games = group_by_game(rows)

    index_items = []

    for game_number, game_rows in games.items():
        first = game_rows[0]
        label = f"Game {game_number}: {first['Date']}, {first['Location']}"
        href = f"game_{game_number}.html"
        index_items.append((href, label))

        body = (
            f'<p class="meta">{esc(first["Date"])} — {esc(first["Location"])}</p>'
            + game_par_stat(game_rows, rows, game_number)
            + shot_breakdown_table(game_rows)
            + scorecard_table(game_rows)
            + '<p><a href="index.html">Back to games</a></p>'
        )

        write(
            docs / "games" / href,
            page(f"Game {game_number}", body)
        )

    body = link_list(index_items)
    body += '<p><a href="../index.html">Back to home</a></p>'

    write(
        docs / "games" / "index.html",
        page("Games", body)
    )


def build_player_pages(rows: list[dict], docs: Path) -> None:
    index_items = []

    for player in PLAYER_COLUMNS:
        href = f"{player.lower()}.html"
        index_items.append((href, player))

        body = (
            player_average_stat(player, rows)
            + shot_breakdown_table(rows, [player])
            + player_game_table(player, rows)
            + '<p><a href="index.html">Back to players</a></p>'
        )

        write(
            docs / "players" / href,
            page(player, body)
        )

    body = link_list(index_items)
    body += '<p><a href="../index.html">Back to home</a></p>'

    write(
        docs / "players" / "index.html",
        page("Players", body)
    )


def player_game_table(player: str, rows: list[dict]) -> str:
    games = group_by_game(rows)

    lines = [
        "<h2>Games</h2>",
        "<table>",
        "<thead>",
        "<tr><th>Game</th><th>Date</th><th>Location</th><th>Total par</th><th>Average par</th></tr>",
        "</thead>",
        "<tbody>",
    ]

    for game_number, game_rows in games.items():
        first = game_rows[0]
        scores = [row[player] for row in game_rows if row[player] is not None]
        total = sum(scores)
        average = total / len(scores) if scores else 0

        lines.append(
            "<tr>"
            f'<td><a href="../games/game_{game_number}.html">Game {game_number}</a></td>'
            f"<td>{esc(first['Date'])}</td>"
            f"<td>{esc(first['Location'])}</td>"
            f"<td>{score_fmt(total)}</td>"
            f"<td>{score_fmt(average)}</td>"
            "</tr>"
        )

    lines += ["</tbody>", "</table>"]
    return "\n".join(lines)


def build_data_page(rows: list[dict], docs: Path) -> None:
    body = full_data_table(rows)
    body += '<p><a href="index.html">Back to home</a></p>'

    write(
        docs / "data.html",
        page("Underlying Data", body)
    )


def build_site() -> None:
    rows = read_rows(CSV_FILE)

    docs = Path(DOCS_DIR)

    if docs.exists():
        shutil.rmtree(docs)

    docs.mkdir(parents=True, exist_ok=True)

    build_home_page(rows, docs)
    build_games_pages(rows, docs)
    build_player_pages(rows, docs)
    build_data_page(rows, docs)

    print(f"Built {DOCS_DIR}/")


if __name__ == "__main__":
    build_site()