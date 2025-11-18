#!/usr/bin/env python3
"""
Genera un gráfico de frecuencia de commits (suma por semana) usando
la API GraphQL de GitHub y guarda assets/commit_frequency.png.

Uso:
- Define GITHUB_TOKEN en el entorno (o en GitHub Actions se usa GITHUB_TOKEN automático).
- Opcional: define GITHUB_USER con tu usuario (por defecto intenta usar GITHUB_ACTOR).
"""
import os
import sys
import requests
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USER = os.environ.get("GITHUB_USER") or os.environ.get("GITHUB_ACTOR") or "LiuNotAnAngel"

if not GITHUB_TOKEN:
    print("Error: define la variable de entorno GITHUB_TOKEN", file=sys.stderr)
    sys.exit(1)

QUERY = """
query ($login: String!) {
  user(login: $login) {
    contributionsCollection {
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

def fetch_contributions(login):
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"bearer {GITHUB_TOKEN}"}
    payload = {"query": QUERY, "variables": {"login": login}}
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for week in weeks:
        for day in week["contributionDays"]:
            days.append({"date": day["date"], "count": day["contributionCount"]})
    return days

def build_dataframe(days):
    df = pd.DataFrame(days)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    return df

def plot_weekly_hist(df, out_path="assets/commit_frequency.png"):
    # Resample by ISO week (sum commits per week)
    weekly = df.resample("W-MON").sum()  # weeks starting Monday
    plt.figure(figsize=(12,4))
    plt.bar(weekly.index, weekly["count"], width=4)
    plt.ylabel("Commits por semana")
    plt.xlabel("Semana (inicio)")
    plt.title(f"Frecuencia de commits — usuario: {GITHUB_USER}")
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Guardado: {out_path}")

def main():
    print(f"Obteniendo datos para usuario: {GITHUB_USER}")
    days = fetch_contributions(GITHUB_USER)
    df = build_dataframe(days)
    plot_weekly_hist(df)

if __name__ == "__main__":
    main()
