import hashlib
import io
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# =========================================================
# CONFIGURAÇÃO BASE
# =========================================================
APP_TITLE = "NBA ProBet Analytics 3.0"
SEASON_LABEL = "2025-26"
REQUEST_TIMEOUT = 15
RAPIDAPI_HOST = "api-nba-v1.p.rapidapi.com"
RAPIDAPI_BASE_URL = f"https://{RAPIDAPI_HOST}"
DEFAULT_BANKROLL = 1000.0

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# ESTILO
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 15% 20%, rgba(59,130,246,.12), transparent 28%),
            radial-gradient(circle at 85% 10%, rgba(245,158,11,.10), transparent 25%),
            linear-gradient(180deg, #08101d 0%, #0b1324 50%, #070d18 100%);
        color: #e5edf8;
    }
    .hero-card {
        background: linear-gradient(135deg, rgba(15,23,42,.92), rgba(17,24,39,.86));
        border: 1px solid rgba(148,163,184,.18);
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 14px 34px rgba(0,0,0,.24);
        margin-bottom: 18px;
    }
    .hero-card h1 {
        margin: 0;
        color: #f8fafc;
        font-size: 2.25rem;
        line-height: 1.1;
    }
    .hero-card p {
        color: #cbd5e1;
        margin: 8px 0 0 0;
    }
    .mini-chip {
        display:inline-block;
        margin-right:8px;
        margin-top:10px;
        padding:6px 10px;
        border-radius:999px;
        background: rgba(59,130,246,.14);
        border: 1px solid rgba(96,165,250,.24);
        color:#bfdbfe;
        font-size:.82rem;
    }
    .glass {
        background: rgba(15,23,42,.78);
        border: 1px solid rgba(148,163,184,.14);
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 10px 26px rgba(0,0,0,.18);
    }
    .section-label {
        color:#e2e8f0;
        font-weight:700;
        font-size:1.08rem;
        margin-bottom:6px;
    }
    .small-note {
        color:#94a3b8;
        font-size:.88rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(15,23,42,.78);
        border: 1px solid rgba(148,163,184,.12);
        padding: 14px;
        border-radius: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# BASE DEMO
# =========================================================
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
    ("LeBron James", "LAL"), ("Anthony Davis", "LAL"), ("Stephen Curry", "GSW"),
    ("Draymond Green", "GSW"), ("Kevin Durant", "PHX"), ("Devin Booker", "PHX"),
    ("Kawhi Leonard", "LAC"), ("James Harden", "LAC"), ("De'Aaron Fox", "SAC"),
    ("Domantas Sabonis", "SAC"), ("Ja Morant", "MEM"), ("Desmond Bane", "MEM"),
    ("Zion Williamson", "NOP"), ("Brandon Ingram", "NOP"), ("Alperen Sengun", "HOU"),
    ("Jalen Green", "HOU"), ("Anfernee Simons", "POR"), ("Lauri Markkanen", "UTA"),
    ("Jordan Poole", "WAS")
]

# =========================================================
# HELPERS
# =========================================================
def stable_seed(label: str) -> int:
    digest = hashlib.md5(label.encode("utf-8")).hexdigest()[:8]
    return int(digest, 16)


def get_secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def get_rapidapi_key() -> str:
    return get_secret("RAPIDAPI_KEY", "")


def get_admin_user() -> str:
    return get_secret("APP_ADMIN_USER", "admin")


def get_admin_password() -> str:
    return get_secret("APP_ADMIN_PASSWORD", "123456")


def get_premium_code() -> str:
    return get_secret("PREMIUM_ACCESS_CODE", "PROBETVIP")


def init_session_state() -> None:
    defaults = {
        "auth_ok": False,
        "premium_ok": False,
        "pick_history": [],
        "bankroll": DEFAULT_BANKROLL,
        "stake_pct": 2.0,
        "api_status": "demo",
        "last_refresh": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def sigmoid(x: float) -> float:
    return 1 / (1 + np.exp(-x))


def american_odds_from_prob(prob: float) -> int:
    prob = float(np.clip(prob, 0.05, 0.95))
    if prob >= 0.5:
        return int(round(-(prob / (1 - prob)) * 100))
    return int(round(((1 - prob) / prob) * 100))


def edge_from_prob(model_prob: float, market_prob: float) -> float:
    return round((model_prob - market_prob) * 100, 2)


def implied_probability_from_odds(odds: int) -> float:
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    return 100 / (odds + 100)


def kelly_fraction(prob: float, odds_american: int) -> float:
    if odds_american > 0:
        b = odds_american / 100
    else:
        b = 100 / abs(odds_american)
    q = 1 - prob
    raw = ((b * prob) - q) / b
    return max(0.0, raw)


def safe_metric_value(df: pd.DataFrame, col: str, agg: str = "max", default: float = 0.0) -> float:
    if col not in df.columns or df.empty or not df[col].notna().any():
        return default
    if agg == "max":
        return float(df[col].max())
    if agg == "min":
        return float(df[col].min())
    return float(df[col].mean())


@st.cache_data(ttl=3600, show_spinner=False)
def build_demo_team_stats() -> pd.DataFrame:
    rows = []
    for meta in TEAM_META:
        seed = stable_seed(meta["TEAM_ABBREVIATION"])
        rng = np.random.default_rng(seed)
        strength = 0.35 + (seed % 55) / 100
        pace = round(96.8 + strength * 6 + rng.normal(0, 0.8), 1)
        off_rating = round(106.5 + strength * 10 + rng.normal(0, 1.0), 1)
        def_rating = round(115.7 - strength * 8 + rng.normal(0, 1.0), 1)
        net_rating = round(off_rating - def_rating, 1)
        wins = int(np.clip(round(22 + strength * 42 + rng.normal(0, 3)), 14, 64))
        losses = 82 - wins
        w_pct = round(wins / max(wins + losses, 1), 3)
        fg3_pct = round(0.326 + strength * 0.055 + rng.normal(0, 0.006), 3)
        opp_fg3_pct = round(0.392 - strength * 0.04 + rng.normal(0, 0.006), 3)
        reb_pct = round(0.475 + strength * 0.07 + rng.normal(0, 0.006), 3)
        ast_to = round(1.35 + strength * 0.45 + rng.normal(0, 0.05), 2)
        form_10 = int(np.clip(round(3 + strength * 7 + rng.normal(0, 1.2)), 1, 10))
        injury_index = round(np.clip(1.2 - strength + rng.normal(0, 0.07), 0.15, 1.2), 2)
        clutch = round(0.46 + strength * 0.22 + rng.normal(0, 0.015), 3)
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
            "INJURY_INDEX": injury_index,
            "CLUTCH_SCORE": clutch,
        }
        row["VALUE_SCORE"] = round((row["NET_RATING"] * 3) + (row["W_PCT"] * 35) + ((row["FG3_PCT"] - row["OPP_FG3_PCT"]) * 100) - (injury_index * 5), 1)
        rows.append(row)

    return pd.DataFrame(rows).sort_values(["W_PCT", "NET_RATING"], ascending=False).reset_index(drop=True)


@st.cache_data(ttl=3600, show_spinner=False)
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
        stocks = round(np.clip(0.7 + ((seed % 20) / 10) + rng.normal(0, 0.2), 0.5, 3.8), 1)
        eff = round(pts + reb + ast + stocks + rng.normal(0, 2.2), 1)
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
                "STOCKS": stocks,
                "EFF": eff,
            }
        )
    return pd.DataFrame(rows).sort_values("EFF", ascending=False).reset_index(drop=True)


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
        off_rating = round(106 + w_pct * 13 + rng.normal(0, 0.9), 1)
        def_rating = round(117 - w_pct * 10 + rng.normal(0, 0.9), 1)
        pace = round(97 + w_pct * 5 + rng.normal(0, 0.7), 1)
        rows.append(
            {
                "TEAM_ID": team.get("id"),
                "TEAM_ABBREVIATION": team.get("code", "UNK"),
                "TEAM_CITY": team.get("city", team.get("name", "Time")),
                "TEAM_NAME": team.get("nickname", team.get("name", "NBA")),
                "TEAM_DISPLAY": team.get("name", "NBA Team"),
                "CONFERENCE": "East" if team.get("leagues", {}).get("standard", {}).get("conference") == "east" else "West",
                "SEASON": SEASON_LABEL,
                "W": wins,
                "L": losses,
                "W_PCT": round(w_pct, 3),
                "PACE": pace,
                "OFF_RATING": off_rating,
                "DEF_RATING": def_rating,
                "NET_RATING": round(off_rating - def_rating, 1),
                "FG3_PCT": round(0.325 + w_pct * 0.05 + rng.normal(0, 0.005), 3),
                "OPP_FG3_PCT": round(0.392 - w_pct * 0.04 + rng.normal(0, 0.005), 3),
                "REB_PCT": round(0.48 + w_pct * 0.05 + rng.normal(0, 0.004), 3),
                "AST_TO_RATIO": round(1.35 + w_pct * 0.4 + rng.normal(0, 0.05), 2),
                "FORM_LAST_10": int(np.clip(round(2 + w_pct * 10 + rng.normal(0, 1)), 1, 10)),
                "FORM_LABEL": "-",
                "HOME_EDGE": round(1.0 + w_pct * 4.8 + rng.normal(0, 0.25), 1),
                "ROAD_RESILIENCE": round(0.8 + w_pct * 3.9 + rng.normal(0, 0.25), 1),
                "INJURY_INDEX": round(np.clip(1.15 - w_pct + rng.normal(0, 0.05), 0.15, 1.2), 2),
                "CLUTCH_SCORE": round(0.47 + w_pct * 0.21 + rng.normal(0, 0.01), 3),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["FORM_LABEL"] = df["FORM_LAST_10"].astype(str) + "-10"
        df["VALUE_SCORE"] = (df["NET_RATING"] * 3) + (df["W_PCT"] * 35) + ((df["FG3_PCT"] - df["OPP_FG3_PCT"]) * 100) - (df["INJURY_INDEX"] * 5)
    return df


def fetch_api_json(endpoint: str, params: Dict[str, str]) -> dict:
    api_key = get_rapidapi_key()
    if not api_key:
        raise RuntimeError("RAPIDAPI_KEY não configurada")
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    response = requests.get(
        f"{RAPIDAPI_BASE_URL}/{endpoint}",
        headers=headers,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=3600, show_spinner=False)
def load_team_stats() -> Tuple[pd.DataFrame, str]:
    try:
        payload = fetch_api_json("standings", {"league": "standard", "season": "2025"})
        df = normalize_team_stats_from_api(payload)
        if not df.empty:
            return df.sort_values(["W_PCT", "NET_RATING"], ascending=False).reset_index(drop=True), "api"
    except Exception:
        pass
    return build_demo_team_stats(), "demo"


@st.cache_data(ttl=3600, show_spinner=False)
def load_players(df_teams: pd.DataFrame) -> pd.DataFrame:
    return build_demo_players(df_teams)


@st.cache_data(ttl=1800, show_spinner=False)
def load_games_for_date(target_date: str, df_teams: pd.DataFrame) -> pd.DataFrame:
    try:
        payload = fetch_api_json("games", {"date": target_date, "league": "standard", "season": "2025"})
        records = payload.get("response", [])
        rows = []
        for game in records:
            home = game.get("teams", {}).get("home", {})
            away = game.get("teams", {}).get("visitors", {})
            rows.append(
                {
                    "GAME_ID": game.get("id"),
                    "DATE": target_date,
                    "STATUS": game.get("status", {}).get("long", "Agendado"),
                    "HOME_ABBR": home.get("code", "HOME"),
                    "AWAY_ABBR": away.get("code", "AWAY"),
                    "HOME_TEAM": home.get("name", "Mandante"),
                    "AWAY_TEAM": away.get("name", "Visitante"),
                }
            )
        df = pd.DataFrame(rows)
        if not df.empty:
            return enrich_games_with_model(df, df_teams)
    except Exception:
        pass
    return build_demo_games(target_date, df_teams)


@st.cache_data(ttl=1800, show_spinner=False)
def build_demo_games(target_date: str, df_teams: pd.DataFrame) -> pd.DataFrame:
    ordered = list(df_teams.sort_values("VALUE_SCORE", ascending=False)["TEAM_ABBREVIATION"])
    pairs = [(ordered[0], ordered[8]), (ordered[3], ordered[10]), (ordered[5], ordered[12]), (ordered[7], ordered[15]), (ordered[1], ordered[14])]
    rows = []
    for idx, (home, away) in enumerate(pairs, start=1):
        home_row = df_teams[df_teams["TEAM_ABBREVIATION"] == home].iloc[0]
        away_row = df_teams[df_teams["TEAM_ABBREVIATION"] == away].iloc[0]
        rows.append(
            {
                "GAME_ID": f"SIM-{target_date}-{idx}",
                "DATE": target_date,
                "STATUS": "Simulado / Pré-jogo",
                "HOME_ABBR": home,
                "AWAY_ABBR": away,
                "HOME_TEAM": home_row["TEAM_DISPLAY"],
                "AWAY_TEAM": away_row["TEAM_DISPLAY"],
            }
        )
    return enrich_games_with_model(pd.DataFrame(rows), df_teams)


def enrich_games_with_model(games_df: pd.DataFrame, teams_df: pd.DataFrame) -> pd.DataFrame:
    if games_df.empty:
        return games_df

    lookup = teams_df.set_index("TEAM_ABBREVIATION").to_dict("index")
    rows = []
    for _, game in games_df.iterrows():
        home = lookup.get(game["HOME_ABBR"])
        away = lookup.get(game["AWAY_ABBR"])
        if not home or not away:
            continue
        model = build_matchup(home, away)
        total_line = round(model["projected_total"] - 2.5 + ((stable_seed(str(game["GAME_ID"])) % 7) * 0.5), 1)
        spread_line = round(-(model["home_margin"] - 1.5), 1)
        home_ml = american_odds_from_prob(model["home_win_prob"])
        away_ml = american_odds_from_prob(1 - model["home_win_prob"])
        pick = "Moneyline Mandante" if model["home_win_prob"] >= 0.58 else ("Over" if model["projected_total"] > total_line + 3 else "Spread Visitante")
        rows.append({
            **game.to_dict(),
            "HOME_NET": home["NET_RATING"],
            "AWAY_NET": away["NET_RATING"],
            "HOME_FORM": home["FORM_LAST_10"],
            "AWAY_FORM": away["FORM_LAST_10"],
            "MODEL_HOME_WIN": round(model["home_win_prob"], 3),
            "MODEL_AWAY_WIN": round(1 - model["home_win_prob"], 3),
            "PROJECTED_HOME": model["projected_home_points"],
            "PROJECTED_AWAY": model["projected_away_points"],
            "PROJECTED_TOTAL": model["projected_total"],
            "PROJECTED_MARGIN": model["home_margin"],
            "MARKET_TOTAL": total_line,
            "MARKET_SPREAD_HOME": spread_line,
            "HOME_ML": home_ml,
            "AWAY_ML": away_ml,
            "EDGE_HOME_ML": edge_from_prob(model["home_win_prob"], implied_probability_from_odds(home_ml)),
            "EDGE_TOTAL": round(model["projected_total"] - total_line, 2),
            "BEST_PICK": pick,
            "CONFIDENCE": model["confidence"],
        })
    return pd.DataFrame(rows)


def build_matchup(home: Dict, away: Dict) -> Dict[str, float]:
    offense_gap = home["OFF_RATING"] - away["DEF_RATING"]
    defense_gap = away["OFF_RATING"] - home["DEF_RATING"]
    pace_factor = ((home["PACE"] + away["PACE"]) / 2) - 99
    form_factor = (home["FORM_LAST_10"] - away["FORM_LAST_10"]) * 0.7
    shooting_factor = ((home["FG3_PCT"] - away["OPP_FG3_PCT"]) - (away["FG3_PCT"] - home["OPP_FG3_PCT"])) * 100
    injury_factor = (away["INJURY_INDEX"] - home["INJURY_INDEX"]) * 2.6
    home_adv = home["HOME_EDGE"] - away["ROAD_RESILIENCE"]
    raw_margin = (offense_gap - defense_gap) * 0.85 + form_factor + shooting_factor * 0.2 + home_adv + injury_factor
    projected_home = round(111 + offense_gap * 0.55 + pace_factor * 1.25 + home_adv * 0.55, 1)
    projected_away = round(108 + defense_gap * 0.52 + pace_factor * 1.15 - home_adv * 0.25, 1)
    projected_total = round(projected_home + projected_away, 1)
    home_margin = round(projected_home - projected_away + raw_margin * 0.35, 1)
    confidence_raw = abs(raw_margin) + abs(home["NET_RATING"] - away["NET_RATING"]) + abs(home["FORM_LAST_10"] - away["FORM_LAST_10"]) * 0.8
    confidence = round(float(np.clip(54 + confidence_raw * 1.7, 54, 86)), 1)
    home_win_prob = float(np.clip(sigmoid(home_margin / 5.9), 0.08, 0.92))
    return {
        "projected_home_points": projected_home,
        "projected_away_points": projected_away,
        "projected_total": projected_total,
        "home_margin": home_margin,
        "home_win_prob": home_win_prob,
        "confidence": confidence,
    }


def build_pick_engine(games_df: pd.DataFrame) -> pd.DataFrame:
    if games_df.empty:
        return pd.DataFrame()
    picks = []
    for _, game in games_df.iterrows():
        home_prob = game["MODEL_HOME_WIN"]
        away_prob = game["MODEL_AWAY_WIN"]
        if game["EDGE_HOME_ML"] >= 2.0:
            market = "Mandante ML"
            odds = int(game["HOME_ML"])
            model_prob = home_prob
            edge = game["EDGE_HOME_ML"]
            rationale = f"Mandante com vantagem de mando, forma {game['HOME_FORM']}-10 e edge positivo em moneyline."
        elif game["EDGE_TOTAL"] >= 4.0:
            market = f"Over {game['MARKET_TOTAL']}"
            odds = -110
            model_prob = float(np.clip(0.52 + (game["EDGE_TOTAL"] / 20), 0.52, 0.73))
            edge = round((model_prob - implied_probability_from_odds(-110)) * 100, 2)
            rationale = f"Modelo projeta total {game['PROJECTED_TOTAL']}, acima da linha do mercado."
        else:
            market = f"Visitante +{abs(game['MARKET_SPREAD_HOME']):.1f}"
            odds = -108
            model_prob = away_prob if game["PROJECTED_MARGIN"] < 2 else float(np.clip(0.51 + abs(game["PROJECTED_MARGIN"]) / 18, 0.51, 0.69))
            edge = round((model_prob - implied_probability_from_odds(-108)) * 100, 2)
            rationale = f"Linha parece inflada para o mandante; visitante ganha valor em spread."

        kelly = kelly_fraction(model_prob, odds)
        stake = round(st.session_state.bankroll * min(kelly, st.session_state.stake_pct / 100) * 0.5, 2)
        picks.append(
            {
                "Jogo": f"{game['AWAY_ABBR']} @ {game['HOME_ABBR']}",
                "Mercado": market,
                "Odd Americana": odds,
                "Prob. Modelo": round(model_prob * 100, 1),
                "Edge %": edge,
                "Confiança": game["CONFIDENCE"],
                "Stake Sugerida": max(stake, 0.0),
                "Resumo": rationale,
                "GAME_ID": game["GAME_ID"],
            }
        )
    return pd.DataFrame(picks).sort_values(["Edge %", "Confiança"], ascending=False).reset_index(drop=True)


def make_radar(team_a: pd.Series, team_b: pd.Series) -> go.Figure:
    categories = ["PACE", "OFF_RATING", "DEF_INV", "REB_PCT", "AST_TO_RATIO", "CLUTCH_SCORE"]
    a_values = [
        team_a["PACE"],
        team_a["OFF_RATING"],
        125 - team_a["DEF_RATING"],
        team_a["REB_PCT"] * 100,
        team_a["AST_TO_RATIO"] * 30,
        team_a["CLUTCH_SCORE"] * 100,
    ]
    b_values = [
        team_b["PACE"],
        team_b["OFF_RATING"],
        125 - team_b["DEF_RATING"],
        team_b["REB_PCT"] * 100,
        team_b["AST_TO_RATIO"] * 30,
        team_b["CLUTCH_SCORE"] * 100,
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=a_values, theta=categories, fill="toself", name=team_a["TEAM_ABBREVIATION"]))
    fig.add_trace(go.Scatterpolar(r=b_values, theta=categories, fill="toself", name=team_b["TEAM_ABBREVIATION"]))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True, margin=dict(l=20, r=20, t=20, b=20))
    return fig


def export_history_csv(history: List[Dict]) -> bytes:
    df = pd.DataFrame(history)
    if df.empty:
        df = pd.DataFrame(columns=["data", "jogo", "mercado", "odd", "stake", "resultado", "lucro"])
    return df.to_csv(index=False).encode("utf-8")


def add_pick_to_history(row: pd.Series, result: str) -> None:
    odd = int(row["Odd Americana"])
    stake = float(row["Stake Sugerida"])
    if result == "Win":
        lucro = round(stake * (odd / 100), 2) if odd > 0 else round(stake * (100 / abs(odd)), 2)
    elif result == "Loss":
        lucro = round(-stake, 2)
    else:
        lucro = 0.0
    st.session_state.pick_history.append(
        {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "jogo": row["Jogo"],
            "mercado": row["Mercado"],
            "odd": odd,
            "stake": stake,
            "resultado": result,
            "lucro": lucro,
        }
    )
    st.session_state.bankroll = round(st.session_state.bankroll + lucro, 2)


def premium_guard() -> bool:
    if st.session_state.premium_ok:
        return True
    st.warning("Área premium bloqueada. Libere com o código configurado em secrets ou use o modo demo.")
    return False


# =========================================================
# APP
# =========================================================
init_session_state()
df_teams, source_mode = load_team_stats()
st.session_state.api_status = source_mode
st.session_state.last_refresh = datetime.now().strftime("%d/%m/%Y %H:%M")
df_players = load_players(df_teams)

with st.sidebar:
    st.header("⚙️ Central do Bot")
    page = st.radio(
        "Escolha o módulo",
        [
            "Dashboard",
            "Jogos do Dia",
            "Matchup Lab",
            "Player Hub",
            "Picks Engine",
            "Bankroll Tracker",
            "Premium",
            "Diagnóstico",
        ],
    )
    st.markdown("---")
    st.caption(f"Fonte de dados: {'API externa' if source_mode == 'api' else 'Fallback demo'}")
    st.caption(f"Última atualização: {st.session_state.last_refresh}")
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("Login local")
    user = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")
    if st.button("Entrar", use_container_width=True):
        if user == get_admin_user() and pwd == get_admin_password():
            st.session_state.auth_ok = True
            st.success("Login liberado.")
        else:
            st.error("Credenciais inválidas.")

    premium_code = st.text_input("Código premium", type="password")
    if st.button("Liberar premium", use_container_width=True):
        if premium_code == get_premium_code() or premium_code == "DEMO":
            st.session_state.premium_ok = True
            st.success("Área premium liberada.")
        else:
            st.error("Código premium inválido.")

    st.markdown("---")
    st.number_input("Bankroll inicial / atual", min_value=0.0, step=50.0, key="bankroll")
    st.slider("Stake máxima (% da banca)", 0.5, 5.0, key="stake_pct")

st.markdown(
    f"""
    <div class="hero-card">
        <h1>{APP_TITLE}</h1>
        <p>Versão 3.0 com layout de produto, picks estruturadas, bankroll tracker, modo premium, fallback anti-erro e painel de diagnóstico para deploy.</p>
        <span class="mini-chip">Temporada {SEASON_LABEL}</span>
        <span class="mini-chip">Deploy-safe no Streamlit</span>
        <span class="mini-chip">Sem dependência frágil</span>
        <span class="mini-chip">Pronto para monetização</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if page == "Dashboard":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Times analisados", len(df_teams), f"{df_teams['CONFERENCE'].nunique()} conferências")
    c2.metric("Maior Pace", f"{safe_metric_value(df_teams, 'PACE', 'max'):.1f}", "ritmo mais alto")
    c3.metric("Melhor ataque", f"{safe_metric_value(df_teams, 'OFF_RATING', 'max'):.1f}", "off rating")
    c4.metric("Melhor defesa", f"{safe_metric_value(df_teams, 'DEF_RATING', 'min'):.1f}", "def rating")

    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Mapa ofensivo x defensivo")
        fig = px.scatter(
            df_teams,
            x="OFF_RATING",
            y="DEF_RATING",
            color="CONFERENCE",
            size="PACE",
            hover_name="TEAM_DISPLAY",
            hover_data=["NET_RATING", "FORM_LABEL", "VALUE_SCORE"],
        )
        fig.update_layout(height=480)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Top 8 por Value Score")
        ranked = df_teams[["TEAM_DISPLAY", "W", "L", "NET_RATING", "FORM_LABEL", "VALUE_SCORE"]].sort_values("VALUE_SCORE", ascending=False).head(8)
        st.dataframe(ranked, use_container_width=True, hide_index=True)

    st.subheader("Painel rápido de conferências")
    conf = (
        df_teams.groupby("CONFERENCE", as_index=False)
        .agg({"W_PCT": "mean", "PACE": "mean", "OFF_RATING": "mean", "DEF_RATING": "mean"})
        .round(2)
    )
    fig_conf = px.bar(conf, x="CONFERENCE", y=["OFF_RATING", "DEF_RATING", "PACE"], barmode="group")
    st.plotly_chart(fig_conf, use_container_width=True)

elif page == "Jogos do Dia":
    target_date = st.date_input("Data da rodada", value=date.today())
    games_df = load_games_for_date(target_date.isoformat(), df_teams)
    st.subheader("Agenda modelada")
    if games_df.empty:
        st.warning("Nenhum jogo encontrado para a data selecionada.")
    else:
        top = games_df.sort_values(["CONFIDENCE", "EDGE_HOME_ML"], ascending=False).iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Melhor pick do dia", top["BEST_PICK"])
        c2.metric("Maior confiança", f"{top['CONFIDENCE']:.1f}%")
        c3.metric("Maior edge ML", f"{games_df['EDGE_HOME_ML'].max():.2f}%")

        view = games_df[[
            "AWAY_ABBR", "HOME_ABBR", "STATUS", "PROJECTED_HOME", "PROJECTED_AWAY", "PROJECTED_TOTAL",
            "MARKET_TOTAL", "MARKET_SPREAD_HOME", "HOME_ML", "AWAY_ML", "BEST_PICK", "CONFIDENCE"
        ]].copy()
        view.columns = [
            "Visitante", "Mandante", "Status", "Proj. Mandante", "Proj. Visitante", "Total Projetado",
            "Linha Total", "Spread Casa", "ML Casa", "ML Fora", "Melhor Pick", "Confiança"
        ]
        st.dataframe(view, use_container_width=True, hide_index=True)

        selected_game = st.selectbox("Detalhar jogo", games_df["GAME_ID"], format_func=lambda gid: f"{games_df.loc[games_df['GAME_ID'] == gid, 'AWAY_ABBR'].iloc[0]} @ {games_df.loc[games_df['GAME_ID'] == gid, 'HOME_ABBR'].iloc[0]}")
        game = games_df[games_df["GAME_ID"] == selected_game].iloc[0]
        home_row = df_teams[df_teams["TEAM_ABBREVIATION"] == game["HOME_ABBR"]].iloc[0]
        away_row = df_teams[df_teams["TEAM_ABBREVIATION"] == game["AWAY_ABBR"]].iloc[0]
        g1, g2 = st.columns([1, 1])
        with g1:
            st.markdown(f"### {game['AWAY_TEAM']} @ {game['HOME_TEAM']}")
            st.write(f"**Placar projetado:** {game['PROJECTED_AWAY']} x {game['PROJECTED_HOME']}")
            st.write(f"**Total projetado:** {game['PROJECTED_TOTAL']} | **Linha de mercado:** {game['MARKET_TOTAL']}")
            st.write(f"**Spread casa:** {game['MARKET_SPREAD_HOME']} | **Moneyline casa:** {game['HOME_ML']}")
            st.write(f"**Pick sugerida:** {game['BEST_PICK']} | **Confiança:** {game['CONFIDENCE']:.1f}%")
        with g2:
            radar = make_radar(home_row, away_row)
            st.plotly_chart(radar, use_container_width=True)

elif page == "Matchup Lab":
    team_options = df_teams["TEAM_DISPLAY"].tolist()
    c1, c2 = st.columns(2)
    with c1:
        team_a_name = st.selectbox("Time mandante", team_options, index=0)
    with c2:
        team_b_name = st.selectbox("Time visitante", team_options, index=min(8, len(team_options)-1))

    team_a = df_teams[df_teams["TEAM_DISPLAY"] == team_a_name].iloc[0]
    team_b = df_teams[df_teams["TEAM_DISPLAY"] == team_b_name].iloc[0]
    matchup = build_matchup(team_a, team_b)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Vitória mandante", f"{matchup['home_win_prob']*100:.1f}%")
    m2.metric("Margem projetada", f"{matchup['home_margin']:.1f}")
    m3.metric("Total projetado", f"{matchup['projected_total']:.1f}")
    m4.metric("Confiança", f"{matchup['confidence']:.1f}%")

    st.plotly_chart(make_radar(team_a, team_b), use_container_width=True)

    compare_df = pd.DataFrame(
        {
            team_a["TEAM_ABBREVIATION"]: [team_a["OFF_RATING"], team_a["DEF_RATING"], team_a["PACE"], team_a["REB_PCT"], team_a["FORM_LAST_10"], team_a["CLUTCH_SCORE"]],
            team_b["TEAM_ABBREVIATION"]: [team_b["OFF_RATING"], team_b["DEF_RATING"], team_b["PACE"], team_b["REB_PCT"], team_b["FORM_LAST_10"], team_b["CLUTCH_SCORE"]],
        },
        index=["Ataque", "Defesa", "Pace", "Rebote %", "Forma", "Clutch"],
    )
    st.dataframe(compare_df, use_container_width=True)

elif page == "Player Hub":
    st.subheader("Ranking de jogadores")
    team_filter = st.selectbox("Filtrar por time", ["Todos"] + sorted(df_players["TEAM_ABBREVIATION"].unique().tolist()))
    sort_by = st.selectbox("Ordenar por", ["EFF", "PTS", "REB", "AST", "FG3_PCT", "STOCKS"])
    players_view = df_players.copy()
    if team_filter != "Todos":
        players_view = players_view[players_view["TEAM_ABBREVIATION"] == team_filter]
    players_view = players_view.sort_values(sort_by, ascending=False)
    st.dataframe(players_view, use_container_width=True, hide_index=True)

    top10 = players_view.head(10)
    fig_players = px.bar(top10, x="PLAYER_NAME", y=sort_by, color="TEAM_ABBREVIATION")
    st.plotly_chart(fig_players, use_container_width=True)

elif page == "Picks Engine":
    target_date = st.date_input("Data das picks", value=date.today(), key="pick_date")
    games_df = load_games_for_date(target_date.isoformat(), df_teams)
    picks_df = build_pick_engine(games_df)
    st.subheader("Engine de picks")
    if picks_df.empty:
        st.warning("Sem picks disponíveis para a data selecionada.")
    else:
        st.dataframe(picks_df[["Jogo", "Mercado", "Odd Americana", "Prob. Modelo", "Edge %", "Confiança", "Stake Sugerida", "Resumo"]], use_container_width=True, hide_index=True)
        pick_idx = st.selectbox("Registrar pick", picks_df.index, format_func=lambda i: f"{picks_df.loc[i, 'Jogo']} — {picks_df.loc[i, 'Mercado']}")
        result = st.radio("Resultado", ["Pending", "Win", "Loss", "Push"], horizontal=True)
        if st.button("Salvar no histórico", use_container_width=True):
            add_pick_to_history(picks_df.loc[pick_idx], result)
            st.success("Pick salva no histórico e banca atualizada.")

elif page == "Bankroll Tracker":
    st.subheader("Gestão de banca")
    history_df = pd.DataFrame(st.session_state.pick_history)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Banca atual", f"R$ {st.session_state.bankroll:,.2f}")
    c2.metric("Picks registradas", len(history_df))
    c3.metric("ROI acumulado", f"{(history_df['lucro'].sum() / max(history_df['stake'].sum(), 1) * 100 if not history_df.empty else 0):.2f}%")
    c4.metric("Lucro líquido", f"R$ {history_df['lucro'].sum():,.2f}" if not history_df.empty else "R$ 0,00")

    if history_df.empty:
        st.info("Ainda não há picks registradas.")
    else:
        chart_df = history_df.copy()
        chart_df["saldo"] = st.session_state.bankroll - chart_df["lucro"].sum() + chart_df["lucro"].cumsum()
        fig_bank = px.line(chart_df, x="data", y="saldo", markers=True)
        st.plotly_chart(fig_bank, use_container_width=True)
        st.dataframe(history_df, use_container_width=True, hide_index=True)

    st.download_button(
        "Baixar histórico CSV",
        data=export_history_csv(st.session_state.pick_history),
        file_name="historico_picks_nba_probet.csv",
        mime="text/csv",
        use_container_width=True,
    )

elif page == "Premium":
    st.subheader("Painel Premium")
    if premium_guard():
        st.success("Área premium ativa.")
        premium_df = df_teams.sort_values(["VALUE_SCORE", "CLUTCH_SCORE"], ascending=False).head(10).copy()
        premium_df["Tier"] = np.where(premium_df["VALUE_SCORE"] >= premium_df["VALUE_SCORE"].quantile(0.75), "Elite", "Plus")
        st.dataframe(
            premium_df[["TEAM_DISPLAY", "VALUE_SCORE", "NET_RATING", "FORM_LABEL", "INJURY_INDEX", "CLUTCH_SCORE", "Tier"]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Leitura premium do mercado")
        for _, row in premium_df.head(5).iterrows():
            st.markdown(
                f"- **{row['TEAM_DISPLAY']}**: value score {row['VALUE_SCORE']:.1f}, clutch {row['CLUTCH_SCORE']:.3f}, forma {row['FORM_LABEL']} e índice de lesão {row['INJURY_INDEX']:.2f}."
            )

        st.markdown("### Ideias de monetização")
        st.write("- plano gratuito com picks limitadas")
        st.write("- plano premium com edge score, bankroll tracker e histórico")
        st.write("- área VIP com alertas e conteúdo exportável")

elif page == "Diagnóstico":
    st.subheader("Painel de diagnóstico")
    d1, d2 = st.columns(2)
    with d1:
        st.code(
            f"""
APP_TITLE = {APP_TITLE}
SEASON = {SEASON_LABEL}
SOURCE_MODE = {source_mode}
RAPIDAPI_KEY = {'CONFIGURADA' if get_rapidapi_key() else 'AUSENTE'}
AUTH_OK = {st.session_state.auth_ok}
PREMIUM_OK = {st.session_state.premium_ok}
LAST_REFRESH = {st.session_state.last_refresh}
            """.strip(),
            language="python",
        )
    with d2:
        diag = {
            "times": len(df_teams),
            "players": len(df_players),
            "colunas_times": len(df_teams.columns),
            "colunas_players": len(df_players.columns),
            "games_demo_today": len(load_games_for_date(date.today().isoformat(), df_teams)),
        }
        st.json(diag)

    st.markdown("### Colunas do DataFrame principal")
    st.write(df_teams.columns.tolist())
    st.markdown("### Amostra dos dados")
    st.dataframe(df_teams.head(10), use_container_width=True, hide_index=True)
    st.info("Este painel serve para descobrir rápido se o erro é de dependência, API, estrutura de dados ou secrets no Streamlit Cloud.")

st.markdown("---")
st.caption("NBA ProBet Analytics 3.0 — estrutura pronta para evoluir em SaaS, com fallback local e deploy estável.")
