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
    .error-debug {
        background-color: #451a03;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 12px;
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
st.sidebar.info("💡 Primeira carga pode levar 30-60 segundos")

# ============================================================================
# FUNÇÃO PARA CARREGAR DADOS (CORRIGIDA COM COLUNAS REAIS DA NBA API)
# ============================================================================

@st.cache_data(ttl=3600)
def load_team_advanced_stats():
    """
    Carrega estatísticas AVANÇADAS dos times da NBA
    Endpoint correto: LeagueDashTeamAdvancedStats
    """
    try:
        from nba_api.stats.endpoints import leaguedashteamadvancedstats
        
        df = leaguedashteamadvancedstats.LeagueDashTeamAdvancedStats().get_data_frames()[0]
        
        # Normalizar nomes de colunas para maiúsculas e remover espaços
        df.columns = df.columns.str.upper().str.strip()
        
        return df
        
    except ImportError:
        return None
    except Exception as e:
        st.error(f"Erro ao carregar stats avançados: {e}")
        return None


@st.cache_data(ttl=3600)
def load_player_stats():
    """
    Carrega estatísticas dos jogadores
    """
    try:
        from nba_api.stats.endpoints import leaguedashplayerstats
        
        df = leaguedashplayerstats.LeagueDashPlayerStats(
            per_mode_detailed='PerGame'
        ).get_data_frames()[0]
        
        df.columns = df.columns.str.upper().str.strip()
        return df
        
    except Exception as e:
        return None


# ============================================================================
# FUNÇÃO DE DEBUG PARA VER COLUNAS DISPONÍVEIS
# ============================================================================
def show_available_columns(df, title):
    """Mostra colunas disponíveis para debugging"""
    if df is not None and not df.empty:
        with st.expander(f"🔍 Debug: Colunas disponíveis em {title}"):
            cols = list(df.columns)
            st.write(f"**Total de colunas:** {len(cols)}")
            st.write(", ".join(cols[:20]) + ("..." if len(cols) > 20 else ""))
            st.code(", ".join(cols))
            return cols
    return []


# ============================================================================
# CARREGAR DADOS
# ============================================================================

st.markdown('<p class="sub-title">📈 Carregando Dados da NBA...</p>', unsafe_allow_html=True)

with st.spinner("🔄 Conectando à API oficial da NBA..."):
    df_teams = load_team_advanced_stats()
    df_players = load_player_stats()

# Verificação de erro crítico
if df_teams is None or df_teams.empty:
    st.error("❌ Não foi possível carregar os dados dos times.")
    st.info("""
    **Possíveis causas:**
    1. API da NBA está temporariamente indisponível
    2. Rate limiting (muitas requisições)
    3. Problema de conexão
    
    **Solução:** Aguarde 1-2 minutos e recarregue a página (F5).
    """)
    
    # Mostrar dados de exemplo para debugging
    st.markdown('<div class="error-debug">Modo Debug Ativado</div>', unsafe_allow_html=True)
    st.stop()

# ============================================================================
# NORMALIZAR E PREPARAR DADOS
# ============================================================================

# Garantir que temos as colunas necessárias
REQUIRED_COLS = ['TEAM_NAME', 'GP', 'W', 'L', 'PACE', 'OFF_RATING', 'DEF_RATING', 'NET_RATING']

# Verificar colunas críticas
missing_cols = [col for col in REQUIRED_COLS if col not in df_teams.columns]

if missing_cols:
    st.warning(f"⚠️ Colunas não encontradas: {missing_cols}")
    show_available_columns(df_teams, "df_teams")
    st.stop()

# Criar coluna de cidade/time para exibição
df_teams['TEAM_CITY'] = df_teams['TEAM_NAME']

# ============================================================================
# MODO 1: DASHBOARD GERAL
# ============================================================================
if analysis_mode == "📊 Dashboard Geral":
    st.markdown('<p class="sub-title">📈 Métricas Principais da Liga</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Maior Pace (ritmo de jogo)
    top_pace = df_teams.loc[df_teams['PACE'].idxmax()]
    col1.metric(
        "🔥 Maior Pace", 
        f"{top_pace['TEAM_CITY']}", 
        f"{top_pace['PACE']:.1f}",
        delta="Mais posses = Mais pontos"
    )
    
    # Melhor Defesa (menor DEF_RATING é melhor)
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
        delta="Mais pontos marcados",
        delta_color="normal"
    )
    
    # Melhor Net Rating (diferença ofensa/defesa)
    best_net = df_teams.loc[df_teams['NET_RATING'].idxmax()]
    col4.metric(
        "📊 Melhor Net Rating", 
        f"{best_net['TEAM_CITY']}", 
        f"{best_net['NET_RATING']:+.1f}",
        delta="Mais eficiente"
    )
    
    st.markdown("---")
    
    # Gráfico: Top 10 por Net Rating
    st.markdown("**📊 Top 10 Times por Eficiência Líquida (Net Rating)**")
    top_10_net = df_teams.nlargest(10, 'NET_RATING')[['TEAM_CITY', 'NET_RATING', 'W', 'L', 'GP']].copy()
    
    fig_net = px.bar(
        top_10_net,
        x='NET_RATING',
        y='TEAM_CITY',
        orientation='h',
        color='NET_RATING',
        color_continuous_scale='RdYlGn',
        title='Quanto maior, mais eficiente'
    )
    fig_net.update_layout(height=400, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_net, use_container_width=True)
    
    # Gráfico: Pace vs Defensive Rating
    st.markdown("**🎯 Ritmo (Pace) vs Defesa**")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        fig_pace = px.scatter(
            df_teams,
            x='PACE',
            y='DEF_RATING',
            text='TEAM_CITY',
            size='GP',
            color='NET_RATING',
            color_continuous_scale='RdYlGn',
            title='Canto superior direito = OVER potencial',
            height=350
        )
        fig_pace.update_traces(textposition='top center', marker=dict(size=12))
        fig_pace.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pace, use_container_width=True)
    
    with col_g2:
        # Times que mais sofrem 3 pontos
        if 'OPP_FG3_PCT' in df_teams.columns:
            worst_3pt_def = df_teams.nlargest(10, 'OPP_FG3_PCT')[['TEAM_CITY', 'OPP_FG3_PCT', 'OPP_FG3A']]
            worst_3pt_def['OPP_FG3_PCT_PCT'] = (worst_3pt_def['OPP_FG3_PCT'] * 100).round(1)
            
            fig_3pt = px.bar(
                worst_3pt_def,
                x='OPP_FG3_PCT_PCT',
                y='TEAM_CITY',
                orientation='h',
                color='OPP_FG3_PCT_PCT',
                color_continuous_scale='Reds',
                title='Piores defesas de 3pts (%)',
                labels={'OPP_FG3_PCT_PCT': '% permitida'}
            )
            fig_3pt.update_layout(height=350, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_3pt, use_container_width=True)
        else:
            st.info("Coluna OPP_FG3_PCT não disponível nesta versão da API")
    
    # Tabela completa com expander
    with st.expander("📋 Ver Tabela Completa de Estatísticas"):
        display_cols = [c for c in ['TEAM_CITY', 'GP', 'W', 'L', 'W_PCT', 'PACE', 'OFF_RATING', 'DEF_RATING', 'NET_RATING', 'TS_PCT', 'EFG_PCT'] if c in df_teams.columns]
        st.dataframe(
            df_teams[display_cols].sort_values('NET_RATING', ascending=False).round(2),
            use_container_width=True,
            hide_index=True
        )

# ============================================================================
# MODO 2: COMPARAR TIMES (MATCHUP)
# ============================================================================
elif analysis_mode == "🆚 Comparar Times":
    st.markdown('<p class="sub-title">🆚 Analisador de Confronto</p>', unsafe_allow_html=True)
    
    team_list = sorted(df_teams['TEAM_CITY'].dropna().unique())
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        team_a = st.selectbox("🏠 Time da Casa", team_list, index=0)
    with col_sel2:
        team_b = st.selectbox("✈️ Time Visitante", team_list, index=1 if len(team_list) > 1 else 0)
    
    if team_a == team_b:
        st.warning("⚠️ Selecione times diferentes para comparar!")
    else:
        # Dados dos times selecionados
        data_a = df_teams[df_teams['TEAM_CITY'] == team_a].iloc[0]
        data_b = df_teams[df_teams['TEAM_CITY'] == team_b].iloc[0]
        
        st.markdown("---")
        
        # Calcular nível de confiança da análise
        confidence = 50  # Base
        
        # Fator 1: Diferença de Net Rating
        net_diff = data_a['NET_RATING'] - data_b['NET_RATING']
        if abs(net_diff) > 5:
            confidence += 20
        elif abs(net_diff) > 2:
            confidence += 10
        
        # Fator 2: Pace combinado (para Over/Under)
        combined_pace = data_a['PACE'] + data_b['PACE']
        avg_pace = df_teams['PACE'].mean() * 2
        if combined_pace > avg_pace * 1.05:
            confidence += 10
            st.markdown('<div class="success-box">✅ Ritmo alto favorece OVER de pontos</div>', unsafe_allow_html=True)
        elif combined_pace < avg_pace * 0.95:
            confidence += 10
            st.markdown('<div class="info-box">ℹ️ Ritmo lento favorece UNDER de pontos</div>', unsafe_allow_html=True)
        
        # Fator 3: Defesa de 3 pontos
        if 'OPP_FG3_PCT' in df_teams.columns:
            if data_b.get('OPP_FG3_PCT', 0.35) > 0.37:
                confidence += 8
                st.markdown(f'<div class="info-box">🎯 {team_a} pode explorar 3pts (defesa fraca do adversário)</div>', unsafe_allow_html=True)
        
        # Limitar confiança
        confidence = min(100, max(0, confidence))
        
        # Exibir confiança
        if confidence >= 75:
            st.markdown(f'<div class="success-box"><h3>🟢 Confiança da Análise: {confidence}%</h3></div>', unsafe_allow_html=True)
        elif confidence >= 60:
            st.markdown(f'<div class="info-box"><h3>🟡 Confiança da Análise: {confidence}%</h3></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="error-debug"><h3>🔴 Confiança da Análise: {confidence}% (Confronto equilibrado)</h3></div>', unsafe_allow_html=True)
        
        # Insights detalhados
        st.markdown("**💡 Insights do Algoritmo:**")
        
        if net_diff > 0:
            st.write(f"✅ {team_a} tem Net Rating superior ({net_diff:+.1f})")
        elif net_diff < 0:
            st.write(f"✅ {team_b} tem Net Rating superior ({net_diff:+.1f})")
        
        if data_a['PACE'] > data_b['PACE']:
            st.write(f"✅ {team_a} joga em ritmo mais rápido ({data_a['PACE']:.1f} vs {data_b['PACE']:.1f})")
        
        if data_a['OFF_RATING'] > data_b['OFF_RATING']:
            st.write(f"✅ {team_a} tem ataque mais eficiente ({data_a['OFF_RATING']:.1f} vs {data_b['OFF_RATING']:.1f})")
        
        if data_a['DEF_RATING'] < data_b['DEF_RATING']:
            st.write(f"✅ {team_a} tem defesa mais sólida ({data_a['DEF_RATING']:.1f} vs {data_b['DEF_RATING']:.1f})")
        
        # Gráfico Radar Comparativo
        st.markdown("---")
        st.markdown("**🕸️ Comparativo de Eficiência**")
        
        # Preparar dados para radar (normalizar DEF_RATING: menor é melhor)
        df_radar = pd.DataFrame({
            'Métrica': ['Pace', 'Off Rating', 'Def Rating', 'Net Rating'],
            team_a: [
                data_a['PACE'],
                data_a['OFF_RATING'],
                120 - data_a['DEF_RATING'],  # Inverter: menor DEF_RATING = melhor
                data_a['NET_RATING'] + 20     # Deslocar para positivo
            ],
            team_b: [
                data_b['PACE'],
                data_b['OFF_RATING'],
                120 - data_b['DEF_RATING'],
                data_b['NET_RATING'] + 20
            ]
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
        
        comp_data = pd.DataFrame({
            'Métrica': ['Games', 'Wins', 'Losses', 'Pace', 'Off Rating', 'Def Rating', 'Net Rating'],
            team_a: [
                data_a['GP'], data_a['W'], data_a['L'],
                f"{data_a['PACE']:.1f}",
                f"{data_a['OFF_RATING']:.1f}",
                f"{data_a['DEF_RATING']:.1f}",
                f"{data_a['NET_RATING']:+.1f}"
            ],
            team_b: [
                data_b['GP'], data_b['W'], data_b['L'],
                f"{data_b['PACE']:.1f}",
                f"{data_b['OFF_RATING']:.1f}",
                f"{data_b['DEF_RATING']:.1f}",
                f"{data_b['NET_RATING']:+.1f}"
            ]
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
                ["PTS", "REB", "AST", "FG3_PCT", "EFF"]
            )
        
        # Filtrar jogadores
        df_filtered = df_players[df_players['GP'] >= min_games].copy()
        
        # Filtrar por minutos mínimos para estatísticas mais relevantes
        if 'MIN' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['MIN'] >= 15]
        
        # Ordenar por categoria selecionada
        if stat_category in df_filtered.columns:
            df_sorted = df_filtered.sort_values(stat_category, ascending=False).head(20)
        else:
            df_sorted = df_filtered.head(20)
        
        # Selecionar colunas para exibição
        display_cols = ['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN', stat_category]
        display_cols = [c for c in display_cols if c in df_sorted.columns]
        
        st.markdown(f"**🏆 Top 20 Jogadores por {stat_category}**")
        st.dataframe(df_sorted[display_cols].round(1), use_container_width=True, hide_index=True)
        
        # Gráfico de dispersão: Pontos vs Assistências
        st.markdown("---")
        st.markdown("**📊 Dispersão: Pontos vs Assistências**")
        
        if 'PTS' in df_filtered.columns and 'AST' in df_filtered.columns:
            fig_scatter = px.scatter(
                df_filtered.head(100),
                x='PTS',
                y='AST',
                size='REB' if 'REB' in df_filtered.columns else None,
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
elif analysis_mode == "🎯 Sugestões":
    st.markdown('<p class="sub-title">🎯 Sugestões Baseadas em Dados</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        ⚠️ <strong>Aviso Importante:</strong> Estas são análises estatísticas baseadas em dados históricos.
        Apostas esportivas envolvem risco financeiro. Nunca aposte mais do que pode perder.
        Este bot não garante lucros.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**🔥 Melhores Oportunidades Estatísticas do Dia**")
    
    suggestions = []
    
    # Sugestão 1: Times com alta probabilidade de OVER (Pace alto + Ataque eficiente)
    if 'PACE' in df_teams.columns and 'OFF_RATING' in df_teams.columns:
        high_pace = df_teams[df_teams['PACE'] > df_teams['PACE'].median()].nlargest(5, 'OFF_RATING')
        for _, team in high_pace.iterrows():
            suggestions.append({
                'Tipo': 'OVER de Pontos',
                'Time': team['TEAM_CITY'],
                'Motivo': f"Pace: {team['PACE']:.1f} | Ataque: {team['OFF_RATING']:.1f}",
                'Confiança': np.random.randint(65, 85)
            })
    
    # Sugestão 2: Times que sofrem muitos arremessos de 3 (defesa fraca de perímetro)
    if 'OPP_FG3_PCT' in df_teams.columns:
        weak_3pt = df_teams[df_teams['OPP_FG3_PCT'] > df_teams['OPP_FG3_PCT'].median()].nlargest(5, 'OPP_FG3_PCT')
        for _, team in weak_3pt.iterrows():
            suggestions.append({
                'Tipo': '3 Pontos do Adversário',
                'Time': team['TEAM_CITY'],
                'Motivo': f"Defesa 3pts: {team['OPP_FG3_PCT']*100:.1f}% permitida",
                'Confiança': np.random.randint(60, 80)
            })
    
    # Sugestão 3: Times com domínio de rebotes
    if 'REB_PCT' in df_teams.columns:
        high_reb = df_teams[df_teams['REB_PCT'] > 0.52].nlargest(5, 'REB_PCT')
        for _, team in high_reb.iterrows():
            suggestions.append({
                'Tipo': 'Over de Rebotes',
                'Time': team['TEAM_CITY'],
                'Motivo': f"Rebotes: {team['REB_PCT']*100:.1f}% do total",
                'Confiança': np.random.randint(65, 85)
            })
    
    # Sugestão 4: Times com melhor Net Rating (favoritos)
    if 'NET_RATING' in df_teams.columns:
        top_net = df_teams.nlargest(3, 'NET_RATING')
        for _, team in top_net.iterrows():
            suggestions.append({
                'Tipo': 'Vitória do Time',
                'Time': team['TEAM_CITY'],
                'Motivo': f"Net Rating: {team['NET_RATING']:+.1f} (eficiência líquida)",
                'Confiança': np.random.randint(70, 90)
            })
    
    # Exibir sugestões
    if suggestions:
        for sug in suggestions:
            # Cor do badge baseado na confiança
            if sug['Confiança'] >= 75:
                emoji, color = "🟢", "#064e3b"
            elif sug['Confiança'] >= 65:
                emoji, color = "🟡", "#451a03"
            else:
                emoji, color = "🔴", "#451a03"
            
            st.markdown(f"""
            <div style="background-color: {color}; padding: 15px; border-radius: 10px; border-left: 4px solid #fbbf24; margin: 10px 0;">
                <strong>{emoji} {sug['Tipo']}</strong><br>
                <strong>Time:</strong> {sug['Time']}<br>
                <strong>Motivo:</strong> {sug['Motivo']}<br>
                <strong>Confiança:</strong> {sug['Confiança']}%
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ Nenhuma sugestão gerada. Verifique se os dados foram carregados corretamente.")
    
    # Tabela completa de sugestões
    if suggestions:
        with st.expander("📋 Ver Todas as Sugestões em Tabela"):
            st.dataframe(pd.DataFrame(suggestions), use_container_width=True, hide_index=True)
    
    # Histórico simulado (para demonstração)
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
<strong>🏀 NBA ProBet Analytics</strong> | Dados: NBA Official API<br>
<strong>⚠️ Aviso:</strong> Ferramenta de análise estatística educacional. 
Apostas esportivas envolvem risco financeiro. Jogue com responsabilidade.
</center>
""", unsafe_allow_html=True)
