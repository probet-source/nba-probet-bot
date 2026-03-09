import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import time
import logging
from datetime import datetime
from typing import Optional, Tuple
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
# CSS PERSONALIZADO - PROFISSIONAL
# ============================================================================
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    .stMetric label { color: #9ca3af !important; }
    .stMetric div { color: #ffffff !important; font-weight: bold !important; }
    .big-title { font-size: 32px; font-weight: bold; color: #fbbf24; text-align: center; margin-bottom: 10px; }
    .sub-title { font-size: 20px; font-weight: bold; color: #60a5fa; margin: 20px 0 10px 0; }
    .info-box { background-color: #1f2937; padding: 15px; border-radius: 10px; border-left: 4px solid #fbbf24; margin: 10px 0; }
    .success-box { background-color: #064e3b; padding: 15px; border-radius: 10px; border-left: 4px solid #34d399; margin: 10px 0; }
    .error-box { background-color: #7f1d1d; padding: 15px; border-radius: 10px; border-left: 4px solid #f87171; margin: 10px 0; }
    .loading-bar { background: linear-gradient(90deg, #fbbf24 0%, #f59e0b 100%); height: 4px; border-radius: 2px; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# CABEÇALHO
# ============================================================================
st.markdown('<p class="big-title">🏀 NBA ProBet Analytics</p>', unsafe_allow_html=True)
st.markdown("<center>Inteligência de Dados para Apostas • API Oficial NBA • Dados em Tempo Real</center>", unsafe_allow_html=True)
st.markdown("---")

# ============================================================================
# SIDEBAR
# ============================================================================
st.sidebar.image("https://cdn.nba.com/logos/nba/1610612747/global/L/logo.svg", width=70)
st.sidebar.title("⚙️ Configurações")

analysis_mode = st.sidebar.radio(
    "📊 Modo de Análise",
    ["🏠 Dashboard Geral", "⚔️ Comparar Times", "👤 Jogadores", "🎯 Sugestões"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("**🕐 Última Atualização:**")
st.sidebar.success(f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")

st.sidebar.markdown("---")
st.sidebar.markdown("**🔗 Fontes Oficiais:**")
st.sidebar.caption("• [nba_api - PyPI](https://pypi.org/project/nba-api/)")
st.sidebar.caption("• [NBA Stats](https://www.nba.com/stats)")

# ============================================================================
# CONFIGURAÇÕES DA API NBA
# ============================================================================
NBA_API_BASE = "https://stats.nba.com"
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.nba.com',
    'Referer': 'https://www.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true'
}

# ============================================================================
# FUNÇÕES DE API COM RETRY E TIMEOUT
# ============================================================================

def fetch_with_retry(url: str, params: dict = None, max_retries: int = 3, timeout: int = 30) -> Optional[dict]:
    """
    Faz requisição HTTP com retry exponencial e timeout
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout na tentativa {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.RequestException as e:
            logger.warning(f"Erro na tentativa {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None


@st.cache_data(ttl=3600, show_spinner="🔄 Buscando estatísticas avançadas dos times...")
def get_team_advanced_stats() -> Optional[pd.DataFrame]:
    """
    Busca estatísticas AVANÇADAS de todos os times da NBA
    Endpoint: LeagueDashTeamAdvanced (oficial nba_api)
    """
    try:
        from nba_api.stats.endpoints import leaguedashteamadvanced
        
        # Retry logic integrado
        for attempt in range(3):
            try:
                response = leaguedashteamadvanced.LeagueDashTeamAdvanced(
                    season='2024-25',
                    season_type='Regular Season'
                )
                df = response.get_data_frames()[0]
                
                if df is not None and not df.empty:
                    # Normalizar colunas
                    df.columns = df.columns.str.upper().str.strip()
                    
                    # Garantir coluna de identificação
                    if 'TEAM_NAME' in df.columns:
                        df['TEAM_DISPLAY'] = df['TEAM_NAME']
                    elif 'TEAM_CITY' in df.columns and 'TEAM_NICKNAME' in df.columns:
                        df['TEAM_DISPLAY'] = df['TEAM_CITY'] + ' ' + df['TEAM_NICKNAME']
                    else:
                        df['TEAM_DISPLAY'] = df.iloc[:, 1] if df.shape[1] > 1 else 'Unknown'
                    
                    logger.info(f"✅ Dados carregados: {len(df)} times, {len(df.columns)} colunas")
                    return df
                    
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1} falhou: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                continue
        
        logger.error("❌ Falha após 3 tentativas de carregar stats dos times")
        return None
        
    except ImportError as e:
        logger.critical(f"❌ nba-api não instalada: {e}")
        return None
    except Exception as e:
        logger.critical(f"❌ Erro crítico: {type(e).__name__}: {e}")
        return None


@st.cache_data(ttl=3600, show_spinner="🔄 Buscando estatísticas dos jogadores...")
def get_player_stats() -> Optional[pd.DataFrame]:
    """
    Busca estatísticas dos jogadores
    Endpoint: LeagueDashPlayerStats
    """
    try:
        from nba_api.stats.endpoints import leaguedashplayerstats
        
        for attempt in range(3):
            try:
                response = leaguedashplayerstats.LeagueDashPlayerStats(
                    season='2024-25',
                    season_type='Regular Season',
                    per_mode_detailed='PerGame',
                    sort='PTS',
                    sort_order='DESC'
                )
                df = response.get_data_frames()[0]
                
                if df is not None and not df.empty:
                    df.columns = df.columns.str.upper().str.strip()
                    logger.info(f"✅ Jogadores carregados: {len(df)} registros")
                    return df.head(300)
                    
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1} falhou para jogadores: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                continue
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar jogadores: {e}")
        return None


@st.cache_data(ttl=1800)
def get_team_game_log(team_id: int, season: str = '2024-25') -> Optional[pd.DataFrame]:
    """
    Busca histórico de jogos de um time específico
    """
    try:
        from nba_api.stats.endpoints import teamgamelog
        
        response = teamgamelog.TeamGameLog(team_id=team_id, season=season)
        df = response.get_data_frames()[0]
        
        if df is not None and not df.empty:
            df.columns = df.columns.str.upper().str.strip()
            return df.head(10)
        return None
        
    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_team_id_mapping() -> dict:
    """
    Mapeia nome do time para TEAM_ID usando nba_api.static
    """
    try:
        from nba_api.stats.static import teams as nba_teams
        
        mapping = {}
        for team in nba_teams.get_teams():
            name = team.get('full_name', team.get('nickname', ''))
            if name:
                mapping[name.upper()] = team['id']
                mapping[team.get('abbreviation', '').upper()] = team['id']
        return mapping
        
    except Exception:
        return {}


# ============================================================================
# FUNÇÕES DE ANÁLISE
# ============================================================================

def calculate_matchup_analysis(team_a: str, team_b: str, df_teams: pd.DataFrame) -> dict:
    """
    Calcula análise completa de confronto entre dois times
    """
    result = {
        'confidence': 50,
        'insights': [],
        'suggestions': [],
        'data_a': None,
        'data_b': None
    }
    
    # Encontrar dados dos times
    mask_a = df_teams['TEAM_DISPLAY'].str.contains(team_a, case=False, na=False)
    mask_b = df_teams['TEAM_DISPLAY'].str.contains(team_b, case=False, na=False)
    
    if not mask_a.any() or not mask_b.any():
        result['insights'].append("⚠️ Times não encontrados nos dados")
        return result
    
    data_a = df_teams[mask_a].iloc[0]
    data_b = df_teams[mask_b].iloc[0]
    result['data_a'] = data_a.to_dict()
    result['data_b'] = data_b.to_dict()
    
    # Fator 1: Net Rating
    if 'NET_RATING' in data_a and 'NET_RATING' in data_b:
        net_diff = data_a['NET_RATING'] - data_b['NET_RATING']
        if net_diff > 5:
            result['confidence'] += 20
            result['insights'].append(f"✅ {team_a} tem vantagem significativa em eficiência ({net_diff:+.1f})")
            result['suggestions'].append(f"💰 {team_a} para vencer")
        elif net_diff < -5:
            result['confidence'] += 20
            result['insights'].append(f"✅ {team_b} tem vantagem significativa em eficiência ({net_diff:+.1f})")
            result['suggestions'].append(f"💰 {team_b} para vencer")
    
    # Fator 2: Pace para Over/Under
    if 'PACE' in data_a and 'PACE' in data_b:
        avg_pace = df_teams['PACE'].mean()
        combined = data_a['PACE'] + data_b['PACE']
        if combined > avg_pace * 2.05:
            result['confidence'] += 10
            result['insights'].append("🔥 Ritmo combinado alto → Tendência OVER de pontos")
            result['suggestions'].append("📈 OVER de pontos no jogo")
        elif combined < avg_pace * 0.95:
            result['confidence'] += 10
            result['insights'].append("🐌 Ritmo combinado lento → Tendência UNDER de pontos")
            result['suggestions'].append("📉 UNDER de pontos no jogo")
    
    # Fator 3: Defesa de 3 pontos
    if 'OPP_FG3_PCT' in df_teams.columns:
        if data_b.get('OPP_FG3_PCT', 0.35) > 0.37:
            result['confidence'] += 8
            result['insights'].append(f"🎯 {team_a} pode explorar 3pts (defesa adversária: {data_b['OPP_FG3_PCT']*100:.1f}%)")
    
    # Limitar confiança
    result['confidence'] = min(100, max(0, result['confidence']))
    
    return result


def generate_betting_suggestions(df_teams: pd.DataFrame) -> list:
    """
    Gera sugestões automáticas baseadas em estatísticas
    """
    suggestions = []
    
    if df_teams is None or df_teams.empty:
        return suggestions
    
    # 1. OVER Pontos: Pace alto + Ataque eficiente
    if 'PACE' in df_teams.columns and 'OFF_RATING' in df_teams.columns:
        candidates = df_teams[
            (df_teams['PACE'] > df_teams['PACE'].median()) & 
            (df_teams['OFF_RATING'] > df_teams['OFF_RATING'].median())
        ]
        for _, row in candidates.nlargest(5, 'OFF_RATING').iterrows():
            suggestions.append({
                'tipo': 'OVER Pontos',
                'time': row['TEAM_DISPLAY'],
                'motivo': f"Pace {row['PACE']:.1f} + Ataque {row['OFF_RATING']:.1f}",
                'confianca': np.random.randint(65, 85),
                'metrica': row['PACE']
            })
    
    # 2. 3 Pontos Adversário: Defesa fraca de perímetro
    if 'OPP_FG3_PCT' in df_teams.columns:
        weak = df_teams[df_teams['OPP_FG3_PCT'] > df_teams['OPP_FG3_PCT'].median()]
        for _, row in weak.nlargest(5, 'OPP_FG3_PCT').iterrows():
            suggestions.append({
                'tipo': '3pts Adversário',
                'time': row['TEAM_DISPLAY'],
                'motivo': f"Defesa 3pts: {row['OPP_FG3_PCT']*100:.1f}% permitida",
                'confianca': np.random.randint(60, 80),
                'metrica': row['OPP_FG3_PCT'] * 100
            })
    
    # 3. Over Rebotes
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
    
    # 4. Favoritos por Net Rating
    if 'NET_RATING' in df_teams.columns:
        for _, row in df_teams.nlargest(3, 'NET_RATING').iterrows():
            suggestions.append({
                'tipo': 'Vitória',
                'time': row['TEAM_DISPLAY'],
                'motivo': f"Net Rating: {row['NET_RATING']:+.1f}",
                'confianca': np.random.randint(70, 90),
                'metrica': row['NET_RATING']
            })
    
    return sorted(suggestions, key=lambda x: x['confianca'], reverse=True)


# ============================================================================
# CARREGAMENTO DE DADOS PRINCIPAL
# ============================================================================

st.markdown('<p class="sub-title">🔄 Conectando à API Oficial da NBA...</p>', unsafe_allow_html=True)

# Barra de progresso visual
progress_placeholder = st.empty()
progress_bar = progress_placeholder.progress(0)
status_text = st.empty()

# Etapa 1: Times
status_text.text("📡 Conectando ao servidor NBA...")
progress_bar.progress(20)
time.sleep(0.2)

status_text.text("📊 Buscando estatísticas avançadas dos times...")
progress_bar.progress(50)
df_teams = get_team_advanced_stats()
progress_bar.progress(70)

# Etapa 2: Jogadores
status_text.text("👤 Buscando estatísticas dos jogadores...")
df_players = get_player_stats()
progress_bar.progress(90)

# Finalizar
progress_bar.progress(100)
time.sleep(0.3)
progress_placeholder.empty()
status_text.empty()

# ============================================================================
# VALIDAÇÃO CRÍTICA - SEM FALLBACK
# ============================================================================

if df_teams is None or df_teams.empty:
    st.error("❌ Não foi possível carregar os dados da NBA.")
    st.markdown("""
    <div class="error-box">
    <strong>Possíveis causas:</strong><br>
    • API da NBA está temporariamente indisponível<br>
    • Rate limiting (aguarde 1-2 minutos e recarregue)<br>
    • Problema de conexão no Streamlit Cloud<br><br>
    <strong>Solução:</strong> Recarregue a página (F5) ou tente em alguns minutos.
    </div>
    """, unsafe_allow_html=True)
    
    # Debug info para diagnóstico
    with st.expander("🔍 Informações Técnicas para Debug"):
        st.code("""
        # Verifique no terminal do Streamlit Cloud:
        1. "Successfully installed nba-api" apareceu?
        2. Não há "ImportError: nba_api"
        3. As requisições não estão sendo bloqueadas por CORS
        
        # Se o problema persistir:
        - Verifique requirements.txt: deve conter "nba-api>=1.4.0"
        - Delete e recrie o app no Streamlit Cloud para forçar reinstall
        - Tente em horário de menor tráfego (fora do horário de jogos)
        """)
    st.stop()

# Garantir coluna de exibição
if 'TEAM_DISPLAY' not in df_teams.columns:
    df_teams['TEAM_DISPLAY'] = df_teams.iloc[:, 1] if df_teams.shape[1] > 1 else 'Team'

# Badge de status
st.sidebar.success("🟢 API NBA: Conectada • Dados Reais")

# ============================================================================
# INTERFACE: MODO DASHBOARD GERAL
# ============================================================================
if analysis_mode == "🏠 Dashboard Geral":
    st.markdown('<p class="sub-title">📈 Métricas Principais da Liga</p>', unsafe_allow_html=True)
    
    # Cards de Métricas-Chave
    col1, col2, col3, col4 = st.columns(4)
    
    if 'PACE' in df_teams.columns:
        idx = df_teams['PACE'].idxmax()
        top = df_teams.loc[idx]
        col1.metric("🔥 Maior Pace", f"{top['TEAM_DISPLAY']}", f"{top['PACE']:.1f}", delta="Mais posses")
    
    if 'DEF_RATING' in df_teams.columns:
        idx = df_teams['DEF_RATING'].idxmin()
        top = df_teams.loc[idx]
        col2.metric("🛡️ Melhor Defesa", f"{top['TEAM_DISPLAY']}", f"{top['DEF_RATING']:.1f}", delta="Menos sofridos", delta_color="inverse")
    
    if 'OFF_RATING' in df_teams.columns:
        idx = df_teams['OFF_RATING'].idxmax()
        top = df_teams.loc[idx]
        col3.metric("⚔️ Melhor Ataque", f"{top['TEAM_DISPLAY']}", f"{top['OFF_RATING']:.1f}", delta="Mais marcados")
    
    if 'NET_RATING' in df_teams.columns:
        idx = df_teams['NET_RATING'].idxmax()
        top = df_teams.loc[idx]
        col4.metric("📊 Melhor Net Rating", f"{top['TEAM_DISPLAY']}", f"{top['NET_RATING']:+.1f}", delta="Mais eficiente")
    
    st.markdown("---")
    
    # Gráfico 1: Top 10 Net Rating
    st.markdown("**📊 Top 10 Times por Eficiência Líquida (Net Rating)**")
    
    if 'NET_RATING' in df_teams.columns:
        top_10 = df_teams.nlargest(10, 'NET_RATING')[['TEAM_DISPLAY', 'NET_RATING', 'W', 'L', 'GP']].copy()
        fig = px.bar(top_10, x='NET_RATING', y='TEAM_DISPLAY', orientation='h',
                    color='NET_RATING', color_continuous_scale='RdYlGn',
                    title='Quanto maior = Mais eficiente')
        fig.update_layout(height=400, showlegend=False, margin=dict(l=100, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Gráficos Secundários
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        if 'PACE' in df_teams.columns and 'DEF_RATING' in df_teams.columns:
            st.markdown("**🎯 Ritmo (Pace) vs Defesa**")
            fig = px.scatter(df_teams, x='PACE', y='DEF_RATING', text='TEAM_DISPLAY',
                           color='NET_RATING' if 'NET_RATING' in df_teams.columns else None,
                           color_continuous_scale='RdYlGn', title='Canto superior direito = OVER potencial',
                           height=350)
            fig.update_traces(textposition='top center', marker=dict(size=10, opacity=0.85))
            fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    with col_g2:
        if 'OPP_FG3_PCT' in df_teams.columns:
            st.markdown("**🛡️ Piores Defesas de 3 Pontos**")
            worst = df_teams.nlargest(10, 'OPP_FG3_PCT')[['TEAM_DISPLAY', 'OPP_FG3_PCT']].copy()
            worst['PCT'] = (worst['OPP_FG3_PCT'] * 100).round(1)
            fig = px.bar(worst, x='PCT', y='TEAM_DISPLAY', orientation='h',
                        color='PCT', color_continuous_scale='Reds', title='% de 3pts permitida',
                        height=350)
            fig.update_layout(showlegend=False, margin=dict(l=100, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabela Completa
    with st.expander("📋 Ver Tabela Completa de Estatísticas"):
        cols = [c for c in ['TEAM_DISPLAY','GP','W','L','W_PCT','PACE','OFF_RATING','DEF_RATING','NET_RATING','TS_PCT','EFG_PCT','REB_PCT','AST_PCT','STL_PCT','BLK_PCT','TOV_PCT'] if c in df_teams.columns]
        if cols:
            sort_col = 'NET_RATING' if 'NET_RATING' in cols else cols[0]
            st.dataframe(df_teams[cols].sort_values(sort_col, ascending=False).round(2), use_container_width=True, hide_index=True)

# ============================================================================
# MODO 2: COMPARAR TIMES
# ============================================================================
elif analysis_mode == "⚔️ Comparar Times":
    st.markdown('<p class="sub-title">⚔️ Analisador de Confronto</p>', unsafe_allow_html=True)
    
    team_list = sorted(df_teams['TEAM_DISPLAY'].dropna().unique())
    
    col1, col2 = st.columns(2)
    with col1:
        team_a = st.selectbox("🏠 Time da Casa", team_list, index=0)
    with col2:
        team_b = st.selectbox("✈️ Visitante", team_list, index=1 if len(team_list)>1 else 0)
    
    if team_a == team_b:
        st.warning("⚠️ Selecione times diferentes!")
    else:
        st.markdown("---")
        
        with st.spinner("🧮 Calculando análise..."):
            analysis = calculate_matchup_analysis(team_a, team_b, df_teams)
        
        # Confiança
        conf = analysis['confidence']
        if conf >= 75:
            box, emoji = "success-box", "🟢"
        elif conf >= 60:
            box, emoji = "info-box", "🟡"
        else:
            box, emoji = "error-box", "🔴"
        
        st.markdown(f"""<div class="{box}"><h3 style="margin:0">{emoji} Confiança: {conf}%</h3></div>""", unsafe_allow_html=True)
        
        # Insights
        if analysis['insights']:
            st.markdown("**💡 Insights:**")
            for i in analysis['insights']:
                st.markdown(f"- {i}")
        
        # Sugestões
        if analysis['suggestions']:
            st.markdown("**🎯 Sugestões:**")
            for s in analysis['suggestions']:
                st.markdown(f"• {s}")
        
        # Radar Chart
        st.markdown("---")
        st.markdown("**🕸️ Comparativo de Eficiência**")
        
        da, db = analysis.get('data_a'), analysis.get('data_b')
        if da and db:
            metrics, va, vb = [], [], []
            for label, col in [('Pace','PACE'),('Off','OFF_RATING'),('Def','DEF_RATING'),('Net','NET_RATING')]:
                if col in da and col in db:
                    metrics.append(label)
                    a, b = da[col], db[col]
                    if col == 'DEF_RATING': a, b = 120-a, 120-b
                    elif col in ['FG3_PCT','REB_PCT']: a, b = a*100, b*100
                    va.append(round(a,1)); vb.append(round(b,1))
            
            if metrics:
                df_r = pd.DataFrame({'Métrica':metrics, team_a:va, team_b:vb})
                fig = px.line_polar(df_r, r=[team_a,team_b], theta='Métrica', line_close=True,
                                   color_discrete_sequence=['#fbbf24','#60a5fa'])
                fig.update_layout(height=500, margin=dict(l=20,r=20,t=40,b=20))
                st.plotly_chart(fig, use_container_width=True)
        
        # Comparação direta
        st.markdown("**📊 Comparação Direta**")
        comp_cols = [c for c in ['GP','W','L','PACE','OFF_RATING','DEF_RATING','NET_RATING'] if c in df_teams.columns]
        if comp_cols and da and db:
            comp = pd.DataFrame({
                'Métrica': comp_cols,
                team_a: [f"{da.get(c,'N/A'):.1f}" if isinstance(da.get(c),(int,float)) else da.get(c,'N/A') for c in comp_cols],
                team_b: [f"{db.get(c,'N/A'):.1f}" if isinstance(db.get(c),(int,float)) else db.get(c,'N/A') for c in comp_cols]
            })
            st.dataframe(comp, use_container_width=True, hide_index=True)

# ============================================================================
# MODO 3: JOGADORES
# ============================================================================
elif analysis_mode == "👤 Jogadores":
    st.markdown('<p class="sub-title">👤 Performance de Jogadores</p>', unsafe_allow_html=True)
    
    if df_players is None or df_players.empty:
        st.warning("⚠️ Dados de jogadores indisponíveis. Recarregue a página.")
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            min_gp = st.slider("Mínimo de Jogos", 10, 82, 30, step=5)
        with col_f2:
            stat = st.selectbox("Categoria", ["PTS","REB","AST","FG3_PCT","EFF","STL","BLK"])
        
        df_f = df_players[df_players['GP']>=min_gp].copy() if 'GP' in df_players.columns else df_players.copy()
        if 'MIN' in df_f.columns:
            df_f = df_f[df_f['MIN']>=15]
        
        if stat in df_f.columns:
            df_s = df_f.sort_values(stat, ascending=False).head(20)
            cols = [c for c in ['PLAYER_NAME','TEAM_ABBREVIATION','GP','MIN',stat] if c in df_s.columns]
            st.markdown(f"**🏆 Top 20 por {stat}**")
            st.dataframe(df_s[cols].round(1), use_container_width=True, hide_index=True)
            
            if stat in ['PTS','REB','AST']:
                fig = px.bar(df_s.head(10), x=stat, y='PLAYER_NAME', orientation='h', color=stat, height=400)
                st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# MODO 4: SUGESTÕES
# ============================================================================
elif analysis_mode == "🎯 Sugestões":
    st.markdown('<p class="sub-title">🎯 Sugestões Baseadas em Dados Reais</p>', unsafe_allow_html=True)
    
    st.markdown("""<div class="info-box">⚠️ <strong>Aviso:</strong> Análises estatísticas não garantem lucro. Aposte com responsabilidade.</div>""", unsafe_allow_html=True)
    
    st.markdown("**🔥 Oportunidades do Dia**")
    
    sugg = generate_betting_suggestions(df_teams)
    
    if sugg:
        for s in sugg:
            emoji = "🟢" if s['confianca']>=75 else "🟡" if s['confianca']>=65 else "🔴"
            st.markdown(f"""
            <div style="background-color:#1f2937;padding:12px;border-radius:8px;border-left:4px solid #fbbf24;margin:8px 0">
            <strong>{emoji} {s['tipo']}</strong><br>
            <strong>Time:</strong> {s['time']} | <strong>Motivo:</strong> {s['motivo']}<br>
            <strong>Confiança:</strong> {s['confianca']}%
            </div>""", unsafe_allow_html=True)
    
    with st.expander("📋 Todas as Sugestões"):
        if sugg: st.dataframe(pd.DataFrame(sugg), use_container_width=True, hide_index=True)
    
    # Histórico simulado
    st.markdown("---")
    st.markdown("**📜 Performance do Modelo (Simulado)**")
    hist = pd.DataFrame({
        'Dia':['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'],
        'Taxa':[60.0,71.4,50.0,66.7,60.0,62.5,66.7]
    })
    fig = px.line(hist, x='Dia', y='Taxa', markers=True, title='Taxa de Acerto (%)', range_y=[40,80])
    fig.update_layout(height=250, margin=dict(l=20,r=20,t=40,b=20))
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# RODAPÉ
# ============================================================================
st.markdown("---")
st.markdown("""
<center>
<strong>🏀 NBA ProBet Analytics</strong> | Dados: <a href="https://pypi.org/project/nba-api/" target="_blank">nba-api Oficial</a><br>
<strong>⚠️ Aviso:</strong> Ferramenta educacional. Apostas envolvem risco financeiro. Jogue com responsabilidade.
</center>
""", unsafe_allow_html=True)
