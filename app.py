import hashlib
import math
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

APP_TITLE = "NBA ProBet SaaS 5.0"
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "probet_saas_v5.db"
SEED_PATH = BASE_DIR / "data" / "seed_team_ratings.csv"

st.set_page_config(page_title=APP_TITLE, page_icon="🏀", layout="wide", initial_sidebar_state="expanded")

# -----------------------------
# VISUAL IDENTITY
# -----------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"]  {font-family: 'Inter', sans-serif;}
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at top left, rgba(79,70,229,.18), transparent 28%),
    radial-gradient(circle at top right, rgba(14,165,233,.14), transparent 24%),
    linear-gradient(180deg, #07111f 0%, #091224 40%, #0b1320 100%);
}
.block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1400px;}
.hero {
  border: 1px solid rgba(255,255,255,.08);
  background: linear-gradient(135deg, rgba(14,24,42,.92), rgba(16,29,54,.88));
  border-radius: 28px;
  padding: 1.35rem 1.35rem;
  box-shadow: 0 18px 50px rgba(0,0,0,.25);
  margin-bottom: 1rem;
}
.glass {
  border: 1px solid rgba(255,255,255,.08);
  background: rgba(10,18,32,.72);
  border-radius: 24px;
  padding: 1rem 1rem;
  box-shadow: 0 10px 40px rgba(0,0,0,.18);
}
.kpi {
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(18,28,48,.95), rgba(9,16,28,.95));
  padding: 1rem;
  min-height: 120px;
}
.muted {opacity: .76; font-size: .92rem;}
.tag {
  display: inline-block;
  padding: .28rem .65rem;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,.12);
  background: rgba(255,255,255,.03);
  font-size: .83rem;
  margin-right: .35rem;
}
.plan-card {
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(13,23,40,.94), rgba(8,13,24,.94));
  padding: 1rem;
  min-height: 250px;
}
.soft-divider {height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,.10), transparent); margin: .8rem 0 1rem;}
.big-number {font-size: 2rem; font-weight: 800; letter-spacing: -.04em;}
.small {font-size: .85rem; opacity: .78;}
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #08111f 0%, #09131f 100%);
  border-right: 1px solid rgba(255,255,255,.06);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------
# DATABASE / AUTH
# -----------------------------
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            plan TEXT NOT NULL DEFAULT 'free',
            is_admin INTEGER NOT NULL DEFAULT 0,
            favorite_team TEXT,
            risk_profile TEXT DEFAULT 'moderado',
            onboarding_done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            last_login TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS picks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            created_at TEXT NOT NULL,
            provider_snapshot TEXT,
            game_label TEXT NOT NULL,
            market TEXT NOT NULL,
            pick TEXT NOT NULL,
            confidence REAL NOT NULL,
            edge REAL NOT NULL,
            stake_units REAL NOT NULL,
            result TEXT NOT NULL DEFAULT 'open',
            profit_units REAL NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            created_at TEXT NOT NULL,
            rating INTEGER NOT NULL,
            message TEXT,
            area TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()

    admin_email = os.getenv("APP_ADMIN_EMAIL", st.secrets.get("APP_ADMIN_EMAIL", "admin@probet.local") if hasattr(st, "secrets") else "admin@probet.local")
    admin_name = os.getenv("APP_ADMIN_NAME", st.secrets.get("APP_ADMIN_NAME", "Administrador") if hasattr(st, "secrets") else "Administrador")
    admin_password = os.getenv("APP_ADMIN_PASSWORD", st.secrets.get("APP_ADMIN_PASSWORD", "admin123") if hasattr(st, "secrets") else "admin123")
    if not get_user_by_email(admin_email):
        create_user(admin_name, admin_email, admin_password, plan="premium", is_admin=True)
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(name: str, email: str, password: str, plan: str = "free", is_admin: bool = False) -> Tuple[bool, str]:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash, plan, is_admin, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (name.strip(), email.strip().lower(), hash_password(password), plan, int(is_admin), datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True, "Conta criada com sucesso."
    except sqlite3.IntegrityError:
        return False, "Este e-mail já está cadastrado."
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE email = ? AND password_hash = ?",
        (email.strip().lower(), hash_password(password)),
    )
    user = cur.fetchone()
    if user:
        cur.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.utcnow().isoformat(), user["id"]))
        conn.commit()
        cur.execute("SELECT * FROM users WHERE id = ?", (user["id"],))
        user = cur.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    conn.close()
    return row


def update_user_profile(user_id: int, favorite_team: str, risk_profile: str, onboarding_done: int = 1) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE users SET favorite_team = ?, risk_profile = ?, onboarding_done = ? WHERE id = ?",
        (favorite_team, risk_profile, onboarding_done, user_id),
    )
    conn.commit()
    conn.close()


def update_user_plan(user_id: int, plan: str) -> None:
    conn = get_conn()
    conn.execute("UPDATE users SET plan = ? WHERE id = ?", (plan, user_id))
    conn.commit()
    conn.close()


def list_users() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query("SELECT id, name, email, plan, is_admin, favorite_team, risk_profile, onboarding_done, created_at, last_login FROM users ORDER BY id DESC", conn)
    conn.close()
    return df


def insert_pick(user_id: int, provider_snapshot: str, game_label: str, market: str, pick: str, confidence: float, edge: float, stake_units: float) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO picks (user_id, created_at, provider_snapshot, game_label, market, pick, confidence, edge, stake_units)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, datetime.utcnow().isoformat(), provider_snapshot, game_label, market, pick, confidence, edge, stake_units),
    )
    conn.commit()
    conn.close()


def list_user_picks(user_id: int) -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query("SELECT id, created_at, provider_snapshot, game_label, market, pick, confidence, edge, stake_units, result, profit_units FROM picks WHERE user_id = ? ORDER BY id DESC", conn, params=(user_id,))
    conn.close()
    return df


def list_all_picks() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query("SELECT p.*, u.email, u.plan FROM picks p LEFT JOIN users u ON p.user_id = u.id ORDER BY p.id DESC", conn)
    conn.close()
    return df


def update_pick_result(pick_id: int, result: str, profit_units: float) -> None:
    conn = get_conn()
    conn.execute("UPDATE picks SET result = ?, profit_units = ? WHERE id = ?", (result, profit_units, pick_id))
    conn.commit()
    conn.close()


def insert_feedback(user_id: int, rating: int, message: str, area: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO feedback (user_id, created_at, rating, message, area) VALUES (?, ?, ?, ?, ?)",
        (user_id, datetime.utcnow().isoformat(), rating, message.strip(), area),
    )
    conn.commit()
    conn.close()


def list_feedback() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query("SELECT f.*, u.email FROM feedback f LEFT JOIN users u ON f.user_id = u.id ORDER BY f.id DESC", conn)
    conn.close()
    return df


init_db()

# -----------------------------
# DATA PROVIDERS
# -----------------------------
def get_secret(name: str, default: str = "") -> str:
    try:
        return os.getenv(name) or st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)


SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 NBA-ProBet/5.0"})


@st.cache_data(ttl=12 * 3600)
def load_seed_ratings() -> pd.DataFrame:
    df = pd.read_csv(SEED_PATH)
    df["power_index"] = (df["off_rating"] - df["def_rating"]) + (df["form"] * 5)
    return df


def provider_status_dict() -> Dict[str, Dict[str, str]]:
    return {
        "espn": {"enabled": "sim", "mode": "sem chave", "purpose": "placar, jogos do dia e headlines"},
        "balldontlie": {"enabled": "sim" if bool(get_secret("BDL_API_KEY")) else "parcial", "mode": "API key opcional", "purpose": "jogos, box score e enriquecimento NBA"},
        "thesportsdb": {"enabled": "sim", "mode": "chave pública 123 ou chave própria", "purpose": "logos, imagens e metadata"},
        "csv_history": {"enabled": "sim", "mode": "upload manual", "purpose": "backtest e histórico próprio"},
    }


@st.cache_data(ttl=10 * 60)
def fetch_espn_scoreboard(game_date: str) -> pd.DataFrame:
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    resp = SESSION.get(url, params={"dates": game_date.replace("-", "")}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    rows: List[Dict[str, object]] = []
    for event in data.get("events", []):
        comp = (event.get("competitions") or [{}])[0]
        competitors = comp.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        status_obj = comp.get("status", {})
        status_type = status_obj.get("type", {})
        rows.append(
            {
                "game_id": event.get("id"),
                "provider": "ESPN",
                "start_time": event.get("date"),
                "status": status_type.get("description") or status_type.get("shortDetail") or "Agendado",
                "state": status_type.get("state") or "pre",
                "home_team": home.get("team", {}).get("displayName"),
                "home_abbr": home.get("team", {}).get("abbreviation"),
                "home_score": safe_int(home.get("score")),
                "away_team": away.get("team", {}).get("displayName"),
                "away_abbr": away.get("team", {}).get("abbreviation"),
                "away_score": safe_int(away.get("score")),
                "broadcast": ", ".join(b.get("names", [""])[0] for b in comp.get("broadcasts", []) if b.get("names")),
                "venue": comp.get("venue", {}).get("fullName") or "",
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(ttl=10 * 60)
def fetch_espn_news(limit: int = 8) -> pd.DataFrame:
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/news"
    resp = SESSION.get(url, timeout=15)
    resp.raise_for_status()
    items = resp.json().get("articles", [])[:limit]
    rows = []
    for item in items:
        rows.append(
            {
                "headline": item.get("headline"),
                "description": item.get("description"),
                "published": item.get("published"),
                "source": (item.get("source") or {}).get("name", "ESPN"),
                "link": item.get("links", {}).get("web", {}).get("href", ""),
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(ttl=30 * 60)
def fetch_bdl_games(game_date: str) -> pd.DataFrame:
    api_key = get_secret("BDL_API_KEY")
    if not api_key:
        return pd.DataFrame()
    headers = {"Authorization": api_key}
    endpoints = [
        ("https://api.balldontlie.io/nba/v1/games", {"dates[]": game_date}),
        ("https://api.balldontlie.io/v1/games", {"dates[]": game_date}),
    ]
    for url, params in endpoints:
        try:
            resp = SESSION.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code >= 400:
                continue
            payload = resp.json()
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, list):
                continue
            rows = []
            for g in data:
                home_team = g.get("home_team") or {}
                away_team = g.get("visitor_team") or g.get("away_team") or {}
                rows.append(
                    {
                        "game_id": str(g.get("id")),
                        "provider": "BALLDONTLIE",
                        "start_time": g.get("datetime") or g.get("date"),
                        "status": g.get("status") or "Agendado",
                        "state": "in" if "Q" in str(g.get("status", "")) else "pre",
                        "home_team": home_team.get("full_name") or home_team.get("name"),
                        "home_abbr": home_team.get("abbreviation"),
                        "home_score": safe_int(g.get("home_team_score")),
                        "away_team": away_team.get("full_name") or away_team.get("name"),
                        "away_abbr": away_team.get("abbreviation"),
                        "away_score": safe_int(g.get("visitor_team_score") or g.get("away_team_score")),
                        "broadcast": "",
                        "venue": g.get("venue") or "",
                    }
                )
            return pd.DataFrame(rows)
        except Exception:
            continue
    return pd.DataFrame()


@st.cache_data(ttl=24 * 3600)
def fetch_team_logo(team_name: str) -> str:
    api_key = get_secret("THESPORTSDB_API_KEY", "123")
    candidates = [team_name, team_name.replace("Portland Trail Blazers", "Portland Trailblazers")]
    for query in candidates:
        try:
            url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/searchteams.php"
            resp = SESSION.get(url, params={"t": query}, timeout=15)
            if resp.status_code >= 400:
                continue
            teams = resp.json().get("teams") or []
            for team in teams:
                league = (team.get("strLeague") or "")
                sport = (team.get("strSport") or "")
                if sport.lower() == "basketball" and "nba" in league.lower():
                    return team.get("strBadge") or team.get("strLogo") or team.get("strTeamBadge") or ""
        except Exception:
            continue
    return ""


def safe_int(value: object) -> int:
    try:
        return int(value)
    except Exception:
        return 0


@st.cache_data(ttl=10 * 60)
def get_live_games(game_date: str) -> pd.DataFrame:
    espn_df = pd.DataFrame()
    bdl_df = pd.DataFrame()
    try:
        espn_df = fetch_espn_scoreboard(game_date)
    except Exception:
        espn_df = pd.DataFrame()
    try:
        bdl_df = fetch_bdl_games(game_date)
    except Exception:
        bdl_df = pd.DataFrame()

    primary = espn_df if not espn_df.empty else bdl_df
    if primary.empty:
        return build_seed_schedule(game_date)

    if not bdl_df.empty and not primary.empty:
        merge_cols = ["home_abbr", "away_abbr"]
        helper = bdl_df[[c for c in ["home_abbr", "away_abbr", "status"] if c in bdl_df.columns]].copy()
        helper = helper.rename(columns={"status": "bdl_status"})
        primary = primary.merge(helper, on=merge_cols, how="left")
    return primary


def build_seed_schedule(game_date: str) -> pd.DataFrame:
    seed = load_seed_ratings().copy()
    teams = seed["team_abbr"].tolist()
    seed_games = []
    for idx in range(0, min(10, len(teams) // 2 * 2), 2):
        away = seed.iloc[idx]
        home = seed.iloc[idx + 1]
        seed_games.append(
            {
                "game_id": f"seed-{game_date}-{idx}",
                "provider": "LOCAL",
                "start_time": f"{game_date}T23:00:00Z",
                "status": "Simulado local",
                "state": "pre",
                "home_team": home["team_name"],
                "home_abbr": home["team_abbr"],
                "home_score": 0,
                "away_team": away["team_name"],
                "away_abbr": away["team_abbr"],
                "away_score": 0,
                "broadcast": "Fallback interno",
                "venue": "ProBet Arena",
            }
        )
    return pd.DataFrame(seed_games)


# -----------------------------
# MODEL / ENRICHMENT
# -----------------------------
def logistic(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def deterministic_noise(key: str, scale: float = 1.0) -> float:
    h = hashlib.md5(key.encode("utf-8")).hexdigest()[:8]
    num = int(h, 16) / 0xFFFFFFFF
    return (num - 0.5) * 2 * scale


def add_model_features(games_df: pd.DataFrame) -> pd.DataFrame:
    ratings = load_seed_ratings().copy()
    ratings = ratings.rename(columns={"team_abbr": "abbr"})
    out = games_df.copy()
    out = out.merge(ratings.add_prefix("home_"), left_on="home_abbr", right_on="home_abbr", how="left")
    out = out.merge(ratings.add_prefix("away_"), left_on="away_abbr", right_on="away_abbr", how="left")

    out["home_power"] = (out["home_off_rating"] - out["home_def_rating"]) + out["home_home_advantage"].fillna(2.5) - (out["home_injury_index"].fillna(0.1) * 15)
    out["away_power"] = (out["away_off_rating"] - out["away_def_rating"]) - (out["away_injury_index"].fillna(0.1) * 15)
    out["model_spread_home"] = (out["home_power"] - out["away_power"]) + ((out["home_form"].fillna(0) - out["away_form"].fillna(0)) * 1.6)
    out["projected_total"] = (out["home_pace"].fillna(99) + out["away_pace"].fillna(99)) + ((out["home_off_rating"].fillna(114) + out["away_off_rating"].fillna(114)) - 210)
    out["win_prob_home"] = out["model_spread_home"].apply(lambda x: round(logistic(x / 6.5), 4))
    out["edge_score"] = ((out["win_prob_home"] - 0.5).abs() * 100) + ((out["projected_total"] - out["projected_total"].median()).abs() / 2)
    out["recommended_market"] = out.apply(recommend_market, axis=1)
    out["confidence"] = out.apply(calc_confidence, axis=1)
    out["stake_units"] = out["confidence"].apply(lambda x: round(0.5 + (x - 50) / 18, 2)).clip(lower=0.5, upper=3.0)
    out["provider_stack"] = out.apply(lambda r: provider_snapshot_for_row(r), axis=1)
    return out


def recommend_market(row: pd.Series) -> str:
    if abs(row.get("model_spread_home", 0)) >= 4.2:
        side = row.get("home_abbr") if row.get("model_spread_home", 0) > 0 else row.get("away_abbr")
        return f"Spread lean: {side}"
    if row.get("projected_total", 0) >= 222:
        return "Total lean: Over"
    return "Total lean: Under"


def calc_confidence(row: pd.Series) -> float:
    base = 52
    base += min(abs(row.get("model_spread_home", 0)) * 2.1, 14)
    base += min(abs((row.get("home_form", 0) - row.get("away_form", 0))) * 4, 8)
    base -= max((row.get("home_injury_index", 0.1) + row.get("away_injury_index", 0.1) - 0.22) * 25, 0)
    base += deterministic_noise(str(row.get("game_id", "")), scale=2.0)
    return round(max(50, min(base, 78)), 1)


def provider_snapshot_for_row(row: pd.Series) -> str:
    stack = [row.get("provider", "LOCAL")]
    if bool(get_secret("BDL_API_KEY")):
        stack.append("BALLDONTLIE")
    stack.append("TheSportsDB")
    return " + ".join(stack)


def bankroll_summary(picks_df: pd.DataFrame, bankroll: float = 1000.0) -> Dict[str, float]:
    if picks_df.empty:
        return {"bankroll": bankroll, "closed_picks": 0, "roi": 0.0, "profit": 0.0, "win_rate": 0.0}
    closed = picks_df[picks_df["result"].isin(["win", "loss", "push"])]
    profit = float(closed["profit_units"].sum()) if not closed.empty else 0.0
    wins = int((closed["result"] == "win").sum())
    losses = int((closed["result"] == "loss").sum())
    decided = wins + losses
    roi = (profit / max(float(closed["stake_units"].sum()), 1.0)) * 100 if not closed.empty else 0.0
    win_rate = (wins / decided) * 100 if decided else 0.0
    return {
        "bankroll": bankroll + profit * 50,
        "closed_picks": int(len(closed)),
        "roi": round(roi, 2),
        "profit": round(profit, 2),
        "win_rate": round(win_rate, 2),
    }


# -----------------------------
# AUTH UI
# -----------------------------
def render_auth() -> None:
    st.markdown(
        """
        <div class='hero'>
            <div class='tag'>NBA analytics</div>
            <div class='tag'>onboarding premium</div>
            <div class='tag'>multifonte</div>
            <h1 style='margin:.35rem 0 0 0;'>NBA ProBet SaaS 5.0</h1>
            <p class='muted'>Stack híbrido com ESPN para placar e notícias, BALLDONTLIE para enriquecimento NBA quando houver chave, TheSportsDB para identidade visual dos times e fallback local para o app nunca morrer no deploy.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("Entrar")
        with st.form("login_form"):
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Acessar", use_container_width=True)
            if submitted:
                user = authenticate_user(email, password)
                if user:
                    st.session_state["user_id"] = user["id"]
                    st.success("Login realizado com sucesso.")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("Criar conta")
        with st.form("register_form"):
            name = st.text_input("Nome")
            email = st.text_input("E-mail", key="register_email")
            password = st.text_input("Senha", type="password", key="register_password")
            plan = st.selectbox("Plano inicial", ["free", "premium"], index=0)
            submitted = st.form_submit_button("Criar conta", use_container_width=True)
            if submitted:
                ok, msg = create_user(name, email, password, plan=plan)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)


def current_user() -> Optional[sqlite3.Row]:
    uid = st.session_state.get("user_id")
    if not uid:
        return None
    return get_user_by_id(uid)


def render_onboarding(user: sqlite3.Row) -> None:
    seed = load_seed_ratings()
    st.markdown("<div class='hero'><h2 style='margin:0;'>Onboarding premium</h2><p class='muted'>Deixe o produto com a sua cara. Isso melhora filtros, picks e a experiência do dashboard.</p></div>", unsafe_allow_html=True)
    with st.form("onboarding_form"):
        favorite_team = st.selectbox("Time favorito", sorted(seed["team_name"].tolist()))
        risk_profile = st.select_slider("Perfil de risco", options=["conservador", "moderado", "agressivo"], value="moderado")
        plan_goal = st.selectbox("Objetivo principal", ["placar ao vivo", "picks", "monitoramento", "conteúdo e insights"])
        submitted = st.form_submit_button("Salvar onboarding", use_container_width=True)
        if submitted:
            update_user_profile(user["id"], favorite_team, risk_profile, onboarding_done=1)
            st.session_state["goal"] = plan_goal
            st.success("Onboarding salvo. Seu ambiente foi configurado.")
            st.rerun()


# -----------------------------
# PAGE HELPERS
# -----------------------------
def render_topbar(user: sqlite3.Row) -> None:
    favorite = user["favorite_team"] or "Não definido"
    plan = str(user["plan"]).upper()
    st.markdown(
        f"""
        <div class='hero'>
            <div style='display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap; align-items:center;'>
                <div>
                    <div class='tag'>{plan}</div>
                    <div class='tag'>Favorito: {favorite}</div>
                    <h2 style='margin:.35rem 0 0 0;'>Olá, {user['name']}</h2>
                    <p class='muted'>Plataforma estilo SaaS com foco em consistência operacional, identidade premium e multifonte confiável.</p>
                </div>
                <div>
                    <div class='small'>Motor de dados</div>
                    <div class='big-number'>ESPN + BDL + TheSportsDB</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(user: sqlite3.Row) -> str:
    with st.sidebar:
        st.markdown("### 🏀 NBA ProBet 5.0")
        st.caption("SaaS de análise, monitoramento e picks")
        choice = st.radio(
            "Navegação",
            ["Dashboard", "Live Center", "Matchup Studio", "Picks Lab", "Bankroll", "Newsroom", "Data Hub", "Diagnóstico", "Configurações"] + (["Admin"] if user["is_admin"] else []),
        )
        st.markdown("---")
        if st.button("Sair", use_container_width=True):
            st.session_state.pop("user_id", None)
            st.rerun()
        return choice


def render_dashboard(user: sqlite3.Row, games_df: pd.DataFrame) -> None:
    enriched = add_model_features(games_df)
    picks_df = list_user_picks(user["id"])
    bank = bankroll_summary(picks_df)

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f"<div class='kpi'><div class='small'>Jogos no radar</div><div class='big-number'>{len(enriched)}</div><div class='muted'>Agenda do dia</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi'><div class='small'>ROI fechado</div><div class='big-number'>{bank['roi']:.1f}%</div><div class='muted'>Baseado nos picks liquidados</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi'><div class='small'>Win rate</div><div class='big-number'>{bank['win_rate']:.1f}%</div><div class='muted'>Decisões com resultado</div></div>", unsafe_allow_html=True)
    k4.markdown(f"<div class='kpi'><div class='small'>Bankroll simulado</div><div class='big-number'>R$ {bank['bankroll']:.0f}</div><div class='muted'>Unidade x R$50</div></div>", unsafe_allow_html=True)

    left, right = st.columns([1.3, 1])
    with left:
        st.subheader("Radar de valor do dia")
        radar = enriched[["away_abbr", "home_abbr", "confidence", "edge_score", "recommended_market", "stake_units"]].copy()
        radar["jogo"] = radar["away_abbr"] + " @ " + radar["home_abbr"]
        st.dataframe(radar[["jogo", "recommended_market", "confidence", "edge_score", "stake_units"]], use_container_width=True, hide_index=True)

    with right:
        st.subheader("Distribuição de confiança")
        fig = px.histogram(enriched, x="confidence", nbins=10, title="Confiança do motor")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Mapa de ataque x defesa")
    ratings = load_seed_ratings()
    fig2 = px.scatter(ratings, x="off_rating", y="def_rating", hover_name="team_name", size="pace", color="conference")
    st.plotly_chart(fig2, use_container_width=True)


def render_live_center(games_df: pd.DataFrame) -> None:
    enriched = add_model_features(games_df)
    st.subheader("Live Center")
    if enriched.empty:
        st.warning("Nenhum jogo disponível para a data selecionada.")
        return
    for _, row in enriched.iterrows():
        logo_home = fetch_team_logo(row["home_team"]) if row.get("home_team") else ""
        logo_away = fetch_team_logo(row["away_team"]) if row.get("away_team") else ""
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.2, .25, 1.2, 1.2])
            with c1:
                if logo_away:
                    st.image(logo_away, width=56)
                st.markdown(f"### {row['away_team']}")
                st.caption(f"{row['away_abbr']} | Score: {row['away_score']}")
            with c2:
                st.markdown("<div style='text-align:center; font-size:28px; padding-top:26px;'>@</div>", unsafe_allow_html=True)
            with c3:
                if logo_home:
                    st.image(logo_home, width=56)
                st.markdown(f"### {row['home_team']}")
                st.caption(f"{row['home_abbr']} | Score: {row['home_score']}")
            with c4:
                st.write(f"**Status:** {row['status']}")
                st.write(f"**Mercado favorito:** {row['recommended_market']}")
                st.write(f"**Confiança:** {row['confidence']}%")
                st.write(f"**Provider:** {row['provider_stack']}")


def render_matchup_studio(games_df: pd.DataFrame) -> None:
    ratings = load_seed_ratings()
    team_names = sorted(ratings["team_name"].tolist())
    st.subheader("Matchup Studio")
    col1, col2 = st.columns(2)
    home_team = col1.selectbox("Time mandante", team_names, index=1)
    away_team = col2.selectbox("Time visitante", team_names, index=0)

    home = ratings.loc[ratings["team_name"] == home_team].iloc[0]
    away = ratings.loc[ratings["team_name"] == away_team].iloc[0]
    synthetic = pd.DataFrame([{ 
        "game_id": f"custom-{home['team_abbr']}-{away['team_abbr']}",
        "provider": "MODEL",
        "start_time": datetime.utcnow().isoformat(),
        "status": "Simulação personalizada",
        "state": "pre",
        "home_team": home_team,
        "home_abbr": home["team_abbr"],
        "home_score": 0,
        "away_team": away_team,
        "away_abbr": away["team_abbr"],
        "away_score": 0,
        "broadcast": "",
        "venue": "Custom Arena",
    }])
    result = add_model_features(synthetic).iloc[0]

    a, b, c = st.columns(3)
    a.metric("Win prob. mandante", f"{result['win_prob_home']*100:.1f}%")
    b.metric("Spread do modelo", f"{result['model_spread_home']:+.1f}")
    c.metric("Total projetado", f"{result['projected_total']:.1f}")

    compare_df = pd.DataFrame({
        "Métrica": ["Ataque", "Defesa", "Pace", "Forma", "Vitórias L10"],
        home_team: [home["off_rating"], home["def_rating"], home["pace"], home["form"], home["last10_wins"]],
        away_team: [away["off_rating"], away["def_rating"], away["pace"], away["form"], away["last10_wins"]],
    })
    st.dataframe(compare_df, use_container_width=True, hide_index=True)

    fig = px.line_polar(
        compare_df.melt(id_vars="Métrica", var_name="Time", value_name="Valor"),
        r="Valor", theta="Métrica", color="Time", line_close=True,
        title="Radar comparativo",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_picks_lab(user: sqlite3.Row, games_df: pd.DataFrame) -> None:
    enriched = add_model_features(games_df).sort_values(["confidence", "edge_score"], ascending=False).copy()
    st.subheader("Picks Lab")
    if user["plan"] == "free":
        st.info("No plano Free, você visualiza os 3 melhores sinais. No Premium, libera o painel completo, stake e log persistente.")
        enriched = enriched.head(3)
    for _, row in enriched.iterrows():
        with st.container(border=True):
            st.markdown(f"### {row['away_abbr']} @ {row['home_abbr']}")
            l, r = st.columns([1.25, 1])
            with l:
                st.write(f"**Mercado:** {row['recommended_market']}")
                st.write(f"**Confiança:** {row['confidence']}%")
                st.write(f"**Total projetado:** {row['projected_total']:.1f}")
                st.write(f"**Spread do modelo:** {row['model_spread_home']:+.1f}")
            with r:
                st.write(f"**Stake sugerida:** {row['stake_units']:.2f}u")
                st.write(f"**Edge score:** {row['edge_score']:.1f}")
                st.write(f"**Stack:** {row['provider_stack']}")
                if user["plan"] == "premium":
                    if st.button(f"Salvar pick {row['game_id']}", key=f"save_pick_{row['game_id']}"):
                        insert_pick(
                            user["id"],
                            row["provider_stack"],
                            f"{row['away_abbr']} @ {row['home_abbr']}",
                            row["recommended_market"],
                            row["recommended_market"],
                            float(row["confidence"]),
                            float(row["edge_score"]),
                            float(row["stake_units"]),
                        )
                        st.success("Pick salvo no seu histórico.")
                        st.rerun()


def render_bankroll(user: sqlite3.Row) -> None:
    st.subheader("Bankroll Tracker")
    picks = list_user_picks(user["id"])
    summary = bankroll_summary(picks)
    a, b, c, d = st.columns(4)
    a.metric("Picks fechados", summary["closed_picks"])
    b.metric("Lucro (u)", f"{summary['profit']:+.2f}")
    c.metric("ROI", f"{summary['roi']:.2f}%")
    d.metric("Win rate", f"{summary['win_rate']:.2f}%")

    if picks.empty:
        st.info("Ainda não há picks salvos.")
        return
    st.dataframe(picks, use_container_width=True, hide_index=True)
    csv = picks.to_csv(index=False).encode("utf-8")
    st.download_button("Exportar histórico CSV", csv, file_name="probet_picks.csv", mime="text/csv")

    if user["plan"] == "premium":
        open_picks = picks[picks["result"] == "open"]
        if not open_picks.empty:
            st.markdown("#### Atualizar pick")
            target_id = st.selectbox("Selecione o pick", open_picks["id"].tolist())
            result = st.selectbox("Resultado", ["win", "loss", "push"])
            profit = st.number_input("Profit units", value=1.0, step=0.25)
            if st.button("Atualizar resultado"):
                update_pick_result(int(target_id), result, float(profit))
                st.success("Pick atualizado.")
                st.rerun()


def render_newsroom() -> None:
    st.subheader("Newsroom")
    try:
        news_df = fetch_espn_news(8)
    except Exception:
        news_df = pd.DataFrame()
    if news_df.empty:
        st.warning("Não foi possível carregar notícias agora.")
        return
    for _, row in news_df.iterrows():
        with st.container(border=True):
            st.markdown(f"### {row['headline']}")
            st.write(row['description'] or "Sem descrição disponível.")
            st.caption(f"Fonte: {row['source']} | Publicado: {row['published']}")
            if row['link']:
                st.link_button("Abrir matéria", row['link'])


def render_data_hub() -> None:
    st.subheader("Data Hub")
    st.markdown("Use fontes confiáveis em camadas: ESPN para placar e notícias, BALLDONTLIE para dados NBA com autenticação, TheSportsDB para identidade visual, e CSV próprio para histórico e backtest.")
    status = provider_status_dict()
    cols = st.columns(len(status))
    for col, (name, info) in zip(cols, status.items()):
        col.markdown(f"<div class='plan-card'><div class='tag'>{name.upper()}</div><h4>{info['enabled'].upper()}</h4><p>{info['purpose']}</p><div class='small'>{info['mode']}</div></div>", unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload CSV histórico (Kaggle, ESPN export, planilha própria)", type=["csv"])
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            st.success(f"Arquivo carregado com {len(df)} linhas e {len(df.columns)} colunas.")
            st.dataframe(df.head(20), use_container_width=True)
        except Exception as exc:
            st.error(f"Falha ao ler CSV: {exc}")


def render_diagnostics(games_df: pd.DataFrame) -> None:
    st.subheader("Diagnóstico")
    diagnostics = pd.DataFrame([
        {"item": "Banco SQLite", "status": "OK" if DB_PATH.exists() else "ERRO", "detalhe": str(DB_PATH)},
        {"item": "Seed ratings", "status": "OK" if SEED_PATH.exists() else "ERRO", "detalhe": str(SEED_PATH)},
        {"item": "Jogos carregados", "status": "OK" if not games_df.empty else "FALLBACK", "detalhe": f"{len(games_df)} jogos"},
        {"item": "BDL_API_KEY", "status": "OK" if bool(get_secret('BDL_API_KEY')) else "OPCIONAL", "detalhe": "preencha para enriquecer dados BALLDONTLIE"},
        {"item": "THESPORTSDB_API_KEY", "status": "OK" if bool(get_secret('THESPORTSDB_API_KEY')) else "USANDO 123", "detalhe": "chave pública padrão"},
    ])
    st.dataframe(diagnostics, use_container_width=True, hide_index=True)
    st.code("\n".join([
        f"BDL_API_KEY={'set' if bool(get_secret('BDL_API_KEY')) else 'missing'}",
        f"THESPORTSDB_API_KEY={'set' if bool(get_secret('THESPORTSDB_API_KEY')) else 'default_123'}",
        f"APP_ADMIN_EMAIL={get_secret('APP_ADMIN_EMAIL', 'admin@probet.local')}",
    ]), language="bash")


def render_settings(user: sqlite3.Row) -> None:
    st.subheader("Configurações")
    with st.form("settings_form"):
        favorite_team = st.text_input("Time favorito", value=user["favorite_team"] or "")
        risk_profile = st.selectbox("Perfil", ["conservador", "moderado", "agressivo"], index=["conservador", "moderado", "agressivo"].index(user["risk_profile"] or "moderado"))
        submitted = st.form_submit_button("Salvar configurações")
        if submitted:
            update_user_profile(user["id"], favorite_team, risk_profile, onboarding_done=1)
            st.success("Preferências salvas.")
            st.rerun()

    st.markdown("### Feedback")
    with st.form("feedback_form"):
        rating = st.slider("Nota da experiência", 1, 5, 5)
        area = st.selectbox("Área", ["geral", "live center", "picks", "bankroll", "onboarding", "design"])
        message = st.text_area("Comentário")
        submitted = st.form_submit_button("Enviar feedback")
        if submitted:
            insert_feedback(user["id"], rating, message, area)
            st.success("Feedback registrado.")

    if user["plan"] == "free":
        st.markdown("### Upgrade")
        if st.button("Ativar Premium agora"):
            update_user_plan(user["id"], "premium")
            st.success("Plano atualizado para Premium.")
            st.rerun()


def render_admin() -> None:
    st.subheader("Painel Admin")
    users_df = list_users()
    picks_df = list_all_picks()
    feedback_df = list_feedback()
    tabs = st.tabs(["Usuários", "Picks", "Feedback"])
    with tabs[0]:
        st.dataframe(users_df, use_container_width=True, hide_index=True)
    with tabs[1]:
        st.dataframe(picks_df, use_container_width=True, hide_index=True)
    with tabs[2]:
        st.dataframe(feedback_df, use_container_width=True, hide_index=True)


# -----------------------------
# APP FLOW
# -----------------------------
def main() -> None:
    user = current_user()
    if not user:
        render_auth()
        return

    if not user["onboarding_done"]:
        render_onboarding(user)
        return

    render_topbar(user)
    page = render_sidebar(user)
    selected_date = st.date_input("Data de análise", value=date.today())
    games_df = get_live_games(selected_date.isoformat())

    if page == "Dashboard":
        render_dashboard(user, games_df)
    elif page == "Live Center":
        render_live_center(games_df)
    elif page == "Matchup Studio":
        render_matchup_studio(games_df)
    elif page == "Picks Lab":
        render_picks_lab(user, games_df)
    elif page == "Bankroll":
        render_bankroll(user)
    elif page == "Newsroom":
        render_newsroom()
    elif page == "Data Hub":
        render_data_hub()
    elif page == "Diagnóstico":
        render_diagnostics(games_df)
    elif page == "Configurações":
        render_settings(user)
    elif page == "Admin" and user["is_admin"]:
        render_admin()


if __name__ == "__main__":
    main()
