"""
JULIANA - Gestão Clínica (MVP)
Aplicação Streamlit com SQLite (sem dependências externas de DB)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

# Banco de dados local (db.py deve estar na mesma pasta)
try:
	import db
except Exception as e:
	st.error(f"Erro ao importar o módulo de banco de dados: {e}")
	st.stop()


class ModalidadeAtendimento(Enum):
	ADMISSIONAL = "Admissional"
	PERIODICO = "Periódico"
	DEMISSIONAL = "Demissional"
	RETORNO = "Retorno"


@dataclass
class AtendimentoData:
	empresa: str
	nome: str
	modalidade: str
	data: str
	hora: str
	laudo_pdf: Optional[str] = None
	avaliacao_pdf: Optional[str] = None


def configure_page() -> None:
	st.set_page_config(
		page_title="🧠 JULIANA - Gestão Clínica",
		page_icon="🧠",
		layout="wide",
		initial_sidebar_state="expanded",
	)


def apply_custom_css() -> None:
	st.markdown(
		"""
		<style>
		.stApp { background: linear-gradient(135deg, #1abc9c 0%, #16a085 100%); }
		section[data-testid="stSidebar"] > div { background: linear-gradient(180deg, #1abc9c 0%, #16a085 100%) !important; }
		h1, h2, h3, h4, h5, h6 { color: #fff !important; font-weight: 600; text-shadow: 1px 1px 2px rgba(0,0,0,.12); }
		.stButton > button { background: linear-gradient(45deg, #1abc9c, #16a085) !important; color: #fff !important; border: 0; border-radius: 8px; font-weight: 700; }
		.stDataFrame { background: rgba(255,255,255,.95); border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,.1); }

		/* Métricas gerais (mantidas) */
		.css-1aumxhk { background-color: #f9f9f9; border-radius: 10px; padding: 10px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); transition: transform 0.2s; }
		.css-1aumxhk:hover { transform: scale(1.05); }
		h1, h2, h3 { font-family: 'Arial', sans-serif; color: #333333; }
		.stButton button { background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 10px 20px; font-size: 16px; cursor: pointer; transition: background-color 0.3s; }
		.stButton button:hover { background-color: #45a049; }

		/* Cards de KPI (Relatórios) - sem alterar paleta */
		.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 8px 0 16px; }
		.kpi-card { background: rgba(255,255,255,0.92); border: 1px solid rgba(255,255,255,0.25); border-radius: 14px; padding: 16px 18px; box-shadow: 0 8px 18px rgba(0,0,0,0.12); backdrop-filter: blur(3px); }
		.kpi-title { font-size: 0.9rem; opacity: 0.85; margin-bottom: 6px; }
		.kpi-value { font-size: 1.8rem; font-weight: 800; line-height: 1.1; }
		</style>
		""",
		unsafe_allow_html=True,
	)


class DatabaseManager:
	@staticmethod
	@st.cache_resource
	def initialize_database() -> bool:
		try:
			return bool(db.init_db())
		except Exception as e:
			st.error(f"Falha ao inicializar DB: {e}")
			return False

	@staticmethod
	@st.cache_data(ttl=30)
	def get_all_appointments() -> List[Tuple]:
		try:
			return db.listar_atendimentos()
		except Exception as e:
			st.error(f"Erro ao listar atendimentos: {e}")
			return []

	@staticmethod
	def add_appointment(a: AtendimentoData) -> bool:
		ok = db.inserir_atendimento(a.empresa, a.nome, a.modalidade, a.data, a.hora)
		if ok:
			st.cache_data.clear()
		return bool(ok)

	@staticmethod
	def update_appointment(id_atendimento: int, **campos) -> bool:
		ok = db.atualizar_atendimento(id_atendimento, **campos)
		if ok:
			st.cache_data.clear()
		return bool(ok)

	@staticmethod
	def delete_appointment(id_atendimento: int) -> bool:
		ok = db.excluir_atendimento(id_atendimento)
		if ok:
			st.cache_data.clear()
		return bool(ok)

	@staticmethod
	@st.cache_data(ttl=60)
	def get_statistics() -> Dict:
		return db.obter_estatisticas()


class UIComponents:
	@staticmethod
	def render_header(page: str) -> None:
		if page == "🏠 Dashboard":
			col1, col2, col3 = st.columns([1, 2, 1])
			with col2:
				st.title("🧠 JULIANA - Gestão Clínica")
				st.markdown("### 👩‍⚕️ Sistema Profissional de Psicologia")
		else:
			# Outras páginas já possuem seus próprios títulos nas seções específicas
			pass

	@staticmethod
	def render_sidebar() -> Dict[str, Any]:
		st.sidebar.markdown("### 📍 Navegação")
		page = st.sidebar.radio(
			"Selecione uma seção:",
			["🏠 Dashboard", "📝 Atendimentos", "📊 Relatórios", "📄 Upload", "⚙️ Configurações"],
		)

		st.sidebar.markdown("### 🔍 Filtros")
		use_date_filter = st.sidebar.checkbox("Filtrar por data", value=False)
		date_filter = st.sidebar.date_input("Data:") if use_date_filter else None
		modalidade_filter = st.sidebar.selectbox(
			"Modalidade:", [""] + [m.value for m in ModalidadeAtendimento], index=0,
			format_func=lambda x: "Selecione..." if x == "" else x,
		)
		empresa_filter = st.sidebar.text_input("Empresa:", value="")
		paciente_filter = st.sidebar.text_input("Nome do paciente:", value="")
		return {
			"page": page,
			"date_filter": date_filter,
			"modalidade_filter": modalidade_filter,
			"empresa_filter": empresa_filter,
			"paciente_filter": paciente_filter,
		}

	@staticmethod
	def render_appointment_form() -> Optional[AtendimentoData]:
		with st.expander("➕ Cadastrar Novo Atendimento", expanded=False):
			with st.form("appointment_form", clear_on_submit=True):
				col1, col2 = st.columns(2)
				with col1:
					empresa = st.text_input("🏢 Empresa/Organização")
					modalidade = st.selectbox("🏥 Modalidade", [m.value for m in ModalidadeAtendimento])
					data_sel = st.date_input("📅 Data", min_value=date.today())
				with col2:
					nome = st.text_input("👤 Nome do Paciente")
					hora_sel = st.time_input("🕐 Horário")
				c1, c2, _ = st.columns([1, 1, 4])
				with c1:
					submitted = st.form_submit_button("💾 Salvar", type="primary")
				with c2:
					st.form_submit_button("🔄 Limpar")
				if submitted:
					if not empresa or not nome:
						st.error("Preencha os campos obrigatórios.")
					else:
						return AtendimentoData(
							empresa=empresa.strip(),
							nome=nome.strip(),
							modalidade=modalidade,
							data=data_sel.strftime("%d/%m/%Y"),
							hora=hora_sel.strftime("%H:%M"),
						)
		return None


class DashboardPage:
	@staticmethod
	def render() -> None:
		st.markdown("## 📊 Visão Geral do Sistema")
		stats = DatabaseManager.get_statistics()
		col1, col2, col3, col4 = st.columns(4)
		st.metric("👥 Atendimentos", stats.get("total_atendimentos", 0))
		st.metric("🏢 Empresas", stats.get("total_empresas", 0))
		st.metric("📄 Relatórios", stats.get("laudos_enviados", 0))
		st.metric("📝 Avaliações", stats.get("avaliacoes_enviadas", 0))

		# Remover exibição de funções vazias
		if stats.get("modalidades"):
			fig = px.pie(
				values=list(stats["modalidades"].values()),
				names=list(stats["modalidades"].keys()),
				title="Distribuição por Modalidade",
				color_discrete_sequence=px.colors.sequential.Blues_r,
			)
			fig.update_traces(textposition="inside", textinfo="percent+label")
			st.plotly_chart(fig, use_container_width=True)


class AppointmentsPage:
	@staticmethod
	def render(filters: Dict) -> None:
		st.markdown("## 📝 Gerenciamento de Atendimentos")

		# Excluir (com snapshot para desfazer)
		try:
			appts = DatabaseManager.get_all_appointments()
			if appts:
				df_head = pd.DataFrame(
					appts,
					columns=[
						"ID",
						"Empresa",
						"Nome",
						"Modalidade",
						"Data",
						"Hora",
						"Laudo PDF",
						"Avaliação PDF",
						"Status",
						"Observações",
					],
				)
				col_sel, col_del, col_undo = st.columns([3, 1, 1])
				with col_sel:
					labels = [
						f"ID {int(r.ID)} — {r.Nome} • {r.Empresa} • {r.Data} {r.Hora}"
						for _, r in df_head.iterrows()
					]
					opt = dict(zip(labels, df_head.ID.astype(int).tolist()))
					chosen = st.selectbox("Selecione para excluir:", labels) if labels else None
				with col_del:
					if st.button("🗑️ Excluir") and chosen:
						sel_id = opt.get(chosen)
						if sel_id is None:
							st.error("Seleção inválida.")
						else:
							snapshot = df_head[df_head.ID == sel_id].iloc[0].to_dict()
							st.session_state["last_deleted_snapshot"] = snapshot
							if DatabaseManager.delete_appointment(int(sel_id)):
								st.success(f"Excluído ID {sel_id}.")
								st.rerun()
				with col_undo:
					if st.session_state.get("last_deleted_snapshot"):
						if st.button("↩️ Desfazer"):
							s = st.session_state["last_deleted_snapshot"]
							db.inserir_atendimento(
								s.get("Empresa", ""),
								s.get("Nome", ""),
								s.get("Modalidade", ""),
								s.get("Data", ""),
								s.get("Hora", ""),
								s.get("Laudo PDF"),
							 s.get("Avaliação PDF"),
								s.get("Observações"),
							)
							st.session_state.pop("last_deleted_snapshot", None)
							st.success("Registro restaurado.")
							st.rerun()
		except Exception as e:
			st.error(f"Erro ao montar exclusão/desfazer: {e}")

		new_item = UIComponents.render_appointment_form()
		if new_item and DatabaseManager.add_appointment(new_item):
			st.success("✅ Atendimento cadastrado!")
			st.rerun()

		AppointmentsPage._render_table(filters)

	@staticmethod
	def _render_table(filters: Dict) -> None:
		appts = DatabaseManager.get_all_appointments()
		if not appts:
			st.info("Nenhum atendimento encontrado.")
			return

		df = pd.DataFrame(
			appts,
			columns=[
				"ID",
				"Empresa",
				"Nome",
				"Modalidade",
				"Data",
				"Hora",
				"Laudo PDF",
				"Avaliação PDF",
				"Status",
				"Observações",
			],
		)

		if filters.get("modalidade_filter"):
			df = df[df["Modalidade"] == filters["modalidade_filter"]]
		if filters.get("date_filter"):
			try:
				d = filters["date_filter"].strftime("%d/%m/%Y")
				df = df[df["Data"] == d]
			except Exception:
				pass
		emp = (filters.get("empresa_filter") or "").strip()
		if emp:
			df = df[df["Empresa"].str.contains(emp, case=False, na=False)]
		pac = (filters.get("paciente_filter") or "").strip()
		if pac:
			df = df[df["Nome"].str.contains(pac, case=False, na=False)]

		st.markdown("### 📋 Lista de Atendimentos")
		st.dataframe(df[["Empresa", "Nome", "Modalidade", "Data", "Hora"]], use_container_width=True, height=400)

		with st.expander("✏️ Editar Atendimento"):
			ids = df["ID"].astype(int).tolist()
			if not ids:
				st.info("Sem registros para editar.")
				return
			sel = st.selectbox("Selecione (ID):", ids)
			row = df[df["ID"] == sel].iloc[0]
			try:
				cur_date = datetime.strptime(row["Data"], "%d/%m/%Y").date()
			except Exception:
				cur_date = date.today()
			try:
				h, m = (row["Hora"] or "09:00").split(":")
				cur_time = time(int(h), int(m))
			except Exception:
				cur_time = time(9, 0)

			with st.form("edit_form"):
				c1, c2 = st.columns(2)
				with c1:
					empresa_n = st.text_input("🏢 Empresa", value=str(row["Empresa"]))
					modalidade_n = st.selectbox("🏥 Modalidade", [m.value for m in ModalidadeAtendimento], index=max(0, [m.value for m in ModalidadeAtendimento].index(str(row["Modalidade"])) if str(row["Modalidade"]) in [m.value for m in ModalidadeAtendimento] else 0))
					data_n = st.date_input("📅 Data", value=cur_date)
				with c2:
					nome_n = st.text_input("👤 Nome", value=str(row["Nome"]))
					hora_n = st.time_input("🕒 Hora", value=cur_time)
					status_n = st.selectbox("📌 Status", ["Agendado", "Concluído", "Cancelado"], index=["Agendado", "Concluído", "Cancelado"].index(str(row.get("Status", "Agendado")) if row.get("Status") else "Agendado"))
				obs_n = st.text_area("📝 Observações", value=str(row.get("Observações", "")))
				if st.form_submit_button("Salvar alterações", type="primary"):
					ok = DatabaseManager.update_appointment(
						int(sel),
						empresa=(empresa_n or "").strip(),
						nome=(nome_n or "").strip(),
						modalidade=modalidade_n,
						data=data_n.strftime("%d/%m/%Y"),
						hora=hora_n.strftime("%H:%M"),
						status=status_n,
						observacoes=obs_n.strip(),
					)
					if ok:
						st.success("Atualizado!")
						st.rerun()
					else:
						st.error("Falha ao atualizar.")


class ReportsPage:
	@staticmethod
	def render() -> None:
		st.markdown("## 📊 Relatórios")
		c1, c2 = st.columns(2)
		with c1:
			d_ini = st.date_input("Data inicial", date.today() - timedelta(days=30))
		with c2:
			d_fim = st.date_input("Data final", date.today())
		if d_ini > d_fim:
			st.error("Data inicial deve ser anterior à final.")
			return
		stats = DatabaseManager.get_statistics()

		# Limpar chaves vazias e evitar mostrar dicionário cru
		stats_clean = {k: v for k, v in stats.items() if v not in (None, {}, [])}

		# KPI Cards (sem alterar cores)
		kpis = [
			("👥 Atendimentos", stats_clean.get("total_atendimentos", 0)),
			("🏢 Empresas", stats_clean.get("total_empresas", 0)),
			("📄 Relatórios", stats_clean.get("laudos_enviados", 0)),
			("📝 Avaliações", stats_clean.get("avaliacoes_enviadas", 0)),
		]
		cards_html = '<div class="kpi-grid">' + ''.join(
			f'<div class="kpi-card"><div class="kpi-title">{t}</div><div class="kpi-value">{v}</div></div>'
			for t, v in kpis
		) + '</div>'
		st.markdown(cards_html, unsafe_allow_html=True)

		# Gráfico Modalidades se houver dados
		if stats_clean.get("modalidades"):
			fig = px.bar(
				x=list(stats_clean["modalidades"].keys()),
				y=list(stats_clean["modalidades"].values()),
				title="Atendimentos por Modalidade",
			)
			st.plotly_chart(fig, use_container_width=True)


class UploadPage:
	@staticmethod
	def render() -> None:
		st.markdown("## 📄 Upload de PDFs")
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
		up = st.file_uploader("Selecione um PDF", type=["pdf"])
		if up is not None:
			size_mb = len(up.getvalue()) / (1024 * 1024)
			st.info(f"Arquivo: {up.name} — {size_mb:.2f} MB")
			nome_seguro = up.name.replace(" ", "_")
			destino = os.path.join(UploadPage._uploads_dir(), f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{nome_seguro}")
			if st.button("Salvar PDF", type="primary"):
				if size_mb > 10:
					st.error("Arquivo > 10MB")
					return
				with open(destino, "wb") as f:
					f.write(up.getbuffer())
				st.success("PDF salvo.")
				st.download_button("Baixar agora", up.getvalue(), file_name=nome_seguro)

	@staticmethod
	def _render_download_list() -> None:
		pasta = UploadPage._uploads_dir()
		arqs = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
		if not arqs:
			st.info("Nenhum PDF encontrado.")
			return
		for i, nome in enumerate(sorted(arqs, reverse=True)):
			caminho = os.path.join(pasta, nome)
			cols = st.columns([4, 1])
			with cols[0]:
				st.write(f"📄 {nome}")
				st.caption(f"{os.path.getsize(caminho)//1024} KB")
			with cols[1]:
				with open(caminho, "rb") as f:
					st.download_button("Baixar", f.read(), file_name=nome, key=f"dl_{i}")


class SettingsPage:
	@staticmethod
	def render() -> None:
		st.markdown("## ⚙️ Configurações")
		col1, col2, col3 = st.columns(3)
		with col1:
			if st.button("🔄 Limpar cache"):
				st.cache_data.clear(); st.cache_resource.clear(); st.success("Cache limpo.")
		with col2:
			if st.button("🗄️ Verificar Banco"):
				ok = db.verificar_conexao()
				st.success("Conexão OK.") if ok else st.error("Falha na conexão.")
		with col3:
			if st.button("🛠️ Reinicializar"):
				st.cache_resource.clear(); DatabaseManager.initialize_database(); st.success("Reinicializado.")


class ClinicalManagementApp:
	def run(self) -> None:
		configure_page()
		apply_custom_css()
		if not DatabaseManager.initialize_database():
			st.stop()
		filters = UIComponents.render_sidebar()
		page = filters["page"]
		UIComponents.render_header(page)
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


if __name__ == "__main__":
	ClinicalManagementApp().run()
