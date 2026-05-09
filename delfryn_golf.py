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

PLAYERS = ["Tom", "Jonny", "Ben"]


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
            }
        }

        h1, h2, h3 {
            text-align: left;
            line-height: 1.2;
            margin: 0 0 0.45em 0;
        }

        h1 {
            font-size: 2em;
            font-weight: 700;
        }

        h2 {
            font-size: 1.5em;
            font-weight: 700;
            margin-top: 1.2em;
        }

        h3 {
            font-size: 1.25em;
            font-weight: 600;
            margin-top: 1em;
        }

        p {
            margin: 0 0 0.45em 0;
        }

        ul {
            list-style-type: none;
            padding: 0;
            margin: 0 0 0.45em 0;
        }

        ul li {
            margin: 0.5em 0;
            text-indent: -1em;
            padding-left: 1em;
        }

        ul li::before {
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

        .stat {
            border: 1px solid #444;
            border-radius: 0;
            padding: 0.8em 1em;
            margin: 0.8em 0 1em 0;
        }

        .stat-label {
            font-size: 0.85em;
            color: #ccc;
            margin-bottom: 0.2em;
        }

        .ranking-table {
            display: grid;
            grid-template-columns: 2ch minmax(5ch, 1fr) auto auto;
            column-gap: 0.7em;
            row-gap: 0.25em;
            align-items: baseline;
            margin: 0.4em 0 1em 0;
        }

        .rank-no {
            color: #ccc;
            text-align: right;
        }

        .rank-player {
            font-weight: 700;
        }

        .rank-score {
            text-align: right;
        }

        .rank-detail {
            color: #ccc;
            font-size: 0.9em;
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

        .table-scroll {
            width: 100%;
            overflow-x: auto;
            margin: 0.8em 0 1.2em 0;
        }

        table {
            border-collapse: collapse;
            font-size: 0.9em;
            min-width: max-content;
        }

        th, td {
            border: 1px solid #444;
            padding: 0.35em 0.45em;
            text-align: left;
            vertical-align: top;
            white-space: nowrap;
        }

        th {
            font-weight: 700;
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


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def score_fmt(score: float | int) -> str:
    if isinstance(score, float):
        return f"+{score:.2f}" if score > 0 else f"{score:.2f}"

    return f"+{score}" if score > 0 else str(score)


def trend_arrow(current: float, previous: float) -> str:
    """
    Golf logic:
    higher than previous = worse = red up
    lower than previous = better = green down
    same = flat
    """
    if current > previous:
        return '<span class="up">▲</span>'
    if current < previous:
        return '<span class="down">▼</span>'
    return '<span class="flat">■</span>'


def avg_fmt(current: float, previous: float) -> str:
    return f"{score_fmt(current)} {trend_arrow(current, previous)}"


def read_rows(filename: str = CSV_FILE) -> list[dict]:
    rows = []

    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required_columns = {"Date", "Location", "Game", "Hole", "Par", "Starter", *PLAYERS}
        missing = required_columns - set(reader.fieldnames or [])

        if missing:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}")

        for row in reader:
            clean = {
                "Date": row["Date"],
                "Location": row["Location"],
                "Game": int(row["Game"]),
                "Hole": int(row["Hole"]),
                "Par": int(row["Par"]),
                "Starter": row["Starter"],
            }

            for player in PLAYERS:
                clean[player] = int(row[player]) if row[player] != "" else None

            rows.append(clean)

    return rows


def group_by_game(rows: list[dict]) -> dict[int, list[dict]]:
    games = defaultdict(list)

    for row in rows:
        games[row["Game"]].append(row)

    return dict(sorted(games.items()))


def strokes(score_vs_par: int, par: int) -> int:
    return par + score_vs_par


def player_total_vs_par(rows: list[dict], player: str) -> int:
    return sum(row[player] for row in rows if row[player] is not None)


def player_holes(rows: list[dict], player: str) -> int:
    return sum(1 for row in rows if row[player] is not None)


def player_average_vs_par(rows: list[dict], player: str) -> float:
    holes = player_holes(rows, player)
    return player_total_vs_par(rows, player) / holes if holes else 0


def player_total_shots(rows: list[dict], player: str) -> int:
    return sum(
        strokes(row[player], row["Par"])
        for row in rows
        if row[player] is not None
    )


def total_course_par(rows: list[dict]) -> int:
    return sum(row["Par"] for row in rows)


def total_unique_holes(rows: list[dict]) -> int:
    return len({(row["Game"], row["Hole"]) for row in rows})


def total_games(rows: list[dict]) -> int:
    return len({row["Game"] for row in rows})


def collective_total_vs_par(rows: list[dict]) -> int:
    return sum(player_total_vs_par(rows, player) for player in PLAYERS)


def collective_player_holes(rows: list[dict]) -> int:
    return sum(player_holes(rows, player) for player in PLAYERS)


def collective_average_vs_par(rows: list[dict]) -> float:
    holes = collective_player_holes(rows)
    return collective_total_vs_par(rows) / holes if holes else 0


def collective_total_shots(rows: list[dict]) -> int:
    return sum(player_total_shots(rows, player) for player in PLAYERS)


def ranking_by_average(rows: list[dict]) -> list[str]:
    return sorted(
        PLAYERS,
        key=lambda player: (
            player_average_vs_par(rows, player),
            player_total_vs_par(rows, player),
        ),
    )


def ranking_by_total(rows: list[dict]) -> list[str]:
    return sorted(
        PLAYERS,
        key=lambda player: (
            player_total_vs_par(rows, player),
            player_average_vs_par(rows, player),
        ),
    )


def previous_game_rows(all_rows: list[dict], game_number: int) -> list[dict]:
    games = group_by_game(all_rows)
    previous_games = [g for g in sorted(games) if g < game_number]

    if not previous_games:
        return []

    return games[previous_games[-1]]


def latest_game_number(rows: list[dict]) -> int | None:
    games = group_by_game(rows)
    return max(games) if games else None


def previous_collective_average(all_rows: list[dict], game_number: int | None = None) -> float:
    if game_number is None:
        latest = latest_game_number(all_rows)
        if latest is None:
            return 0
        prev_rows = previous_game_rows(all_rows, latest)
        return collective_average_vs_par(prev_rows) if prev_rows else 0

    prev_rows = previous_game_rows(all_rows, game_number)
    return collective_average_vs_par(prev_rows) if prev_rows else 0


def previous_player_average(all_rows: list[dict], player: str, game_number: int | None = None) -> float:
    if game_number is None:
        latest = latest_game_number(all_rows)
        if latest is None:
            return 0
        prev_rows = previous_game_rows(all_rows, latest)
        return player_average_vs_par(prev_rows, player) if prev_rows else 0

    prev_rows = previous_game_rows(all_rows, game_number)
    return player_average_vs_par(prev_rows, player) if prev_rows else 0


def hole_breakdown(rows: list[dict]) -> dict[str, dict[str, int]]:
    out = {}

    for player in PLAYERS:
        eagle_plus = 0
        birdies = 0
        pars = 0
        bogeys = 0
        double_bogeys = 0
        triple_plus = 0

        for row in rows:
            score = row[player]

            if score is None:
                continue

            if score <= -2:
                eagle_plus += 1
            elif score == -1:
                birdies += 1
            elif score == 0:
                pars += 1
            elif score == 1:
                bogeys += 1
            elif score == 2:
                double_bogeys += 1
            else:
                triple_plus += 1

        out[player] = {
            "Eagle+": eagle_plus,
            "Birdies": birdies,
            "Par": pars,
            "Bogeys": bogeys,
            "Double bogeys": double_bogeys,
            "Triple+": triple_plus,
            "Under par holes": eagle_plus + birdies,
            "Over par holes": bogeys + double_bogeys + triple_plus,
            "Total shots": player_total_shots(rows, player),
            "Total vs par": player_total_vs_par(rows, player),
        }

    return out


def page(title: str, body: str) -> str:
    return HTML_START + f"<h1>{esc(title)}</h1>\n" + body + HTML_END


def write(path: Path, html_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8")


def link_list(items: list[tuple[str, str]]) -> str:
    lines = ["<ul>"]

    for href, label in items:
        lines.append(f'<li><a href="{esc(href)}">{esc(label)}</a></li>')

    lines.append("</ul>")
    return "\n".join(lines)


def average_vs_par_stat(rows: list[dict], all_rows: list[dict]) -> str:
    ranking = ranking_by_average(rows)
    total = collective_total_vs_par(rows)
    average = collective_average_vs_par(rows)
    previous = previous_collective_average(all_rows)

    lines = [
        "<h2>Average vs Par</h2>",
        '<div class="stat">',
        '<div class="stat-label">Ranking</div>',
        '<div class="ranking-table">',
    ]

    for i, player in enumerate(ranking, start=1):
        current_avg = player_average_vs_par(rows, player)
        prev_avg = previous_player_average(all_rows, player)

        lines += [
            f'<div class="rank-no">{i}.</div>',
            f'<div class="rank-player">{esc(player)}</div>',
            f'<div class="rank-score">{avg_fmt(current_avg, prev_avg)}</div>',
            f'<div class="rank-detail">({score_fmt(player_total_vs_par(rows, player))} total)</div>',
        ]

    lines += [
        "</div>",
        '<div class="stat-label">Collective average vs par</div>',
        f'<div class="big-number">{avg_fmt(average, previous)}</div>',
        f'<div class="small-detail">overall {score_fmt(total)} between all players</div>',
        f'<div class="small-detail">{total_games(rows)} games · {total_unique_holes(rows)} holes</div>',
        "</div>",
    ]

    return "\n".join(lines)


def game_par_ranking_stat(game_rows: list[dict], all_rows: list[dict], game_number: int) -> str:
    ranking = ranking_by_total(game_rows)
    total = collective_total_vs_par(game_rows)
    average = collective_average_vs_par(game_rows)
    previous = previous_collective_average(all_rows, game_number)

    lines = [
        "<h2>Par Ranking</h2>",
        '<div class="stat">',
        '<div class="stat-label">Ranking</div>',
        '<div class="ranking-table">',
    ]

    for i, player in enumerate(ranking, start=1):
        current_avg = player_average_vs_par(game_rows, player)
        prev_avg = previous_player_average(all_rows, player, game_number)

        lines += [
            f'<div class="rank-no">{i}.</div>',
            f'<div class="rank-player">{esc(player)}</div>',
            f'<div class="rank-score">{score_fmt(player_total_vs_par(game_rows, player))}</div>',
            f'<div class="rank-detail">({avg_fmt(current_avg, prev_avg)} average)</div>',
        ]

    lines += [
        "</div>",
        '<div class="stat-label">Collective score vs par</div>',
        f'<div class="big-number">{score_fmt(total)}</div>',
        f'<div class="small-detail">average {avg_fmt(average, previous)} between all players</div>',
        f'<div class="small-detail">{total_unique_holes(game_rows)} holes</div>',
        "</div>",
    ]

    return "\n".join(lines)


def player_average_stat(player: str, rows: list[dict]) -> str:
    current_avg = player_average_vs_par(rows, player)
    previous_avg = previous_player_average(rows, player)

    return f"""
<h2>Average vs Par</h2>

<div class="stat">
    <div class="stat-label">{esc(player)}</div>
    <div class="big-number">{avg_fmt(current_avg, previous_avg)}</div>
    <div class="small-detail">overall {score_fmt(player_total_vs_par(rows, player))}</div>
    <div class="small-detail">{total_games(rows)} games · {total_unique_holes(rows)} holes</div>
</div>
"""


def hole_breakdown_table(rows: list[dict], players: list[str] | None = None) -> str:
    players = players or PLAYERS
    data = hole_breakdown(rows)

    total_eagle_plus = 0
    total_birdies = 0
    total_par = 0
    total_bogeys = 0
    total_double_bogeys = 0
    total_triple_plus = 0
    total_shots = 0
    total_vs_par = 0

    lines = [
        "<h2>Hole Breakdown</h2>",
        '<div class="table-scroll">',
        "<table>",
        "<thead>",
        "<tr>"
        '<th rowspan="2">Player</th>'
        '<th colspan="2">Under par holes</th>'
        '<th rowspan="2">Par</th>'
        '<th colspan="3">Over par holes</th>'
        '<th rowspan="2">Total shots</th>'
        '<th rowspan="2">Total vs par</th>'
        "</tr>",
        "<tr>"
        "<th>Eagle+</th>"
        "<th>Birdies</th>"
        "<th>Bogeys</th>"
        "<th>Double bogeys</th>"
        "<th>Triple+</th>"
        "</tr>",
        "</thead>",
        "<tbody>",
    ]

    for player in players:
        d = data[player]

        total_eagle_plus += d["Eagle+"]
        total_birdies += d["Birdies"]
        total_par += d["Par"]
        total_bogeys += d["Bogeys"]
        total_double_bogeys += d["Double bogeys"]
        total_triple_plus += d["Triple+"]
        total_shots += d["Total shots"]
        total_vs_par += d["Total vs par"]

        lines.append(
            "<tr>"
            f"<td>{esc(player)}</td>"
            f"<td>{d['Eagle+']}</td>"
            f"<td>{d['Birdies']}</td>"
            f"<td>{d['Par']}</td>"
            f"<td>{d['Bogeys']}</td>"
            f"<td>{d['Double bogeys']}</td>"
            f"<td>{d['Triple+']}</td>"
            f"<td>{d['Total shots']}</td>"
            f"<td>{score_fmt(d['Total vs par'])}</td>"
            "</tr>"
        )

    under_total = total_eagle_plus + total_birdies
    over_total = total_bogeys + total_double_bogeys + total_triple_plus

    lines.append(
        "<tr>"
        "<th>Total</th>"
        f"<th>{total_eagle_plus}</th>"
        f"<th>{total_birdies}</th>"
        f"<th>{total_par}</th>"
        f"<th>{total_bogeys}</th>"
        f"<th>{total_double_bogeys}</th>"
        f"<th>{total_triple_plus}</th>"
        f"<th>{total_shots}</th>"
        f"<th>{score_fmt(total_vs_par)}</th>"
        "</tr>"
    )

    lines.append(
        "<tr>"
        "<th>Grouped total</th>"
        f'<th colspan="2">{under_total} under par holes</th>'
        f"<th>{total_par} par holes</th>"
        f'<th colspan="3">{over_total} over par holes</th>'
        f"<th>{total_shots}</th>"
        f"<th>{score_fmt(total_vs_par)}</th>"
        "</tr>"
    )

    lines += ["</tbody>", "</table>", "</div>"]
    return "\n".join(lines)


def scorecard_table(rows: list[dict]) -> str:
    course_par = total_course_par(rows)

    lines = [
        "<h2>Scorecard</h2>",
        '<div class="table-scroll">',
        "<table>",
        "<thead>",
        "<tr>"
        "<th>Hole</th>"
        "<th>Par</th>"
        "<th>Tom</th>"
        "<th>Jonny</th>"
        "<th>Ben</th>"
        "<th>Starter</th>"
        "</tr>",
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

    lines.append(
        "<tr>"
        "<th>Total vs par</th>"
        f"<th>{course_par}</th>"
        f"<th>{score_fmt(player_total_vs_par(rows, 'Tom'))}</th>"
        f"<th>{score_fmt(player_total_vs_par(rows, 'Jonny'))}</th>"
        f"<th>{score_fmt(player_total_vs_par(rows, 'Ben'))}</th>"
        "<th></th>"
        "</tr>"
    )

    lines.append(
        "<tr>"
        "<th>Total shots</th>"
        "<th></th>"
        f"<th>{player_total_shots(rows, 'Tom')}</th>"
        f"<th>{player_total_shots(rows, 'Jonny')}</th>"
        f"<th>{player_total_shots(rows, 'Ben')}</th>"
        "<th></th>"
        "</tr>"
    )

    lines += ["</tbody>", "</table>", "</div>"]
    return "\n".join(lines)


def full_data_table(rows: list[dict]) -> str:
    lines = [
        '<div class="table-scroll">',
        "<table>",
        "<thead>",
        "<tr>"
        "<th>Date</th>"
        "<th>Location</th>"
        "<th>Game</th>"
        "<th>Hole</th>"
        "<th>Par</th>"
        "<th>Tom</th>"
        "<th>Jonny</th>"
        "<th>Ben</th>"
        "<th>Starter</th>"
        "</tr>",
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

    lines += ["</tbody>", "</table>", "</div>"]
    return "\n".join(lines)


def games_portal_table(rows: list[dict]) -> str:
    games = group_by_game(rows)

    lines = [
        "<h2>Games</h2>",
        '<div class="table-scroll">',
        "<table>",
        "<thead>",
        "<tr>"
        "<th>Game</th>"
        "<th>Date</th>"
        "<th>Location</th>"
        "<th>Winner</th>"
        "<th>Average vs par</th>"
        "<th>Total vs par</th>"
        "<th>Total shots</th>"
        "<th>Holes</th>"
        "</tr>",
        "</thead>",
        "<tbody>",
    ]

    for game_number, game_rows in games.items():
        first = game_rows[0]
        ranking = ranking_by_total(game_rows)
        winner = ranking[0]
        avg = collective_average_vs_par(game_rows)
        prev = previous_collective_average(rows, game_number)

        lines.append(
            "<tr>"
            f'<td><a href="game_{game_number}.html">Game {game_number}</a></td>'
            f"<td>{esc(first['Date'])}</td>"
            f"<td>{esc(first['Location'])}</td>"
            f"<td>{esc(winner)}</td>"
            f"<td>{avg_fmt(avg, prev)}</td>"
            f"<td>{score_fmt(collective_total_vs_par(game_rows))}</td>"
            f"<td>{collective_total_shots(game_rows)}</td>"
            f"<td>{total_unique_holes(game_rows)}</td>"
            "</tr>"
        )

    lines += ["</tbody>", "</table>", "</div>"]
    return "\n".join(lines)


def players_portal_table(rows: list[dict]) -> str:
    players = ranking_by_average(rows)

    lines = [
        "<h2>Players</h2>",
        '<div class="table-scroll">',
        "<table>",
        "<thead>",
        "<tr>"
        "<th>Rank</th>"
        "<th>Player</th>"
        "<th>Average vs par</th>"
        "<th>Total vs par</th>"
        "<th>Total shots</th>"
        "<th>Games</th>"
        "<th>Holes</th>"
        "</tr>",
        "</thead>",
        "<tbody>",
    ]

    for i, player in enumerate(players, start=1):
        avg = player_average_vs_par(rows, player)
        prev = previous_player_average(rows, player)

        lines.append(
            "<tr>"
            f"<td>{i}</td>"
            f'<td><a href="{player.lower()}.html">{esc(player)}</a></td>'
            f"<td>{avg_fmt(avg, prev)}</td>"
            f"<td>{score_fmt(player_total_vs_par(rows, player))}</td>"
            f"<td>{player_total_shots(rows, player)}</td>"
            f"<td>{total_games(rows)}</td>"
            f"<td>{player_holes(rows, player)}</td>"
            "</tr>"
        )

    lines += ["</tbody>", "</table>", "</div>"]
    return "\n".join(lines)


def player_game_table(player: str, rows: list[dict]) -> str:
    games = group_by_game(rows)

    lines = [
        "<h2>Games</h2>",
        '<div class="table-scroll">',
        "<table>",
        "<thead>",
        "<tr>"
        "<th>Game</th>"
        "<th>Date</th>"
        "<th>Location</th>"
        "<th>Total vs par</th>"
        "<th>Average vs par</th>"
        "<th>Total shots</th>"
        "</tr>",
        "</thead>",
        "<tbody>",
    ]

    for game_number, game_rows in games.items():
        first = game_rows[0]
        current_avg = player_average_vs_par(game_rows, player)
        prev_avg = previous_player_average(rows, player, game_number)

        lines.append(
            "<tr>"
            f'<td><a href="../games/game_{game_number}.html">Game {game_number}</a></td>'
            f"<td>{esc(first['Date'])}</td>"
            f"<td>{esc(first['Location'])}</td>"
            f"<td>{score_fmt(player_total_vs_par(game_rows, player))}</td>"
            f"<td>{avg_fmt(current_avg, prev_avg)}</td>"
            f"<td>{player_total_shots(game_rows, player)}</td>"
            "</tr>"
        )

    lines += ["</tbody>", "</table>", "</div>"]
    return "\n".join(lines)


def build_home_page(rows: list[dict], docs: Path) -> None:
    body = ""
    body += average_vs_par_stat(rows, rows)
    body += hole_breakdown_table(rows)

    body += "<h2>Links</h2>"
    body += link_list([
        ("games/index.html", "List of games"),
        ("players/index.html", "List of players"),
        ("data.html", "Underlying data"),
    ])

    write(docs / "index.html", page(SITE_TITLE, body))


def build_games_pages(rows: list[dict], docs: Path) -> None:
    games = group_by_game(rows)

    for game_number, game_rows in games.items():
        first = game_rows[0]

        body = (
            f'<p class="meta">{esc(first["Date"])} — {esc(first["Location"])}</p>'
            + game_par_ranking_stat(game_rows, rows, game_number)
            + hole_breakdown_table(game_rows)
            + scorecard_table(game_rows)
            + '<p><a href="index.html">Back to games</a></p>'
        )

        write(docs / "games" / f"game_{game_number}.html", page(f"Game {game_number}", body))

    body = games_portal_table(rows)
    body += '<p><a href="../index.html">Back to home</a></p>'

    write(docs / "games" / "index.html", page("Games", body))


def build_player_pages(rows: list[dict], docs: Path) -> None:
    for player in PLAYERS:
        body = (
            player_average_stat(player, rows)
            + hole_breakdown_table(rows, [player])
            + player_game_table(player, rows)
            + '<p><a href="index.html">Back to players</a></p>'
        )

        write(docs / "players" / f"{player.lower()}.html", page(player, body))

    body = players_portal_table(rows)
    body += '<p><a href="../index.html">Back to home</a></p>'

    write(docs / "players" / "index.html", page("Players", body))


def build_data_page(rows: list[dict], docs: Path) -> None:
    body = full_data_table(rows)
    body += '<p><a href="index.html">Back to home</a></p>'

    write(docs / "data.html", page("Underlying Data", body))


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