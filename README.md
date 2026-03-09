# NBA ProBet Analytics 3.0

Versão 3.0 com foco em estabilidade no Streamlit Cloud, visual mais profissional e estrutura pronta para monetização.

## Recursos
- Dashboard executivo
- Jogos do dia com projeções
- Matchup Lab
- Player Hub
- Picks Engine
- Bankroll Tracker
- Área Premium
- Diagnóstico de deploy
- Fallback local caso a API externa falhe

## Secrets opcionais no Streamlit Cloud
```toml
RAPIDAPI_KEY = "sua_chave"
APP_ADMIN_USER = "admin"
APP_ADMIN_PASSWORD = "123456"
PREMIUM_ACCESS_CODE = "PROBETVIP"
```

## Deploy
1. Envie os arquivos para o GitHub.
2. Aponte o Streamlit Cloud para `app.py`.
3. Configure os secrets se quiser liberar API/login premium personalizados.
4. Faça reboot após subir a nova versão.
