# 🧠 JULIANA - Gestão Clínica (MVP)

Aplicação Streamlit com SQLite, pronta para deploy.

## Rodar local

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Acesse http://localhost:8501

## Docker

```powershell
docker build -t gestao-clinica .
docker run -p 8501:8501 gestao-clinica
```

## Estrutura
- app.py
- db.py
- .streamlit/config.toml
- requirements.txt
- Dockerfile
- Procfile

Banco e uploads são criados em runtime (ignorar no Git).
