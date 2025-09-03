# 🧠 JULIANA - Gestão Clínica (MVP)

Aplicação Streamlit para gestão clínica psicológica, com tema visual "Verde Piscina", SQLite como banco padrão, e páginas: Dashboard, Atendimentos, Relatórios, Upload e Configurações.

## Como rodar

- Python 3.12+
- Instale dependências:

```
pip install -r requirements.txt
```

- Rode:

```
streamlit run app.py
```

Acesse http://localhost:8501

## Docker

```
docker build -t gestao-clinica .
docker run -p 8501:8501 gestao-clinica
```

## Estrutura mínima

- app.py (principal)
- db.py (SQLite)
- .streamlit/config.toml (server/theme)
- requirements.txt
- Procfile (PaaS)
- Dockerfile

## Observações

- O arquivo gestao_clinica.db e a pasta uploads são criados em runtime e devem ser ignorados no Git.
- Não há necessidade de .env para SQLite.
