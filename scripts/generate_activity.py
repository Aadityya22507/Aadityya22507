
import os
import json
import urllib.request
from datetime import date, timedelta

TOKEN = os.environ.get("GH_TOKEN")
USERNAME = "Aadityya22507"
OUTPUT = "assets/activity.svg"

if not TOKEN:
    raise RuntimeError("GH_TOKEN secret is missing.")

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
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Aadityya-Activity-Graph"
    }
)

with urllib.request.urlopen(request) as response:
    result = json.loads(response.read())

if result.get("errors"):
    raise RuntimeError(json.dumps(result["errors"], indent=2))

user = result.get("data", {}).get("user")

if user is None:
    raise RuntimeError("GitHub user not found.")

calendar = user["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]
total = calendar["totalContributions"]

cell = 13
gap = 4
step = cell + gap
left = 55
top = 55
width = left + len(weeks) * step + 20
height = 175

colors = [
    "#161B22",
    "#5C1010",
    "#A51D2D",
    "#E02D3C",
    "#FF5555"
]

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    '<rect width="100%" height="100%" rx="12" fill="#0D1117"/>',
    '<text x="20" y="27" fill="#FF5555" font-size="18" font-weight="bold">Contribution Activity</text>',
    f'<text x="{width-20}" y="27" fill="#FFFFFF" font-size="12" text-anchor="end">{total} contributions in the last year</text>'
]

last_month = None

for week_index, week in enumerate(weeks):
    for day in week["contributionDays"]:
        current = date.fromisoformat(day["date"])
        count = day["contributionCount"]

        if current.month != last_month and current.weekday() <= 2:
            x = left + week_index * step
            svg.append(
                f'<text x="{x}" y="47" fill="#AAAAAA" font-size="10">{current.strftime("%b")}</text>'
            )
            last_month = current.month

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
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{color}">'
            f'<title>{current}: {count} contributions</title></rect>'
        )

svg.append("</svg>")

os.makedirs("assets", exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as file:
    file.write("\n".join(svg))

print(f"SUCCESS: Generated {OUTPUT}")
print(f"Total contributions: {total}")
