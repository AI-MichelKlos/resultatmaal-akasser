"""Synkroniser kontrollerede offentlige RM01AK-data fra samme kildecommit."""
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "AI-MichelKlos/A-kasseindsigt-dashboard"

def read(url, api=False):
    headers = {"User-Agent": "resultatmaal-akasser"}
    if api and os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)

def main():
    head = read(f"https://api.github.com/repos/{REPO}/commits/main", api=True)["sha"]
    base = f"https://raw.githubusercontent.com/{REPO}/{head}/"
    data = read(base + "data/rm01ak.json")
    status = read(base + "status/rm01ak.json")
    assert data["meta"]["dataset"] == "rm01ak"
    assert data["meta"]["state"] == "ok"
    latest = data["meta"]["latestStatusMonth"]
    for horizon in ("three", "six"):
        cohort = data["meta"]["latestCohort"][horizon]
        assert isinstance(data["series"][horizon]["TOTAL"][cohort], (int, float))
        assert isinstance(data["counts"][horizon]["TOTAL"][cohort], (int, float))
    assert all(data["subgroups"][k]["categories"] for k in ("sex","age","origin","region"))
    data["meta"]["mirrorSourceCommit"] = head
    status["mirrorSourceCommit"] = head
    for path, payload in (("data/rm01ak.json", data), ("status/rm01ak.json", status)):
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(target)
    print(f"Synkroniseret RM01AK: {latest}, kildecommit {head}, kildestatus {status['state']}")

if __name__ == "__main__":
    main()
