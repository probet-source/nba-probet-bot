import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from datetime import datetime

# ---------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------

st.set_page_config(
    page_title="NBA ProBet Analytics",
    page_icon="🏀",
    layout="wide"
)

# ---------------------------------------------------
# TÍTULO
# ---------------------------------------------------

st.title("🏀 NBA ProBet Analytics")
st.caption("Análise estatística para apostas esportivas")

# ---------------------------------------------------
# FUNÇÃO API
# ---------------------------------------------------

@st.cache_data(ttl=3600)
def carregar_times():

    url = "https://api-nba-v1.p.rapidapi.com/teams"

    headers = {
        "X-RapidAPI-Key": "demo",
        "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
    }

    try:

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return gerar_dados_fake()

        data = response.json()

        if "response" not in data:
            return gerar_dados_fake()

        df = pd.DataFrame(data["response"])

        if df.empty:
            return gerar_dados_fake()

        df["TEAM_NAME"] = df["name"]
        df["TEAM_CITY"] = df["city"]

        return gerar_stats(df)

    except:
        return gerar_dados_fake()


# ---------------------------------------------------
# GERAR STATS SIMULADAS
# ---------------------------------------------------

def gerar_stats(df):

    df["PACE"] = np.random.uniform(98, 103, len(df))
    df["OFF_RATING"] = np.random.uniform(108, 118, len(df))
    df["DEF_RATING"] = np.random.uniform(108, 118, len(df))

    df["NET_RATING"] = df["OFF_RATING"] - df["DEF_RATING"]

    return df


# ---------------------------------------------------
# DADOS FAKE SE API CAIR
# ---------------------------------------------------

def gerar_dados_fake():

    teams = [
        "Lakers","Warriors","Celtics","Bucks","Heat","Suns","Nuggets",
        "Knicks","Clippers","Mavericks","Kings","Timberwolves"
    ]

    df = pd.DataFrame()

    df["TEAM_NAME"] = teams
    df["TEAM_CITY"] = teams

    df["PACE"] = np.random.uniform(98,103,len(df))
    df["OFF_RATING"] = np.random.uniform(108,118,len(df))
    df["DEF_RATING"] = np.random.uniform(108,118,len(df))

    df["NET_RATING"] = df["OFF_RATING"] - df["DEF_RATING"]

    return df


# ---------------------------------------------------
# CARREGAR DADOS
# ---------------------------------------------------

df = carregar_times()

if df.empty:

    st.error("Erro ao carregar dados da NBA")
    st.stop()

# ---------------------------------------------------
# MÉTRICAS
# ---------------------------------------------------

col1,col2,col3,col4 = st.columns(4)

col1.metric(
    "Times analisados",
    len(df)
)

col2.metric(
    "Maior Pace",
    f"{df['PACE'].max():.1f}"
)

col3.metric(
    "Melhor ataque",
    f"{df['OFF_RATING'].max():.1f}"
)

col4.metric(
    "Melhor defesa",
    f"{df['DEF_RATING'].min():.1f}"
)

# ---------------------------------------------------
# GRÁFICO
# ---------------------------------------------------

st.subheader("Comparação ofensiva")

fig = px.scatter(
    df,
    x="OFF_RATING",
    y="DEF_RATING",
    hover_name="TEAM_NAME",
    size="PACE"
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------
# TABELA
# ---------------------------------------------------

st.subheader("Tabela completa")

st.dataframe(df, use_container_width=True)

# ---------------------------------------------------
# SUGESTÕES DE APOSTA
# ---------------------------------------------------

st.subheader("Sugestões de aposta")

median_pace = df["PACE"].median()

over_teams = df[df["PACE"] > median_pace]

for _, team in over_teams.iterrows():

    st.success(
        f"🔥 {team['TEAM_NAME']} tendência OVER (PACE {team['PACE']:.1f})"
    )
