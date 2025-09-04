# 🏥 JULIANA - Sistema de Gestão Clínica

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)

Sistema moderno de gestão clínica desenvolvido em Streamlit, com interface intuitiva e recursos completos para administração de atendimentos médicos.

## ✨ Características Principais

- 🎨 **Interface Moderna**: Design responsivo com tema verde profissional
- 📊 **Dashboard Interativo**: Métricas em tempo real e gráficos dinâmicos
- 📝 **Gestão de Atendimentos**: CRUD completo para consultas médicas
- 📈 **Relatórios Avançados**: Analytics e exportação de dados
- 📄 **Upload de Documentos**: Gerenciamento de laudos e documentos PDF
- 🔒 **Sistema de Segurança**: Logs de auditoria e sanitização de dados
- ⚙️ **Configurações**: Painel administrativo completo

## 🚀 Funcionalidades

### Dashboard
- Cards estatísticos modernos com animações
- Gráficos interativos (Plotly)
- Métricas de performance em tempo real
- Sparklines e indicadores visuais

### Atendimentos
- Cadastro completo de consultas
- Filtros avançados por data, empresa e modalidade
- Edição e exclusão de registros
- Visualização em tabela responsiva

### Relatórios
- Gráficos de distribuição por modalidade
- Timeline de atendimentos
- Estatísticas por empresa
- Exportação de dados

### Upload de Documentos
- Interface drag-and-drop
- Suporte a arquivos PDF
- Gerenciamento de laudos e avaliações
- Validação de arquivos

### Configurações
- Logs de segurança e auditoria
- Limpeza de cache do sistema
- Verificação de banco de dados
- Dados de exemplo para demonstração

## 🛠️ Tecnologias Utilizadas

- **Frontend**: Streamlit com CSS customizado
- **Backend**: Python 3.12+
- **Banco de Dados**: SQLite
- **Gráficos**: Plotly
- **Segurança**: Sistema de logs e sanitização
- **Deploy**: Docker + Heroku ready

## 📦 Instalação e Execução

### Pré-requisitos
- Python 3.12 ou superior
- pip (gerenciador de pacotes Python)

### Instalação Local

```bash
# Clone o repositório
git clone https://github.com/JeanCarlos08/gestao-clinica.git
cd gestao-clinica

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
streamlit run app.py
```

Acesse http://localhost:8501

### Execução com porta específica

```bash
streamlit run app.py --server.port 8510
```

## 🐳 Docker

```bash
# Build da imagem
docker build -t gestao-clinica .

# Executar container
docker run -p 8501:8501 gestao-clinica
```

## 🌐 Deploy (Heroku)

O projeto está configurado para deploy automático no Heroku:

```bash
# Heroku CLI
git push heroku main
```

Arquivos de configuração inclusos:
- `Procfile`: Configuração do servidor
- `runtime.txt`: Versão do Python
- `requirements.txt`: Dependências

## 📁 Estrutura do Projeto

```
gestao_clinica/
├── app.py                 # Aplicação principal Streamlit
├── db.py                  # Módulo do banco de dados
├── security.py            # Sistema de segurança e logs
├── requirements.txt       # Dependências Python
├── Dockerfile            # Configuração Docker
├── Procfile              # Configuração Heroku
├── runtime.txt           # Versão Python para deploy
├── .streamlit/           # Configurações Streamlit
├── logs/                 # Logs de segurança (auto-criado)
├── uploads/              # Arquivos enviados (auto-criado)
└── README.md            # Documentação

# Arquivos auto-gerados (ignorados no Git)
├── gestao_clinica.db     # Banco SQLite
├── __pycache__/          # Cache Python
└── .venv/               # Ambiente virtual
```

## 🎨 Interface

### Tema de Cores
- **Verde Principal**: `#4DA768`
- **Verde Claro**: `#99E89D`
- **Verde Escuro**: `#2d5a3d`
- **Acentos**: Gradientes e transparências

### Componentes UI
- Cards modernos com hover effects
- Botões com gradientes
- Inputs estilizados
- Tabelas responsivas
- Sidebar personalizada

## 🔐 Segurança

- **Sanitização**: Todos os inputs são sanitizados
- **Logs de Auditoria**: Registro de todas as ações
- **Validação**: Formatos de data, hora e tipos de arquivo
- **Backup**: Sistema de logs rotativos

## 📊 Modalidades de Atendimento

- **Admissional**: Exames de admissão
- **Periódico**: Consultas de rotina
- **Demissional**: Exames de desligamento
- **Retorno**: Consultas de acompanhamento

## 🗃️ Banco de Dados

### Tabela: atendimentos
```sql
CREATE TABLE atendimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa TEXT NOT NULL,
    nome TEXT NOT NULL,
    modalidade TEXT NOT NULL,
    data TEXT NOT NULL,
    hora TEXT NOT NULL,
    laudo_pdf TEXT,
    avaliacao_pdf TEXT,
    status TEXT DEFAULT 'Pendente',
    observacoes TEXT
);
```

## 🚦 Status do Projeto

- ✅ **MVP Completo**: Todas as funcionalidades básicas implementadas
- ✅ **Interface Moderna**: Design profissional e responsivo
- ✅ **Sistema de Segurança**: Logs e validações ativas
- ✅ **Deploy Ready**: Configurado para produção
- ✅ **Documentação**: README completo

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Autor

**Jean Carlos**
- GitHub: [@JeanCarlos08](https://github.com/JeanCarlos08)
- Projeto: Sistema de Gestão Clínica JULIANA

---

⭐ **Se este projeto foi útil, considere dar uma estrela!**
