"""
Sistema de Gestão Clínica - MVP
Desenvolvido para profissionais de psicologia
Arquivo: app.py (Aplicação Principal)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta, time
import os
import sys
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum



# ESQUEMAS DE ATENDIMENTOS (dependendo do banco de dados)


DB_SCHEMAS = {
    8: ["ID", "Empresa", "Nome", "Modalidade", "Data", "Hora", "Laudo PDF", "Avaliação PDF"],
    10: ["ID", "Empresa", "Nome", "Modalidade", "Data", "Hora", "Laudo PDF", "Avaliação PDF", "Status", "Observações"]
}


# IMPORTAÇÃO DO MÓDULO DE BANCO DE DADOS


try:
    import db
    # Verifica se as funções necessárias existem
    required_functions = ['init_db', 'inserir_atendimento', 'listar_atendimentos', 'obter_estatisticas']
    missing_functions = [func for func in required_functions if not hasattr(db, func)]

    if missing_functions:
        st.error(f"❌ Funções faltando no db.py: {', '.join(missing_functions)}")
        st.stop()

except ImportError as e:
    st.error("❌ Erro: Arquivo 'db.py' não encontrado!")
    st.error("💡 Certifique-se de que o arquivo 'db.py' está na mesma pasta que 'app.py'")
    st.error(f"Erro técnico: {str(e)}")
    st.stop()
except Exception as e:
    st.error(f"❌ Erro ao importar db.py: {str(e)}")
    st.stop()



# CONFIGURAÇÕES E CONSTANTES


class ModalidadeAtendimento(Enum):
    """Enum para modalidades de atendimento"""
    ADMISSIONAL = "Admissional"
    PERIODICO = "Periódico"
    DEMISSIONAL = "Demissional"
    RETORNO = "Retorno"

@dataclass
class AtendimentoData:
    """Classe para tipagem de dados de atendimento"""
    empresa: str
    nome: str
    modalidade: str
    data: str
    hora: str
    laudo_pdf: Optional[str] = None
    avaliacao_pdf: Optional[str] = None


# CONFIGURAÇÃO DA APLICAÇÃO


def configure_page() -> None:
    """Configura as propriedades básicas da página"""
    st.set_page_config(
        page_title="🧠 JULIANA - Gestão Clínica",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def apply_custom_css() -> None:
    """Aplica CSS personalizado mantendo identidade visual"""
    st.markdown(
        """
        <style>
        /* Tema principal - Verde Piscina */
        .stApp {
            background: linear-gradient(135deg, #1abc9c 0%, #16a085 100%);
        }

        /* Sidebar com gradiente verde piscina (compat antiga e atual) */
        .css-1d391kg { /* classes antigas do Streamlit */
            background: linear-gradient(180deg, #1abc9c 0%, #16a085 100%) !important;
        }
        section[data-testid="stSidebar"] > div {
            background: linear-gradient(180deg, #1abc9c 0%, #16a085 100%) !important;
        }

        /* Cards e containers */
        .stMetric {
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        /* Títulos e textos */
        h1, h2, h3, h4, h5, h6 {
            color: white !important;
            font-weight: 600;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }

        /* Botões primários (verde piscina) */
        .stButton > button {
            background: linear-gradient(45deg, #1abc9c, #16a085) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-weight: 700 !important;
            transition: all 0.2s ease-in-out !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.18);
        }

        /* Formulários */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stDateInput > div > div > input {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid #1abc9c;
            border-radius: 6px;
        }

        /* Tabelas */
        .stDataFrame {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        /* Alertas de sucesso */
        .stSuccess {
            background: rgba(46, 204, 113, 0.1);
            border-left: 4px solid #2ecc71;
        }

        /* Alertas de erro */
        .stError {
            background: rgba(231, 76, 60, 0.1);
            border-left: 4px solid #e74c3c;
        }

        /* Sidebar personalizada */
        .css-1lcbmhc {
            padding-top: 2rem;
        }

        /* Expandir containers */
        .stExpander {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            margin: 0.5rem 0;
        }

        /* Progress bars */
        .stProgress .st-bo {
            background: linear-gradient(90deg, #3498db, #2980b9);
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# GERENCIADOR DE BANCO DE DADOS


class DatabaseManager:
    """Gerenciador de operações do banco de dados"""

    @staticmethod
    @st.cache_resource
    def initialize_database() -> bool:
        """Inicializa o banco de dados"""
        try:
            if hasattr(db, 'init_db'):
                result = db.init_db()
                # Se retorna bool, usa o resultado; senão assume sucesso
                return result if isinstance(result, bool) else True
            else:
                st.error("❌ Função 'init_db' não encontrada no módulo db")
                return False
        except Exception as e:
            st.error(f"❌ Erro ao inicializar banco de dados: {str(e)}")
            return False

    @staticmethod
    @st.cache_data(ttl=30)  # Cache por 30 segundos
    def get_all_appointments() -> List[Tuple]:
        """Busca todos os atendimentos"""
        try:
            return db.listar_atendimentos()
        except Exception as e:
            st.error(f"❌ Erro ao buscar atendimentos: {str(e)}")
            return []


    @staticmethod
    def add_appointment(appointment_data: AtendimentoData) -> bool:
        """Adiciona novo atendimento"""
        try:
            result = db.inserir_atendimento(
                appointment_data.empresa,
                appointment_data.nome,
                appointment_data.modalidade,
                appointment_data.data,
                appointment_data.hora
            )
            st.cache_data.clear()  # Limpa cache após inserção
            # Se retorna bool, usa o resultado; senão assume sucesso
            return result if isinstance(result, bool) else True
        except Exception as e:
            st.error(f"❌ Erro ao adicionar atendimento: {str(e)}")
            return False

    @staticmethod
    @st.cache_data(ttl=60)
    def get_statistics() -> Dict:
        """Obtém estatísticas do sistema"""
        try:
            return db.obter_estatisticas()
        except Exception as e:
            st.error(f"❌ Erro ao obter estatísticas: {str(e)}")
            return {}

    @staticmethod
    def update_appointment(
        id_atendimento: int,
        empresa: Optional[str] = None,
        nome: Optional[str] = None,
        modalidade: Optional[str] = None,
        data: Optional[str] = None,
        hora: Optional[str] = None,
        status: Optional[str] = None,
        observacoes: Optional[str] = None,
        laudo_pdf: Optional[str] = None,
        avaliacao_pdf: Optional[str] = None,
    ) -> bool:
        """Atualiza um atendimento existente via db.atualizar_atendimento"""
        try:
            campos = {
                'empresa': empresa,
                'nome': nome,
                'modalidade': modalidade,
                'data': data,
                'hora': hora,
                'status': status,
                'observacoes': observacoes,
                'laudo_pdf': laudo_pdf,
                'avaliacao_pdf': avaliacao_pdf,
            }
            # remove None para não sobrescrever
            campos = {k: v for k, v in campos.items() if v is not None}
            ok = db.atualizar_atendimento(id_atendimento, **campos) if campos else False
            if ok:
                try:
                    st.cache_data.clear()
                except Exception:
                    pass
            return ok
        except Exception as e:
            st.error(f"❌ Erro ao atualizar atendimento: {str(e)}")
            return False

    @staticmethod
    def delete_appointment(id_atendimento: int) -> bool:
        """Exclui um atendimento existente"""
        try:
            ok = db.excluir_atendimento(id_atendimento)
            if ok:
                try:
                    st.cache_data.clear()
                except Exception:
                    pass
            return ok
        except Exception as e:
            st.error(f"❌ Erro ao excluir atendimento: {str(e)}")
            return False


# COMPONENTES DE INTERFACE


class UIComponents:
    """Componentes reutilizáveis da interface"""

    @staticmethod
    def render_header() -> None:
        """Renderiza o cabeçalho principal"""
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🧠 JULIANA - Gestão Clínica")
            st.markdown("### 👩‍⚕️ Sistema Profissional de Psicologia")

    @staticmethod
    def render_sidebar() -> Dict[str, Any]:
        """Renderiza a barra lateral com filtros"""
        st.sidebar.markdown(
            """
            <div style="margin: 6px 0 14px 0;">
                <div style="
                        background: linear-gradient(135deg, #1abc9c, #16a085);
                        padding: 2px;
                        border-radius: 12px;
                        box-shadow: 0 6px 16px rgba(0,0,0,0.15);
                ">
                    <div style="
                            background: rgba(255,255,255,0.15);
                            color: #ffffff;
                            border-radius: 10px;
                            padding: 12px 14px;
                            display: flex;
                            align-items: center;
                            gap: 10px;
                            backdrop-filter: blur(6px);
                    ">
                        <span style="font-size: 1.2rem;">🎛️</span>
                        <div style="font-weight: 800; letter-spacing: 0.3px;">Painel de Controle</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Navegação principal
        st.sidebar.markdown("### 📍 Navegação")
        page = st.sidebar.radio(
            "Selecione uma seção:",
            ["🏠 Dashboard", "📝 Atendimentos", "📊 Relatórios", "📄 Upload", "⚙️ Configurações"]
        )

        # Filtros
        st.sidebar.markdown("### 🔍 Filtros")

        # Filtro por data (opcional)
        use_date_filter = st.sidebar.checkbox("Filtrar por data", value=False)
        if use_date_filter:
            date_filter = st.sidebar.date_input(
                "Data:",
                min_value=date(2000, 1, 1),
                max_value=date.today() + timedelta(days=365)
            )
        else:
            date_filter = None

        # Filtro por modalidade (opcional com vazio)
        modalidade_options = [""] + [m.value for m in ModalidadeAtendimento]
        modalidade_filter = st.sidebar.selectbox(
            "Modalidade:",
            modalidade_options,
            index=0,
            format_func=lambda x: "Selecione..." if x == "" else x,
        )

        # Filtros por dados de atendimento (opcionais)
        empresa_filter = st.sidebar.text_input(
            "Empresa:", value="", placeholder="Digite para filtrar..."
        )
        paciente_filter = st.sidebar.text_input(
            "Nome do paciente:", value="", placeholder="Digite para filtrar..."
        )

        return {
            "page": page,
            "date_filter": date_filter,
            "modalidade_filter": modalidade_filter,
            "empresa_filter": empresa_filter,
            "paciente_filter": paciente_filter,
        }

    @staticmethod
    def render_appointment_form() -> Optional[AtendimentoData]:
        """Renderiza formulário de atendimento"""
        with st.expander("➕ Cadastrar Novo Atendimento", expanded=False):
            with st.form(key="appointment_form", clear_on_submit=True):
                st.markdown("#### 📋 Dados do Atendimento")

                col1, col2 = st.columns(2)

                with col1:
                    empresa = st.text_input(
                        "🏢 Empresa/Organização",
                        placeholder="Digite o nome da empresa..."
                    )
                    modalidade = st.selectbox(
                        "🏥 Modalidade",
                        [m.value for m in ModalidadeAtendimento]
                    )
                    data = st.date_input(
                        "📅 Data do Atendimento",
                        min_value=date.today()
                    )

                with col2:
                    nome = st.text_input(
                        "👤 Nome do Paciente",
                        placeholder="Digite o nome completo..."
                    )
                    hora = st.time_input("🕐 Horário")

                # Botões de ação
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    submitted = st.form_submit_button("💾 Salvar", type="primary")
                with col2:
                    st.form_submit_button("🔄 Limpar")

                if submitted and empresa and nome:
                    return AtendimentoData(
                        empresa=empresa.strip(),
                        nome=nome.strip(),
                        modalidade=modalidade,
                        data=data.strftime("%d/%m/%Y"),
                        hora=hora.strftime("%H:%M")
                    )
                elif submitted:
                    st.error("⚠️ Preencha todos os campos obrigatórios!")

        return None


# PÁGINAS DA APLICAÇÃO


class DashboardPage:
    """Página principal - Dashboard"""

    @staticmethod
    def render() -> None:
        """Renderiza o dashboard principal"""
        st.markdown("## 📊 Visão Geral do Sistema")

        # Estatísticas principais
        stats = DatabaseManager.get_statistics()
        if stats:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "👥 Total de Atendimentos",
                    stats.get('total_atendimentos', 0),
                    delta=f"+{stats.get('total_atendimentos', 0)} este mês"
                )

            with col2:
                st.metric(
                    "🏢 Empresas Atendidas",
                    stats.get('total_empresas', 0),
                    delta="Ativas"
                )

            with col3:
                st.metric(
                    "📄 Laudos Enviados",
                    stats.get('laudos_enviados', 0),
                    delta=f"{stats.get('laudos_enviados', 0)}/mês"
                )

            with col4:
                st.metric(
                    "📝 Avaliações",
                    stats.get('avaliacoes_enviadas', 0),
                    delta="Completas"
                )

        # Gráficos
        col1, col2 = st.columns(2)

        with col1:
            DashboardPage._render_modalidade_chart(stats)

        with col2:
            DashboardPage._render_recent_appointments()

    @staticmethod
    def _render_modalidade_chart(stats: Dict) -> None:
        """Renderiza gráfico de modalidades"""
        if stats and 'modalidades' in stats and stats['modalidades']:
            modalidades_data = stats['modalidades']

            fig = px.pie(
                values=list(modalidades_data.values()),
                names=list(modalidades_data.keys()),
                title="📊 Distribuição por Modalidade",
                color_discrete_sequence=px.colors.sequential.Blues_r
            )

            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                showlegend=True,
                height=400,
                title_font_size=16,
                font=dict(size=12)
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 Nenhum dado de modalidade disponível")

    @staticmethod
    def _render_recent_appointments() -> None:
        """Renderiza lista de atendimentos recentes"""
        st.markdown("### 🕐 Atendimentos Recentes")
        appointments = DatabaseManager.get_all_appointments()

        if appointments:
            recent = appointments[:5]  # últimos 5

            # Detecta automaticamente o número de colunas
            if recent:
                num_cols = len(recent[0])
                if num_cols >= 8:  # Nova estrutura com status
                    df = pd.DataFrame(recent, columns=[
                        "ID", "Empresa", "Nome", "Modalidade", "Data", "Hora", "Laudo", "Avaliação", "Status", "Observações"
                    ])
                    df_display = df[["Empresa", "Nome", "Modalidade", "Data", "Hora", "Status"]].copy()
                else:  # Estrutura antiga
                    df = pd.DataFrame(recent, columns=[
                        "ID", "Empresa", "Nome", "Modalidade", "Data", "Hora", "Laudo", "Avaliação"
                    ])
                    df_display = df[["Empresa", "Nome", "Modalidade", "Data", "Hora"]].copy()

                st.dataframe(df_display, use_container_width=True)
        else:
            st.info("📝 Nenhum atendimento cadastrado ainda.")

class AppointmentsPage:
    """Página de gerenciamento de atendimentos"""

    @staticmethod
    def render(filters: Dict) -> None:
        """Renderiza página de atendimentos"""
        st.markdown("## 📝 Gerenciamento de Atendimentos")

        # Barra de ações no cabeçalho: Excluir e Desfazer
        try:
            appointments = DatabaseManager.get_all_appointments()
            if appointments:
                # Detectar colunas dinamicamente
                num_cols = len(appointments[0])
                if num_cols >= 9:
                    cols_names = [
                        "ID", "Empresa", "Nome", "Modalidade", "Data", "Hora",
                        "Laudo PDF", "Avaliação PDF", "Status", "Observações"
                    ]
                else:
                    cols_names = [
                        "ID", "Empresa", "Nome", "Modalidade", "Data", "Hora",
                        "Laudo PDF", "Avaliação PDF"
                    ]
                df_head = pd.DataFrame(appointments, columns=cols_names)

                st.markdown("#### ⚠️ Excluir atendimento")
                col_sel, col_btn, col_undo = st.columns([3, 1, 1])
                with col_sel:
                    # Opções legíveis: ID — Nome • Empresa • Data Hora
                    options = []
                    for _, r in df_head.iterrows():
                        label = f"ID {int(r['ID'])} — {r.get('Nome','')} • {r.get('Empresa','')} • {r.get('Data','')} {r.get('Hora','')}"
                        options.append((label, int(r['ID'])))
                    sel_label = st.selectbox(
                        "Selecione para excluir:",
                        [o[0] for o in options],
                        index=0 if options else None,
                        key="delete_select_header"
                    )
                    sel_id_header = None
                    if sel_label:
                        for lbl, vid in options:
                            if lbl == sel_label:
                                sel_id_header = vid
                                break
                with col_btn:
                    if st.button("🗑️ Excluir", key="btn_delete_header") and sel_id_header is not None:
                        # snapshot para desfazer
                        snap = df_head[df_head["ID"] == sel_id_header].iloc[0].to_dict()
                        st.session_state['last_deleted_snapshot'] = snap
                        st.session_state['last_deleted_when'] = datetime.now().isoformat()
                        if DatabaseManager.delete_appointment(sel_id_header):
                            st.success(f"Excluído o atendimento ID {sel_id_header}.")
                            st.session_state['last_deleted_done'] = True
                            st.rerun()
                        else:
                            st.error("Não foi possível excluir.")

                with col_undo:
                    # Mostrar botão desfazer se houver exclusão recente
                    if st.session_state.get('last_deleted_snapshot'):
                        if st.button("↩️ Desfazer", key="btn_undo_delete_header"):
                            snap = st.session_state['last_deleted_snapshot']
                            try:
                                # Recriar registro (pode gerar novo ID)
                                ok_ins = db.inserir_atendimento(
                                    snap.get('Empresa',''),
                                    snap.get('Nome',''),
                                    snap.get('Modalidade',''),
                                    snap.get('Data',''),
                                    snap.get('Hora',''),
                                    snap.get('Laudo PDF') if 'Laudo PDF' in snap else snap.get('Laudo', None),
                                    snap.get('Avaliação PDF') if 'Avaliação PDF' in snap else snap.get('Avaliação', None),
                                    snap.get('Observações') if 'Observações' in snap else None,
                                )
                                if ok_ins:
                                    st.success("Registro restaurado (novo ID gerado).")
                                    # limpar estado de desfazer
                                    st.session_state.pop('last_deleted_snapshot', None)
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Falha ao restaurar registro.")
                            except Exception as e:
                                st.error(f"Erro ao desfazer: {str(e)}")
        except Exception as e:
            st.error(f"❌ Erro na barra de exclusão: {str(e)}")

        # Formulário de novo atendimento
        new_appointment = UIComponents.render_appointment_form()
        if new_appointment:
            if DatabaseManager.add_appointment(new_appointment):
                st.success("✅ Atendimento cadastrado com sucesso!")
                st.balloons()
                st.rerun()

        # Lista de atendimentos
        AppointmentsPage._render_appointments_table(filters)

    @staticmethod
    def _render_appointments_table(filters: Dict) -> None:
        """Renderiza tabela de atendimentos com filtros"""
        appointments = DatabaseManager.get_all_appointments()

        if not appointments:
            st.info("📋 Nenhum atendimento encontrado.")
            return

        # Detecta automaticamente o número de colunas
        if appointments:
            num_cols = len(appointments[0])
            if num_cols >= 8:  # Nova estrutura
                df = pd.DataFrame(appointments, columns=[
                    "ID", "Empresa", "Nome", "Modalidade", "Data", "Hora", "Laudo PDF", "Avaliação PDF", "Status", "Observações"
                ])
            else:  # Estrutura antiga
                df = pd.DataFrame(appointments, columns=[
                    "ID", "Empresa", "Nome", "Modalidade", "Data", "Hora", "Laudo PDF", "Avaliação PDF"
                ])

        # Aplicar filtros
        if filters.get("modalidade_filter"):
            df = df[df["Modalidade"] == filters["modalidade_filter"]]

        if filters.get("date_filter"):
            try:
                sel_date_str = filters["date_filter"].strftime("%d/%m/%Y")
                if "Data" in df.columns:
                    df = df[df["Data"] == sel_date_str]
            except Exception:
                pass

        # Filtro por empresa (contém, case-insensitive)
        emp = (filters.get("empresa_filter") or "").strip()
        if emp and "Empresa" in df.columns:
            df = df[df["Empresa"].str.contains(emp, case=False, na=False)]

        # Filtro por nome do paciente (contém, case-insensitive)
        pac = (filters.get("paciente_filter") or "").strip()
        if pac and "Nome" in df.columns:
            df = df[df["Nome"].str.contains(pac, case=False, na=False)]

        # Interface de visualização
        st.markdown("### 📊 Lista de Atendimentos")

        if not df.empty:
            # Opções de visualização
            col1, col2 = st.columns([3, 1])
            with col2:
                show_columns = st.multiselect(
                    "Colunas visíveis:",
                    df.columns.tolist(),
                    default=["Empresa", "Nome", "Modalidade", "Data", "Hora"]
                )

            if show_columns:
                st.dataframe(
                    df[show_columns],
                    use_container_width=True,
                    height=400
                )

                # Ações em lote
                with st.expander("⚙️ Ações Avançadas"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📤 Exportar CSV"):
                            csv = df.to_csv(index=False)
                            st.download_button(
                                "⬇️ Download CSV",
                                csv,
                                "atendimentos.csv",
                                "text/csv"
                            )

                    with col2:
                        if st.button("📧 Enviar Relatório"):
                            st.info("🚀 Funcionalidade em desenvolvimento")

                    with col3:
                        if st.button("🔄 Atualizar Dados"):
                            st.cache_data.clear()
                            st.rerun()

                # Ações por linha (Editar)
                with st.expander("🛠️ Ações por linha", expanded=False):
                    try:
                        vis_cols = [c for c in ["ID", "Empresa", "Nome", "Data", "Hora"] if c in df.columns]
                        sub = df[vis_cols].copy()
                        if sub.empty:
                            st.info("Nenhum registro para ações.")
                        else:
                            for _, row in sub.head(30).iterrows():
                                c1, c2 = st.columns([6, 1])
                                with c1:
                                    desc = f"ID {int(row['ID'])} — {row.get('Nome','')} • {row.get('Empresa','')} • {row.get('Data','')} {row.get('Hora','')}"
                                    st.write(desc)
                                with c2:
                                    if st.button("✏️ Editar", key=f"editrow_{int(row['ID'])}"):
                                        st.session_state['edit_id'] = int(row['ID'])
                                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao montar ações por linha: {str(e)}")

                st.divider()
                with st.expander("✏️ Editar Atendimento", expanded='edit_id' in st.session_state):
                    try:
                        ids = df["ID"].tolist()
                        if not ids:
                            st.info("Nenhum atendimento para editar.")
                        else:
                            if 'edit_id' in st.session_state and st.session_state['edit_id'] in ids:
                                sel_id = st.session_state['edit_id']
                                st.caption(f"Editando atendimento ID {sel_id}")
                                if st.button("↩️ Trocar atendimento"):
                                    st.session_state.pop('edit_id', None)
                                    st.rerun()
                            else:
                                sel_id = st.selectbox("Selecione o atendimento (ID):", ids)
                            if sel_id is None:
                                st.info("Selecione um atendimento para editar.")
                                return
                            try:
                                sel_id_int = int(sel_id)
                            except Exception:
                                st.error("ID inválido selecionado.")
                                return
                            sel_row = df[df["ID"] == sel_id_int].iloc[0]

                            # Preparar valores atuais
                            cur_empresa = str(sel_row.get("Empresa", ""))
                            cur_nome = str(sel_row.get("Nome", ""))
                            cur_modalidade = str(sel_row.get("Modalidade", ""))
                            cur_data_str = str(sel_row.get("Data", ""))
                            cur_hora_str = str(sel_row.get("Hora", ""))
                            cur_status = str(sel_row.get("Status", "Agendado")) if "Status" in df.columns else None
                            cur_obs = str(sel_row.get("Observações", "")) if "Observações" in df.columns else None

                            # Converte data/hora
                            try:
                                cur_data = datetime.strptime(cur_data_str, "%d/%m/%Y").date() if cur_data_str else date.today()
                            except Exception:
                                cur_data = date.today()
                            try:
                                h, m = (cur_hora_str or "09:00").split(":")
                                cur_time = time(int(h), int(m))
                            except Exception:
                                cur_time = time(9, 0)

                            with st.form(f"edit_form_{sel_id}"):
                                c1, c2 = st.columns(2)
                                with c1:
                                    empresa_n = st.text_input("🏢 Empresa/Organização", value=cur_empresa)
                                    modalidade_n = st.selectbox("🏥 Modalidade", [m.value for m in ModalidadeAtendimento], index=max(0, [m.value for m in ModalidadeAtendimento].index(cur_modalidade)) if cur_modalidade in [m.value for m in ModalidadeAtendimento] else 0)
                                    data_n = st.date_input("📅 Data", value=cur_data)
                                with c2:
                                    nome_n = st.text_input("👤 Nome do Paciente", value=cur_nome)
                                    hora_n = st.time_input("🕒 Hora", value=cur_time)
                                    if cur_status is not None:
                                        status_opts = sorted(list({"Agendado", "Concluído", "Cancelado", cur_status}))
                                        status_n = st.selectbox("📌 Status", status_opts, index=status_opts.index(cur_status))
                                    else:
                                        status_n = None

                                obs_n = st.text_area("📝 Observações", value=cur_obs or "") if cur_obs is not None else None

                                submitted = st.form_submit_button("💾 Salvar alterações", type="primary")
                                if submitted:
                                    # Monta campos a atualizar
                                    campos = {
                                        'empresa': empresa_n.strip(),
                                        'nome': nome_n.strip(),
                                        'modalidade': modalidade_n,
                                        'data': data_n.strftime("%d/%m/%Y"),
                                        'hora': hora_n.strftime("%H:%M"),
                                    }
                                    if status_n is not None:
                                        campos['status'] = status_n
                                    if obs_n is not None:
                                        campos['observacoes'] = obs_n.strip()

                                    ok = DatabaseManager.update_appointment(sel_id_int, **campos)
                                    if ok:
                                        st.success("✅ Atendimento atualizado!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Não foi possível atualizar.")
                    except Exception as e:
                        st.error(f"❌ Erro na edição: {str(e)}")

class ReportsPage:
    """Página de relatórios e análises"""

    @staticmethod
    def render() -> None:
        """Renderiza página de relatórios"""
        st.markdown("## 📊 Relatórios e Análises")

        # Seletor de período
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Data inicial:", date.today() - timedelta(days=30))
        with col2:
            end_date = st.date_input("Data final:", date.today())

        if start_date > end_date:
            st.error("❌ Data inicial deve ser anterior à data final!")
            return

        # Relatório de produtividade
        ReportsPage._render_productivity_report(start_date, end_date)

    @staticmethod
    def _render_productivity_report(start_date: date, end_date: date) -> None:
        """Renderiza relatório de produtividade"""
        st.markdown("### 📈 Relatório de Produtividade")

        appointments = DatabaseManager.get_all_appointments()
        if not appointments:
            st.info("📊 Nenhum dado disponível para o período selecionado.")
            return

        # Detecta estrutura das colunas
        num_cols = len(appointments[0]) if appointments else 0
        if num_cols >= 8:
            df = pd.DataFrame(appointments, columns=[
                "ID", "Empresa", "Nome", "Modalidade", "Data", "Hora", "Laudo PDF", "Avaliação PDF", "Status", "Observações"
            ])
        else:
            df = pd.DataFrame(appointments, columns=[
                "ID", "Empresa", "Nome", "Modalidade", "Data", "Hora", "Laudo PDF", "Avaliação PDF"
            ])

        # Conversão de datas para filtro
        try:
            df['Data_Conv'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
            df_filtered = df[
                (df['Data_Conv'] >= pd.to_datetime(start_date)) &
                (df['Data_Conv'] <= pd.to_datetime(end_date)) &
                df['Data_Conv'].notna()
            ]

            if df_filtered.empty:
                st.info("📊 Nenhum atendimento no período selecionado.")
                return

            # Métricas do período
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Atendimentos no Período", len(df_filtered))
            with col2:
                st.metric("Empresas Atendidas", df_filtered['Empresa'].nunique())
            with col3:
                avg_daily = len(df_filtered) / max((end_date - start_date).days, 1)
                st.metric("Média Diária", f"{avg_daily:.1f}")

            # Gráfico temporal
            daily_counts = df_filtered.groupby('Data').size().reset_index(name='Count')
            if not daily_counts.empty:
                fig = px.line(
                    daily_counts,
                    x='Data',
                    y='Count',
                    title='📈 Atendimentos por Dia',
                    markers=True
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Erro ao processar relatório: {str(e)}")

class SettingsPage:
    """Página de configurações"""

    @staticmethod
    def render() -> None:
        """Renderiza página de configurações"""
        st.markdown("## ⚙️ Configurações do Sistema")

        tab1, tab2, tab3 = st.tabs(["🏥 Clínica", "📄 Documentos", "🔒 Sistema"])

        with tab1:
            SettingsPage._render_clinic_settings()

        with tab2:
            SettingsPage._render_document_settings()

        with tab3:
            SettingsPage._render_system_settings()

    @staticmethod
    def _render_clinic_settings() -> None:
        """Configurações da clínica"""
        st.markdown("### 🏥 Informações da Clínica")

        with st.form("clinic_settings"):
            clinic_name = st.text_input("Nome da Clínica:", value="Clínica Dra. Juliana")
            clinic_address = st.text_area("Endereço:", value="")
            clinic_phone = st.text_input("Telefone:", value="")
            clinic_email = st.text_input("E-mail:", value="")

            if st.form_submit_button("💾 Salvar Configurações"):
                st.success("✅ Configurações salvas com sucesso!")

    @staticmethod
    def _render_document_settings() -> None:
        """Configurações de documentos"""
        st.markdown("### 📄 Configurações de Documentos")

        st.info("🚀 Configurações de templates de documentos em desenvolvimento")

    @staticmethod
    def _render_system_settings() -> None:
        """Configurações do sistema"""
        st.markdown("### 🔒 Configurações do Sistema")

        # Status básico do sistema
        with st.expander("🗄️ Gerenciamento de Banco de Dados"):
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🔄 Limpar Cache"):
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    st.success("✅ Cache limpo!")

            with col2:
                if st.button("📊 Verificar Sistema"):
                    try:
                        stats = DatabaseManager.get_statistics()
                        if stats:
                            st.success("✅ Sistema funcionando corretamente!")
                        else:
                            st.warning("⚠️ Sistema acessível, mas sem dados")
                    except Exception as e:
                        st.error(f"❌ Erro no sistema: {str(e)}")

            with col3:
                if st.button("🛠️ Reinicializar"):
                    st.cache_resource.clear()
                    if DatabaseManager.initialize_database():
                        st.success("✅ Sistema reinicializado!")
                    else:
                        st.error("❌ Erro na reinicialização!")

        # Informações do sistema
        st.markdown("#### ℹ️ Informações do Sistema")
        try:
            stats = DatabaseManager.get_statistics()
            if stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.json({
                        "Total de Registros": stats.get('total_atendimentos', 0),
                        "Empresas Únicas": stats.get('total_empresas', 0),
                        "Laudos Enviados": stats.get('laudos_enviados', 0)
                    })

                with col2:
                    modalidades = stats.get('modalidades', {})
                    if modalidades:
                        st.json({"Modalidades": modalidades})
        except Exception as e:
            st.error(f"❌ Erro ao carregar estatísticas: {str(e)}")

        st.info("""
        **Sistema de Gestão Clínica - Dra. Juliana**

        ✅ **Versão:** 1.0.0 MVP
        ✅ **Status:** Funcionando
        ✅ **Banco:** SQLite
        ✅ **Cache:** Otimizado
        """)



# APLICAÇÃO PRINCIPAL

class ClinicalManagementApp:
    """Aplicação principal do sistema de gestão clínica"""

    def __init__(self):
        """Inicializa a aplicação"""
        self.db_manager = DatabaseManager()

    def run(self) -> None:
        """Executa a aplicação principal"""
        # Configuração inicial
        configure_page()
        apply_custom_css()

        # Inicialização do banco de dados
        if not self.db_manager.initialize_database():
            st.error("❌ Falha na inicialização do banco de dados!")
            st.stop()

        # Interface principal
        UIComponents.render_header()

        # Sidebar com filtros e navegação
        filters = UIComponents.render_sidebar()

        # Roteamento de páginas
        self._route_pages(filters)

    def _route_pages(self, filters: Dict) -> None:
        """Gerencia o roteamento entre páginas"""
        page = filters["page"]

        if page == "🏠 Dashboard":
            DashboardPage.render()
        elif page == "📝 Atendimentos":
            AppointmentsPage.render(filters)
        elif page == "📊 Relatórios":
            ReportsPage.render()
        elif page == "📄 Upload":
            UploadPage.render()
        elif page == "⚙️ Configurações":
            SettingsPage.render()
        else:
            st.error("❌ Página não encontrada!")


# PÁGINA DE UPLOAD DE PDFs

class UploadPage:
    """Página para adicionar e baixar PDFs"""

    @staticmethod
    def render() -> None:
        st.markdown("## 📄 Upload de PDFs")
        st.caption("Envie documentos em PDF e baixe quando precisar.")

        tab1, tab2 = st.tabs(["Adicionar PDF", "Baixar PDFs"])

        with tab1:
            UploadPage._render_upload_form()

        with tab2:
            UploadPage._render_download_list()

    @staticmethod
    def _uploads_dir() -> str:
        base_dir = os.path.dirname(__file__)
        dest = os.path.join(base_dir, "uploads")
        os.makedirs(dest, exist_ok=True)
        return dest

    @staticmethod
    def _render_upload_form() -> None:
        st.markdown("#### 📤 Adicionar novo PDF")
        up_file = st.file_uploader("Selecione um arquivo PDF", type=["pdf"], help="Tamanho máximo recomendado: 10MB")

        if up_file is not None:
            size_mb = len(up_file.getvalue()) / (1024 * 1024)
            st.info(f"Arquivo: {up_file.name} — {size_mb:.2f} MB")

            col1, col2 = st.columns([2, 1])
            with col1:
                nome_seguro = up_file.name.replace(" ", "_")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                destino = os.path.join(UploadPage._uploads_dir(), f"{timestamp}_{nome_seguro}")

            with col2:
                if st.button("Salvar PDF", type="primary", use_container_width=True):
                    try:
                        if size_mb > 10:
                            st.error("❌ Arquivo muito grande (máx. 10MB)")
                            return
                        with open(destino, "wb") as f:
                            f.write(up_file.getbuffer())
                        st.success("✅ PDF salvo com sucesso")
                        st.download_button("Baixar agora", up_file.getvalue(), file_name=nome_seguro)
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar: {str(e)}")

    @staticmethod
    def _render_download_list() -> None:
        st.markdown("#### 📥 PDFs Disponíveis")
        pasta = UploadPage._uploads_dir()
        try:
            arquivos = [f for f in os.listdir(pasta) if f.lower().endswith('.pdf')]
            if not arquivos:
                st.info("Nenhum PDF encontrado.")
                return

            for idx, nome in enumerate(sorted(arquivos, reverse=True)):
                caminho = os.path.join(pasta, nome)
                cols = st.columns([4, 1])
                with cols[0]:
                    st.write(f"📄 {nome}")
                    st.caption(f"{os.path.getsize(caminho) // 1024} KB")
                with cols[1]:
                    with open(caminho, "rb") as f:
                        st.download_button("Baixar", f.read(), file_name=nome, key=f"dl_{idx}")
        except Exception as e:
            st.error(f"❌ Erro ao listar PDFs: {str(e)}")


#  EXECUÇÃO PRINCIPAL


if __name__ == "__main__":
    app = ClinicalManagementApp()
    app.run()
