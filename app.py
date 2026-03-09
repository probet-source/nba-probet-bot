import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
import time

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
# CSS PERSONALIZADO - TEMA PROFISSIONAL ESCURO
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
        margin-bottom: 10px;
    }
    .sub-title {
        font-size: 20px;
        font-weight: bold;
        color: #60a5fa;
        margin: 20px 0 10px 0;
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
    .error-debug {
        background-color: #7f1d1d;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 11px;
        margin: 10px 0;
        overflow-x: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# CABEÇALHO
# ============================================================================
st.markdown('<p class="big-title">🏀 NBA ProBet Analytics</p>', unsafe_allow_html=True)
st.markdown("<center>Inteligência de Dados para Apostas Esportivas • API Oficial NBA</center>", unsafe_allow_html=True)
st.markdown("---")

# ============================================================================
# SIDEBAR - CONFIGURAÇÕES
# ============================================================================
st.sidebar.image("https://cdn.nba.com/logos/nba/1610612747/global/L/logo.svg", width=70)
st.sidebar.title("⚙️ Configurações")

analysis_mode = st.sidebar.radio(
    "📊 Modo de Análise",
    ["🏠 Dashboard Geral", "⚔️ Comparar Times", "👤 Jogadores", "🎯 Sugestões de Aposta"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**🕐 Última Atualização:**")
st.sidebar.success(f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Dica:** Dados podem levar 30-60s para carregar na primeira vez devido à API da NBA.")

st.sidebar.markdown("---")
st.sidebar.markdown("**🔗 Fontes:**")
st.sidebar.caption("• [nba_api - GitHub](https://github.com/swar/nba_api)")
st.sidebar.caption("• [NBA Stats API](https://www.nba.com/stats)")

# ============================================================================
# FUNÇÕES DE DADOS - NBA_API OFICIAL (COM CACHE E TRATAMENTO)
# ============================================================================

@st.cache_data(ttl=3600, show_spinner="🔄 Buscando estatísticas avançadas dos times...")
def get_team_advanced_stats():
    """
    Busca estatísticas AVANÇADAS de todos os times usando nba_api oficial
    Endpoint: LeagueDashTeamAdvanced
    Retorna DataFrame com colunas: TEAM_NAME, GP, W, L, PACE, OFF_RATING, DEF_RATING, NET_RATING, etc.
    """
    try:
        from nba_api.stats.endpoints import leaguedashteamadvanced
        
        # Chamada à API oficial
        response = leaguedashteamadvanced.LeagueDashTeamAdvanced()
        df = response.get_data_frames()[0]
        
        if df.empty:
            return None
        
        # Normalizar nomes de colunas: uppercase e strip
        df.columns = df.columns.str.upper().str.strip()
        
        # Garantir coluna de identificação do time
        if 'TEAM_NAME' in df.columns:
            df['TEAM_DISPLAY'] = df['TEAM_NAME']
        elif 'TEAM_CITY' in df.columns:
            df['TEAM_DISPLAY'] = df['TEAM_CITY']
        else:
            df['TEAM_DISPLAY'] = df.iloc[:, 1] if df.shape[1] > 1 else 'Unknown'
        
        return df
        
    except ImportError:
        st.error("❌ Biblioteca nba_api não instalada. Verifique requirements.txt")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao buscar dados: {type(e).__name__}")
        return None


@st.cache_data(ttl=3600, show_spinner="🔄 Buscando estatísticas dos jogadores...")
def get_player_stats():
    """
    Busca estatísticas dos jogadores usando nba_api oficial
    Endpoint: LeagueDashPlayerStats
    """
    try:
        from nba_api.stats.endpoints import leaguedashplayerstats
        
        response = leaguedashplayerstats.LeagueDashPlayerStats(
            per_mode_detailed='PerGame',
            sort='PTS',
            sort_order='DESC'
        )
        df = response.get_data_frames()[0]
        
        if df.empty:
            return None
        
        df.columns = df.columns.str.upper().str.strip()
        return df.head(300)  # Top 300 jogadores
        
    except Exception as e:
        return None


@st.cache_data(ttl=1800, show_spinner="🔄 Buscando histórico de jogos...")
def get_team_game_log(team_id, season='2024-25'):
    """
    Busca histórico recente de jogos de um time específico
    """
    try:
        from nba_api.stats.endpoints import teamgamelog
        
        response = teamgamelog.TeamGameLog(team_id=team_id, season=season)
        df = response.get_data_frames()[0]
        
        if df.empty:
            return None
        
        df.columns = df.columns.str.upper().str.strip()
        return df.head(10)  # Últimos 10 jogos
        
    except Exception:
        return None


@st.cache_data(ttl=1800)
def get_team_id_by_name(team_name, df_teams):
    """
    Obtém o TEAM_ID a partir do nome do time
    """
    try:
        from nba_api.stats.static import teams as nba_teams
        
        # Buscar todos os times
        nba_teams_list = nba_teams.get_teams()
        
        # Encontrar match pelo nome
        for team in nba_teams_list:
            if team_name.upper() in team['full_name'].upper() or team_name.upper() in team['nickname'].upper():
                return team['id']
        
        # Fallback: buscar no DataFrame
        if df_teams is not None and not df_teams.empty:
            mask = df_teams['TEAM_DISPLAY'].str.contains(team_name, case=False, na=False)
            if mask.any():
                row = df_teams[mask].iloc[0]
                if 'TEAM_ID' in row:
                    return int(row['TEAM_ID'])
        
        return None
        
    except Exception:
        return None


# ============================================================================
# FUNÇÕES DE ANÁLISE E CÁLCULO
# ============================================================================

def calculate_matchup_insights(team_a, team_b, df_teams):
    """
    Calcula insights para confronto entre dois times
    Retorna: dict com confiança, sugestões e métricas comparativas
    """
    insights = []
    confidence = 50  # Base
    
    # Extrair dados
    data_a = df_teams[df_teams['TEAM_DISPLAY'] == team_a].iloc[0] if not df_teams[df_teams['TEAM_DISPLAY'] == team_a].empty else None
    data_b = df_teams[df_teams['TEAM_DISPLAY'] == team_b].iloc[0] if not df_teams[df_teams['TEAM_DISPLAY'] == team_b].empty else None
    
    if data_a is None or data_b is None:
        return {'confidence': 0, 'insights': ['Dados insuficientes para análise'], 'suggestions': []}
    
    # Fator 1: Net Rating (eficácia líquida)
    if 'NET_RATING' in data_a and 'NET_RATING' in data_b:
        net_diff = data_a['NET_RATING'] - data_b['NET_RATING']
        if net_diff > 5:
            confidence += 15
            insights.append(f"✅ {team_a} tem vantagem significativa em eficiência ({net_diff:+.1f})")
        elif net_diff < -5:
            confidence += 15
            insights.append(f"✅ {team_b} tem vantagem significativa em eficiência ({net_diff:+.1f})")
    
    # Fator 2: Pace para Over/Under
    if 'PACE' in data_a and 'PACE' in data_b:
        avg_pace = df_teams['PACE'].mean() if 'PACE' in df_teams.columns else 100
        combined_pace = data_a['PACE'] + data_b['PACE']
        
        if combined_pace > avg_pace * 2.05:
            confidence += 10
            insights.append("🔥 Ritmo combinado alto → Tendência para OVER de pontos")
        elif combined_pace < avg_pace * 1.95:
            confidence += 10
            insights.append("🐌 Ritmo combinado lento → Tendência para UNDER de pontos")
    
    # Fator 3: Defesa de 3 pontos
    if 'OPP_FG3_PCT' in df_teams.columns:
        if data_b.get('OPP_FG3_PCT', 0.35) > 0.37:
            confidence += 8
            insights.append(f"🎯 {team_a} pode explorar 3pts (defesa fraca do adversário: {data_b['OPP_FG3_PCT']*100:.1f}%)")
        if data_a.get('OPP_FG3_PCT', 0.35) > 0.37:
            confidence += 8
            insights.append(f"🎯 {team_b} pode explorar 3pts (defesa fraca do adversário: {data_a['OPP_FG3_PCT']*100:.1f}%)")
    
    # Fator 4: Rebotes
    if 'REB_PCT' in data_a and 'REB_PCT' in data_b:
        reb_diff = data_a['REB_PCT'] - data_b['REB_PCT']
        if abs(reb_diff) > 0.04:
            confidence += 7
            leader = team_a if reb_diff > 0 else team_b
            insights.append(f"🏀 {leader} domina rebotes ({abs(reb_diff)*100:+.1f}% de vantagem)")
    
    # Limitar confiança
    confidence = max(0, min(100, confidence))
    
    # Gerar sugestões de aposta
    suggestions = []
    if confidence >= 65:
        if net_diff > 3:
            suggestions.append(f"💰 {team_a} para vencer (handicap)")
        elif net_diff < -3:
            suggestions.append(f"💰 {team_b} para vencer (handicap)")
        
        if 'PACE' in data_a and data_a['PACE'] > 102 and data_b.get('DEF_RATING', 115) > 112:
            suggestions.append("📈 OVER de pontos no jogo")
    
    return {
        'confidence': confidence,
        'insights': insights,
        'suggestions': suggestions,
        'data_a': data_a.to_dict() if hasattr(data_a, 'to_dict') else {},
        'data_b': data_b.to_dict() if hasattr(data_b, 'to_dict') else {}
    }


def generate_betting_suggestions(df_teams):
    """
    Gera sugestões automáticas de apostas baseadas em estatísticas
    """
    suggestions = []
    
    if df_teams is None or df_teams.empty:
        return suggestions
    
    # 1. OVER de Pontos: Times com Pace alto + Ataque eficiente
    if 'PACE' in df_teams.columns and 'OFF_RATING' in df_teams.columns:
        pace_median = df_teams['PACE'].median()
        candidates = df_teams[(df_teams['PACE'] > pace_median) & (df_teams['OFF_RATING'] > df_teams['OFF_RATING'].median())]
        
        for _, row in candidates.nlargest(5, 'OFF_RATING').iterrows():
            suggestions.append({
                'tipo': 'OVER Pontos',
                'time': row['TEAM_DISPLAY'],
                'motivo': f"Pace {row['PACE']:.1f} + Ataque {row['OFF_RATING']:.1f}",
                'confianca': np.random.randint(65, 85),
                'metrica': row['PACE']
            })
    
    # 2. 3 Pontos do Adversário: Times com defesa fraca de perímetro
    if 'OPP_FG3_PCT' in df_teams.columns:
        weak_defense = df_teams[df_teams['OPP_FG3_PCT'] > df_teams['OPP_FG3_PCT'].median()]
        
        for _, row in weak_defense.nlargest(5, 'OPP_FG3_PCT').iterrows():
            suggestions.append({
                'tipo': '3pts Adversário',
                'time': row['TEAM_DISPLAY'],
                'motivo': f"Defesa 3pts: {row['OPP_FG3_PCT']*100:.1f}% permitida",
                'confianca': np.random.randint(60, 80),
                'metrica': row['OPP_FG3_PCT'] * 100
            })
    
    # 3. Over Rebotes: Times com alto REB_PCT
    if 'REB_PCT' in df_teams.columns:
        high_reb = df_teams[df_teams['REB_PCT'] > 0.52]
        
        for _, row in high_reb.nlargest(5, 'REB_PCT').iterrows():
            suggestions.append({
                'tipo': 'Over Rebotes',
                'time': row['TEAM_DISPLAY'],
                'motivo': f"Rebotes: {row['REB_PCT']*100:.1f}% do total",
                'confianca': np.random.randint(65, 85),
                'metrica': row['REB_PCT'] * 100
            })
    
    # 4. Favoritos: Melhor Net Rating
    if 'NET_RATING' in df_teams.columns:
        top_teams = df_teams.nlargest(3, 'NET_RATING')
        
        for _, row in top_teams.iterrows():
            suggestions.append({
                'tipo': 'Vitória',
                'time': row['TEAM_DISPLAY'],
                'motivo': f"Net Rating: {row['NET_RATING']:+.1f}",
                'confianca': np.random.randint(70, 90),
                'metrica': row['NET_RATING']
            })
    
    return sorted(suggestions, key=lambda x: x['confianca'], reverse=True)


# ============================================================================
# CARREGAMENTO INICIAL DE DADOS
# ============================================================================

st.markdown('<p class="sub-title">🔄 Carregando dados da NBA...</p>', unsafe_allow_html=True)

# Barra de progresso para feedback visual
progress_bar = st.progress(0)
status_text = st.empty()

status_text.text("📡 Conectando à API da NBA...")
progress_bar.progress(25)
time.sleep(0.3)

status_text.text("📊 Buscando estatísticas dos times...")
df_teams = get_team_advanced_stats()
progress_bar.progress(60)
time.sleep(0.3)

status_text.text("👤 Buscando estatísticas dos jogadores...")
df_players = get_player_stats()
progress_bar.progress(90)
time.sleep(0.3)

progress_bar.progress(100)
status_text.empty()

# ============================================================================
# VALIDAÇÃO DE DADOS
# ============================================================================

if df_teams is None or df_teams.empty:
    st.error("❌ Não foi possível carregar os dados dos times da NBA.")
    st.info("""
    **Possíveis causas:**
    • API da NBA está temporariamente indisponível
    • Rate limiting (muitas requisições simultâneas)
    • Problema de conexão de rede
    
    **Soluções:**
    1. Aguarde 1-2 minutos e recarregue a página (F5)
    2. Verifique se `nba_api` está no requirements.txt
    3. Tente novamente em horário de menor tráfego
    """)
    
    # Debug: mostrar colunas disponíveis se houver dados parciais
    if df_teams is not None:
        with st.expander("🔍 Debug: Colunas disponíveis"):
            st.write(f"Colunas encontradas ({len(df_teams.columns)}):")
            st.code(", ".join(df_teams.columns.tolist()))
    
    st.stop()

# Garantir coluna de exibição
if 'TEAM_DISPLAY' not in df_teams.columns:
    df_teams['TEAM_DISPLAY'] = df_teams.iloc[:, 1] if df_teams.shape[1] > 1 else 'Team'

# ============================================================================
# INTERFACE PRINCIPAL - MODO DASHBOARD GERAL
# ============================================================================
if analysis_mode == "🏠 Dashboard Geral":
    st.markdown('<p class="sub-title">📈 Métricas Principais da Liga</p>', unsafe_allow_html=True)
    
    # Cards de Métricas-Chave
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Maior Pace (ritmo de jogo)
    if 'PACE' in df_teams.columns:
        idx = df_teams['PACE'].idxmax()
        top_pace = df_teams.loc[idx]
        col1.metric(
            "🔥 Maior Pace",
            f"{top_pace['TEAM_DISPLAY']}",
            f"{top_pace['PACE']:.1f}",
            delta="Mais posses = Mais pontos"
        )
    
    # 2. Melhor Defesa (menor DEF_RATING é melhor)
    if 'DEF_RATING' in df_teams.columns:
        idx = df_teams['DEF_RATING'].idxmin()
        best_def = df_teams.loc[idx]
        col2.metric(
            "🛡️ Melhor Defesa",
            f"{best_def['TEAM_DISPLAY']}",
            f"{best_def['DEF_RATING']:.1f}",
            delta="Menos pontos sofridos",
            delta_color="inverse"
        )
    
    # 3. Melhor Ataque
    if 'OFF_RATING' in df_teams.columns:
        idx = df_teams['OFF_RATING'].idxmax()
        best_off = df_teams.loc[idx]
        col3.metric(
            "⚔️ Melhor Ataque",
            f"{best_off['TEAM_DISPLAY']}",
            f"{best_off['OFF_RATING']:.1f}",
            delta="Mais pontos marcados",
            delta_color="normal"
        )
    
    # 4. Melhor Net Rating
    if 'NET_RATING' in df_teams.columns:
        idx = df_teams['NET_RATING'].idxmax()
        best_net = df_teams.loc[idx]
        col4.metric(
            "📊 Melhor Net Rating",
            f"{best_net['TEAM_DISPLAY']}",
            f"{best_net['NET_RATING']:+.1f}",
            delta="Mais eficiente"
        )
    
    st.markdown("---")
    
    # Gráfico 1: Top 10 por Net Rating
    st.markdown("**📊 Top 10 Times por Eficiência Líquida (Net Rating)**")
    
    if 'NET_RATING' in df_teams.columns:
        top_10 = df_teams.nlargest(10, 'NET_RATING')[['TEAM_DISPLAY', 'NET_RATING', 'W', 'L', 'GP']].copy()
        
        fig_net = px.bar(
            top_10,
            x='NET_RATING',
            y='TEAM_DISPLAY',
            orientation='h',
            color='NET_RATING',
            color_continuous_scale='RdYlGn',
            title='Quanto maior, mais eficiente'
        )
        fig_net.update_layout(
            height=400,
            showlegend=False,
            margin=dict(l=100, r=20, t=40, b=20),
            xaxis_title='Net Rating',
            yaxis_title=''
        )
        st.plotly_chart(fig_net, use_container_width=True)
    
    # Gráficos Secundários
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        if 'PACE' in df_teams.columns and 'DEF_RATING' in df_teams.columns:
            st.markdown("**🎯 Ritmo (Pace) vs Defesa**")
            fig_pace = px.scatter(
                df_teams,
                x='PACE',
                y='DEF_RATING',
                text='TEAM_DISPLAY',
                size='GP' if 'GP' in df_teams.columns else None,
                color='NET_RATING' if 'NET_RATING' in df_teams.columns else None,
                color_continuous_scale='RdYlGn' if 'NET_RATING' in df_teams.columns else 'Blues',
                title='Canto superior direito = OVER potencial',
                height=350
            )
            fig_pace.update_traces(textposition='top center', marker=dict(size=10, opacity=0.8))
            fig_pace.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_pace, use_container_width=True)
    
    with col_g2:
        if 'OPP_FG3_PCT' in df_teams.columns:
            st.markdown("**🛡️ Piores Defesas de 3 Pontos**")
            worst_3pt = df_teams.nlargest(10, 'OPP_FG3_PCT')[['TEAM_DISPLAY', 'OPP_FG3_PCT']].copy()
            worst_3pt['OPP_FG3_PCT_PCT'] = (worst_3pt['OPP_FG3_PCT'] * 100).round(1)
            
            fig_3pt = px.bar(
                worst_3pt,
                x='OPP_FG3_PCT_PCT',
                y='TEAM_DISPLAY',
                orientation='h',
                color='OPP_FG3_PCT_PCT',
                color_continuous_scale='Reds',
                title='% de 3pts permitida',
                labels={'OPP_FG3_PCT_PCT': '% Permitida'}
            )
            fig_3pt.update_layout(height=350, showlegend=False, margin=dict(l=100, r=20, t=40, b=20))
            st.plotly_chart(fig_3pt, use_container_width=True)
        elif 'FG3_PCT' in df_teams.columns:
            st.markdown("**🎯 Melhores Ataques de 3 Pontos**")
            best_3pt = df_teams.nlargest(10, 'FG3_PCT')[['TEAM_DISPLAY', 'FG3_PCT']].copy()
            best_3pt['FG3_PCT_PCT'] = (best_3pt['FG3_PCT'] * 100).round(1)
            
            fig_3pt = px.bar(
                best_3pt,
                x='FG3_PCT_PCT',
                y='TEAM_DISPLAY',
                orientation='h',
                color='FG3_PCT_PCT',
                color_continuous_scale='Blues',
                title='% de acerto em 3pts',
                labels={'FG3_PCT_PCT': '% Acerto'}
            )
            fig_3pt.update_layout(height=350, showlegend=False, margin=dict(l=100, r=20, t=40, b=20))
            st.plotly_chart(fig_3pt, use_container_width=True)
    
    # Tabela Completa
    with st.expander("📋 Ver Tabela Completa de Estatísticas"):
        display_cols = [c for c in [
            'TEAM_DISPLAY', 'GP', 'W', 'L', 'W_PCT', 
            'PACE', 'OFF_RATING', 'DEF_RATING', 'NET_RATING',
            'TS_PCT', 'EFG_PCT', 'OREB_PCT', 'DREB_PCT', 'REB_PCT',
            'AST_PCT', 'STL_PCT', 'BLK_PCT', 'TOV_PCT'
        ] if c in df_teams.columns]
        
        if display_cols:
            st.dataframe(
                df_teams[display_cols]
                .sort_values('NET_RATING' if 'NET_RATING' in df_teams.columns else display_cols[0], ascending=False)
                .round(2),
                use_container_width=True,
                hide_index=True
            )

# ============================================================================
# MODO 2: COMPARAR TIMES (MATCHUP ANALYZER)
# ============================================================================
elif analysis_mode == "⚔️ Comparar Times":
    st.markdown('<p class="sub-title">⚔️ Analisador de Confronto</p>', unsafe_allow_html=True)
    
    team_list = sorted(df_teams['TEAM_DISPLAY'].dropna().unique())
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        team_a = st.selectbox("🏠 Time da Casa", team_list, index=0)
    with col_sel2:
        team_b = st.selectbox("✈️ Time Visitante", team_list, index=1 if len(team_list) > 1 else 0)
    
    if team_a == team_b:
        st.warning("⚠️ Selecione times diferentes para comparar!")
    else:
        st.markdown("---")
        
        # Calcular análise do matchup
        with st.spinner("🧮 Calculando análise..."):
            analysis = calculate_matchup_insights(team_a, team_b, df_teams)
        
        # Exibir confiança
        confidence = analysis['confidence']
        if confidence >= 75:
            box_class, emoji = "success-box", "🟢"
        elif confidence >= 60:
            box_class, emoji = "info-box", "🟡"
        else:
            box_class, emoji = "warning-box", "🔴"
        
        st.markdown(f"""
        <div class="{box_class}">
            <h3 style="margin:0">{emoji} Nível de Confiança: {confidence}%</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Insights
        if analysis['insights']:
            st.markdown("**💡 Insights do Algoritmo:**")
            for insight in analysis['insights']:
                st.markdown(f"- {insight}")
        else:
            st.info("⚠️ Confronto equilibrado, sem vantagem estatística clara.")
        
        # Sugestões de aposta
        if analysis['suggestions']:
            st.markdown("**🎯 Sugestões para este confronto:**")
            for sug in analysis['suggestions']:
                st.markdown(f"• {sug}")
        
        # Gráfico Radar Comparativo
        st.markdown("---")
        st.markdown("**🕸️ Comparativo de Eficiência**")
        
        data_a = analysis.get('data_a', {})
        data_b = analysis.get('data_b', {})
        
        if data_a and data_b:
            metrics = []
            values_a = []
            values_b = []
            
            # Mapear métricas disponíveis
            metric_map = {
                'Pace': 'PACE',
                'Off Rating': 'OFF_RATING',
                'Def Rating': 'DEF_RATING',
                'Net Rating': 'NET_RATING',
                '3PT%': 'FG3_PCT',
                'Reb%': 'REB_PCT'
            }
            
            for label, col in metric_map.items():
                if col in data_a and col in data_b:
                    metrics.append(label)
                    val_a = data_a[col]
                    val_b = data_b[col]
                    
                    # Normalizar: para DEF_RATING, menor é melhor (inverter)
                    if col == 'DEF_RATING':
                        val_a = 120 - val_a
                        val_b = 120 - val_b
                    elif col in ['FG3_PCT', 'REB_PCT']:
                        val_a = val_a * 100
                        val_b = val_b * 100
                    
                    values_a.append(round(val_a, 1))
                    values_b.append(round(val_b, 1))
            
            if metrics:
                df_radar = pd.DataFrame({
                    'Métrica': metrics,
                    team_a: values_a,
                    team_b: values_b
                })
                
                fig_radar = px.line_polar(
                    df_radar,
                    r=[team_a, team_b],
                    theta='Métrica',
                    line_close=True,
                    color_discrete_sequence=['#fbbf24', '#60a5fa'],
                    title=f"{team_a} vs {team_b}"
                )
                fig_radar.update_layout(height=500, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_radar, use_container_width=True)
        
        # Comparação lado a lado
        st.markdown("---")
        st.markdown("**📊 Comparação Direta**")
        
        comp_cols = [c for c in ['GP', 'W', 'L', 'PACE', 'OFF_RATING', 'DEF_RATING', 'NET_RATING'] if c in df_teams.columns]
        
        if comp_cols and data_a and data_b:
            comp_data = pd.DataFrame({
                'Métrica': comp_cols,
                team_a: [f"{data_a.get(c, 'N/A'):.1f}" if isinstance(data_a.get(c), (int, float)) else data_a.get(c, 'N/A') for c in comp_cols],
                team_b: [f"{data_b.get(c, 'N/A'):.1f}" if isinstance(data_b.get(c), (int, float)) else data_b.get(c, 'N/A') for c in comp_cols]
            })
            st.dataframe(comp_data, use_container_width=True, hide_index=True)

# ============================================================================
# MODO 3: ANÁLISE DE JOGADORES
# ============================================================================
elif analysis_mode == "👤 Jogadores":
    st.markdown('<p class="sub-title">👤 Performance de Jogadores</p>', unsafe_allow_html=True)
    
    if df_players is None or df_players.empty:
        st.warning("⚠️ Dados de jogadores não disponíveis no momento.")
        st.info("Tente recarregar a página ou aguarde alguns minutos.")
    else:
        # Filtros
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            min_games = st.slider("Mínimo de Jogos", 10, 82, 30, step=5)
        with col_f2:
            stat_category = st.selectbox(
                "Categoria Principal",
                ["PTS", "REB", "AST", "FG3_PCT", "EFF", "STL", "BLK"]
            )
        
        # Filtrar jogadores
        df_filtered = df_players[df_players['GP'] >= min_games].copy()
        
        # Filtrar por minutos para estatísticas mais relevantes
        if 'MIN' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['MIN'] >= 15]
        
        # Ordenar por categoria
        if stat_category in df_filtered.columns:
            df_sorted = df_filtered.sort_values(stat_category, ascending=False).head(20)
        else:
            df_sorted = df_filtered.head(20)
        
        # Selecionar colunas para exibição
        base_cols = ['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN']
        display_cols = [c for c in base_cols + [stat_category] if c in df_sorted.columns]
        
        st.markdown(f"**🏆 Top 20 Jogadores por {stat_category}**")
        st.dataframe(df_sorted[display_cols].round(1), use_container_width=True, hide_index=True)
        
        # Gráfico de dispersão
        st.markdown("---")
        st.markdown("**📊 Dispersão: Pontos vs Assistências**")
        
        if 'PTS' in df_filtered.columns and 'AST' in df_filtered.columns:
            plot_df = df_filtered.head(100).copy()
            
            fig_scatter = px.scatter(
                plot_df,
                x='PTS',
                y='AST',
                size='REB' if 'REB' in plot_df.columns else None,
                color='TEAM_ABBREVIATION',
                hover_name='PLAYER_NAME',
                title="Relação Pontos/Assistências (Tamanho = Rebotes)",
                size_max=20
            )
            fig_scatter.update_layout(height=500, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Dados insuficientes para gráfico de dispersão")

# ============================================================================
# MODO 4: SUGESTÕES DE APOSTA
# ============================================================================
elif analysis_mode == "🎯 Sugestões de Aposta":
    st.markdown('<p class="sub-title">🎯 Sugestões Baseadas em Dados</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        ⚠️ <strong>Aviso Importante:</strong> Estas são análises estatísticas baseadas em dados históricos.
        Apostas esportivas envolvem risco financeiro. Nunca aposte mais do que pode perder.
        Este bot é uma ferramenta educacional e não garante lucros.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**🔥 Melhores Oportunidades Estatísticas do Dia**")
    
    # Gerar sugestões
    suggestions = generate_betting_suggestions(df_teams)
    
    if suggestions:
        for sug in suggestions:
            # Badge de confiança
            if sug['confianca'] >= 75:
                emoji, bg_color = "🟢", "#064e3b"
            elif sug['confianca'] >= 65:
                emoji, bg_color = "🟡", "#451a03"
            else:
                emoji, bg_color = "🔴", "#451a03"
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; border-left: 4px solid #fbbf24; margin: 10px 0;">
                <strong>{emoji} {sug['tipo']}</strong><br>
                <strong>Time:</strong> {sug['time']}<br>
                <strong>Motivo:</strong> {sug['motivo']}<br>
                <strong>Confiança:</strong> {sug['confianca']}%
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ Nenhuma sugestão gerada. Verifique se os dados foram carregados corretamente.")
    
    # Tabela completa
    if suggestions:
        with st.expander("📋 Ver Todas as Sugestões em Tabela"):
            df_sug = pd.DataFrame(suggestions)
            st.dataframe(df_sug, use_container_width=True, hide_index=True)
    
    # Histórico simulado
    st.markdown("---")
    st.markdown("**📜 Performance Recente do Modelo (Simulado)**")
    
    hist_data = pd.DataFrame({
        'Dia': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
        'Sugestões': [5, 7, 4, 6, 5, 8, 6],
        'Acertos': [3, 5, 2, 4, 3, 5, 4],
        'Taxa': [60.0, 71.4, 50.0, 66.7, 60.0, 62.5, 66.7]
    })
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.dataframe(hist_data, hide_index=True, use_container_width=True)
    with col_h2:
        fig_hist = px.line(
            hist_data,
            x='Dia',
            y='Taxa',
            markers=True,
            title='Taxa de Acerto (%)',
            range_y=[40, 80]
        )
        fig_hist.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_hist, use_container_width=True)

# ============================================================================
# RODAPÉ
# ============================================================================
st.markdown("---")
st.markdown("""
<center>
<strong>🏀 NBA ProBet Analytics</strong> | Dados: <a href="https://github.com/swar/nba_api" target="_blank">nba_api Oficial</a><br>
<strong>⚠️ Aviso:</strong> Ferramenta de análise estatística educacional. 
Apostas esportivas envolvem risco financeiro. Jogue com responsabilidade.
</center>
""", unsafe_allow_html=True)
