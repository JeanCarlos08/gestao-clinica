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
	import security
except Exception as e:
	st.error(f"Erro ao importar módulos: {e}")
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


# Utilitário para normalizar datas para dd/mm/YYYY
def to_ddmmyyyy(s: str) -> str:
	try:
		# Tenta dd/mm/YYYY (já ok)
		dt = datetime.strptime(str(s), "%d/%m/%Y")
		return dt.strftime("%d/%m/%Y")
	except Exception:
		pass
	for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
		try:
			dt = datetime.strptime(str(s), fmt)
			return dt.strftime("%d/%m/%Y")
		except Exception:
			pass
	return str(s)


def panel_cards_html(cards: List[Dict[str, Any]]) -> str:
	parts = ["""
	<style>
	.panel-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 18px;
		margin: 8px 0 18px;
	}
	.panel-card {
		position: relative;
		background: #ffffff;
		border: 1px solid rgba(0,0,0,0.06);
		border-radius: 16px;
		padding: 18px;
		box-shadow: 0 10px 20px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.6);
		transform: translateZ(0);
		transition: transform .2s ease, box-shadow .2s ease;
	}
	.panel-card:hover {
		transform: translateY(-4px);
		box-shadow: 0 16px 28px rgba(0,0,0,0.16), inset 0 1px 0 rgba(255,255,255,0.6);
	}
	.panel-accent {
		height: 4px;
		border-radius: 6px 6px 0 0;
		margin: -18px -18px 14px;
	}
	.panel-icon {
		width: 44px; 
		height: 44px;
		border-radius: 12px;
		display: flex; 
		align-items: center; 
		justify-content: center;
		font-size: 22px;
		color: #0b2b29;
		box-shadow: 0 6px 14px rgba(0,0,0,0.12);
	}
	.panel-title { 
		font-weight: 700; 
		opacity: .85; 
		margin-top: 8px; 
		font-size: 14px;
		color: #333;
	}
	.panel-value { 
		font-size: 2.0rem; 
		font-weight: 900; 
		line-height: 1; 
		margin-top: 6px; 
		color: #1abc9c;
	}
	.panel-spark { margin-top: 10px; }
	</style>
	"""]
	
	parts.append("<div class='panel-grid'>")
	for c in cards:
		acc = c.get("acc", "#1abc9c")
		icon = c.get("icon", "📦")
		title = c.get("title", "Item")
		value = c.get("value", 0)
		spark = c.get("spark", [])
		
		# Gerar sparkline SVG (opcional)
		svg = ""
		if isinstance(spark, list) and len(spark) >= 2:
			w, h = 140, 36
			mn, mx = min(spark), max(spark)
			rng = (mx - mn) or 1
			pts = []
			for i, v in enumerate(spark):
				x = int(i * (w / max(1, len(spark) - 1)))
				y = int(h - ((v - mn) / rng) * (h - 6) - 3)
				pts.append(f"{x},{y}")
			svg = f"<svg width='{w}' height='{h}' viewBox='0 0 {w} {h}' xmlns='http://www.w3.org/2000/svg'>" \
					f"<polyline fill='none' stroke='{acc}' stroke-width='2' points='{' '.join(pts)}' />" \
					"</svg>"
		
		parts.append(f"""
			<div class='panel-card'>
				<div class='panel-accent' style='background: linear-gradient(90deg, {acc}, rgba(0,0,0,0.05));'></div>
				<div class='panel-icon' style='background: radial-gradient(65% 65% at 30% 30%, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.2) 100%), {acc};'>{icon}</div>
				<div class='panel-title'>{title}</div>
				<div class='panel-value'>{value}</div>
				<div class='panel-spark'>{svg}</div>
			</div>
		""")
	parts.append("</div>")
	return "\n".join(parts)


def panel_cards_native(cards: List[Dict[str, Any]]) -> None:
	"""Versão nativa usando st.metric para melhor compatibilidade"""
	cols = st.columns(len(cards))
	for i, card in enumerate(cards):
		with cols[i]:
			icon = card.get("icon", "📦")
			title = card.get("title", "Item")
			value = card.get("value", 0)
			
			# Criar um container estilizado
			with st.container():
				st.markdown(f"""
				<div style='
					background: white;
					padding: 1rem;
					border-radius: 15px;
					box-shadow: 0 4px 12px rgba(0,0,0,0.1);
					border-left: 4px solid {card.get("acc", "#1abc9c")};
					margin-bottom: 1rem;
				'>
					<div style='text-align: center;'>
						<div style='font-size: 2rem; margin-bottom: 0.5rem;'>{icon}</div>
						<div style='font-size: 0.9rem; color: #666; margin-bottom: 0.3rem;'>{title}</div>
						<div style='font-size: 1.8rem; font-weight: bold; color: {card.get("acc", "#1abc9c")};'>{value}</div>
					</div>
				</div>
				""", unsafe_allow_html=True)


def display_cards(cards: List[Dict[str, Any]]) -> None:
	"""Função que exibe cards modernos usando componentes nativos do Streamlit"""
	if not cards:
		return
		
	# Usar st.columns para layout
	cols = st.columns(len(cards))
	
	for i, card in enumerate(cards):
		with cols[i]:
			icon = card.get("icon", "📦")
			title = card.get("title", "Item")
			value = card.get("value", 0)
			color = card.get("acc", "#4DA768")
			
			# Cards modernos e compactos
			st.markdown(f"""
			<div class='card-modern' style='border-top: 3px solid {color};'>
				<div class='card-icon'>{icon}</div>
				<div class='card-title'>{title}</div>
				<div class='card-value' style='color: {color};'>{value}</div>
			</div>
			""", unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = "", icon: str = "") -> None:
	"""Renderiza um cabeçalho profissional padronizado para todas as páginas"""
	st.markdown(f"""
	<div style='margin-bottom: 2rem;'>
		<h2 style='
			font-size: 1.8rem; 
			font-weight: 700; 
			color: #2d5a3d; 
			margin-bottom: 0.5rem;
			border-bottom: 3px solid #4DA768;
			padding-bottom: 0.5rem;
			text-transform: uppercase;
			letter-spacing: 1px;
		'>{icon} {title}</h2>
		{f'<p style="color: #4DA768; font-size: 1rem; margin: 0; font-style: italic;">{subtitle}</p>' if subtitle else ''}
	</div>
	""", unsafe_allow_html=True)


def configure_page() -> None:
	st.set_page_config(
		page_title="JULIANA | Sistema de Gestão Clínica",
		page_icon="🧠",
		layout="wide",
		initial_sidebar_state="expanded",
	)


def apply_custom_css() -> None:
	st.markdown(
		"""
		<style>
		.stApp { background: linear-gradient(135deg, #99E89D 0%, #99E89D 100%); }
		
		/* Sidebar personalizada - fundo verde escuro #4DA768 com texto branco */
		section[data-testid="stSidebar"] > div { 
			background: #4DA768 !important; 
		}
		
		/* Textos e elementos da sidebar em branco */
		section[data-testid="stSidebar"] * {
			color: #ffff !important;
		}
		
		/* Links e botões da sidebar */
		section[data-testid="stSidebar"] a,
		section[data-testid="stSidebar"] button,
		section[data-testid="stSidebar"] .stSelectbox label,
		section[data-testid="stSidebar"] .stTextInput label,
		section[data-testid="stSidebar"] .stNumberInput label,
		section[data-testid="stSidebar"] .stDateInput label,
		section[data-testid="stSidebar"] .stTimeInput label,
		section[data-testid="stSidebar"] .stTextArea label,
		section[data-testid="stSidebar"] .stCheckbox label,
		section[data-testid="stSidebar"] .stRadio label,
		section[data-testid="stSidebar"] .stSlider label,
		section[data-testid="stSidebar"] h1,
		section[data-testid="stSidebar"] h2,
		section[data-testid="stSidebar"] h3,
		section[data-testid="stSidebar"] h4,
		section[data-testid="stSidebar"] h5,
		section[data-testid="stSidebar"] h6,
		section[data-testid="stSidebar"] p,
		section[data-testid="stSidebar"] span,
		section[data-testid="stSidebar"] div {
			color: #ffffff !important;
		}
		
		/* Ícones da sidebar em branco */
		section[data-testid="stSidebar"] svg {
			fill: #ffffff !important;
			color: #ffffff !important;
		}
		
		/* Menu de navegação da sidebar */
		section[data-testid="stSidebar"] .css-1d391kg,
		section[data-testid="stSidebar"] .css-1d391kg p {
			color: #ffffff !important;
		}
		
		h1, h2, h3, h4, h5, h6 { 
			color: #2d5a3d !important; 
			font-weight: 600; 
			text-shadow: 1px 1px 2px rgba(0,0,0,.08); 
		}
		
		/* Textos principais do conteúdo */
		.main .block-container {
			color: #2d5a3d !important;
		}
		
		/* Labels e textos em geral */
		.stMarkdown, .stText, .stCaption, p, span, div {
			color: #2d5a3d !important;
		}
		
		/* Labels de formulários */
		.stTextInput label, .stSelectbox label, .stNumberInput label, 
		.stDateInput label, .stTimeInput label, .stTextArea label,
		.stCheckbox label, .stRadio label, .stSlider label {
			color: #4DA768 !important;
			font-weight: 600 !important;
		}
		
		/* Métricas e indicadores */
		[data-testid="metric-container"] {
			color: #2d5a3d !important;
		}
		
		/* Captions e textos secundários */
		.stCaption {
			color: #4DA768 !important;
			opacity: 0.8;
		}
		.stButton > button { background: linear-gradient(45deg, #1abc9c, #16a085) !important; color: #fff !important; border: 0; border-radius: 8px; font-weight: 700; }
		.stDataFrame { 
			background: rgba(255,255,255,.98) !important; 
			border-radius: 12px !important; 
			box-shadow: 0 4px 12px rgba(77, 167, 104, 0.15) !important;
			border: 1px solid rgba(77, 167, 104, 0.2) !important;
		}
		
		/* Headers de tabela */
		.stDataFrame th {
			background: linear-gradient(135deg, #4DA768, #2d5a3d) !important;
			color: white !important;
			font-weight: 600 !important;
		}
		
		/* Células de tabela */
		.stDataFrame td {
			color: #2d5a3d !important;
			font-weight: 500 !important;
		}
		
		/* Alertas e mensagens */
		.stSuccess {
			background-color: rgba(77, 167, 104, 0.1) !important;
			border-left: 4px solid #4DA768 !important;
			color: #2d5a3d !important;
		}
		
		.stInfo {
			background-color: rgba(77, 167, 104, 0.05) !important;
			border-left: 4px solid #4DA768 !important;
			color: #2d5a3d !important;
		}
		
		.stWarning {
			color: #2d5a3d !important;
		}
		
		.stError {
			color: #2d5a3d !important;
		}

		/* Métricas gerais (mantidas) */
		.css-1aumxhk { background-color: #f9f9f9; border-radius: 10px; padding: 10px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); transition: transform 0.2s; }
		.css-1aumxhk:hover { transform: scale(1.05); }
		
		/* Botões padronizados */
		.stButton button { 
			background: linear-gradient(45deg, #4DA768, #2d5a3d) !important; 
			color: white !important; 
			border: none; 
			border-radius: 8px; 
			padding: 10px 20px; 
			font-size: 16px; 
			font-weight: 600 !important;
			cursor: pointer; 
			transition: all 0.3s ease !important; 
		}
		.stButton button:hover { 
			background: linear-gradient(45deg, #2d5a3d, #1a3d26) !important; 
			transform: translateY(-2px) !important;
			box-shadow: 0 4px 12px rgba(77, 167, 104, 0.3) !important;
		}
		
		/* Inputs e formulários */
		.stTextInput input, .stSelectbox select, .stNumberInput input,
		.stDateInput input, .stTimeInput input, .stTextArea textarea {
			border: 2px solid #4DA768 !important;
			border-radius: 8px !important;
			color: #2d5a3d !important;
			font-weight: 500 !important;
			background-color: #ffffff !important;
		}
		
		/* Texto digitado nos inputs */
		.stTextInput input::placeholder,
		.stTextArea textarea::placeholder {
			color: #4DA768 !important;
			opacity: 0.7 !important;
		}
		
		/* Selectbox - texto das opções */
		.stSelectbox select option {
			color: #2d5a3d !important;
			background-color: #ffffff !important;
		}
		
		/* Selectbox - valor selecionado */
		.stSelectbox div[data-baseweb="select"] > div {
			color: #2d5a3d !important;
		}
		
		/* Input focus */
		.stTextInput input:focus, .stSelectbox select:focus, .stNumberInput input:focus,
		.stDateInput input:focus, .stTimeInput input:focus, .stTextArea textarea:focus {
			border-color: #2d5a3d !important;
			box-shadow: 0 0 0 2px rgba(77, 167, 104, 0.2) !important;
			color: #2d5a3d !important;
		}
		
		/* Dropdown do selectbox */
		div[data-baseweb="popover"] {
			color: #2d5a3d !important;
		}
		
		div[data-baseweb="popover"] ul li {
			color: #2d5a3d !important;
		}
		
		/* Texto dos valores nos inputs */
		.stSelectbox > div > div > div > div {
			color: #2d5a3d !important;
		}
		
		/* Estilos adicionais para garantir visibilidade do texto */
		[data-baseweb="input"] input {
			color: #2d5a3d !important;
			background-color: #ffffff !important;
		}
		
		[data-baseweb="select"] {
			color: #2d5a3d !important;
		}
		
		[data-baseweb="select"] > div {
			color: #2d5a3d !important;
		}
		
		/* Dropdown options */
		[role="listbox"] [role="option"] {
			color: #2d5a3d !important;
		}
		
		/* Text area específico */
		[data-baseweb="textarea"] textarea {
			color: #2d5a3d !important;
			background-color: #ffffff !important;
		}
		
		/* Number input específico */
		[data-baseweb="input"][data-type="number"] input {
			color: #2d5a3d !important;
		}

		/* Cards de KPI (Relatórios) - sem alterar paleta */
		.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 8px 0 16px; }
		.kpi-card { background: rgba(255,255,255,0.92); border: 1px solid rgba(255,255,255,0.25); border-radius: 14px; padding: 16px 18px; box-shadow: 0 8px 18px rgba(0,0,0,0.12); backdrop-filter: blur(3px); }
		.kpi-title { font-size: 0.9rem; opacity: 0.85; margin-bottom: 6px; }
		.kpi-value { font-size: 1.8rem; font-weight: 800; line-height: 1.1; }

		/* Date input refinado */
		[data-baseweb="input"] input[type="text"] {
			border-radius: 8px !important;
			border: 1px solid rgba(0,0,0,0.1) !important;
			box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
			padding: 10px 12px !important;
		}
		[data-baseweb="datepicker"] {
			border-radius: 12px !important;
			box-shadow: 0 10px 18px rgba(0,0,0,0.12) !important;
		}

		/* Painel 3D moderno (Dashboard) */
		.panel-grid {
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
			gap: 18px;
			margin: 8px 0 18px;
		}
		.panel-card {
			position: relative;
			background: #ffffff;
			border: 1px solid rgba(0,0,0,0.06);
			border-radius: 16px;
			padding: 18px;
			box-shadow:
				0 10px 20px rgba(0,0,0,0.12),
				inset 0 1px 0 rgba(255,255,255,0.6);
			transform: translateZ(0);
			transition: transform .2s ease, box-shadow .2s ease;
		}
		.panel-card:hover {
			transform: translateY(-4px);
			box-shadow:
				0 16px 28px rgba(0,0,0,0.16),
				inset 0 1px 0 rgba(255,255,255,0.6);
		}
		.panel-accent {
			height: 4px;
			border-radius: 6px 6px 0 0;
			margin: -18px -18px 14px;
			background: linear-gradient(90deg, var(--acc, #1abc9c), rgba(0,0,0,0.05));
		}
		.panel-icon {
			width: 44px; height: 44px;
			border-radius: 12px;
			display: grid; place-items: center;
			font-size: 22px;
			background: radial-gradient(65% 65% at 30% 30%, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.2) 100%), var(--acc, #1abc9c);
			color: #0b2b29;
			box-shadow: 0 6px 14px rgba(0,0,0,0.12);
		}
		.panel-title { font-weight: 700; opacity: .85; margin-top: 8px; }
		.panel-value { font-size: 2.0rem; font-weight: 900; line-height: 1; margin-top: 6px; }
		.panel-spark { margin-top: 10px; }

		/* Contraste para verde escuro */
		.contrast-green-dark {
			background: #1abc9c !important;
			color: #fff200 !important; /* Amarelo forte para contraste */
			border: 2px solid #145a32 !important;
			font-weight: bold;
		}
		
		/* Cards nativos modernos e compactos */
		.card-modern {
			background: linear-gradient(135deg, rgba(0,191,165,0.15) 0%, rgba(248,249,250,0.8) 100%) !important;
			border: 1px solid rgba(76, 167, 104, 0.2) !important;
			border-radius: 16px !important;
			padding: 1rem !important;
			margin: 0.3rem 0 !important;
			box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
			text-align: center !important;
			transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
			backdrop-filter: blur(10px) !important;
			position: relative !important;
			overflow: hidden !important;
		}
		
		/* Estilos específicos para a página de Configurações - texto branco */
		.main .block-container p,
		.main .block-container div,
		.main .block-container span {
			color: white !important;
			text-shadow: 1px 1px 2px rgba(0,0,0,0.5) !important;
			font-weight: 500 !important;
		}
		
		/* Textos específicos de configurações */
		.stExpander p,
		.stExpander div,
		.stExpander span {
			color: white !important;
			text-shadow: 1px 1px 2px rgba(0,0,0,0.5) !important;
		}
		
		/* Labels e informações da página de configurações */
		.stWrite p,
		.stWrite div {
			color: white !important;
			text-shadow: 1px 1px 2px rgba(0,0,0,0.5) !important;
			font-weight: 500 !important;
		}
		
		/* Text areas na página de configurações */
		.stTextArea div[data-baseweb="textarea"] {
			background-color: rgba(255,255,255,0.9) !important;
		}
		
		.stTextArea textarea {
			color: #2d5a3d !important;
			background-color: rgba(255,255,255,0.9) !important;
		}
		
		.card-modern::before {
			content: '' !important;
			position: absolute !important;
			top: 0 !important;
			left: 0 !important;
			right: 0 !important;
			height: 3px !important;
			border-radius: 16px 16px 0 0 !important;
		}
		
		.card-modern:hover {
			transform: translateY(-4px) scale(1.02) !important;
			box-shadow: 0 12px 24px rgba(0,0,0,0.15) !important;
			background: linear-gradient(135deg, rgba(0,191,165,0.15) 0%, rgba(0,191,165,0.05) 100%) !important;
		}
		
		.card-icon {
			font-size: 1.8rem !important;
			margin-bottom: 0.4rem !important;
			filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1)) !important;
			display: block !important;
			opacity: 0.9 !important;
			transition: all 0.3s ease !important;
		}
		
		.card-modern:hover .card-icon {
			transform: scale(1.1) !important;
			opacity: 1 !important;
		}
		
		.card-title {
			font-size: 0.75rem !important;
			color: #2d5a3d !important;
			font-weight: 700 !important;
			text-transform: uppercase !important;
			letter-spacing: 0.8px !important;
			margin-bottom: 0.4rem !important;
			opacity: 0.9 !important;
		}
		
		.card-value {
			font-size: 1.8rem !important;
			font-weight: 900 !important;
			line-height: 1 !important;
			text-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
			margin: 0 !important;
		}
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
			rows = db.listar_atendimentos()
			# Normalizar a coluna Data (índice 4) para dd/mm/YYYY
			fixed: List[Tuple] = []
			for r in rows:
				lst = list(r)
				if len(lst) > 4:
					lst[4] = to_ddmmyyyy(lst[4])
				fixed.append(tuple(lst))
			return fixed
		except Exception as e:
			st.error(f"Erro ao listar atendimentos: {e}")
			return []

	@staticmethod
	def add_appointment(a: AtendimentoData) -> bool:
		# Sanitizar dados de entrada
		empresa_clean = security.sanitize_input(a.empresa)
		nome_clean = security.sanitize_input(a.nome)
		
		# Validar formatos
		if not security.validate_date_input(a.data):
			st.error("Formato de data inválido.")
			return False
		if not security.validate_time_input(a.hora):
			st.error("Formato de hora inválido.")
			return False
		
		# Registrar ação
		security.log_access("ADD_APPOINTMENT", f"Empresa: {empresa_clean}, Paciente: {nome_clean}")
		
		ok = db.inserir_atendimento(empresa_clean, nome_clean, a.modalidade, a.data, a.hora)
		if ok:
			st.cache_data.clear()
		return bool(ok)

	@staticmethod
	def update_appointment(id_atendimento: int, **campos) -> bool:
		# Sanitizar campos de entrada
		if 'empresa' in campos:
			campos['empresa'] = security.sanitize_input(campos['empresa'])
		if 'nome' in campos:
			campos['nome'] = security.sanitize_input(campos['nome'])
		if 'observacoes' in campos:
			campos['observacoes'] = security.sanitize_input(campos['observacoes'], max_length=500)
		
		# Registrar ação
		security.log_access("UPDATE_APPOINTMENT", f"ID: {id_atendimento}")
		
		ok = db.atualizar_atendimento(id_atendimento, **campos)
		if ok:
			st.cache_data.clear()
		return bool(ok)

	@staticmethod
	def delete_appointment(id_atendimento: int) -> bool:
		# Registrar ação crítica
		security.log_access("DELETE_APPOINTMENT", f"ID: {id_atendimento}")
		
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
				st.markdown("""
				<div style='text-align: center; padding: 1rem 0;'>
					<h1 style='
						font-size: 2.5rem; 
						font-weight: 800; 
						color: #2d5a3d; 
						margin-bottom: 0.5rem;
						text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
						letter-spacing: 1px;
					'>JULIANA</h1>
					<p style='
						font-size: 1.2rem; 
						color: #4DA768; 
						font-weight: 600;
						margin: 0;
						text-transform: uppercase;
						letter-spacing: 2px;
					'>Sistema de Gestão Clínica</p>
				</div>
				""", unsafe_allow_html=True)
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
					data_sel = st.date_input("📅 Data", min_value=date(2022, 1, 1), value=date.today())
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
		st.markdown("""
		<div style='margin-bottom: 2rem;'>
			<h2 style='
				font-size: 1.8rem; 
				font-weight: 700; 
				color: #2d5a3d; 
				margin-bottom: 0.5rem;
				border-bottom: 3px solid #4DA768;
				padding-bottom: 0.5rem;
				text-transform: uppercase;
				letter-spacing: 1px;
			'>Dashboard Executivo</h2>
			<p style='
				color: #4DA768; 
				font-size: 1rem;
				margin: 0;
				font-style: italic;
			'>Indicadores e métricas principais do sistema</p>
		</div>
		""", unsafe_allow_html=True)
		# Status de conexão
		conn_ok = False
		try:
			conn_ok = db.verificar_conexao()
		except Exception:
			conn_ok = False
		st.caption(f"🔌 Banco de Dados: {'Conectado' if conn_ok else 'Desconectado'}")

		# Estatísticas + fallback direto dos registros para evitar zeros indevidos
		try:
			stats = DatabaseManager.get_statistics() or {}
			appts = DatabaseManager.get_all_appointments() or []
			total_at = len(appts)
			empresas_unicas = set()
			laudos_env = 0
			avals_env = 0
			
			for a in appts:
				if len(a) > 1:
					empresas_unicas.add(str(a[1]))  # coluna empresa
				if len(a) > 6 and a[6]:  # laudo_pdf
					laudos_env += 1
				if len(a) > 7 and a[7]:  # avaliacao_pdf
					avals_env += 1
			
			total_emp = len(empresas_unicas)
		except Exception as e:
			st.error(f"Erro ao carregar estatísticas: {e}")
			total_at = total_emp = laudos_env = avals_env = 0

		cards = [
			{"icon": "👥", "title": "Atendimentos", "value": total_at, "acc": "#0fb9b1", "spark": [0,2,3,5,4,6,7]},
			{"icon": "🏢", "title": "Empresas", "value": total_emp, "acc": "#10ac84", "spark": [0,1,1,2,2,3,3]},
			{"icon": "📄", "title": "Relatórios", "value": laudos_env, "acc": "#2e86de", "spark": [0,0,1,1,2,2,2]},
			{"icon": "📝", "title": "Avaliações", "value": avals_env, "acc": "#ee5253", "spark": [0,1,0,1,1,1,2]},
		]
		display_cards(cards)

		# Dica se não houver dados
		if not total_at:
			st.info("Sem dados ainda. Vá em ⚙️ Configurações > 'Popular dados de exemplo (demo)' para visualizar o painel.")

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
		render_page_header("Gestão de Atendimentos", "Cadastro e controle de consultas médicas", "📝")
		# Painel rápido com métricas da sessão
		try:
			appts = DatabaseManager.get_all_appointments()
			cards = [
				{"icon": "🗓️", "title": "Total", "value": len(appts), "acc": "#0fb9b1"},
				{"icon": "📅", "title": "Hoje", "value": sum(1 for a in appts if to_ddmmyyyy(a[4]) == date.today().strftime('%d/%m/%Y')), "acc": "#2e86de"},
				{"icon": "✅", "title": "Concluídos", "value": sum(1 for a in appts if (a[8] or '').lower().startswith('concl')), "acc": "#10ac84"},
			]
			display_cards(cards)
		except Exception:
			pass

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
				# Normalizar datas nas labels de exclusão
				df_head["Data"] = df_head["Data"].apply(to_ddmmyyyy)
				col_sel, col_del, col_undo = st.columns([3, 1, 1])
				with col_sel:
					labels = [
						f"ID {int(r.ID)} — {r.Nome} • {r.Empresa} • {to_ddmmyyyy(r.Data)} {r.Hora}"
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

		# Normalizar datas recebidas do banco
		df["Data"] = df["Data"].apply(to_ddmmyyyy)

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

		st.markdown("""
		<h3 style='
			font-size: 1.4rem; 
			font-weight: 600; 
			color: #2d5a3d; 
			margin: 2rem 0 1rem 0;
			padding-left: 1rem;
			border-left: 4px solid #4DA768;
		'>📋 Lista de Atendimentos</h3>
		""", unsafe_allow_html=True)
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
					data_n = st.date_input("📅 Data", value=cur_date, min_value=date(2022, 1, 1))
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
		render_page_header("Relatórios e Analytics", "Análise de dados e indicadores de performance", "📊")
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
		
		# Converter para formato compatível com display_cards
		cards_reports = []
		colors = ["#0fb9b1", "#10ac84", "#2e86de", "#ee5253"]
		for i, (title, value) in enumerate(kpis):
			icon = title.split()[0]
			title_clean = title.split()[1]
			cards_reports.append({
				"icon": icon, 
				"title": title_clean, 
				"value": value, 
				"acc": colors[i]
			})
		display_cards(cards_reports)

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
		render_page_header("Gestão de Documentos", "Upload e download de laudos e avaliações", "📄")
		# Painel rápido com métricas de uploads
		try:
			up_dir = UploadPage._uploads_dir()
			pdfs = [f for f in os.listdir(up_dir) if f.lower().endswith('.pdf')]
			total_size_kb = sum(os.path.getsize(os.path.join(up_dir, f)) for f in pdfs)//1024 if pdfs else 0
			cards = [
				{"icon": "📄", "title": "PDFs", "value": len(pdfs), "acc": "#2e86de"},
				{"icon": "💾", "title": "Tamanho (KB)", "value": total_size_kb, "acc": "#ee5253"},
			]
			display_cards(cards)
		except Exception:
			pass
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
			
			# Validação de segurança
			if not security.validate_pdf_content(up.getvalue()):
				st.error("❌ Arquivo PDF inválido ou potencialmente perigoso.")
				security.log_access("UPLOAD_REJECTED", f"Arquivo: {up.name}")
				return
			
			st.info(f"Arquivo: {up.name} — {size_mb:.2f} MB")
			nome_seguro = security.safe_filename(up.name)
			destino = os.path.join(UploadPage._uploads_dir(), nome_seguro)
			
			if st.button("Salvar PDF", type="primary"):
				if size_mb > 10:
					st.error("Arquivo > 10MB")
					return
				
				try:
					with open(destino, "wb") as f:
						f.write(up.getbuffer())
					
					# Registrar upload bem-sucedido
					security.log_access("UPLOAD_SUCCESS", f"Arquivo: {nome_seguro}")
					st.success("PDF salvo com segurança.")
					st.download_button("Baixar agora", up.getvalue(), file_name=nome_seguro)
				except Exception as e:
					st.error("Erro ao salvar arquivo.")
					security.log_access("UPLOAD_ERROR", f"Erro: {str(e)}")

	@staticmethod
	def _render_download_list() -> None:
		pasta = UploadPage._uploads_dir()
		if not os.path.exists(pasta):
			st.info("Nenhum PDF encontrado.")
			return
			
		arqs = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
		if not arqs:
			st.info("Nenhum PDF encontrado.")
			return
			
		for i, nome in enumerate(sorted(arqs, reverse=True)):
			caminho = os.path.join(pasta, nome)
			
			# Verificar se arquivo existe e é seguro
			if not os.path.exists(caminho):
				continue
				
			size_kb = os.path.getsize(caminho)//1024
			
			# Caixinha branca para cada PDF
			st.markdown(
				f"""
				<div class="pdf-item">
					<div class="pdf-name">📄 {nome}</div>
					<div class="pdf-meta">{size_kb} KB</div>
				</div>
				""",
				unsafe_allow_html=True,
			)
			
			# Botão de download
			try:
				with open(caminho, "rb") as f:
					content = f.read()
					if st.download_button("Baixar", content, file_name=nome, key=f"dl_{i}", use_container_width=True):
						# Registrar download
						security.log_access("DOWNLOAD_PDF", f"Arquivo: {nome}")
			except Exception as e:
				st.error(f"Erro ao acessar arquivo: {nome}")
				security.log_access("DOWNLOAD_ERROR", f"Arquivo: {nome}, Erro: {str(e)}")


class SettingsPage:
	@staticmethod
	def render() -> None:
		render_page_header("Configurações do Sistema", "Segurança, manutenção e dados de exemplo", "⚙️")
		
		# Seção de Logs de Segurança
		st.markdown("""
		<h3 style='
			font-size: 1.4rem; 
			font-weight: 600; 
			color: white; 
			margin: 2rem 0 1rem 0;
			padding-left: 1rem;
			border-left: 4px solid #4DA768;
			text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
		'>🔒 Segurança</h3>
		""", unsafe_allow_html=True)
		col_sec1, col_sec2 = st.columns(2)
		with col_sec1:
			if st.button("📊 Ver Logs de Acesso"):
				try:
					log_file = os.path.join(os.path.dirname(__file__), "logs", "security.log")
					if os.path.exists(log_file):
						with open(log_file, "r", encoding="utf-8") as f:
							logs = f.readlines()[-50:]  # Últimas 50 linhas
						# Limpar e sanitizar logs para evitar exibição de código
						clean_logs = []
						for log in logs:
							# Remover caracteres especiais e limitar tamanho
							clean_log = log.strip()[:200]
							if clean_log and not clean_log.startswith('"""'):
								clean_logs.append(clean_log)
						st.text_area("Últimos acessos:", "\n".join(clean_logs), height=200)
					else:
						st.info("Nenhum log encontrado.")
				except Exception as e:
					st.error(f"Erro ao ler logs: {e}")
		
		with col_sec2:
			if st.button("🧹 Limpar Logs"):
				try:
					log_file = os.path.join(os.path.dirname(__file__), "logs", "security.log")
					if os.path.exists(log_file):
						open(log_file, 'w').close()
						st.success("Logs limpos.")
					security.log_access("CLEAR_LOGS", "Logs de segurança limpos")
				except Exception as e:
					st.error(f"Erro ao limpar logs: {e}")
		
		st.markdown("---")
		st.markdown("""
		<h3 style='
			font-size: 1.4rem; 
			font-weight: 600; 
			color: white; 
			margin: 2rem 0 1rem 0;
			padding-left: 1rem;
			border-left: 4px solid #4DA768;
			text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
		'>⚙️ Sistema</h3>
		""", unsafe_allow_html=True)
		col1, col2, col3 = st.columns(3)
		with col1:
			if st.button("🔄 Limpar cache"):
				st.cache_data.clear(); st.cache_resource.clear()
				security.log_access("CLEAR_CACHE", "Cache do sistema limpo")
				st.success("Cache limpo.")
		with col2:
			if st.button("🗄️ Verificar Banco"):
				ok = db.verificar_conexao()
				security.log_access("CHECK_DB", f"Verificação DB: {'OK' if ok else 'FALHA'}")
				st.success("Conexão OK.") if ok else st.error("Falha na conexão.")
		with col3:
			if st.button("🛠️ Reinicializar"):
				st.cache_resource.clear(); DatabaseManager.initialize_database()
				security.log_access("REINIT_SYSTEM", "Sistema reinicializado")
				st.success("Reinicializado.")

		st.markdown("---")
		st.markdown("""
		<h3 style='
			font-size: 1.4rem; 
			font-weight: 600; 
			color: white; 
			margin: 2rem 0 1rem 0;
			padding-left: 1rem;
			border-left: 4px solid #4DA768;
			text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
		'>📥 Dados de Exemplo (Demo)</h3>
		""", unsafe_allow_html=True)
		if st.button("Popular dados de exemplo (demo)"):
			try:
				amostras = [
					("Alpha Ltda", "Maria Silva", ModalidadeAtendimento.ADMISSIONAL.value, "04/09/2025", "09:00"),
					("Beta Corp", "João Souza", ModalidadeAtendimento.PERIODICO.value, "15/08/2024", "10:30"),
					("Alpha Ltda", "Carla Dias", ModalidadeAtendimento.DEMISSIONAL.value, "21/03/2023", "14:00"),
					("Gamma SA", "Pedro Lima", ModalidadeAtendimento.RETORNO.value, "10/12/2022", "11:15"),
				]
				ok_all = True
				for emp, nome, mod, data_s, hora_s in amostras:
					ok = db.inserir_atendimento(emp, nome, mod, data_s, hora_s)
					ok_all = ok_all and bool(ok)
				if ok_all:
					st.cache_data.clear()
					security.log_access("SEED_DEMO_DATA", f"Inseridos {len(amostras)} registros demo")
					st.success("Dados de exemplo inseridos.")
					st.rerun()
				else:
					st.warning("Alguns registros não puderam ser inseridos.")
			except Exception as e:
				st.error(f"Falha ao inserir dados de exemplo: {e}")

		st.markdown("---")
		with st.expander("🧪 Diagnóstico rápido"):
			from pathlib import Path
			import os
			import pandas as pd
			try:
				st.write("Verificando conexão com o banco...")
				st.success("Conectado") if db.verificar_conexao() else st.error("Desconectado")
				db_path = os.path.join(os.path.dirname(__file__), "gestao_clinica.db")
				st.write("Caminho do DB:", Path(db_path))
				st.write("Arquivo existe:", os.path.exists(db_path))
				appts = DatabaseManager.get_all_appointments()
				st.write("Total de atendimentos:", len(appts))
				if appts:
					df_dbg = pd.DataFrame(appts, columns=["ID","Empresa","Nome","Modalidade","Data","Hora","Laudo PDF","Avaliação PDF","Status","Observações"])
					st.dataframe(df_dbg.head(10), use_container_width=True)
				stats = DatabaseManager.get_statistics()
				# Exibir apenas valores numéricos das estatísticas, não o dict completo
				st.write("Total atendimentos:", stats.get("total_atendimentos", 0))
				st.write("Total empresas:", stats.get("total_empresas", 0))
				st.write("Relatórios enviados:", stats.get("laudos_enviados", 0))
			except Exception as e:
				st.error(f"Falha no diagnóstico: {e}")


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
