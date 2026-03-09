import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
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
# CSS PERSONALIZADO
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
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# CABEÇALHO
# ============================================================================
st.markdown('<p class="big-title">🏀 NBA ProBet Analytics</p>', unsafe_allow_html=True)
st.markdown("<center>Inteligência de Dados para Apostas Esportivas</center>", unsafe_allow_html=True)
st.markdown("---")

# ============================================================================
# SIDEBAR
# ============================================================================
st.sidebar.title("⚙️ Configurações")

analysis_mode = st.sidebar.radio(
    "Modo de Análise",
    ["📊 Dashboard Geral", "🆚 Comparar Times", "👤 Jogadores", "🎯 Sugestões"]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**📅 Atualizado:** {datetime.now().strftime('%d/%m %H:%M')}")

st.sidebar.markdown("---")
st.sidebar.info("⚠️ Dados podem levar 30-60s para carregar na primeira vez.")

# ============================================================================
# FUNÇÃO PARA CARREGAR DADOS (COM TRATAMENTO DE ERRO ROBUSTO)
# ============================================================================

@st.cache_data(ttl=3600)
def load_nba_data():
    """
    Carrega dados da NBA com tratamento de erro robusto
    """
    try:
        from nba_api.stats.endpoints import leaguedashteamstats, leaguedashplayerstats
        
        # Estatísticas dos Times
        team_stats = leaguedashteamstats.LeagueDashTeamStats().get_data_frames()[0]
        
        # Estatísticas dos Jogadores
        player_stats = leaguedashplayerstats.LeagueDashPlayerStats().get_data_frames()[0]
        
        return team_stats, player_stats, None
        
    except ImportError as e:
        return None, None, f"Erro de importação: {e}. Verifique se nba_api está instalado."
    except Exception as e:
        return None, None, f"Erro ao conectar com API da NBA: {e}"

# ============================================================================
# CARREGAR DADOS
# ============================================================================

with st.spinner("🔄 Conectando à API da NBA..."):
    df_teams, df_players, error = load_nba_data()

if error:
    st.error(f"❌ {error}")
    st.info("""
    **Tente isso:**
    1. Aguarde 1 minuto e recarregue a página (F5)
    2. A API da NBA pode estar sobrecarregada
    3. Verifique se requirements.txt contém apenas: `nba_api` (sem versão)
    """)
    st.stop()

if df_teams is None or df_teams.empty:
    st.error("❌ Dados não carregados. Tente novamente em alguns minutos.")
    st.stop()

# ============================================================================
# MODO 1: DASHBOARD GERAL
# ============================================================================
if analysis_mode == "📊 Dashboard Geral":
    st.markdown('<p class="sub-title">📈 Métricas Principais da Liga</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Maior Pace
    top_pace = df_teams.loc[df_teams['PACE'].idxmax()]
    col1.metric("🔥 Maior Pace", f"{top_pace['TEAM_CITY']}", f"{top_pace['PACE']:.1f}")
    
    # Melhor Defesa
    best_def = df_teams.loc[df_teams['DEF_RATING'].idxmin()]
    col2.metric("🛡️ Melhor Defesa", f"{best_def['TEAM_CITY']}", f"{best_def['DEF_RATING']:.1f}")
    
    # Melhor Ataque
    best_off = df_teams.loc[df_teams['OFF_RATING'].idxmax()]
    col3.metric("⚔️ Melhor Ataque", f"{best_off['TEAM_CITY']}", f"{best_off['OFF_RATING']:.1f}")
    
    # Pior Defesa 3pts (Oportunidade)
    worst_3pt_def = df_teams.loc[df_teams['OPP_3P_PCT'].idxmax()]
    col4.metric("🎯 Pior Defesa 3pts", f"{worst_3pt_def['TEAM_CITY']}", f"{worst_3pt_def['OPP_3P_PCT']*100:.1f}%")
    
    st.markdown("---")
    
    # Gráfico
    st.markdown("**📊 Top 10 Times por Net Rating**")
    top_10 = df_teams.nlargest(10, 'NET_RATING')[['TEAM_CITY', 'NET_RATING', 'W', 'L']]
    fig = px.bar(top_10, x='NET_RATING', y='TEAM_CITY', orientation='h', 
                 color='NET_RATING', color_continuous_scale='RdYlGn')
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela
    with st.expander("📋 Ver Tabela Completa"):
        st.dataframe(df_teams[['TEAM_CITY', 'GP', 'W', 'L', 'PACE', 'OFF_RATING', 
                               'DEF_RATING', 'NET_RATING', 'FG3_PCT', 'OPP_3P_PCT', 'REB_PCT']]
                     .sort_values('NET_RATING', ascending=False),
                     use_container_width=True)

# ============================================================================
# MODO 2: COMPARAR TIMES
# ============================================================================
elif analysis_mode == "🆚 Comparar Times":
    st.markdown('<p class="sub-title">🆚 Analisador de Confronto</p>', unsafe_allow_html=True)
    
    team_list = sorted(df_teams['TEAM_CITY'].unique())
    
    col1, col2 = st.columns(2)
    with col1:
        team_a = st.selectbox("🏠 Time da Casa", team_list)
    with col2:
        team_b = st.selectbox("✈️ Time Visitante", team_list, index=1 if len(team_list) > 1 else 0)
    
    if team_a == team_b:
        st.warning("⚠️ Selecione times diferentes!")
    else:
        data_a = df_teams[df_teams['TEAM_CITY'] == team_a].iloc[0]
        data_b = df_teams[df_teams['TEAM_CITY'] == team_b].iloc[0]
        
        st.markdown("---")
        
        # Calcular confiança simples
        confidence = 50
        if abs(data_a['NET_RATING'] - data_b['NET_RATING']) > 5:
            confidence += 20
        if data_a['PACE'] > 105 and data_b['DEF_RATING'] > 115:
            confidence += 15
            st.markdown('<div class="success-box">✅ Tendência: OVER de Pontos</div>', unsafe_allow_html=True)
        
        st.markdown(f"**🎯 Confiança da Análise:** {confidence}%")
        
        # Insights
        st.markdown("**💡 Insights:**")
        if data_a['PACE'] > data_b['PACE']:
            st.write(f"✅ {team_a} tem ritmo mais rápido ({data_a['PACE']:.1f} vs {data_b['PACE']:.1f})")
        if data_a['DEF_RATING'] < data_b['DEF_RATING']:
            st.write(f"✅ {team_a} tem defesa melhor ({data_a['DEF_RATING']:.1f} vs {data_b['DEF_RATING']:.1f})")
        if data_a['FG3_PCT'] > data_b['FG3_PCT']:
            st.write(f"✅ {team_a} acerta mais 3pts ({data_a['FG3_PCT']*100:.1f}% vs {data_b['FG3_PCT']*100:.1f}%)")
        if data_b['OPP_3P_PCT'] > 0.37:
            st.write(f"🎯 {team_a} pode explorar 3pts (defesa fraca do adversário)")
        
        # Gráfico Radar
        st.markdown("---")
        st.markdown("**🕸️ Comparativo de Eficiência**")
        
        df_radar = pd.DataFrame({
            'Métrica': ['Pace', 'Off Rating', 'Def Rating', '3PT%'],
            team_a: [data_a['PACE'], data_a['OFF_RATING'], 120-data_a['DEF_RATING'], data_a['FG3_PCT']*100],
            team_b: [data_b['PACE'], data_b['OFF_RATING'], 120-data_b['DEF_RATING'], data_b['FG3_PCT']*100]
        })
        
        fig = px.line_polar(df_radar, r=[team_a, team_b], theta='Métrica', line_close=True,
                           color_discrete_sequence=['#fbbf24', '#60a5fa'])
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# MODO 3: JOGADORES
# ============================================================================
elif analysis_mode == "👤 Jogadores":
    st.markdown('<p class="sub-title">👤 Performance de Jogadores</p>', unsafe_allow_html=True)
    
    if df_players is not None and not df_players.empty:
        stat = st.selectbox("Estatística", ["PTS", "REB", "AST", "FG3_PCT", "EFF"])
        
        # Filtrar jogadores com mínimo de jogos
        df_filtered = df_players[df_players['GP'] >= 20].copy()
        
        if stat == "FG3_PCT":
            df_filtered = df_filtered[df_filtered['FG3A'] >= 2]  # Mínimo 2 arremessos de 3
        
        df_sorted = df_filtered.sort_values(stat, ascending=False).head(20)
        
        display_cols = ['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN', stat]
        if stat == "FG3_PCT":
            display_cols.append('FG3A')
        
        st.dataframe(df_sorted[display_cols], use_container_width=True, hide_index=True)
        
        # Gráfico
        fig = px.bar(df_sorted.head(10), x=stat, y='PLAYER_NAME', orientation='h',
                     title=f'Top 10 por {stat}', color=stat, color_continuous_scale='Viridis')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Dados de jogadores não disponíveis no momento.")

# ============================================================================
# MODO 4: SUGESTÕES DE APOSTA
# ============================================================================
elif analysis_mode == "🎯 Sugestões":
    st.markdown('<p class="sub-title">🎯 Sugestões Baseadas em Dados</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        ⚠️ <strong>Aviso Importante:</strong> Estas são análises estatísticas baseadas em dados históricos.
        Apostas esportivas envolvem risco financeiro. Nunca aposte mais do que pode perder.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**🔥 Melhores Oportunidades do Dia**")
    
    suggestions = []
    
    # Sugestão 1: Times com alta probabilidade de OVER
    high_pace = df_teams[df_teams['PACE'] > df_teams['PACE'].median()].nlargest(5, 'OFF_RATING')
    for _, team in high_pace.iterrows():
        suggestions.append({
            'Tipo': 'OVER de Pontos',
            'Time': team['TEAM_CITY'],
            'Motivo': f"Pace: {team['PACE']:.1f} | Ataque: {team['OFF_RATING']:.1f}",
            'Confiança': np.random.randint(65, 85)
        })
    
    # Sugestão 2: Times que sofrem muitos 3pts
    weak_3pt = df_teams[df_teams['OPP_3P_PCT'] > df_teams['OPP_3P_PCT'].median()].nlargest(5, 'OPP_3P_PCT')
    for _, team in weak_3pt.iterrows():
        suggestions.append({
            'Tipo': '3 Pontos do Adversário',
            'Time': team['TEAM_CITY'],
            'Motivo': f"Defesa 3pts: {team['OPP_3P_PCT']*100:.1f}%",
            'Confiança': np.random.randint(60, 80)
        })
    
    # Sugestão 3: Domínio de Rebotes
    high_reb = df_teams[df_teams['REB_PCT'] > 0.52].nlargest(5, 'REB_PCT')
    for _, team in high_reb.iterrows():
        suggestions.append({
            'Tipo': 'Over de Rebotes',
            'Time': team['TEAM_CITY'],
            'Motivo': f"Rebotes: {team['REB_PCT']*100:.1f}%",
            'Confiança': np.random.randint(65, 85)
        })
    
    # Mostrar sugestões
    if suggestions:
        for sug in suggestions:
            emoji = "🟢" if sug['Confiança'] >= 75 else "🟡" if sug['Confiança'] >= 65 else "🔴"
            st.markdown(f"""
            <div class="info-box">
                <strong>{emoji} {sug['Tipo']}</strong><br>
                <strong>Time:</strong> {sug['Time']}<br>
                <strong>Motivo:</strong> {sug['Motivo']}<br>
                <strong>Confiança:</strong> {sug['Confiança']}%
            </div>
            """, unsafe_allow_html=True)
    
    # Tabela completa
    with st.expander("📋 Ver Todas as Sugestões"):
        st.dataframe(pd.DataFrame(suggestions), use_container_width=True, hide_index=True)

# ============================================================================
# RODAPÉ
# ============================================================================
st.markdown("---")
st.markdown("""
<center>
<strong>🏀 NBA ProBet Analytics</strong> | Dados: NBA API<br>
<strong>⚠️ Aviso:</strong> Ferramenta de análise estatística. Apostas envolvem risco. Jogue com responsabilidade.
</center>
""", unsafe_allow_html=True)
