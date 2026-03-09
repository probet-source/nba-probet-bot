# NBA ProBet SaaS 4.0

Versão 4.0 em estilo SaaS real, pronta para GitHub + Streamlit Cloud.

## Recursos

- login e cadastro local com SQLite;
- plano Free e Premium;
- painel do usuário;
- jogos do dia com projeções;
- Matchup Lab;
- Player Hub;
- Picks Engine premium;
- Bankroll Tracker com exportação CSV;
- coleta de feedback;
- painel administrativo;
- MRR estimado e gestão básica de assinantes.

## Estrutura

- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `README.md`

## Deploy

1. Envie os arquivos para o GitHub.
2. Aponte o Streamlit Cloud para `app.py`.
3. Faça o deploy.

## Credenciais administrativas padrão

Você pode mudar via Secrets/variáveis de ambiente:

- `APP_ADMIN_EMAIL`
- `APP_ADMIN_NAME`
- `APP_ADMIN_PASSWORD`

Padrões locais:

- e-mail: `admin@probet.local`
- senha: `admin123`

## Observações

- O banco `probet_saas.db` é criado automaticamente.
- Esta versão foi projetada para rodar sem APIs externas, priorizando estabilidade.
- Para produção comercial real, o próximo passo é integrar pagamento, recuperação de senha, e-mail transacional e autenticação robusta.
