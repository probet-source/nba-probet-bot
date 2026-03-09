import os
import sqlite3
import hashlib
from datetime import datetime, date
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

APP_TITLE = "NBA ProBet SaaS 4.0"
DB_PATH = "probet_saas.db"

st.set_page_config(page_title=APP_TITLE, page_icon="🏀", layout="wide")

# -----------------------------
# THEME / CSS
# -----------------------------
CUSTOM_CSS = """
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.hero {
    padding: 1.2rem 1.4rem;
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 22px;
    background: linear-gradient(135deg, rgba(30,41,59,.95), rgba(17,24,39,.95));
    margin-bottom: 1rem;
}
.card {
    padding: 1rem 1rem;
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    background: rgba(17,24,39,.60);
}
.small-muted {opacity: .78; font-size: .92rem;}
.metric-box {
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 1rem;
    background: rgba(15,23,42,.75);
}
.plan-card {
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 18px;
    padding: 1rem;
    background: rgba(17,24,39,.65);
    min-height: 260px;
}
.status-pill {
    display: inline-block;
    padding: .35rem .7rem;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,.10);
    font-size: .85rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------
# DATABASE
# -----------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
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
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()

    admin_email = os.getenv("APP_ADMIN_EMAIL", "admin@probet.local")
    admin_name = os.getenv("APP_ADMIN_NAME", "Administrador")
    admin_password = os.getenv("APP_ADMIN_PASSWORD", "admin123")
    if not get_user_by_email(admin_email):
        create_user(admin_name, admin_email, admin_password, plan="premium", is_admin=True)
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(name: str, email: str, password: str, plan: str = "free", is_admin: bool = False) -> Tuple[bool, str]:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
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
    conn.close()
    return user


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    row = cur.fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def update_user_plan(user_id: int, plan: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET plan = ? WHERE id = ?", (plan, user_id))
    conn.commit()
    conn.close()


def list_users() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT id, name, email, plan, is_admin, created_at, last_login FROM users ORDER BY id DESC",
        conn,
    )
    conn.close()
    return df


def insert_pick(user_id: int, game_label: str, market: str, pick: str, confidence: float, edge: float, stake_units: float):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO picks (user_id, created_at, game_label, market, pick, confidence, edge, stake_units)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, datetime.utcnow().isoformat(), game_label, market, pick, confidence, edge, stake_units),
    )
    conn.commit()
    conn.close()


def update_pick_result(pick_id: int, result: str, profit_units: float):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE picks SET result = ?, profit_units = ? WHERE id = ?", (result, profit_units, pick_id))
    conn.commit()
    conn.close()


def list_user_picks(user_id: int) -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT id, created_at, game_label, market, pick, confidence, edge, stake_units, result, profit_units FROM picks WHERE user_id = ? ORDER BY id DESC",
        conn,
        params=(user_id,),
    )
    conn.close()
    return df


def list_all_picks() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT p.*, u.email, u.plan FROM picks p LEFT JOIN users u ON p.user_id = u.id ORDER BY p.id DESC",
        conn,
    )
    conn.close()
    return df


def save_feedback(user_id: int, rating: int, message: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO feedback (user_id, created_at, rating, message) VALUES (?, ?, ?, ?)",
        (user_id, datetime.utcnow().isoformat(), rating, message.strip()),
    )
    conn.commit()
    conn.close()


def list_feedback() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT f.id, f.created_at, f.rating, f.message, u.email FROM feedback f LEFT JOIN users u ON f.user_id = u.id ORDER BY f.id DESC",
        conn,
    )
    conn.close()
    return df

# -----------------------------
# DATA ENGINE
# -----------------------------
TEAM_BASE = [
    ("Boston Celtics", "BOS"), ("Milwaukee Bucks", "MIL"), ("Denver Nuggets", "DEN"), ("Phoenix Suns", "PHX"),
    ("Los Angeles Lakers", "LAL"), ("Golden State Warriors", "GSW"), ("Dallas Mavericks", "DAL"), ("Minnesota Timberwolves", "MIN"),
    ("Oklahoma City Thunder", "OKC"), ("New York Knicks", "NYK"), ("Miami Heat", "MIA"), ("Philadelphia 76ers", "PHI")
]

PLAYERS = [
    ("Jayson Tatum", "Boston Celtics"), ("Jaylen Brown", "Boston Celtics"), ("Giannis Antetokounmpo", "Milwaukee Bucks"),
    ("Damian Lillard", "Milwaukee Bucks"), ("Nikola Jokic", "Denver Nuggets"), ("Jamal Murray", "Denver Nuggets"),
    ("Kevin Durant", "Phoenix Suns"), ("Devin Booker", "Phoenix Suns"), ("LeBron James", "Los Angeles Lakers"),
    ("Anthony Davis", "Los Angeles Lakers"), ("Stephen Curry", "Golden State Warriors"), ("Jimmy Butler", "Miami Heat"),
    ("Luka Doncic", "Dallas Mavericks"), ("Kyrie Irving", "Dallas Mavericks"), ("Shai Gilgeous-Alexander", "Oklahoma City Thunder"),
    ("Anthony Edwards", "Minnesota Timberwolves"), ("Joel Embiid", "Philadelphia 76ers"), ("Jalen Brunson", "New York Knicks")
]

@st.cache_data(ttl=3600)
def load_teams() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = []
    for idx, (team, abbr) in enumerate(TEAM_BASE):
        off = 110 + rng.uniform(0, 10)
        deff = 106 + rng.uniform(0, 10)
        pace = 97 + rng.uniform(0, 7)
        rebounds = 40 + rng.uniform(2, 9)
        threes = 10 + rng.uniform(2, 8)
        wins = int(rng.integers(32, 61))
        losses = 82 - wins
        form = int(rng.integers(4, 10))
        rows.append({
            "TEAM_NAME": team,
            "TEAM_ABBREVIATION": abbr,
            "OFF_RATING": round(off, 1),
            "DEF_RATING": round(deff, 1),
            "NET_RATING": round(off - deff, 1),
            "PACE": round(pace, 1),
            "REB": round(rebounds, 1),
            "3PM": round(threes, 1),
            "WINS": wins,
            "LOSSES": losses,
            "FORM_SCORE": form,
            "HOME_BONUS": round(rng.uniform(1.2, 3.4), 1),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def load_players() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    rows = []
    for name, team in PLAYERS:
        pts = rng.uniform(14, 33)
        ast = rng.uniform(2, 10)
        reb = rng.uniform(3, 13)
        usage = rng.uniform(18, 35)
        rows.append({
            "PLAYER_NAME": name,
            "TEAM_NAME": team,
            "PTS": round(pts, 1),
            "AST": round(ast, 1),
            "REB": round(reb, 1),
            "USG%": round(usage, 1),
            "VALUE_INDEX": round(pts * 0.6 + ast * 1.5 + reb * 1.1 + usage * 0.3, 1),
        })
    return pd.DataFrame(rows).sort_values("VALUE_INDEX", ascending=False)


@st.cache_data(ttl=600)
def load_games_today() -> pd.DataFrame:
    teams = load_teams().copy()
    today_pairs = [(0, 4), (1, 9), (2, 6), (3, 10), (5, 7), (8, 11)]
    rng = np.random.default_rng(9)
    rows = []
    for home_idx, away_idx in today_pairs:
        home = teams.iloc[home_idx]
        away = teams.iloc[away_idx]
        expected_home = 102 + (home["OFF_RATING"] - away["DEF_RATING"]) * 1.2 + home["HOME_BONUS"]
        expected_away = 100 + (away["OFF_RATING"] - home["DEF_RATING"]) * 1.1
        spread = round(expected_home - expected_away, 1)
        total = round(expected_home + expected_away, 1)
        conf = max(54, min(82, 58 + abs(spread) * 1.8 + rng.uniform(-2, 5)))
        rows.append({
            "GAME": f"{away['TEAM_ABBREVIATION']} @ {home['TEAM_ABBREVIATION']}",
            "HOME_TEAM": home["TEAM_NAME"],
            "AWAY_TEAM": away["TEAM_NAME"],
            "START_TIME": f"{17 + (home_idx % 5)}:30",
            "EXPECTED_HOME": round(expected_home, 1),
            "EXPECTED_AWAY": round(expected_away, 1),
            "PROJECTED_TOTAL": total,
            "PROJECTED_SPREAD": spread,
            "CONFIDENCE": round(conf, 1),
        })
    return pd.DataFrame(rows)


def calc_pick_for_game(row: pd.Series) -> dict:
    market = "spread" if abs(row["PROJECTED_SPREAD"]) >= 4 else "total"
    if market == "spread":
        pick = f"{row['HOME_TEAM']} {-row['PROJECTED_SPREAD']:+.1f}" if row["PROJECTED_SPREAD"] > 0 else f"{row['AWAY_TEAM']} {row['PROJECTED_SPREAD']:+.1f}"
        edge = abs(row["PROJECTED_SPREAD"]) * 1.7
    else:
        side = "OVER" if row["PROJECTED_TOTAL"] >= 223 else "UNDER"
        pick = f"{side} {row['PROJECTED_TOTAL']:.1f}"
        edge = abs(row["PROJECTED_TOTAL"] - 223) * 0.9
    confidence = max(55, min(88, row["CONFIDENCE"] + edge * 0.35))
    stake = round(max(0.5, min(4.5, edge / 4.0)), 1)
    return {
        "market": market,
        "pick": pick,
        "confidence": round(confidence, 1),
        "edge": round(edge, 1),
        "stake": stake,
    }

# -----------------------------
# SESSION
# -----------------------------
if "auth_user_id" not in st.session_state:
    st.session_state.auth_user_id = None
if "show_auth_mode" not in st.session_state:
    st.session_state.show_auth_mode = "login"


def current_user():
    if st.session_state.auth_user_id is None:
        return None
    return get_user_by_id(int(st.session_state.auth_user_id))


def login_ui():
    st.markdown(
        """
        <div class="hero">
            <h1 style="margin-bottom:.3rem;">🏀 NBA ProBet SaaS 4.0</h1>
            <p class="small-muted">Versão estilo SaaS real com cadastro, plano Free/Premium, painel de assinantes, histórico de picks, administração e monetização.</p>
            <span class="status-pill">Produto pronto para GitHub + Streamlit</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown("### Entrar")
        with st.form("login_form"):
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)
        if submitted:
            user = authenticate_user(email, password)
            if user:
                st.session_state.auth_user_id = user["id"]
                st.success("Login realizado com sucesso.")
                st.rerun()
            else:
                st.error("E-mail ou senha inválidos.")

    with col_b:
        st.markdown("### Criar conta")
        with st.form("register_form"):
            name = st.text_input("Nome")
            reg_email = st.text_input("E-mail de cadastro")
            reg_password = st.text_input("Senha de cadastro", type="password")
            plan = st.selectbox("Plano inicial", ["free", "premium"], index=0)
            ok = st.form_submit_button("Criar conta", use_container_width=True)
        if ok:
            if len(reg_password) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            elif "@" not in reg_email:
                st.error("Informe um e-mail válido.")
            else:
                success, msg = create_user(name, reg_email, reg_password, plan=plan)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="plan-card"><h4>Plano Free</h4><p>Dashboard, rankings, jogos do dia e até 3 picks salvos.</p><h3>R$ 0/mês</h3></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="plan-card"><h4>Plano Premium</h4><p>Picks Engine completo, bankroll, área premium, relatórios e exportações.</p><h3>R$ 49/mês</h3></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="plan-card"><h4>Admin</h4><p>Painel de assinantes, métricas do SaaS, feedback e operação do produto.</p><h3>Controle total</h3></div>', unsafe_allow_html=True)

# -----------------------------
# UI HELPERS
# -----------------------------
def render_header(user):
    st.sidebar.title("NBA ProBet 4.0")
    st.sidebar.caption("SaaS de picks e análise NBA")
    st.sidebar.success(f"Logado como: {user['name']}")
    st.sidebar.write(f"Plano: **{user['plan'].upper()}**")
    if user["is_admin"]:
        st.sidebar.info("Perfil administrador")
    if st.sidebar.button("Sair", use_container_width=True):
        st.session_state.auth_user_id = None
        st.rerun()


def render_dashboard(user, teams: pd.DataFrame, games: pd.DataFrame, picks_df: pd.DataFrame):
    st.markdown(
        f"""
        <div class="hero">
            <h2 style="margin-bottom:.2rem;">Bem-vindo, {user['name']}</h2>
            <p class="small-muted">Hoje é {date.today().strftime('%d/%m/%Y')}. Aqui está a visão geral da sua operação no produto.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    premium_count = int((list_users()["plan"] == "premium").sum())
    total_users = len(list_users())
    open_picks = int((picks_df["result"] == "open").sum()) if not picks_df.empty else 0
    roi = round((picks_df["profit_units"].sum() / max(1, picks_df["stake_units"].sum())) * 100, 1) if not picks_df.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Usuários", total_users)
    c2.metric("Premium", premium_count)
    c3.metric("Picks abertas", open_picks)
    c4.metric("ROI pessoal", f"{roi:.1f}%")

    col1, col2 = st.columns([1.2, 1])
    with col1:
        fig = px.scatter(
            teams,
            x="OFF_RATING",
            y="DEF_RATING",
            size="PACE",
            color="NET_RATING",
            hover_name="TEAM_NAME",
            title="Mapa de força dos times",
        )
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        leaderboard = teams.sort_values("NET_RATING", ascending=False)[["TEAM_NAME", "NET_RATING", "PACE", "WINS"]].head(8)
        st.subheader("Leaderboard de times")
        st.dataframe(leaderboard, use_container_width=True, hide_index=True)

    st.subheader("Melhores picks do dia")
    picks_preview = []
    for _, game in games.iterrows():
        p = calc_pick_for_game(game)
        picks_preview.append({
            "Jogo": game["GAME"],
            "Mercado": p["market"],
            "Pick": p["pick"],
            "Confiança": p["confidence"],
            "Stake": p["stake"],
        })
    st.dataframe(pd.DataFrame(picks_preview), use_container_width=True, hide_index=True)


def render_games_today(user, games: pd.DataFrame):
    st.subheader("Jogos do dia")
    st.caption("Projeções internas com spread, total, confiança e stake.")
    for _, row in games.iterrows():
        p = calc_pick_for_game(row)
        with st.container(border=True):
            a, b, c, d = st.columns([2.2, 1, 1, 1])
            a.markdown(f"**{row['GAME']}**  
{row['AWAY_TEAM']} vs {row['HOME_TEAM']}")
            b.metric("Total", row["PROJECTED_TOTAL"])
            c.metric("Spread", row["PROJECTED_SPREAD"])
            d.metric("Confiança", f"{p['confidence']}%")
            st.write(f"**Sugestão:** {p['pick']} | Mercado: {p['market']} | Stake: {p['stake']}u | Edge: {p['edge']}")
            can_save = True
            user_picks = list_user_picks(user["id"])
            if user["plan"] == "free" and len(user_picks) >= 3:
                can_save = False
            if st.button(f"Salvar pick: {row['GAME']}", key=f"save_{row['GAME']}", disabled=not can_save):
                insert_pick(user["id"], row["GAME"], p["market"], p["pick"], p["confidence"], p["edge"], p["stake"])
                st.success("Pick salva no histórico.")
                st.rerun()
            if not can_save:
                st.info("Plano Free permite até 3 picks salvas. Faça upgrade para continuar.")


def render_matchup_lab(teams: pd.DataFrame):
    st.subheader("Matchup Lab")
    team_names = teams["TEAM_NAME"].tolist()
    c1, c2 = st.columns(2)
    team_a = c1.selectbox("Time A", team_names, index=0)
    team_b = c2.selectbox("Time B", team_names, index=1)
    a = teams.loc[teams["TEAM_NAME"] == team_a].iloc[0]
    b = teams.loc[teams["TEAM_NAME"] == team_b].iloc[0]

    compare_df = pd.DataFrame({
        "Métrica": ["OFF_RATING", "DEF_RATING", "NET_RATING", "PACE", "REB", "3PM", "WINS", "FORM_SCORE"],
        team_a: [a["OFF_RATING"], a["DEF_RATING"], a["NET_RATING"], a["PACE"], a["REB"], a["3PM"], a["WINS"], a["FORM_SCORE"]],
        team_b: [b["OFF_RATING"], b["DEF_RATING"], b["NET_RATING"], b["PACE"], b["REB"], b["3PM"], b["WINS"], b["FORM_SCORE"]],
    })
    st.dataframe(compare_df, use_container_width=True, hide_index=True)

    radar_df = pd.DataFrame({
        "Métrica": ["OFF_RATING", "NET_RATING", "PACE", "REB", "3PM", "FORM_SCORE"],
        team_a: [a["OFF_RATING"], a["NET_RATING"], a["PACE"], a["REB"], a["3PM"], a["FORM_SCORE"]],
        team_b: [b["OFF_RATING"], b["NET_RATING"], b["PACE"], b["REB"], b["3PM"], b["FORM_SCORE"]],
    })
    melted = radar_df.melt(id_vars="Métrica", var_name="Time", value_name="Valor")
    fig = px.line_polar(melted, r="Valor", theta="Métrica", color="Time", line_close=True, title="Radar comparativo")
    st.plotly_chart(fig, use_container_width=True)

    projected_margin = round((a["NET_RATING"] - b["NET_RATING"]) + (a["HOME_BONUS"] if a["WINS"] >= b["WINS"] else 0.8), 1)
    winner = team_a if projected_margin >= 0 else team_b
    st.success(f"Projeção interna: vantagem para **{winner}** por aproximadamente **{abs(projected_margin):.1f} pontos**.")


def render_player_hub(players: pd.DataFrame):
    st.subheader("Player Hub")
    search = st.text_input("Buscar jogador")
    filtered = players.copy()
    if search:
        filtered = filtered[filtered["PLAYER_NAME"].str.contains(search, case=False, na=False)]
    top_n = st.slider("Top jogadores", min_value=5, max_value=18, value=10)
    st.dataframe(filtered.head(top_n), use_container_width=True, hide_index=True)
    fig = px.bar(filtered.head(top_n), x="PLAYER_NAME", y="VALUE_INDEX", color="TEAM_NAME", title="Value Index")
    st.plotly_chart(fig, use_container_width=True)


def render_picks_engine(user, games: pd.DataFrame):
    st.subheader("Picks Engine")
    st.caption("Área premium para gerar picks prontas para operação.")
    if user["plan"] != "premium":
        st.warning("Faça upgrade para o plano Premium para liberar o Picks Engine completo.")
        return
    options = games["GAME"].tolist()
    selected = st.selectbox("Escolha um jogo", options)
    row = games.loc[games["GAME"] == selected].iloc[0]
    p = calc_pick_for_game(row)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mercado", p["market"])
    c2.metric("Confiança", f"{p['confidence']}%")
    c3.metric("Edge", p["edge"])
    c4.metric("Stake", f"{p['stake']}u")
    st.success(f"Pick principal: **{p['pick']}**")
    rationale = [
        f"Net rating do mando e encaixe ofensivo/defensivo favorecem a leitura.",
        f"Projeção total de {row['PROJECTED_TOTAL']} pontos.",
        f"Spread projetado em {row['PROJECTED_SPREAD']}.",
        f"Confiança algorítmica final de {p['confidence']}%."
    ]
    st.write("\n".join([f"- {r}" for r in rationale]))
    if st.button("Salvar pick premium", use_container_width=True):
        insert_pick(user["id"], row["GAME"], p["market"], p["pick"], p["confidence"], p["edge"], p["stake"])
        st.success("Pick premium salva.")
        st.rerun()


def render_bankroll(user):
    st.subheader("Bankroll Tracker")
    picks = list_user_picks(user["id"])
    if picks.empty:
        st.info("Você ainda não salvou picks.")
        return
    editable = picks.copy()
    editable["resultado_manual"] = editable["result"]
    editable["lucro_manual"] = editable["profit_units"]
    st.dataframe(editable, use_container_width=True, hide_index=True)

    with st.expander("Atualizar resultado de uma pick"):
        pick_ids = picks["id"].tolist()
        pick_id = st.selectbox("Selecione a pick", pick_ids)
        result = st.selectbox("Resultado", ["open", "win", "loss", "void"])
        profit = st.number_input("Lucro/Prejuízo (unidades)", value=0.0, step=0.5)
        if st.button("Atualizar resultado"):
            update_pick_result(int(pick_id), result, float(profit))
            st.success("Resultado atualizado.")
            st.rerun()

    closed = picks[picks["result"].isin(["win", "loss", "void"])]
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de picks", len(picks))
    c2.metric("Lucro acumulado", f"{picks['profit_units'].sum():.1f}u")
    hit_rate = (len(closed[closed["result"] == "win"]) / len(closed) * 100) if len(closed) else 0
    c3.metric("Hit rate", f"{hit_rate:.1f}%")
    if len(closed):
        closed = closed.sort_values("created_at")
        closed["bankroll_curve"] = closed["profit_units"].cumsum()
        fig = px.line(closed, x="created_at", y="bankroll_curve", title="Curva da bankroll")
        st.plotly_chart(fig, use_container_width=True)
    csv = picks.to_csv(index=False).encode("utf-8")
    st.download_button("Exportar histórico CSV", data=csv, file_name="historico_picks.csv", mime="text/csv")


def render_plan_upgrade(user):
    st.subheader("Planos e monetização")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="plan-card"><h4>Free</h4><p>Dashboard, rankings, matchup e até 3 picks.</p><h2>R$ 0</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="plan-card"><h4>Premium</h4><p>Picks Engine, bankroll tracker, exportações, área premium e prioridade.</p><h2>R$ 49/mês</h2></div>', unsafe_allow_html=True)
    if user["plan"] != "premium":
        if st.button("Fazer upgrade local para Premium", use_container_width=True):
            update_user_plan(user["id"], "premium")
            st.success("Plano atualizado para Premium.")
            st.rerun()
    else:
        st.success("Sua conta já está no plano Premium.")


def render_feedback(user):
    st.subheader("Feedback do produto")
    with st.form("feedback_form"):
        rating = st.slider("Nota do produto", min_value=1, max_value=5, value=5)
        message = st.text_area("Comentário")
        submit = st.form_submit_button("Enviar feedback")
    if submit:
        save_feedback(user["id"], rating, message)
        st.success("Feedback registrado.")


def render_admin_panel():
    st.subheader("Painel administrativo")
    users = list_users()
    picks = list_all_picks()
    feedback = list_feedback()
    revenue_mrr = int((users["plan"] == "premium").sum()) * 49

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de usuários", len(users))
    c2.metric("Premium ativos", int((users["plan"] == "premium").sum()))
    c3.metric("MRR estimado", f"R$ {revenue_mrr}")
    c4.metric("Feedbacks", len(feedback))

    tab1, tab2, tab3 = st.tabs(["Usuários", "Picks", "Feedback"])
    with tab1:
        st.dataframe(users, use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(picks, use_container_width=True, hide_index=True)
    with tab3:
        st.dataframe(feedback, use_container_width=True, hide_index=True)

# -----------------------------
# MAIN
# -----------------------------
init_db()
user = current_user()
if not user:
    login_ui()
    st.stop()

teams = load_teams()
players = load_players()
games = load_games_today()
user_picks_df = list_user_picks(user["id"])

render_header(user)
menu = ["Dashboard", "Jogos do Dia", "Matchup Lab", "Player Hub", "Picks Engine", "Bankroll", "Planos", "Feedback"]
if user["is_admin"]:
    menu.append("Admin")
choice = st.sidebar.radio("Navegação", menu)

if choice == "Dashboard":
    render_dashboard(user, teams, games, user_picks_df)
elif choice == "Jogos do Dia":
    render_games_today(user, games)
elif choice == "Matchup Lab":
    render_matchup_lab(teams)
elif choice == "Player Hub":
    render_player_hub(players)
elif choice == "Picks Engine":
    render_picks_engine(user, games)
elif choice == "Bankroll":
    render_bankroll(user)
elif choice == "Planos":
    render_plan_upgrade(user)
elif choice == "Feedback":
    render_feedback(user)
elif choice == "Admin" and user["is_admin"]:
    render_admin_panel()
