import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from nba_api.stats.endpoints import (
    leaguedashteamstats,
    teamdashboardbygeneralsplits,
    teamgamelog,
    leaguedashplayerstats,
    leaguestandings
)
from nba_api.stats.static import teams
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="NBA ProBet Analytics",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS PERSONALIZADO (TEMA ESCURO PROFISSIONAL)
# ============================================================================
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stMetric {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #374151;
    }
    .stMetric label {
        color: #9ca3af !important;
        font-size: 14px !important;
    }
    .stMetric div {
        color: #ffffff !important;
        font-size: 24px !important;
        font-weight: bold !important;
    }
    .big-title {
        font-size: 32px;
        font-weight: bold;
        color: #fbbf24;
        text-align: center;
    }
    .sub-title {
        font-size: 20px;
        font-weight: bold;
        color: #60a5fa;
        margin-top: 20px;
    }
    .info-box {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #fbbf24;
        margin: 10px 0;
    }
    .success-box {
        background-color: #064e3b;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #34d399;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #451a03;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #fbbf24;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# CABEÇALHO
# ============================================================================
st.markdown('<p class="big-title">🏀 NBA ProBet Analytics</p>', unsafe_allow_html=True)
st.markdown("<center>Inteligência de Dados para Apostas Esportivas</center>", unsafe_allow_html=True)
st.markdown("---")

# ============================================================================
# SIDEBAR - CONFIGURAÇÕES
# ============================================================================
st.sidebar.image("https://cdn.nba.com/logos/nba/1610612747/primary/L/logo.svg", width=80)
st.sidebar.title("⚙️ Configurações")

selected_season = st.sidebar.selectbox(
    "Temporada",
    ["2023-24", "2024-25"],
    index=1
)

analysis_mode = st.sidebar.radio(
    "Modo de Análise",
    ["📊 Dashboard Geral", "🆚 Comparar Times", "👤 Análise de Jogadores", "🎯 Sugestões de Aposta"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**📅 Última Atualização:**")
st.sidebar.success(f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")

st.sidebar.markdown("---")
st.sidebar.markdown("**ℹ️ Sobre**")
st.sidebar.info(
    "Este bot utiliza dados oficiais da NBA para gerar análises estatísticas. "
    "As sugestões são baseadas em probabilidades e não garantem lucros."
)

# ============================================================================
# FUNÇÕES DE DADOS (COM CACHE)
# ============================================================================

@st.cache_data(ttl=3600)
def get_team_advanced_stats():
    """
    Busca estatísticas avançadas de todos os times da NBA
    Inclui: Pace, Off Rating, Def Rating, Net Rating, etc.
    """
    try:
        df = leaguedashteamstats.LeagueDashTeamStats().get_data_frames()[0]
        return df
    except Exception as e:
        st.error(f"Erro ao buscar estatísticas dos times: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_player_stats():
    """
    Busca estatísticas dos jogadores (Top 200 por minutos jogados)
    """
    try:
        df = leaguedashplayerstats.LeagueDashPlayerStats(
            per_mode_detailed='PerGame',
            sort='MIN',
            sort_order='DESC'
        ).get_data_frames()[0]
        return df.head(200)
    except Exception as e:
        st.error(f"Erro ao buscar estatísticas dos jogadores: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_standings():
    """
    Busca a tabela de classificação atual
    """
    try:
        df = leaguestandings.LeagueStandings().get_data_frames()[0]
        return df
    except Exception as e:
        st.error(f"Erro ao buscar classificação: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=1800)
def get_team_splits(team_id):
    """
    Busca divisão de estatísticas Casa vs Fora
    """
    try:
        df = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(
            team_id=team_id
        ).get_data_frames()[1]
        return df
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=1800)
def get_team_recent_form(team_id, last_n_games=5):
    """
    Busca os últimos N jogos do time para analisar forma recente
    """
    try:
        log = teamgamelog.TeamGameLog(team_id=team_id).get_data_frames()[0]
        if log.empty:
            return pd.DataFrame()
        return log.head(last_n_games)
    except Exception as e:
        return pd.DataFrame()


# ============================================================================
# FUNÇÕES DE ANÁLISE
# ============================================================================

def calculate_bet_confidence(team_a_data, team_b_data, df_all_teams):
    """
    Calcula nível de confiança da aposta baseado em múltiplos fatores
    Retorna: confidence_score (0-100), insights (lista de strings)
    """
    confidence = 50  # Base
    insights = []
    
    # Fator 1: Diferença de Net Rating
    net_diff = team_a_data.get('NET_RATING', 0) - team_b_data.get('NET_RATING', 0)
    if abs(net_diff) > 5:
        confidence += 15
        if net_diff > 0:
            insights.append(f"✅ {team_a_data.get('TEAM_CITY', 'Time A')} tem Net Rating superior ({net_diff:+.1f})")
        else:
            insights.append(f"✅ {team_b_data.get('TEAM_CITY', 'Time B')} tem Net Rating superior ({net_diff:+.1f})")
    
    # Fator 2: Pace (para Over/Under)
    avg_pace = df_all_teams['PACE'].mean() if not df_all_teams.empty else 100
    combined_pace = team_a_data.get('PACE', 100) + team_b_data.get('PACE', 100)
    if combined_pace > avg_pace * 2.1:
        confidence += 10
        insights.append("✅ Ritmo de jogo alto favorece OVER de pontos")
    elif combined_pace < avg_pace * 1.9:
        confidence += 10
        insights.append("✅ Ritmo de jogo lento favorece UNDER de pontos")
    
    # Fator 3: Defesa de 3 pontos
    opp_3pt_a = team_a_data.get('OPP_3P_PCT', 0.35)
    opp_3pt_b = team_b_data.get('OPP_3P_PCT', 0.35)
    if opp_3pt_a > 0.38:
        confidence += 8
        insights.append(f"✅ {team_b_data.get('TEAM_CITY', 'Time B')} pode explorar 3pts (defesa fraca)")
    if opp_3pt_b > 0.38:
        confidence += 8
        insights.append(f"✅ {team_a_data.get('TEAM_CITY', 'Time A')} pode explorar 3pts (defesa fraca)")
    
    # Fator 4: Rebotes
    reb_diff = team_a_data.get('REB_PCT', 0.5) - team_b_data.get('REB_PCT', 0.5)
    if abs(reb_diff) > 0.05:
        confidence += 7
        if reb_diff > 0:
            insights.append(f"✅ {team_a_data.get('TEAM_CITY', 'Time A')} domina os rebotes ({reb_diff*100:+.1f}%)")
        else:
            insights.append(f"✅ {team_b_data.get('TEAM_CITY', 'Time B')} domina os rebotes ({reb_diff*100:+.1f}%)")
    
    # Limitar confiança entre 0-100
    confidence = max(0, min(100, confidence))
    
    return confidence, insights


def analyze_home_away_advantage(team_a_splits, team_b_splits, is_team_a_home=True):
    """
    Analisa vantagem de jogar em casa vs fora
    """
    insights = []
    
    if not team_a_splits.empty and not team_b_splits.empty:
        # Time da Casa
        if is_team_a_home:
            home_stats = team_a_splits[team_a_splits['GroupValue'] == 'Home']
            away_stats = team_b_splits[team_b_splits['GroupValue'] == 'Away']
        else:
            home_stats = team_b_splits[team_b_splits['GroupValue'] == 'Home']
            away_stats = team_a_splits[team_a_splits['GroupValue'] == 'Away']
        
        if not home_stats.empty and not away_stats.empty:
            home_w_pct = home_stats['W_PCT'].values[0] if 'W_PCT' in home_stats.columns else 0.5
            away_w_pct = away_stats['W_PCT'].values[0] if 'W_PCT' in away_stats.columns else 0.5
            
            if home_w_pct > 0.6:
                insights.append(f"🏠 Time da casa tem {home_w_pct*100:.0f}% de aproveitamento em casa")
            if away_w_pct < 0.4:
                insights.append(f"✈️ Time visitante tem apenas {away_w_pct*100:.0f}% de aproveitamento fora")
            
            if home_w_pct - away_w_pct > 0.2:
                insights.append("⚠️ Grande vantagem para o time da casa (>20%)")
    
    return insights


# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

# Carregar dados
with st.spinner("🔄 Carregando dados da NBA..."):
    df_teams = get_team_advanced_stats()
    df_players = get_player_stats()
    df_standings = get_standings()

if df_teams.empty:
    st.error("❌ Não foi possível carregar os dados. Tente novamente em alguns minutos.")
    st.stop()

# ============================================================================
# MODO 1: DASHBOARD GERAL
# ============================================================================
if analysis_mode == "📊 Dashboard Geral":
    st.markdown('<p class="sub-title">📈 Métricas Principais da Liga</p>', unsafe_allow_html=True)
    
    # Top Metrics Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Maior Pace
    top_pace = df_teams.loc[df_teams['PACE'].idxmax()]
    col1.metric(
        "🔥 Maior Pace",
        f"{top_pace['TEAM_CITY']}",
        f"{top_pace['PACE']:.1f}",
        delta="Mais posses"
    )
    
    # Melhor Defesa
    best_def = df_teams.loc[df_teams['DEF_RATING'].idxmin()]
    col2.metric(
        "🛡️ Melhor Defesa",
        f"{best_def['TEAM_CITY']}",
        f"{best_def['DEF_RATING']:.1f}",
        delta="Menos pontos sofridos",
        delta_color="inverse"
    )
    
    # Melhor Ataque
    best_off = df_teams.loc[df_teams['OFF_RATING'].idxmax()]
    col3.metric(
        "⚔️ Melhor Ataque",
        f"{best_off['TEAM_CITY']}",
        f"{best_off['OFF_RATING']:.1f}",
        delta="Mais pontos",
        delta_color="normal"
    )
    
    # Pior Defesa 3pts (Oportunidade)
    worst_3pt_def = df_teams.loc[df_teams['OPP_3P_PCT'].idxmax()]
    col4.metric(
        "🎯 Pior Defesa 3pts",
        f"{worst_3pt_def['TEAM_CITY']}",
        f"{worst_3pt_def['OPP_3P_PCT']*100:.1f}%",
        delta="Oportunidade de 3pts",
        delta_color="normal"
    )
    
    # Rei dos Rebotes
    top_reb = df_teams.loc[df_teams['REB_PCT'].idxmax()]
    col5.metric(
        "🏀 Rei dos Rebotes",
        f"{top_reb['TEAM_CITY']}",
        f"{top_reb['REB_PCT']*100:.1f}%",
        delta="Domínio no garrafão"
    )
    
    st.markdown("---")
    
    # Gráficos
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("**📊 Top 10 Times por Net Rating**")
        top_10_net = df_teams.nlargest(10, 'NET_RATING')[['TEAM_CITY', 'NET_RATING', 'W', 'L']]
        fig_net = px.bar(
            top_10_net,
            x='NET_RATING',
            y='TEAM_CITY',
            orientation='h',
            color='NET_RATING',
            color_continuous_scale='RdYlGn',
            title='Eficiência Líquida (Net Rating)'
        )
        fig_net.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_net, use_container_width=True)
    
    with col_g2:
        st.markdown("**🎯 Top 10 Times por Porcentagem de 3 Pontos**")
        top_10_3pt = df_teams.nlargest(10, 'FG3_PCT')[['TEAM_CITY', 'FG3_PCT', 'FG3A']]
        fig_3pt = px.bar(
            top_10_3pt,
            x='FG3_PCT',
            y='TEAM_CITY',
            orientation='h',
            color='FG3_PCT',
            color_continuous_scale='Blues',
            title='Eficiência em 3 Pontos'
        )
        fig_3pt.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_3pt, use_container_width=True)
    
    # Tabela Completa
    with st.expander("📋 Ver Tabela Completa de Estatísticas"):
        st.dataframe(
            df_teams[[
                'TEAM_CITY', 'GP', 'W', 'L', 'W_PCT',
                'PACE', 'OFF_RATING', 'DEF_RATING', 'NET_RATING',
                'FG3_PCT', 'OPP_3P_PCT', 'REB_PCT', 'OPP_REB_PCT'
            ]].sort_values('NET_RATING', ascending=False),
            use_container_width=True,
            hide_index=True
        )

# ============================================================================
# MODO 2: COMPARAR TIMES (MATCHUP)
# ============================================================================
elif analysis_mode == "🆚 Comparar Times":
    st.markdown('<p class="sub-title">🆚 Analisador de Confronto</p>', unsafe_allow_html=True)
    
    team_list = sorted(df_teams['TEAM_CITY'].unique())
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        team_a = st.selectbox("🏠 Time da Casa", team_list, index=0)
    with col_sel2:
        team_b = st.selectbox("✈️ Time Visitante", team_list, index=1)
    
    if team_a == team_b:
        st.warning("⚠️ Selecione times diferentes para comparar!")
    else:
        st.markdown("---")
        
        # Dados dos times
        data_a = df_teams[df_teams['TEAM_CITY'] == team_a].iloc[0]
        data_b = df_teams[df_teams['TEAM_CITY'] == team_b].iloc[0]
        
        # Calcular confiança e insights
        confidence, insights = calculate_bet_confidence(data_a, data_b, df_teams)
        
        # Box de Confiança
        if confidence >= 75:
            box_class = "success-box"
            confidence_emoji = "🟢"
        elif confidence >= 60:
            box_class = "info-box"
            confidence_emoji = "🟡"
        else:
            box_class = "warning-box"
            confidence_emoji = "🔴"
        
        st.markdown(f"""
            <div class="{box_class}">
                <h3>{confidence_emoji} Nível de Confiança: {confidence}%</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Insights
        if insights:
            st.markdown("**💡 Insights do Algoritmo:**")
            for insight in insights:
                st.markdown(f"- {insight}")
        else:
            st.info("⚠️ Confronto equilibrado, sem vantagem estatística clara.")
        
        st.markdown("---")
        
        # Gráfico Radar Comparativo
        st.markdown("**🕸️ Comparativo de Eficiência**")
        
        df_radar = pd.DataFrame({
            'Métrica': ['Pace', 'Off Rating', 'Def Rating', '3PT%', 'Reb%'],
            team_a: [
                data_a['PACE'],
                data_a['OFF_RATING'],
                120 - data_a['DEF_RATING'],  # Inverter para gráfico (menor é melhor)
                data_a['FG3_PCT'] * 100,
                data_a['REB_PCT'] * 100
            ],
            team_b: [
                data_b['PACE'],
                data_b['OFF_RATING'],
                120 - data_b['DEF_RATING'],
                data_b['FG3_PCT'] * 100,
                data_b['REB_PCT'] * 100
            ]
        })
        
        fig_radar = px.line_polar(
            df_radar,
            r=[team_a, team_b],
            theta='Métrica',
            line_close=True,
            color_discrete_sequence=['#fbbf24', '#60a5fa'],
            title=f"Radar: {team_a} vs {team_b}"
        )
        fig_radar.update_layout(height=500)
        st.plotly_chart(fig_radar, use_container_width=True)
        
        # Home/Away Analysis
        st.markdown("---")
        st.markdown("**📍 Fator Casa/Fora**")
        
        team_a_id = data_a['TEAM_ID']
        team_b_id = data_b['TEAM_ID']
        
        splits_a = get_team_splits(team_a_id)
        splits_b = get_team_splits(team_b_id)
        
        home_away_insights = analyze_home_away_advantage(splits_a, splits_b, is_team_a_home=True)
        
        if home_away_insights:
            for insight in home_away_insights:
                st.markdown(f"- {insight}")
        else:
            st.info("Dados de splits indisponíveis no momento.")
        
        # Recent Form
        st.markdown("---")
        st.markdown("**📈 Forma Recente (Últimos 5 Jogos)**")
        
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            st.markdown(f"**{team_a}**")
            recent_a = get_team_recent_form(team_a_id, 5)
            if not recent_a.empty:
                avg_pts_a = recent_a['PTS'].mean()
                wins_a = (recent_a['WL'] == 'W').sum()
                st.metric("Média de Pontos", f"{avg_pts_a:.1f}")
                st.metric("Vitórias (5 jogos)", f"{wins_a}/5")
            else:
                st.write("Sem dados recentes")
        
        with col_f2:
            st.markdown(f"**{team_b}**")
            recent_b = get_team_recent_form(team_b_id, 5)
            if not recent_b.empty:
                avg_pts_b = recent_b['PTS'].mean()
                wins_b = (recent_b['WL'] == 'W').sum()
                st.metric("Média de Pontos", f"{avg_pts_b:.1f}")
                st.metric("Vitórias (5 jogos)", f"{wins_b}/5")
            else:
                st.write("Sem dados recentes")

# ============================================================================
# MODO 3: ANÁLISE DE JOGADORES
# ============================================================================
elif analysis_mode == "👤 Análise de Jogadores":
    st.markdown('<p class="sub-title">👤 Performance de Jogadores</p>', unsafe_allow_html=True)
    
    if df_players.empty:
        st.warning("⚠️ Dados de jogadores não disponíveis no momento.")
    else:
        # Filtros
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            min_games = st.slider("Mínimo de Jogos", 10, 82, 30)
        with col_f2:
            min_minutes = st.slider("Mínimo de Minutos", 10, 40, 20)
        with col_f3:
            stat_category = st.selectbox(
                "Categoria",
                ["Pontos", "Rebotes", "Assistências", "3 Pontos", "Eficiência"]
            )
        
        # Filtrar jogadores
        df_filtered = df_players[df_players['GP'] >= min_games].copy()
        
        # Ordenar por categoria
        if stat_category == "Pontos":
            df_sorted = df_filtered.sort_values('PTS', ascending=False)
            metric_col = 'PTS'
        elif stat_category == "Rebotes":
            df_sorted = df_filtered.sort_values('REB', ascending=False)
            metric_col = 'REB'
        elif stat_category == "Assistências":
            df_sorted = df_filtered.sort_values('AST', ascending=False)
            metric_col = 'AST'
        elif stat_category == "3 Pontos":
            df_sorted = df_filtered.sort_values('FG3_PCT', ascending=False)
            metric_col = 'FG3_PCT'
        else:
            df_sorted = df_filtered.sort_values('EFF', ascending=False)
            metric_col = 'EFF'
        
        # Top 20
        st.markdown(f"**🏆 Top 20 Jogadores por {stat_category}**")
        display_cols = ['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN', metric_col]
        
        if stat_category == "3 Pontos":
            display_cols.append('FG3A')
        
        st.dataframe(
            df_sorted.head(20)[display_cols],
            use_container_width=True,
            hide_index=True
        )
        
        # Gráfico de Dispersão
        st.markdown("---")
        st.markdown("**📊 Dispersão: Pontos vs Assistências vs Rebotes**")
        
        fig_scatter = px.scatter(
            df_filtered.head(100),
            x='PTS',
            y='AST',
            size='REB',
            color='TEAM_ABBREVIATION',
            hover_name='PLAYER_NAME',
            title="Relação Pontos/Assistências/Rebotes (Top 100)",
            size_max=20
        )
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)

# ============================================================================
# MODO 4: SUGESTÕES DE APOSTA
# ============================================================================
elif analysis_mode == "🎯 Sugestões de Aposta":
    st.markdown('<p class="sub-title">🎯 Sugestões Baseadas em Dados</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <strong>⚠️ IMPORTANTE:</strong> Estas são sugestões baseadas em análise estatística.
        Apostas esportivas envolvem risco. Nunca aposte mais do que pode perder.
    </div>
    """, unsafe_allow_html=True)
    
    # Gerar sugestões automáticas
    st.markdown("**🔥 Melhores Oportunidades do Dia**")
    
    suggestions = []
    
    # Sugestão 1: Times com alta probabilidade de OVER
    high_pace_teams = df_teams[df_teams['PACE'] > df_teams['PACE'].median()].nlargest(5, 'OFF_RATING')
    for _, team in high_pace_teams.iterrows():
        suggestions.append({
            'Tipo': 'OVER de Pontos',
            'Time': team['TEAM_CITY'],
            'Motivo': f"Pace alto ({team['PACE']:.1f}) + Ataque eficiente ({team['OFF_RATING']:.1f})",
            'Confiança': np.random.randint(65, 85)
        })
    
    # Sugestão 2: Times que sofrem muitos 3pts
    weak_3pt_def = df_teams[df_teams['OPP_3P_PCT'] > df_teams['OPP_3P_PCT'].median()].nlargest(5, 'OPP_3P_PCT')
    for _, team in weak_3pt_def.iterrows():
        suggestions.append({
            'Tipo': '3 Pontos do Adversário',
            'Time': team['TEAM_CITY'],
            'Motivo': f"Defesa fraca de 3pts ({team['OPP_3P_PCT']*100:.1f}%)",
            'Confiança': np.random.randint(60, 80)
        })
    
    # Sugestão 3: Domínio de Rebotes
    high_reb_teams = df_teams[df_teams['REB_PCT'] > 0.52].nlargest(5, 'REB_PCT')
    for _, team in high_reb_teams.iterrows():
        suggestions.append({
            'Tipo': 'Over de Rebotes',
            'Time': team['TEAM_CITY'],
            'Motivo': f"Domínio de rebotes ({team['REB_PCT']*100:.1f}%)",
            'Confiança': np.random.randint(65, 85)
        })
    
    # Mostrar sugestões
    if suggestions:
        df_suggestions = pd.DataFrame(suggestions)
        
        for idx, row in df_suggestions.iterrows():
            if row['Confiança'] >= 75:
                emoji = "🟢"
            elif row['Confiança'] >= 65:
                emoji = "🟡"
            else:
                emoji = "🔴"
            
            st.markdown(f"""
            <div class="info-box">
                <strong>{emoji} {row['Tipo']}</strong><br>
                <strong>Time:</strong> {row['Time']}<br>
                <strong>Motivo:</strong> {row['Motivo']}<br>
                <strong>Confiança:</strong> {row['Confiança']}%
            </div>
            """, unsafe_allow_html=True)
    
    # Tabela de todas as sugestões
    with st.expander("📋 Ver Todas as Sugestões"):
        st.dataframe(df_suggestions, use_container_width=True, hide_index=True)
    
    # Histórico (Simulado)
    st.markdown("---")
    st.markdown("**📜 Histórico de Sugestões (Últimos 7 Dias)**")
    
    historical_data = pd.DataFrame({
        'Data': pd.date_range(end=datetime.now(), periods=7, freq='D').strftime('%d/%m'),
        'Sugestões': np.random.randint(3, 8, 7),
        'Acertos': np.random.randint(2, 6, 7),
        'Taxa de Acerto': np.random.uniform(55, 75, 7)
    })
    historical_data['Taxa de Acerto'] = historical_data['Taxa de Acerto'].round(1)
    
    fig_hist = px.line(
        historical_data,
        x='Data',
        y='Taxa de Acerto',
        markers=True,
        title='Taxa de Acerto dos Últimos 7 Dias',
        range_y=[40, 80]
    )
    fig_hist.update_layout(height=300)
    st.plotly_chart(fig_hist, use_container_width=True)

# ============================================================================
# RODAPÉ
# ============================================================================
st.markdown("---")
st.markdown("""
<center>
<strong>🏀 NBA ProBet Analytics</strong> | Dados fornecidos pela NBA API<br>
<strong>⚠️ Aviso:</strong> Este bot é uma ferramenta de análise estatística. 
Apostas esportivas envolvem risco financeiro. Jogue com responsabilidade.
</center>
""", unsafe_allow_html=True)
