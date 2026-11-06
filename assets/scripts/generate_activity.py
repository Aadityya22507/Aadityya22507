
import os
import json
import urllib.request
from datetime import date, timedelta
from collections import defaultdict

TOKEN = os.environ.get("GH_TOKEN")

if not TOKEN:
    raise RuntimeError("GH_TOKEN secret is missing.")

USERNAME = "Aadityya22507"
OUTPUT = "assets/activity.svg"

today = date.today()
start_date = today - timedelta(days=364)

query = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

payload = {
    "query": query,
    "variables": {
        "username": USERNAME,
        "from": start_date.isoformat() + "T00:00:00Z",
        "to": today.isoformat() + "T23:59:59Z"
    }
}

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Aadityya-Contribution-Graph"
    }
)

with urllib.request.urlopen(request) as response:
    result = json.loads(response.read().decode("utf-8"))

if "errors" in result:
    raise RuntimeError(json.dumps(result["errors"], indent=2))

user = result.get("data", {}).get("user")

if user is None:
    raise RuntimeError("GitHub user was not found.")

calendar = user["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]
total = calendar["totalContributions"]

# Graph dimensions
cell = 13
gap = 4
step = cell + gap
left = 55
top = 48
width = left + len(weeks) * step + 25
height = 170

colors = [
    "#161B22",
    "#5C1010",
    "#A51D2D",
    "#E02D3C",
    "#FF5555"
]

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">',
    '<rect width="100%" height="100%" rx="12" fill="#0D1117"/>',
    '<style>',
    'text { font-family: Arial, sans-serif; }',
    '</style>',
    f'<text x="20" y="25" fill="#FF5555" '
    f'font-size="17" font-weight="bold">'
    f'Contribution Activity</text>',
    f'<text x="{width-20}" y="25" fill="#FFFFFF" '
    f'font-size="12" text-anchor="end">'
    f'{total} contributions in the last year</text>'
]

# Month labels
last_month = None

for week_index, week in enumerate(weeks):
    days = week["contributionDays"]

    if not days:
        continue

    first_day = date.fromisoformat(days[0]["date"])
    if first_day.month != last_month:
        month_label = first_day.strftime("%b")
        x = left + week_index * step

        svg.append(
            f'<text x="{x}" y="42" fill="#AAAAAA" '
            f'font-size="10">{month_label}</text>'
        )
        last_month = first_day.month

# Weekday labels
weekday_labels = [
    (1, "Mon"),
    (3, "Wed"),
    (5, "Fri")
]

for row, label in weekday_labels:
    y = top + row * step + 10
    svg.append(
        f'<text x="12" y="{y}" fill="#888888" '
        f'font-size="10">{label}</text>'
    )

# Contribution squares
for week_index, week in enumerate(weeks):
    for day in week["contributionDays"]:
        current = date.fromisoformat(day["date"])
        count = day["contributionCount"]

        # Monday = 0, Sunday = 6
        row = current.weekday()

        if count == 0:
            color = colors[0]
        elif count <= 3:
            color = colors[1]
        elif count <= 6:
            color = colors[2]
        elif count <= 9:
            color = colors[3]
        else:
            color = colors[4]

        x = left + week_index * step
        y = top + row * step

        svg.append(
            f'<rect x="{x}" y="{y}" '
            f'width="{cell}" height="{cell}" '
            f'rx="3" fill="{color}">'
            f'<title>{current}: {count} contributions</title>'
            f'</rect>'
        )

# Legend
legend_y = 150
legend_x = width - 175

svg.append(
    f'<text x="{legend_x-45}" y="{legend_y+10}" '
    f'fill="#AAAAAA" font-size="10">Less</text>'
)

for index, color in enumerate(colors):
    x = legend_x + index * 17
    svg.append(
        f'<rect x="{x}" y="{legend_y}" '
        f'width="12" height="12" rx="2" fill="{color}"/>'
    )

svg.append(
    f'<text x="{legend_x+95}" y="{legend_y+10}" '
    f'fill="#AAAAAA" font-size="10">More</text>'
)

svg.append("</svg>")

os.makedirs("assets", exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as file:
    file.write("\n".join(svg))

print(f"Successfully generated {OUTPUT}")
print(f"Total contributions: {total}")
