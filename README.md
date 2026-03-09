# NBA ProBet Analytics 2.0

Versão robusta para Streamlit Cloud, com fallback local para evitar quebra de deploy.

## Recursos
- Dashboard geral
- Jogos do dia
- Comparador de times
- Ranking de jogadores
- Sugestões automáticas
- Diagnóstico técnico

## Deploy
1. Suba os arquivos para o GitHub.
2. No Streamlit Cloud, aponte para `app.py`.
3. Opcional: configure `RAPIDAPI_KEY` em Secrets.

Sem `RAPIDAPI_KEY`, o app continua funcionando em modo demo robusto.
