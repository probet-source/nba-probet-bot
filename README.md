# NBA ProBet SaaS 5.0

Versão mais estável, premium e orientada a produto do bot, com foco em **funcionar no Streamlit Cloud sem quebrar**.

## Stack de dados

- **ESPN**: placar do dia, agenda e notícias NBA
- **BALLDONTLIE**: enriquecimento opcional via `BDL_API_KEY`
- **TheSportsDB**: logos e metadata visual dos times
- **CSV próprio / Kaggle / exports**: histórico manual para backtest e análises futuras
- **Fallback local**: seed interna de ratings para o app continuar funcional mesmo sem API

## O que já vem pronto

- login e cadastro local com SQLite
- onboarding premium
- dashboard estilo SaaS
- live center
- matchup studio
- picks lab
- bankroll tracker
- feedback e painel admin
- diagnóstico de deploy

## Secrets opcionais no Streamlit Cloud

```toml
BDL_API_KEY = "sua_chave_balldontlie"
THESPORTSDB_API_KEY = "sua_chave_ou_123"
APP_ADMIN_EMAIL = "admin@probet.local"
APP_ADMIN_NAME = "Administrador"
APP_ADMIN_PASSWORD = "admin123"
```

## Deploy

1. Suba os arquivos no GitHub.
2. No Streamlit Cloud, aponte para `app.py`.
3. Adicione os secrets opcionais.
4. Faça reboot/redeploy.

## Observação importante

O app foi desenhado para ser resiliente:
- se a ESPN falhar, tenta outras camadas;
- se BALLDONTLIE não estiver configurada, o app continua;
- se TheSportsDB não responder, apenas os logos podem faltar;
- se nada externo funcionar, entra o fallback local.
