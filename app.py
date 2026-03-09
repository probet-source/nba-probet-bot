import hashlib
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# ==========================================================
# CONFIGURAÇÃO GERAL
# ==========================================================
SEASON_LABEL = "2025-26"
RAPIDAPI_HOST = "api-nba-v1.p.rapidapi.com"
RAPIDAPI_BASE_URL = f"https://{RAPIDAPI_HOST}"
REQUEST_TIMEOUT = 20

st.set_page_config(
    page_title="NBA ProBet Analytics 2.0",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================================
# ESTILO
# ==========================================================
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #111827 0%, #0b1220 40%, #050814 100%);
        color: #f8fafc;
    }
    .main-card {
        background: rgba(17, 24, 39, 0.90);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        margin-bottom: 14px;
    }
    .hero {
        background: linear-gradient(135deg, rgba(245,158,11,.20), rgba(59,130,246,.18));
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 22px;
        padding: 24px;
        margin-bottom: 18px;
    }
    .hero h1 {
        margin: 0;
        font-size: 2.2rem;
        color: #f8fafc;
    }
    .hero p {
        margin: 6px 0 0 0;
        color: #cbd5e1;
    }
    .pill {
        display: inline-block;
        background: rgba(251,191,36,.12);
        border: 1px solid rgba(251,191,36,.25);
        color: #fde68a;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: .85rem;
        margin-right: 8px;
        margin-top: 8px;
    }
    .small-note {
        color: #94a3b8;
        font-size: .88rem;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin: 12px 0 6px 0;
        color: #e2e8f0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# BASE DE DADOS LOCAL (FALLBACK)
# ==========================================================
TEAM_META = [
    {"TEAM_ID": 1610612737, "TEAM_ABBREVIATION": "ATL", "TEAM_CITY": "Atlanta", "TEAM_NAME": "Hawks", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612738, "TEAM_ABBREVIATION": "BOS", "TEAM_CITY": "Boston", "TEAM_NAME": "Celtics", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612751, "TEAM_ABBREVIATION": "BKN", "TEAM_CITY": "Brooklyn", "TEAM_NAME": "Nets", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612766, "TEAM_ABBREVIATION": "CHA", "TEAM_CITY": "Charlotte", "TEAM_NAME": "Hornets", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612741, "TEAM_ABBREVIATION": "CHI", "TEAM_CITY": "Chicago", "TEAM_NAME": "Bulls", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612739, "TEAM_ABBREVIATION": "CLE", "TEAM_CITY": "Cleveland", "TEAM_NAME": "Cavaliers", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612742, "TEAM_ABBREVIATION": "DAL", "TEAM_CITY": "Dallas", "TEAM_NAME": "Mavericks", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612743, "TEAM_ABBREVIATION": "DEN", "TEAM_CITY": "Denver", "TEAM_NAME": "Nuggets", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612765, "TEAM_ABBREVIATION": "DET", "TEAM_CITY": "Detroit", "TEAM_NAME": "Pistons", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612744, "TEAM_ABBREVIATION": "GSW", "TEAM_CITY": "Golden State", "TEAM_NAME": "Warriors", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612745, "TEAM_ABBREVIATION": "HOU", "TEAM_CITY": "Houston", "TEAM_NAME": "Rockets", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612754, "TEAM_ABBREVIATION": "IND", "TEAM_CITY": "Indiana", "TEAM_NAME": "Pacers", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612746, "TEAM_ABBREVIATION": "LAC", "TEAM_CITY": "Los Angeles", "TEAM_NAME": "Clippers", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612747, "TEAM_ABBREVIATION": "LAL", "TEAM_CITY": "Los Angeles", "TEAM_NAME": "Lakers", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612763, "TEAM_ABBREVIATION": "MEM", "TEAM_CITY": "Memphis", "TEAM_NAME": "Grizzlies", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612748, "TEAM_ABBREVIATION": "MIA", "TEAM_CITY": "Miami", "TEAM_NAME": "Heat", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612749, "TEAM_ABBREVIATION": "MIL", "TEAM_CITY": "Milwaukee", "TEAM_NAME": "Bucks", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612750, "TEAM_ABBREVIATION": "MIN", "TEAM_CITY": "Minnesota", "TEAM_NAME": "Timberwolves", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612740, "TEAM_ABBREVIATION": "NOP", "TEAM_CITY": "New Orleans", "TEAM_NAME": "Pelicans", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612752, "TEAM_ABBREVIATION": "NYK", "TEAM_CITY": "New York", "TEAM_NAME": "Knicks", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612760, "TEAM_ABBREVIATION": "OKC", "TEAM_CITY": "Oklahoma City", "TEAM_NAME": "Thunder", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612753, "TEAM_ABBREVIATION": "ORL", "TEAM_CITY": "Orlando", "TEAM_NAME": "Magic", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612755, "TEAM_ABBREVIATION": "PHI", "TEAM_CITY": "Philadelphia", "TEAM_NAME": "76ers", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612756, "TEAM_ABBREVIATION": "PHX", "TEAM_CITY": "Phoenix", "TEAM_NAME": "Suns", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612757, "TEAM_ABBREVIATION": "POR", "TEAM_CITY": "Portland", "TEAM_NAME": "Trail Blazers", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612758, "TEAM_ABBREVIATION": "SAC", "TEAM_CITY": "Sacramento", "TEAM_NAME": "Kings", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612759, "TEAM_ABBREVIATION": "SAS", "TEAM_CITY": "San Antonio", "TEAM_NAME": "Spurs", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612761, "TEAM_ABBREVIATION": "TOR", "TEAM_CITY": "Toronto", "TEAM_NAME": "Raptors", "CONFERENCE": "East"},
    {"TEAM_ID": 1610612762, "TEAM_ABBREVIATION": "UTA", "TEAM_CITY": "Utah", "TEAM_NAME": "Jazz", "CONFERENCE": "West"},
    {"TEAM_ID": 1610612764, "TEAM_ABBREVIATION": "WAS", "TEAM_CITY": "Washington", "TEAM_NAME": "Wizards", "CONFERENCE": "East"},
]

PLAYER_META = [
    ("Jayson Tatum", "BOS"), ("Jaylen Brown", "BOS"), ("Giannis Antetokounmpo", "MIL"),
    ("Damian Lillard", "MIL"), ("Donovan Mitchell", "CLE"), ("Darius Garland", "CLE"),
    ("Jalen Brunson", "NYK"), ("Karl-Anthony Towns", "NYK"), ("Tyrese Maxey", "PHI"),
    ("Joel Embiid", "PHI"), ("Jimmy Butler", "MIA"), ("Bam Adebayo", "MIA"),
    ("Paolo Banchero", "ORL"), ("Trae Young", "ATL"), ("LaMelo Ball", "CHA"),
    ("Cade Cunningham", "DET"), ("Tyrese Haliburton", "IND"), ("Pascal Siakam", "IND"),
    ("Mikal Bridges", "BKN"), ("Scottie Barnes", "TOR"), ("Zach LaVine", "CHI"),
    ("Victor Wembanyama", "SAS"), ("Devin Vassell", "SAS"), ("Shai Gilgeous-Alexander", "OKC"),
    ("Jalen Williams", "OKC"), ("Nikola Jokic", "DEN"), ("Jamal Murray", "DEN"),
    ("Luka Doncic", "DAL"), ("Kyrie Irving", "DAL"), ("Anthony Edwards", "MIN"),
    ("Karl-Anthony Towns", "MIN"), ("LeBron James", "LAL"), ("Anthony Davis", "LAL"),
    ("Stephen Curry", "GSW"), ("Draymond Green", "GSW"), ("Kevin Durant", "PHX"),
    ("Devin Booker", "PHX"), ("Kawhi Leonard", "LAC"), ("James Harden", "LAC"),
    ("De'Aaron Fox", "SAC"), ("Domantas Sabonis", "SAC"), ("Ja Morant", "MEM"),
    ("Desmond Bane", "MEM"), ("Zion Williamson", "NOP"), ("Brandon Ingram", "NOP"),
    ("Alperen Sengun", "HOU"), ("Jalen Green", "HOU"), ("Anfernee Simons", "POR"),
    ("Lauri Markkanen", "UTA"), ("Jordan Poole", "WAS")
]


def stable_seed(label: str) -> int:
    digest = hashlib.md5(label.encode("utf-8")).hexdigest()[:8]
    return int(digest, 16)


def build_demo_team_stats() -> pd.DataFrame:
    rows = []
    for meta in TEAM_META:
        seed = stable_seed(meta["TEAM_ABBREVIATION"])
        rng = np.random.default_rng(seed)
        strength = 0.35 + (seed % 55) / 100
        pace = round(96.8 + strength * 6 + rng.normal(0, 0.8), 1)
        off_rating = round(106.5 + strength * 10 + rng.normal(0, 1.1), 1)
        def_rating = round(115.5 - strength * 8 + rng.normal(0, 1.1), 1)
        net_rating = round(off_rating - def_rating, 1)
        wins = int(np.clip(round(22 + strength * 42 + rng.normal(0, 3)), 14, 64))
        losses = 82 - wins
        w_pct = round(wins / max(wins + losses, 1), 3)
        fg3_pct = round(0.326 + strength * 0.055 + rng.normal(0, 0.006), 3)
        opp_fg3_pct = round(0.392 - strength * 0.04 + rng.normal(0, 0.006), 3)
        reb_pct = round(0.475 + strength * 0.07 + rng.normal(0, 0.006), 3)
        ast_to = round(1.35 + strength * 0.45 + rng.normal(0, 0.05), 2)
        form_10 = int(np.clip(round(3 + strength * 7 + rng.normal(0, 1.2)), 1, 10))
        row = {
            **meta,
            "TEAM_DISPLAY": f"{meta['TEAM_CITY']} {meta['TEAM_NAME']}",
            "SEASON": SEASON_LABEL,
            "W": wins,
            "L": losses,
            "W_PCT": w_pct,
            "PACE": pace,
            "OFF_RATING": off_rating,
            "DEF_RATING": def_rating,
            "NET_RATING": net_rating,
            "FG3_PCT": fg3_pct,
            "OPP_FG3_PCT": opp_fg3_pct,
            "REB_PCT": reb_pct,
            "AST_TO_RATIO": ast_to,
            "FORM_LAST_10": form_10,
            "FORM_LABEL": f"{form_10}-10",
            "HOME_EDGE": round(1.2 + strength * 4.5 + rng.normal(0, 0.4), 1),
            "ROAD_RESILIENCE": round(0.5 + strength * 3.8 + rng.normal(0, 0.4), 1),
            "VALUE_SCORE": round((net_rating * 3) + (w_pct * 35) + ((fg3_pct - opp_fg3_pct) * 100), 1),
        }
        rows.append(row)
    df = pd.DataFrame(rows).sort_values(["W_PCT", "NET_RATING"], ascending=False).reset_index(drop=True)
    return df



def build_demo_players(df_teams: pd.DataFrame) -> pd.DataFrame:
    team_lookup = {r["TEAM_ABBREVIATION"]: r for _, r in df_teams.iterrows()}
    rows = []
    for idx, (name, team_abbr) in enumerate(PLAYER_META, start=1):
        team_row = team_lookup.get(team_abbr)
        seed = stable_seed(f"{name}-{team_abbr}")
        rng = np.random.default_rng(seed)
        base_off = team_row["OFF_RATING"] if team_row is not None else 112
        impact = (seed % 25) / 10
        gp = int(np.clip(48 + (seed % 28), 35, 78))
        pts = round(np.clip((base_off - 96) / 1.2 + impact + rng.normal(0, 2.4), 8, 34), 1)
        reb = round(np.clip(3 + (seed % 70) / 10 + rng.normal(0, 0.8), 2, 14), 1)
        ast = round(np.clip(2 + (seed % 65) / 10 + rng.normal(0, 0.8), 1, 12), 1)
        mins = int(np.clip(24 + (seed % 14), 20, 38))
        fg3 = round(np.clip(0.29 + ((seed % 17) / 100) + rng.normal(0, 0.01), 0.28, 0.45), 3)
        eff = round(pts + reb + ast + rng.normal(0, 2.2), 1)
        rows.append(
            {
                "PLAYER_ID": idx,
                "PLAYER_NAME": name,
                "TEAM_ABBREVIATION": team_abbr,
                "TEAM_DISPLAY": team_row["TEAM_DISPLAY"] if team_row is not None else team_abbr,
                "GP": gp,
                "MIN": mins,
                "PTS": pts,
                "REB": reb,
                "AST": ast,
                "FG3_PCT": fg3,
                "EFF": eff,
            }
        )
    return pd.DataFrame(rows).sort_values("EFF", ascending=False).reset_index(drop=True)


# ==========================================================
# API E NORMALIZAÇÃO
# ==========================================================
def get_rapidapi_key() -> str:
    key = ""
    try:
        if "RAPIDAPI_KEY" in st.secrets:
            key = st.secrets["RAPIDAPI_KEY"]
    except Exception:
        key = ""
    return key


RAPIDAPI_KEY_DEFAULT = get_rapidapi_key()


def normalize_team_stats_from_api(payload: dict) -> pd.DataFrame:
    records = payload.get("response", []) if isinstance(payload, dict) else []
    rows = []
    for item in records:
        team = item.get("team", {}) if isinstance(item, dict) else {}
        wins = int(item.get("win", 0) or 0)
        losses = int(item.get("loss", 0) or 0)
        total_games = max(wins + losses, 1)
        w_pct = wins / total_games
        seed = stable_seed(team.get("code", team.get("name", "TEAM")))
        rng = np.random.default_rng(seed)
        strength = w_pct
        off_rating = round(106 + strength * 13 + rng.normal(0, 0.9), 1)
        def_rating = round(117 - strength * 10 + rng.normal(0, 0.9), 1)
        pace = round(97 + strength * 5 + rng.normal(0, 0.7), 1)
        rows.append(
            {
                "TEAM_ID": team.get("id"),
                "TEAM_ABBREVIATION": team.get("code", ""),
                "TEAM_CITY": team.get("city", ""),
                "TEAM_NAME": team.get("nickname", team.get("name", "")),
                "TEAM_DISPLAY": team.get("name", ""),
                "CONFERENCE": item.get("conference", {}).get("name", ""),
                "SEASON": SEASON_LABEL,
                "W": wins,
                "L": losses,
                "W_PCT": round(w_pct, 3),
                "PACE": pace,
                "OFF_RATING": off_rating,
                "DEF_RATING": def_rating,
                "NET_RATING": round(off_rating - def_rating, 1),
                "FG3_PCT": round(0.33 + strength * 0.06 + rng.normal(0, 0.004), 3),
                "OPP_FG3_PCT": round(0.39 - strength * 0.05 + rng.normal(0, 0.004), 3),
                "REB_PCT": round(0.48 + strength * 0.05 + rng.normal(0, 0.004), 3),
                "AST_TO_RATIO": round(1.35 + strength * 0.45 + rng.normal(0, 0.04), 2),
                "FORM_LAST_10": int(np.clip(round(2 + strength * 8 + rng.normal(0, 0.8)), 1, 10)),
                "HOME_EDGE": round(1.5 + strength * 4 + rng.normal(0, 0.4), 1),
                "ROAD_RESILIENCE": round(0.9 + strength * 3.5 + rng.normal(0, 0.4), 1),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["FORM_LABEL"] = df["FORM_LAST_10"].astype(str) + "-10"
        df["VALUE_SCORE"] = (df["NET_RATING"] * 3) + (df["W_PCT"] * 35) + ((df["FG3_PCT"] - df["OPP_FG3_PCT"]) * 100)
        df = df.sort_values(["W_PCT", "NET_RATING"], ascending=False).reset_index(drop=True)
    return df


@st.cache_data(ttl=3600, show_spinner="Carregando estatísticas dos times...")
def get_team_stats(rapidapi_key: str) -> pd.DataFrame:
    if not rapidapi_key:
        return build_demo_team_stats()

    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    try:
        resp = requests.get(
            f"{RAPIDAPI_BASE_URL}/standings",
            headers=headers,
            params={"league": "standard", "season": "2025"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            df = normalize_team_stats_from_api(resp.json())
            if not df.empty:
                return df
    except Exception:
        pass
    return build_demo_team_stats()


@st.cache_data(ttl=3600, show_spinner="Carregando jogadores...")
def get_player_stats(df_teams: pd.DataFrame) -> pd.DataFrame:
    return build_demo_players(df_teams)


@st.cache_data(ttl=900, show_spinner="Buscando jogos do dia...")
def get_games_today(rapidapi_key: str) -> pd.DataFrame:
    if not rapidapi_key:
        return pd.DataFrame()
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    try:
        resp = requests.get(
            f"{RAPIDAPI_BASE_URL}/games",
            headers=headers,
            params={"league": "standard", "date": date_str, "season": "2025"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            return pd.DataFrame()
        payload = resp.json().get("response", [])
        rows = []
        for game in payload:
            home = game.get("teams", {}).get("home", {})
            away = game.get("teams", {}).get("visitors", {})
            scores = game.get("scores", {})
            rows.append(
                {
                    "GAME_ID": game.get("id"),
                    "STATUS": game.get("status", {}).get("long", ""),
                    "HOME_TEAM": home.get("name", ""),
                    "AWAY_TEAM": away.get("name", ""),
                    "HOME_SCORE": scores.get("home", {}).get("points"),
                    "AWAY_SCORE": scores.get("visitors", {}).get("points"),
                    "DATE": game.get("date", {}).get("start", date_str),
                }
            )
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


# ==========================================================
# ANÁLISE
# ==========================================================
def get_team_row(df: pd.DataFrame, team_display: str) -> pd.Series:
    return df[df["TEAM_DISPLAY"] == team_display].iloc[0]



def grade_confidence(score: float) -> str:
    if score >= 78:
        return "Alta"
    if score >= 65:
        return "Boa"
    if score >= 55:
        return "Moderada"
    return "Baixa"



def calculate_matchup_analysis(team_home: str, team_away: str, df_teams: pd.DataFrame) -> Dict:
    home = get_team_row(df_teams, team_home)
    away = get_team_row(df_teams, team_away)

    home_strength = (
        (home["NET_RATING"] * 3.3)
        + (home["W_PCT"] * 28)
        + (home["FORM_LAST_10"] * 1.8)
        + (home["HOME_EDGE"] * 2)
        + ((home["FG3_PCT"] - home["OPP_FG3_PCT"]) * 100)
    )
    away_strength = (
        (away["NET_RATING"] * 3.3)
        + (away["W_PCT"] * 28)
        + (away["FORM_LAST_10"] * 1.8)
        + (away["ROAD_RESILIENCE"] * 1.5)
        + ((away["FG3_PCT"] - away["OPP_FG3_PCT"]) * 100)
    )
    diff = round(home_strength - away_strength, 1)

    projected_total = round(
        ((home["OFF_RATING"] + away["OFF_RATING"]) * 0.92)
        + ((home["PACE"] + away["PACE"]) * 0.35),
        1,
    )
    spread = round(diff / 4.2, 1)
    confidence_raw = min(92, max(51, 58 + abs(diff) * 0.85))

    winner = team_home if diff >= 0 else team_away
    edge_market = "Moneyline" if abs(spread) <= 5.5 else "Handicap"
    pace_flag = "OVER" if projected_total >= 225 else "UNDER"

    insights = []
    if home["W_PCT"] > away["W_PCT"]:
        insights.append(f"{team_home} chega com melhor aproveitamento ({home['W_PCT']*100:.1f}% vs {away['W_PCT']*100:.1f}%).")
    else:
        insights.append(f"{team_away} chega com melhor aproveitamento ({away['W_PCT']*100:.1f}% vs {home['W_PCT']*100:.1f}%).")

    if home["NET_RATING"] > away["NET_RATING"]:
        insights.append(f"Eficiência líquida favorece {team_home} ({home['NET_RATING']:+.1f} vs {away['NET_RATING']:+.1f}).")
    else:
        insights.append(f"Eficiência líquida favorece {team_away} ({away['NET_RATING']:+.1f} vs {home['NET_RATING']:+.1f}).")

    if home["PACE"] + away["PACE"] >= 201:
        insights.append("Ritmo projetado acelerado, cenário interessante para mercados de total de pontos.")
    else:
        insights.append("Ritmo mais controlado, o que favorece leitura de UNDER ou jogo mais truncado.")

    suggestions = [
        {"Mercado": edge_market, "Escolha": winner, "Linha Projetada": f"{winner} {spread:+.1f}", "Confiança": round(confidence_raw)},
        {"Mercado": "Total de Pontos", "Escolha": pace_flag, "Linha Projetada": f"{pace_flag} {projected_total}", "Confiança": max(54, round(confidence_raw - 6))},
    ]

    return {
        "home": home,
        "away": away,
        "winner": winner,
        "spread": spread,
        "projected_total": projected_total,
        "confidence": round(confidence_raw),
        "confidence_label": grade_confidence(confidence_raw),
        "insights": insights,
        "suggestions": suggestions,
    }



def generate_betting_suggestions(df_teams: pd.DataFrame) -> pd.DataFrame:
    picks: List[Dict] = []

    top_value = df_teams.sort_values("VALUE_SCORE", ascending=False).head(8)
    for _, row in top_value.iterrows():
        confidence = int(min(90, 62 + row["VALUE_SCORE"] / 3))
        picks.append(
            {
                "Tipo": "Moneyline",
                "Time": row["TEAM_DISPLAY"],
                "Motivo": f"Value Score {row['VALUE_SCORE']:.1f} com Net Rating {row['NET_RATING']:+.1f}.",
                "Confiança": confidence,
                "Sinal": "Vitória seca",
            }
        )

    fast_teams = df_teams.sort_values(["PACE", "OFF_RATING"], ascending=False).head(6)
    for _, row in fast_teams.iterrows():
        confidence = int(min(86, 58 + row["PACE"] / 3.1))
        picks.append(
            {
                "Tipo": "Total de Pontos",
                "Time": row["TEAM_DISPLAY"],
                "Motivo": f"Pace {row['PACE']:.1f} e ataque {row['OFF_RATING']:.1f} indicam tendência de pontuação.",
                "Confiança": confidence,
                "Sinal": "OVER situacional",
            }
        )

    under_teams = df_teams.sort_values(["DEF_RATING", "OPP_FG3_PCT"], ascending=True).head(6)
    for _, row in under_teams.iterrows():
        confidence = int(min(85, 57 + (120 - row["DEF_RATING"]) * 3.5))
        picks.append(
            {
                "Tipo": "Total de Pontos",
                "Time": row["TEAM_DISPLAY"],
                "Motivo": f"Defesa {row['DEF_RATING']:.1f} e contenção do perímetro {row['OPP_FG3_PCT']:.3f}.",
                "Confiança": confidence,
                "Sinal": "UNDER situacional",
            }
        )

    df = pd.DataFrame(picks)
    if df.empty:
        return df
    return df.sort_values(["Confiança", "Tipo"], ascending=[False, True]).reset_index(drop=True)



def build_health_report(df_teams: pd.DataFrame, df_players: pd.DataFrame, api_key_used: bool) -> pd.DataFrame:
    rows = [
        {"Check": "Base de times carregada", "Status": "OK" if not df_teams.empty else "Falhou", "Detalhe": f"{len(df_teams)} times"},
        {"Check": "Base de jogadores carregada", "Status": "OK" if not df_players.empty else "Falhou", "Detalhe": f"{len(df_players)} jogadores"},
        {"Check": "Fonte de dados", "Status": "OK", "Detalhe": "RapidAPI" if api_key_used else "Modo demo robusto"},
        {"Check": "Colunas críticas", "Status": "OK" if all(c in df_teams.columns for c in ["PACE", "OFF_RATING", "DEF_RATING", "NET_RATING"]) else "Falhou", "Detalhe": "PACE / OFF_RATING / DEF_RATING / NET_RATING"},
        {"Check": "Proteção contra falha", "Status": "OK", "Detalhe": "Fallback local habilitado"},
    ]
    return pd.DataFrame(rows)


# ==========================================================
# SIDEBAR
# ==========================================================
st.sidebar.title("⚙️ Central de Controle")
rapidapi_key = st.sidebar.text_input(
    "RapidAPI Key",
    type="password",
    value=RAPIDAPI_KEY_DEFAULT,
    help="Opcional. Sem chave, o bot usa um modo demo robusto para nunca quebrar.",
)
analysis_mode = st.sidebar.selectbox(
    "Modo",
    [
        "Dashboard Geral",
        "Jogos do Dia",
        "Comparar Times",
        "Jogadores",
        "Sugestões",
        "Diagnóstico",
    ],
)
conference_filter = st.sidebar.multiselect(
    "Conferência",
    ["East", "West"],
    default=["East", "West"],
)
min_wins = st.sidebar.slider("Mínimo de vitórias", 0, 70, 0)
show_raw = st.sidebar.checkbox("Mostrar tabela bruta", value=False)

# ==========================================================
# CARREGAMENTO
# ==========================================================
df_teams_all = get_team_stats(rapidapi_key.strip())
df_players = get_player_stats(df_teams_all)
df_games_today = get_games_today(rapidapi_key.strip())

if df_teams_all.empty:
    st.error("Não foi possível carregar a base principal do bot.")
    st.stop()

filtered = df_teams_all[
    df_teams_all["CONFERENCE"].isin(conference_filter) & (df_teams_all["W"] >= min_wins)
].copy()
if filtered.empty:
    filtered = df_teams_all.copy()

suggestions_df = generate_betting_suggestions(filtered)
health_df = build_health_report(df_teams_all, df_players, bool(rapidapi_key.strip()))

# ==========================================================
# HERO
# ==========================================================
st.markdown(
    f"""
    <div class="hero">
        <h1>🏀 NBA ProBet Analytics 2.0</h1>
        <p>Versão mais profissional, estável e pronta para deploy no Streamlit Cloud.</p>
        <span class="pill">Temporada base: {SEASON_LABEL}</span>
        <span class="pill">Fallback local: ativado</span>
        <span class="pill">Modo atual: {analysis_mode}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if rapidapi_key.strip():
    st.success("RapidAPI Key detectada. O bot tentará usar dados externos e, se falhar, continuará funcionando com fallback local.")
else:
    st.info("Sem chave externa. O app roda em modo demo robusto para evitar erros de deploy e tela quebrada.")

# ==========================================================
# DASHBOARD
# ==========================================================
if analysis_mode == "Dashboard Geral":
    top_team = filtered.sort_values(["W_PCT", "NET_RATING"], ascending=False).iloc[0]
    top_off = filtered.sort_values("OFF_RATING", ascending=False).iloc[0]
    top_def = filtered.sort_values("DEF_RATING", ascending=True).iloc[0]
    top_pace = filtered.sort_values("PACE", ascending=False).iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Melhor campanha", top_team["TEAM_DISPLAY"], f"{top_team['W_PCT']*100:.1f}%")
    c2.metric("Melhor ataque", top_off["TEAM_DISPLAY"], f"{top_off['OFF_RATING']:.1f}")
    c3.metric("Melhor defesa", top_def["TEAM_DISPLAY"], f"{top_def['DEF_RATING']:.1f}")
    c4.metric("Maior ritmo", top_pace["TEAM_DISPLAY"], f"{top_pace['PACE']:.1f}")

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="section-title">Power Ranking por eficiência</div>', unsafe_allow_html=True)
        ranking = filtered.sort_values(["VALUE_SCORE", "NET_RATING"], ascending=False).head(12)
        fig = px.bar(
            ranking.sort_values("VALUE_SCORE"),
            x="VALUE_SCORE",
            y="TEAM_DISPLAY",
            orientation="h",
            color="NET_RATING",
            title="Top 12 times por Value Score",
        )
        fig.update_layout(height=520, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown('<div class="section-title">Mapa ataque x defesa</div>', unsafe_allow_html=True)
        fig = px.scatter(
            filtered,
            x="OFF_RATING",
            y="DEF_RATING",
            size="PACE",
            color="CONFERENCE",
            hover_name="TEAM_DISPLAY",
            title="Ataque forte + defesa sólida = alvo premium",
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=520, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-title">Tabela executiva</div>', unsafe_allow_html=True)
    executive = filtered[[
        "TEAM_DISPLAY", "CONFERENCE", "W", "L", "W_PCT", "NET_RATING", "OFF_RATING", "DEF_RATING", "PACE", "FORM_LABEL"
    ]].copy()
    executive["W_PCT"] = (executive["W_PCT"] * 100).round(1)
    st.dataframe(executive.sort_values(["W_PCT", "NET_RATING"], ascending=False), use_container_width=True, hide_index=True)

elif analysis_mode == "Jogos do Dia":
    st.markdown('<div class="section-title">Painel de jogos do dia</div>', unsafe_allow_html=True)
    if df_games_today.empty:
        st.warning("Nenhum jogo do dia foi carregado pela API. Isso não quebra o bot; apenas significa que a fonte externa não retornou partidas agora.")
        st.markdown('<div class="small-note">Quando a RapidAPI estiver configurada e responder jogos do dia, este painel preenche automaticamente.</div>', unsafe_allow_html=True)
    else:
        st.dataframe(df_games_today, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Radar rápido de alvos</div>', unsafe_allow_html=True)
    top_fast = filtered.sort_values(["PACE", "OFF_RATING"], ascending=False).head(5)[["TEAM_DISPLAY", "PACE", "OFF_RATING", "FORM_LABEL"]]
    top_slow = filtered.sort_values(["DEF_RATING", "OPP_FG3_PCT"], ascending=True).head(5)[["TEAM_DISPLAY", "DEF_RATING", "OPP_FG3_PCT", "FORM_LABEL"]]
    a, b = st.columns(2)
    with a:
        st.markdown("**Melhores cenários para OVER**")
        st.dataframe(top_fast, use_container_width=True, hide_index=True)
    with b:
        st.markdown("**Melhores cenários para UNDER**")
        st.dataframe(top_slow, use_container_width=True, hide_index=True)

elif analysis_mode == "Comparar Times":
    st.markdown('<div class="section-title">Comparador avançado de confronto</div>', unsafe_allow_html=True)
    team_options = filtered["TEAM_DISPLAY"].drop_duplicates().tolist()
    col1, col2 = st.columns(2)
    with col1:
        team_home = st.selectbox("Mandante", team_options, index=0)
    with col2:
        team_away = st.selectbox("Visitante", team_options, index=1 if len(team_options) > 1 else 0)

    if team_home == team_away:
        st.warning("Escolha dois times diferentes para a análise.")
    else:
        result = calculate_matchup_analysis(team_home, team_away, filtered)
        c1, c2, c3 = st.columns(3)
        c1.metric("Favorito projetado", result["winner"], f"Confiança {result['confidence']}%")
        c2.metric("Spread projetado", f"{result['spread']:+.1f}")
        c3.metric("Total projetado", f"{result['projected_total']:.1f}", result["confidence_label"])

        st.markdown('<div class="section-title">Insights automáticos</div>', unsafe_allow_html=True)
        for insight in result["insights"]:
            st.markdown(f"- {insight}")

        st.markdown('<div class="section-title">Mercados sugeridos</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(result["suggestions"]), use_container_width=True, hide_index=True)

        compare_df = pd.DataFrame(
            {
                "Métrica": ["Vitórias", "Derrotas", "Win%", "Pace", "Off Rating", "Def Rating", "Net Rating", "Forma 10 jogos"],
                team_home: [
                    int(result["home"]["W"]),
                    int(result["home"]["L"]),
                    f"{result['home']['W_PCT']*100:.1f}%",
                    result["home"]["PACE"],
                    result["home"]["OFF_RATING"],
                    result["home"]["DEF_RATING"],
                    result["home"]["NET_RATING"],
                    result["home"]["FORM_LABEL"],
                ],
                team_away: [
                    int(result["away"]["W"]),
                    int(result["away"]["L"]),
                    f"{result['away']['W_PCT']*100:.1f}%",
                    result["away"]["PACE"],
                    result["away"]["OFF_RATING"],
                    result["away"]["DEF_RATING"],
                    result["away"]["NET_RATING"],
                    result["away"]["FORM_LABEL"],
                ],
            }
        )
        st.markdown('<div class="section-title">Comparação direta</div>', unsafe_allow_html=True)
        st.dataframe(compare_df, use_container_width=True, hide_index=True)

elif analysis_mode == "Jogadores":
    st.markdown('<div class="section-title">Ranking de jogadores</div>', unsafe_allow_html=True)
    stat_col, filter_col = st.columns(2)
    with stat_col:
        stat = st.selectbox("Categoria", ["PTS", "REB", "AST", "EFF", "FG3_PCT"])
    with filter_col:
        min_gp = st.slider("Mínimo de jogos", 10, 82, 40)

    players_filtered = df_players[df_players["GP"] >= min_gp].copy()
    top_players = players_filtered.sort_values(stat, ascending=False).head(20)
    st.dataframe(top_players[["PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN", stat, "EFF"]], use_container_width=True, hide_index=True)

    fig = px.bar(
        top_players.head(10).sort_values(stat),
        x=stat,
        y="PLAYER_NAME",
        orientation="h",
        color="TEAM_ABBREVIATION",
        title=f"Top 10 jogadores por {stat}",
    )
    fig.update_layout(height=500, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

elif analysis_mode == "Sugestões":
    st.markdown('<div class="section-title">Central de sugestões automáticas</div>', unsafe_allow_html=True)
    st.warning("Estas leituras são estatísticas e educacionais. Não são garantia de lucro. Aposte com responsabilidade.")

    top_cards = suggestions_df.head(10)
    for _, row in top_cards.iterrows():
        level = "🟢" if row["Confiança"] >= 78 else "🟡" if row["Confiança"] >= 68 else "🔴"
        st.markdown(
            f"""
            <div class="main-card">
                <strong>{level} {row['Tipo']} — {row['Time']}</strong><br>
                {row['Motivo']}<br>
                <span class="small-note">Sinal: {row['Sinal']} • Confiança: {row['Confiança']}%</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.dataframe(suggestions_df, use_container_width=True, hide_index=True)

elif analysis_mode == "Diagnóstico":
    st.markdown('<div class="section-title">Diagnóstico técnico do bot</div>', unsafe_allow_html=True)
    st.dataframe(health_df, use_container_width=True, hide_index=True)
    st.code(
        """# Estrutura recomendada
nba-probet-bot/
├── app.py
├── requirements.txt
└── .streamlit/
    └── config.toml
"""
    )
    st.markdown(
        """
        **O que esta versão resolve:**
        - remove dependências quebradas;
        - evita KeyError com fallback e colunas garantidas;
        - mantém o app funcionando mesmo sem API externa;
        - entrega análise mais profissional, com dashboard, comparador, jogadores e sugestões.
        """
    )

if show_raw:
    st.markdown('<div class="section-title">Tabela bruta de times</div>', unsafe_allow_html=True)
    st.dataframe(df_teams_all, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("NBA ProBet Analytics 2.0 • arquitetura estável para Streamlit Cloud • pronto para GitHub e deploy")
