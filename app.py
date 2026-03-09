import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguedashteamstats, teamdashboardbygeneralsplits, teamgamelog
from nba_api.stats.static import teams
import plotly.express as px
import numpy as np

# Configuração
st.set_page_config(page_title="NBA ProBet Bot", layout="wide", page_icon="🏀")
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .metric-card { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏀 NBA ProBet Analytics")
st.markdown("### Análise Preditiva e Estatística Avançada")

# --- CACHE DE DADOS (Para não sobrecarregar a API) ---
@st.cache_data(ttl=3600) # Atualiza a cada 1 hora
def get_advanced_team_stats():
    try:
        # Pega estatísticas avançadas da liga (Pace, Def Rating, etc)
        df = leaguedashteamstats.LeagueDashTeamStats().get_data_frames()[0]
        return df
    except Exception as e:
        st.error(f"Erro na API: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_team_splits(team_id):
    try:
        # Pega divisão Casa/Fora
        df = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(team_id=team_id).get_data_frames()[1]
        return df
    except:
        return pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.header("⚙️ Configurações")
selected_season = st.sidebar.selectbox("Temporada", ["2023-24", "2024-25"])
show_advanced = st.sidebar.checkbox("Exibir Métricas Avançadas", value=True)

# --- DADOS PRINCIPAIS ---
df_stats = get_advanced_team_stats()

if not df_stats.empty:
    # 1. DASHBOARD DE MÉTRICAS CHAVE
    st.subheader("🔥 Top Métricas para Apostas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Pace (Ritmo) - Bom para Over/Under
    top_pace = df_stats.loc[df_stats['PACE'].idxmax()]
    col1.metric("Maior Pace (Ritmo)", f"{top_pace['TEAM_CITY']} ({top_pace['PACE']:.1f})", "Mais posses = Mais pontos")
    
    # Defensive Rating (Defesa) - Bom para Under
    best_def = df_stats.loc[df_stats['DEF_RATING'].idxmin()]
    col2.metric("Melhor Defesa", f"{best_def['TEAM_CITY']} ({best_def['DEF_RATING']:.1f})", "Sofre menos pontos")
    
    # 3PT Allowed (Defesa de 3)
    worst_3pt_def = df_stats.loc[df_stats['OPP_3P_PCT'].idxmax()]
    col3.metric("Pior Defesa 3pts", f"{worst_3pt_def['TEAM_CITY']} ({worst_3pt_def['OPP_3P_PCT']*100:.1f}%)", "Oportunidade de 3pts")
    
    # Rebound Rate
    top_reb = df_stats.loc[df_stats['REB_PCT'].idxmax()]
    col4.metric("Rei dos Rebotes", f"{top_reb['TEAM_CITY']} ({top_reb['REB_PCT']*100:.1f}%)", "Domínio no garrafão")

    st.divider()

    # 2. ANÁLISE DE MATCHUP (Simulação)
    st.subheader("🆚 Analisador de Confronto (Matchup)")
    team_list = df_stats['TEAM_CITY'].unique()
    team_a = st.selectbox("Time da Casa", team_list, index=0)
    team_b = st.selectbox("Time Visitante", team_list, index=1)

    if team_a != team_b:
        data_a = df_stats[df_stats['TEAM_CITY'] == team_a].iloc[0]
        data_b = df_stats[df_stats['TEAM_CITY'] == team_b].iloc[0]

        # Lógica de Sugestão
        score_a = 0
        score_b = 0
        insights = []

        # Lógica 1: Pace
        avg_pace = df_stats['PACE'].mean()
        if data_a['PACE'] > avg_pace and data_b['DEF_RATING'] > df_stats['DEF_RATING'].mean():
            insights.append("✅ Tendência de OVER de Pontos (Ritmo alto vs Defesa fraca)")
            score_a += 1
        elif data_a['PACE'] < avg_pace and data_b['DEF_RATING'] < df_stats['DEF_RATING'].mean():
            insights.append("✅ Tendência de UNDER de Pontos (Ritmo lento vs Defesa forte)")
        
        # Lógica 2: 3 Pontos
        if data_b['OPP_3P_PCT'] > 0.36: # Se o time B deixa bater muito 3
            insights.append(f"✅ {team_a} pode ter sucesso em chutes de 3pts")

        st.info("💡 **Insights do Algoritmo:**")
        for i in insights:
            st.write(i)
        if not insights:
            st.write("⚠️ Confronto equilibrado, sem vantagem estatística clara.")

        # Gráfico Radar de Comparação
        st.markdown("#### Comparativo de Eficiência")
        df_radar = pd.DataFrame({
            'Métrica': ['Pace', 'Off Rating', 'Def Rating', '3PT%', 'Reb%'],
            team_a: [data_a['PACE'], data_a['OFF_RATING'], data_a['DEF_RATING'], data_a['FG3_PCT'], data_a['REB_PCT']],
            team_b: [data_b['PACE'], data_b['OFF_RATING'], data_b['DEF_RATING'], data_b['FG3_PCT'], data_b['REB_PCT']]
        })
        # Normalizar para o gráfico não quebrar (Def Rating quanto menor melhor, inverter para gráfico)
        df_radar[team_a][2] = 120 - df_radar[team_a][2] 
        df_radar[team_b][2] = 120 - df_radar[team_b][2]

        fig = px.line_polar(df_radar, r=[team_a, team_b], theta='Métrica', line_close=True, title=f"Radar: {team_a} vs {team_b}")
        st.plotly_chart(fig, use_container_width=True)

    # 3. TABELA COMPLETA
    with st.expander("Ver Tabela Completa de Estatísticas"):
        st.dataframe(df_stats[['TEAM_CITY', 'GP', 'W', 'L', 'PACE', 'OFF_RATING', 'DEF_RATING', 'NET_RATING']])

else:
    st.warning("Aguardando dados da API...")
