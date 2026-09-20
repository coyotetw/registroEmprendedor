"""
Registro de Emprendedores - Provincia del Chubut
--------------------------------------------------
Prototipo / demo en Streamlit que replica los campos de "Mi Espacio" del
Sistema de Gestión Raíz Emprendedora (documento provisto por Dani Calvo,
Raíz Emprendedora), pensado como punto de partida para el Registro Único
Provincial de Emprendedores.

La app está organizada en 6 segmentos (tabs), en este orden:
1. Inscripción
2. Base de Datos
3. Ejemplo de Registro
4. Otras Provincias: Leyes y Casos de Éxito
5. Programas y Capacitaciones
6. Metodología CFI y Diagnóstico

Sistema de diseño:
- Tipografía: "Sora" (títulos, geométrica y moderna) + "Public Sans" (texto,
  la misma familia que usan los sistemas de diseño de gobierno como el
  USWDS — coherente con que esto es una herramienta de gestión pública) +
  "JetBrains Mono" para datos tabulares (DNI, CUIT, fechas).
- Color: base neutra cálida (no blanco puro) + un solo acento saturado
  (naranja institucional del Gobierno del Chubut) para acción/foco, y el
  teal del isologo reservado para información secundaria/etiquetas.
- Layout: barra superior angosta (sin hero degradé), navegación por pasos
  numerados, contenido en columna centrada con aire, tablas y listas en
  vez de tarjetas repetidas.

IMPORTANTE - Es un SIMULACRO:
La "base de datos" de este prototipo vive únicamente en la sesión de
Streamlit (st.session_state). Se borra sola cada vez que se reinicia la
app o el servidor (por ejemplo, al redeployar en Streamlit Cloud), tal
como se pidió: "simulando un sistema de registro que va a una base que se
borra automáticamente". No hay persistencia real ni se guarda nada fuera
de la sesión activa. Para producción habría que reemplazar
`st.session_state.registros` por una base real (Postgres/SQLite en
Render, como se usa en Herramientas Financieras Chubut).
"""

import streamlit as st
import pandas as pd
from datetime import date
from datetime import datetime
import io

st.set_page_config(
    page_title="Registro de Emprendedores | Chubut",
    page_icon="🦖",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sistema de diseño — fuentes + tokens de color + estilos globales
# ---------------------------------------------------------------------------
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Public+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
        :root {
            --bg: #FAF8F5;
            --surface: #FFFFFF;
            --surface-tint: #FBF3EA;
            --border: #E7E0D5;
            --text: #211C16;
            --text-muted: #756B5E;
            --accent: #D9691D;
            --accent-dark: #B4530F;
            --accent-soft: #F4DFC8;
            --teal: #0F7A73;
            --teal-soft: #DCEEEC;
            --font-display: "Sora", "Helvetica Neue", Arial, sans-serif;
            --font-body: "Public Sans", "Segoe UI", Arial, sans-serif;
            --font-mono: "JetBrains Mono", "SFMono-Regular", Menlo, monospace;
        }

        html, body, [class*="css"] { font-family: var(--font-body); color: var(--text); }
        .stApp { background-color: var(--bg); }

        h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
            font-family: var(--font-display) !important;
            color: var(--text) !important;
            letter-spacing: -0.01em;
        }

        /* ---------- Barra superior ---------- */
        .topbar {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            padding: 18px 4px 16px 4px;
            border-bottom: 3px solid var(--accent);
            margin-bottom: 6px;
        }
        .topbar-id { display: flex; flex-direction: column; gap: 4px; }
        .eyebrow {
            font-family: var(--font-body);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.11em;
            text-transform: uppercase;
            color: var(--teal);
        }
        .topbar h1 {
            font-size: 1.55rem;
            font-weight: 700;
            margin: 0;
            text-wrap: balance;
        }
        .status-pill {
            align-self: center;
            border: 1.5px solid var(--accent);
            color: var(--accent-dark);
            font-family: var(--font-body);
            font-weight: 700;
            font-size: 0.72rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            padding: 5px 14px;
            border-radius: 999px;
            white-space: nowrap;
        }
        .subcaption {
            color: var(--text-muted);
            font-size: 0.85rem;
            margin: 2px 0 18px 0;
        }

        /* ---------- Tabs como navegación por pasos ---------- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            border-bottom: 1px solid var(--border);
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 0;
            font-family: var(--font-body);
            font-weight: 600;
            font-size: 0.88rem;
            color: var(--text-muted);
            padding: 10px 16px;
        }
        .stTabs [aria-selected="true"] {
            background-color: transparent !important;
            color: var(--text) !important;
            box-shadow: inset 0 -3px 0 var(--accent);
        }
        .stTabs [aria-selected="true"] p { color: var(--text) !important; font-weight: 700; }
        .stTabs [data-baseweb="tab-highlight"] { background-color: var(--accent); }
        .stTabs [data-baseweb="tab-border"] { display: none; }

        /* ---------- Formulario ---------- */
        div[data-testid="stForm"] {
            background-color: var(--surface);
            padding: 22px 24px;
            border-radius: 10px;
            border: 1px solid var(--border);
        }
        label, .stMarkdown p, .stCaption, [data-testid="stCaptionContainer"] {
            font-family: var(--font-body);
        }
        [data-testid="stCaptionContainer"] { color: var(--text-muted); }

        .stTextInput input, .stTextArea textarea, .stNumberInput input,
        .stDateInput input, div[data-baseweb="select"] > div {
            border-radius: 7px !important;
            border-color: var(--border) !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 1px var(--accent) !important;
        }

        /* ---------- Botones ---------- */
        .stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {
            background-color: var(--accent);
            color: white;
            border-radius: 7px;
            border: none;
            font-family: var(--font-body);
            font-weight: 700;
            font-size: 0.9rem;
            padding: 0.55rem 1.1rem;
            transition: background-color 0.15s ease;
        }
        .stButton>button:hover, .stFormSubmitButton>button:hover, .stDownloadButton>button:hover {
            background-color: var(--accent-dark);
            color: white;
        }
        .stButton>button:focus-visible, .stFormSubmitButton>button:focus-visible {
            outline: 2px solid var(--teal);
            outline-offset: 2px;
        }

        /* ---------- Utilidades de contenido ---------- */
        .section-eyebrow {
            font-family: var(--font-body);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--teal);
            margin-bottom: 4px;
        }

        .tag {
            display: inline-block;
            background-color: var(--bg);
            border: 1px solid var(--border);
            color: var(--text-muted);
            border-radius: 999px;
            padding: 2px 11px;
            font-size: 0.76rem;
            font-weight: 600;
            margin: 2px 6px 2px 0;
        }
        .tag-mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }

        .callout {
            background-color: var(--surface-tint);
            border-radius: 10px;
            padding: 18px 20px;
            margin: 6px 0 16px 0;
        }
        .callout .section-eyebrow { color: var(--accent-dark); }

        .profile-card {
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 22px 26px;
        }
        .profile-name { font-family: var(--font-display); font-size: 1.25rem; font-weight: 700; margin: 4px 0 10px 0; }
        .kv-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px 28px;
            margin-top: 10px;
        }
        .kv-grid .kv-label {
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 2px;
        }
        .kv-grid .kv-value { font-size: 0.94rem; color: var(--text); }

        .program-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 18px;
            padding: 14px 2px;
            border-bottom: 1px solid var(--border);
        }
        .program-row:last-child { border-bottom: none; }
        .program-title { font-family: var(--font-display); font-weight: 600; font-size: 0.98rem; min-width: 260px; }
        .program-desc { color: var(--text-muted); font-size: 0.88rem; }

        [data-testid="stDataFrame"] { font-family: var(--font-body); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Opciones de listas desplegables (tomadas del documento de Raíz Emprendedora)
# ---------------------------------------------------------------------------
RUBROS = [
    "Producción agrícola, ganadera, apícola, pesquera y forestal",
    "Alimentos y gastronomía",
    "Textil, indumentaria y accesorios",
    "Artesanías, diseño y productos creativos",
    "Comercio y reventa",
    "Industria, construcción y servicios técnicos",
    "Tecnología y servicios digitales",
    "Educación, cultura y comunicación",
    "Salud, belleza y bienestar",
    "Turismo, hotelería, eventos y recreación",
    "Ambiente y economía circular",
    "Otros",
]

CANALES_VENTA = ["WhatsApp", "Redes sociales", "Ferias", "E-commerce", "Local físico", "Otros"]

LOCALIDADES_CHUBUT = [
    "Rawson", "Trelew", "Puerto Madryn", "Comodoro Rivadavia", "Esquel",
    "Trevelin", "Gaiman", "Dolavon", "Rada Tilly", "Sarmiento", "Río Mayo",
    "Camarones", "Gastre", "Paso de Indios", "El Hoyo", "Epuyén",
    "Lago Puelo", "Cholila", "Corcovado", "Río Pico", "Otra",
]

SI_NO = ["Sí", "No"]
SI_NO_DESC = ["Sí", "No", "Desconocido"]
NIVEL_EDUCATIVO = [
    "Primario incompleto", "Primario completo", "Secundario incompleto",
    "Secundario completo", "Terciario/Universitario incompleto",
    "Terciario/Universitario completo", "Posgrado",
]
SITUACION_LABORAL = [
    "Desocupado/a", "Empleado/a en relación de dependencia",
    "Trabajador/a independiente", "Jubilado/a o pensionado/a", "Otra",
]
ANTIGUEDAD = ["Menos de 1 año", "Entre 1 y 5 años", "Entre 5 y 10 años", "Más de 10 años"]
ALCANCE_TERRITORIAL = ["Local", "Regional", "Provincial", "Nacional", "Internacional"]
PERSONAS_INVOLUCRADAS = ["Solo yo", "2 a 3 personas", "4 a 5 personas", "Más de 5 personas"]
FIGURA_IMPOSITIVA = ["No inscripto/a", "Monotributo", "Monotributo Social", "Responsable Inscripto", "Otra"]
BARRERA_FORMALIZACION = [
    "Costos impositivos", "Falta de información", "Trámites complejos",
    "Falta de tiempo", "No lo considera necesario", "Otra",
]
EMISION_FACTURAS = ["Siempre", "A veces", "Nunca"]
NIVEL_DIGITALIZACION = ["Nulo", "Básico", "Intermedio", "Avanzado"]
NIVEL_CONOCIMIENTO_FINANCIERO = ["Bajo", "Medio", "Alto"]
RANGO_VENTAS = [
    "Sin ventas aún", "Menos de $500.000", "Entre $500.000 y $1.000.000",
    "Entre $1.000.000 y $2.000.000", "Entre $2.000.000 y $5.000.000",
    "Más de $5.000.000",
]
NIVEL_INVERSION = ["Baja", "Media", "Alta"]
NIVEL_ENDEUDAMIENTO = ["Nulo", "Bajo", "Medio", "Alto"]

# ---------------------------------------------------------------------------
# Estado de sesión ("base" que se borra sola al reiniciar la app)
# ---------------------------------------------------------------------------
if "registros" not in st.session_state:
    st.session_state.registros = []


def campo_completo(valor):
    if valor is None:
        return False
    if isinstance(valor, (list, tuple)):
        return len(valor) > 0
    if isinstance(valor, str):
        return valor.strip() != ""
    return True


def val(key):
    v = st.session_state.get(key)
    if v == "Seleccionar...":
        return ""
    return v


# ---------------------------------------------------------------------------
# Barra superior
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="topbar">
        <div class="topbar-id">
            <span class="eyebrow">Gobierno del Chubut · Ministerio de Producción</span>
            <h1>Registro de Emprendedores</h1>
        </div>
        <span class="status-pill">Prototipo</span>
    </div>
    <p class="subcaption">Basado en los campos de "Mi Espacio" (Raíz Emprendedora). Lo cargado acá
    vive solo en esta sesión y se borra automáticamente al reiniciar la app — no es la base real.</p>
    """,
    unsafe_allow_html=True,
)

(
    tab_inscripcion,
    tab_base_datos,
    tab_ejemplo,
    tab_otras_provincias,
    tab_programas,
    tab_metodologia,
) = st.tabs(
    [
        "01 · Inscripción",
        "02 · Base de datos",
        "03 · Ejemplo de registro",
        "04 · Otras provincias",
        "05 · Programas y capacitaciones",
        "06 · Metodología y diagnóstico",
    ]
)

# ===========================================================================
# SEGMENTO 1 — INSCRIPCIÓN
# ===========================================================================
with tab_inscripcion:
    st.markdown('<p class="section-eyebrow">Paso 1 de 2 · Carga</p>', unsafe_allow_html=True)
    st.subheader("Formulario de inscripción")
    st.caption("Los mismos campos que usa el sistema de gestión de Raíz Emprendedora.")

    sub_datos, sub_trayectoria, sub_emprendimiento = st.tabs(
        ["Datos personales", "Trayectoria emprendedora", "Emprendimiento"]
    )

    with st.form("form_registro", clear_on_submit=False):

        with sub_datos:
            st.markdown("**1. Datos personales**")
            st.caption("Objetivo: mantener actualizada la información de contacto y residencia.")
            col1, col2 = st.columns(2)
            with col1:
                dni = st.text_input("DNI *", key="dni")
                apellido = st.text_input("Apellido *", key="apellido")
                email = st.text_input("Email", key="email")
                localidad_residencia = st.selectbox(
                    "Localidad de residencia", ["Seleccionar..."] + LOCALIDADES_CHUBUT, key="localidad_residencia"
                )
            with col2:
                nombre = st.text_input("Nombre *", key="nombre")
                fecha_nacimiento = st.date_input(
                    "Fecha de nacimiento", value=None, min_value=date(1920, 1, 1),
                    max_value=date.today(), key="fecha_nacimiento",
                )
                telefono = st.text_input("Teléfono", key="telefono")

        with sub_trayectoria:
            st.markdown("**2. Trayectoria emprendedora**")
            st.caption("Objetivo: datos que ayudan a acompañar mejor el recorrido de la persona emprendedora.")
            col1, col2 = st.columns(2)
            with col1:
                cuil = st.text_input("CUIL", key="cuil")
                hijos = st.number_input("Hijos/as (cantidad)", min_value=0, step=1, key="hijos")
                discapacidad = st.selectbox("¿Tiene discapacidad? *", ["Seleccionar..."] + SI_NO, key="discapacidad")
                situacion_laboral = st.selectbox(
                    "Situación laboral general", ["Seleccionar..."] + SITUACION_LABORAL, key="situacion_laboral"
                )
            with col2:
                whatsapp_personal = st.text_input("WhatsApp", key="whatsapp_personal")
                personas_a_cargo = st.number_input("Personas a cargo (cantidad)", min_value=0, step=1, key="personas_a_cargo")
                nivel_educativo = st.selectbox("Nivel educativo", ["Seleccionar..."] + NIVEL_EDUCATIVO, key="nivel_educativo")
                recibe_ingresos_extra = st.selectbox(
                    "¿Recibe ingresos extra al emprendimiento?", ["Seleccionar..."] + SI_NO, key="recibe_ingresos_extra"
                )
            detalle_ingresos_extra = st.text_area("Detalle de ingresos extra", key="detalle_ingresos_extra")

        with sub_emprendimiento:
            st.markdown("**3. Emprendimiento**")
            st.caption("Objetivo: actualizar rubro, alcance, canales y datos principales del emprendimiento.")

            st.markdown("**3.1 Datos generales**")
            nombre_emprendimiento = st.text_input("Nombre del emprendimiento *", key="nombre_emprendimiento")
            rubros = st.multiselect("Rubros", RUBROS, key="rubros")
            descripcion = st.text_area("Descripción", key="descripcion")
            col1, col2 = st.columns(2)
            with col1:
                tipo_actividad = st.text_input("Tipo de actividad (ej: Servicios)", key="tipo_actividad")
                alcance_territorial = st.selectbox(
                    "Alcance territorial", ["Seleccionar..."] + ALCANCE_TERRITORIAL, key="alcance_territorial"
                )
            with col2:
                antiguedad = st.selectbox("Antigüedad del emprendimiento", ["Seleccionar..."] + ANTIGUEDAD, key="antiguedad")
                localidades_alcance = st.multiselect("Localidades de alcance", LOCALIDADES_CHUBUT, key="localidades_alcance")

            st.markdown("---")
            st.markdown("**3.2 Formalización y aspectos fiscales**")
            col1, col2 = st.columns(2)
            with col1:
                personas_involucradas = st.selectbox(
                    "Personas involucradas en el emprendimiento", ["Seleccionar..."] + PERSONAS_INVOLUCRADAS, key="personas_involucradas"
                )
                figura_impositiva = st.selectbox("Figura impositiva", ["Seleccionar..."] + FIGURA_IMPOSITIVA, key="figura_impositiva")
                barrera_formalizacion = st.selectbox(
                    "Barrera de formalización", ["Seleccionar..."] + BARRERA_FORMALIZACION, key="barrera_formalizacion"
                )
            with col2:
                situacion_fiscal = st.selectbox("Situación fiscal (¿está inscripto/a?)", ["Seleccionar..."] + SI_NO, key="situacion_fiscal")
                estado_formalizacion = st.text_input("Estado de formalización (ej: Monotributo)", key="estado_formalizacion")
                emision_facturas = st.selectbox("Emisión de facturas", ["Seleccionar..."] + EMISION_FACTURAS, key="emision_facturas")
            acceso_regimenes = st.text_area("Acceso a regímenes", key="acceso_regimenes")
            barreras_formalizacion_detalle = st.text_area("Barreras de formalización (detalle)", key="barreras_formalizacion_detalle")

            st.markdown("---")
            st.markdown("**3.3 Comunicación y digitalización**")
            col1, col2 = st.columns(2)
            with col1:
                usa_redes = st.selectbox("¿Usa redes sociales?", ["Seleccionar..."] + SI_NO, key="usa_redes")
                telefono_negocio = st.text_input("Teléfono del negocio", key="telefono_negocio")
                whatsapp_business = st.selectbox("WhatsApp Business", ["Seleccionar..."] + SI_NO_DESC, key="whatsapp_business")
                marca_activa_redes = st.selectbox(
                    "¿La marca tiene actividad activa en redes?", ["Seleccionar..."] + SI_NO_DESC, key="marca_activa_redes"
                )
                cuentas_comerciales = st.selectbox("¿Cuenta con cuentas comerciales?", ["Seleccionar..."] + SI_NO, key="cuentas_comerciales")
            with col2:
                canales_venta = st.multiselect("Canales de venta utilizados", CANALES_VENTA, key="canales_venta")
                telefono_distinto = st.selectbox(
                    "¿Tiene teléfono de negocio distinto al personal?", ["Seleccionar..."] + SI_NO, key="telefono_distinto"
                )
                usa_ia = st.selectbox("¿Usa inteligencia artificial?", ["Seleccionar..."] + SI_NO_DESC, key="usa_ia")
                nivel_digitalizacion = st.selectbox(
                    "Nivel de digitalización", ["Seleccionar..."] + NIVEL_DIGITALIZACION, key="nivel_digitalizacion"
                )
                alcance_mercado = st.selectbox("Alcance de mercado", ["Seleccionar..."] + ALCANCE_TERRITORIAL, key="alcance_mercado")
            medios_cobro = st.text_area("Medios de cobro", key="medios_cobro")
            col1, col2 = st.columns(2)
            with col1:
                whatsapp_emprendimiento = st.text_input("WhatsApp del emprendimiento", key="whatsapp_emprendimiento")
                instagram = st.text_input("Instagram", key="instagram")
                tiktok = st.text_input("TikTok", key="tiktok")
            with col2:
                facebook = st.text_input("Facebook", key="facebook")
                linkedin = st.text_input("LinkedIn", key="linkedin")
                otra_red = st.text_input("Otra red social", key="otra_red")

            st.markdown("---")
            st.markdown("**3.4 Situación financiera**")
            col1, col2 = st.columns(2)
            with col1:
                credito_previo = st.selectbox("¿Tuvo acceso a crédito previo?", ["Seleccionar..."] + SI_NO, key="credito_previo")
                nivel_conocimiento_financiero = st.selectbox(
                    "Nivel de conocimiento financiero", ["Seleccionar..."] + NIVEL_CONOCIMIENTO_FINANCIERO, key="nivel_conocimiento_financiero"
                )
                nivel_inversion = st.selectbox("Nivel de inversión inicial", ["Seleccionar..."] + NIVEL_INVERSION, key="nivel_inversion")
            with col2:
                financiamiento_estado = st.selectbox(
                    "¿Tuvo acceso a financiamiento del Estado?", ["Seleccionar..."] + SI_NO, key="financiamiento_estado"
                )
                rango_ventas = st.selectbox("Rango de ventas mensuales", ["Seleccionar..."] + RANGO_VENTAS, key="rango_ventas")
                nivel_endeudamiento = st.selectbox("Nivel de endeudamiento", ["Seleccionar..."] + NIVEL_ENDEUDAMIENTO, key="nivel_endeudamiento")
            necesidades_financiamiento = st.text_area("Necesidades de financiamiento", key="necesidades_financiamiento")

        st.markdown("&nbsp;", unsafe_allow_html=True)
        enviado = st.form_submit_button("Registrarme", use_container_width=True)

    # -----------------------------------------------------------------------
    # Procesamiento del envío
    # -----------------------------------------------------------------------
    if enviado:
        obligatorios = {
            "DNI": st.session_state.dni,
            "Nombre": st.session_state.nombre,
            "Apellido": st.session_state.apellido,
            "¿Tiene discapacidad?": None if st.session_state.discapacidad == "Seleccionar..." else st.session_state.discapacidad,
            "Nombre del emprendimiento": st.session_state.nombre_emprendimiento,
        }
        faltantes = [campo for campo, valor in obligatorios.items() if not campo_completo(valor)]

        if faltantes:
            st.error("Faltan completar campos obligatorios: " + ", ".join(faltantes))
        else:
            registro = {
                "Fecha de registro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                # 1. Datos personales
                "DNI": val("dni"), "Nombre": val("nombre"), "Apellido": val("apellido"),
                "Fecha de nacimiento": str(val("fecha_nacimiento") or ""), "Email": val("email"),
                "Teléfono": val("telefono"), "Localidad de residencia": val("localidad_residencia"),
                # 2. Trayectoria emprendedora
                "CUIL": val("cuil"), "WhatsApp": val("whatsapp_personal"),
                "Hijos/as": val("hijos"), "Personas a cargo": val("personas_a_cargo"),
                "¿Tiene discapacidad?": val("discapacidad"), "Nivel educativo": val("nivel_educativo"),
                "Situación laboral": val("situacion_laboral"),
                "¿Recibe ingresos extra?": val("recibe_ingresos_extra"),
                "Detalle ingresos extra": val("detalle_ingresos_extra"),
                # 3.1 Emprendimiento - datos generales
                "Nombre del emprendimiento": val("nombre_emprendimiento"),
                "Rubros": ", ".join(val("rubros") or []),
                "Descripción": val("descripcion"), "Tipo de actividad": val("tipo_actividad"),
                "Antigüedad": val("antiguedad"), "Alcance territorial": val("alcance_territorial"),
                "Localidades de alcance": ", ".join(val("localidades_alcance") or []),
                # 3.2 Formalización y fiscal
                "Personas involucradas": val("personas_involucradas"),
                "Situación fiscal": val("situacion_fiscal"), "Figura impositiva": val("figura_impositiva"),
                "Estado de formalización": val("estado_formalizacion"),
                "Acceso a regímenes": val("acceso_regimenes"),
                "Barrera de formalización": val("barrera_formalizacion"),
                "Barreras de formalización (detalle)": val("barreras_formalizacion_detalle"),
                "Emisión de facturas": val("emision_facturas"),
                # 3.3 Comunicación y digitalización
                "¿Usa redes sociales?": val("usa_redes"),
                "Canales de venta": ", ".join(val("canales_venta") or []),
                "Medios de cobro": val("medios_cobro"), "Teléfono del negocio": val("telefono_negocio"),
                "Tel. negocio distinto": val("telefono_distinto"), "WhatsApp Business": val("whatsapp_business"),
                "¿Usa IA?": val("usa_ia"), "Marca activa en redes": val("marca_activa_redes"),
                "Nivel de digitalización": val("nivel_digitalizacion"),
                "WhatsApp del emprendimiento": val("whatsapp_emprendimiento"),
                "Instagram": val("instagram"), "Facebook": val("facebook"), "TikTok": val("tiktok"),
                "LinkedIn": val("linkedin"), "Otra red social": val("otra_red"),
                "¿Cuentas comerciales?": val("cuentas_comerciales"), "Alcance de mercado": val("alcance_mercado"),
                # 3.4 Situación financiera
                "¿Crédito previo?": val("credito_previo"), "¿Financiamiento del Estado?": val("financiamiento_estado"),
                "Nivel conocimiento financiero": val("nivel_conocimiento_financiero"),
                "Rango de ventas mensuales": val("rango_ventas"),
                "Necesidades de financiamiento": val("necesidades_financiamiento"),
                "Nivel de inversión inicial": val("nivel_inversion"),
                "Nivel de endeudamiento": val("nivel_endeudamiento"),
            }
            st.session_state.registros.append(registro)
            st.success(
                f"¡Listo, {val('nombre')}! Tu emprendimiento **{val('nombre_emprendimiento')}** "
                "quedó cargado en el registro (demo)."
            )
            st.balloons()

# ===========================================================================
# SEGMENTO 2 — BASE DE DATOS
# ===========================================================================
with tab_base_datos:
    st.markdown('<p class="section-eyebrow">Estado de la sesión</p>', unsafe_allow_html=True)
    st.subheader("Base de datos")
    st.caption(
        "Esta tabla vive solo en memoria mientras la app está corriendo. Al reiniciar el "
        "servidor (o redeployar), se borra automáticamente — es el comportamiento pedido "
        "para el simulacro."
    )
    if st.session_state.registros:
        df = pd.DataFrame(st.session_state.registros)
        st.dataframe(df, use_container_width=True)

        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.download_button(
                "Descargar registros (Excel)",
                data=buffer.getvalue(),
                file_name="registros_emprendedores_demo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col_b:
            if st.button("Vaciar base ahora", use_container_width=True):
                st.session_state.registros = []
                st.rerun()
    else:
        st.info("Todavía no hay registros cargados en esta sesión. Cargá uno en \"01 · Inscripción\".")

# ===========================================================================
# SEGMENTO 3 — EJEMPLO DE REGISTRO
# ===========================================================================
with tab_ejemplo:
    st.markdown('<p class="section-eyebrow">Vista previa</p>', unsafe_allow_html=True)
    st.subheader("Así queda un registro completo")
    st.caption("Ejemplo ilustrativo con datos ficticios — no corresponde a una persona real.")

    st.markdown(
        """
        <div class="profile-card">
            <span class="tag">Trelew</span>
            <span class="tag tag-mono">DNI 30.XXX.XXX</span>
            <span class="tag tag-mono">Registrado 14/03/2026</span>
            <p class="profile-name">María Fernanda Gómez</p>
            <div class="kv-grid">
                <div><div class="kv-label">Emprendimiento</div><div class="kv-value">Tejidos del Sur — indumentaria y accesorios en lana patagónica</div></div>
                <div><div class="kv-label">Rubro</div><div class="kv-value">Textil, indumentaria y accesorios</div></div>
                <div><div class="kv-label">Antigüedad</div><div class="kv-value">Entre 1 y 5 años</div></div>
                <div><div class="kv-label">Alcance</div><div class="kv-value">Regional</div></div>
                <div><div class="kv-label">Formalización</div><div class="kv-value">Monotributo (Responsable Inscripto en trámite)</div></div>
                <div><div class="kv-label">Emisión de facturas</div><div class="kv-value">A veces</div></div>
                <div><div class="kv-label">Canales de venta</div><div class="kv-value">WhatsApp, redes sociales, ferias</div></div>
                <div><div class="kv-label">Digitalización</div><div class="kv-value">Intermedio · usa IA para diseño y redes</div></div>
                <div><div class="kv-label">Ventas mensuales</div><div class="kv-value">$500.000 – $1.000.000</div></div>
                <div><div class="kv-label">Necesidad de financiamiento</div><div class="kv-value">Telar industrial, sin crédito previo</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Muestra el nivel de detalle que alcanza cada ficha, cruzando datos personales, "
        "trayectoria y situación del emprendimiento — la misma estructura del formulario de "
        "\"01 · Inscripción\"."
    )

# ===========================================================================
# SEGMENTO 4 — OTRAS PROVINCIAS: LEYES Y CASOS DE ÉXITO
# ===========================================================================
with tab_otras_provincias:
    st.markdown('<p class="section-eyebrow">Relevamiento normativo</p>', unsafe_allow_html=True)
    st.subheader("Cómo lo resuelven otras provincias")
    st.caption(
        "Síntesis del relevamiento de registros y leyes de emprendedurismo en Argentina — "
        "insumo para diseñar el marco legal del registro provincial de Chubut."
    )

    df_provincias = pd.DataFrame(
        [
            {
                "Provincia": "Mendoza",
                "Norma": "Ley 9265 (2020)",
                "Qué crea": "Registro y Mapeo de Emprendedores + Registro de Incubadoras/Aceleradoras + "
                            "Fondo Provincial de Inversión para Capital Emprendedor",
                "Por qué es relevante": "Modelo más completo: registro + dirección + fondo en una sola ley. "
                                        "Sigue vigente (Decreto 3001/2025 amplió aportes al fideicomiso).",
            },
            {
                "Provincia": "Córdoba",
                "Norma": "Ley 11.125 (2026)",
                "Qué crea": "Fondo Provincial de Capital Emprendedor financiado con hasta 0,5% de Ingresos Brutos",
                "Por qué es relevante": "Mecanismo de financiamiento más reciente, con comité de inversión mixto.",
            },
            {
                "Provincia": "Neuquén",
                "Norma": "Ley 3360 (2022)",
                "Qué crea": "Programa de Acompañamiento al Empleo y Emprendedurismo Joven (18-35 años)",
                "Por qué es relevante": "Bono de crédito fiscal (50% de contribuciones) aplicable a Ingresos "
                                        "Brutos, Inmobiliario y/o Sellos por 12 meses prorrogables.",
            },
            {
                "Provincia": "Río Negro",
                "Norma": "Ley 5766 (2024)",
                "Qué crea": "Promoción económica e industrial con aval del Fondo de Garantías (FOGARÍO)",
                "Por qué es relevante": "Resuelve el principal obstáculo del emprendedor: la falta de garantías "
                                        "para acceder al crédito.",
            },
            {
                "Provincia": "Chubut",
                "Norma": "Sin ley específica",
                "Qué crea": "Programas administrativos: \"Raíz Emprendedora\" (Secretaría General de Gobierno) "
                            "y \"Chubut Emprende\" (Secretaría de Trabajo)",
                "Por qué es relevante": "Vacío institucional a resolver — este registro es un primer paso "
                                        "hacia un marco formal similar al de Mendoza.",
            },
        ]
    )
    st.dataframe(df_provincias, use_container_width=True, hide_index=True)

    st.markdown(
        """
        <div class="callout">
            <p class="section-eyebrow">Caso destacado</p>
            <p style="margin:0 0 6px 0;"><b>Erisea (Chubut)</b> ganó la categoría "Crecimiento y Expansión" del
            Concurso Nacional Emprendimiento Argentino 2025, frente a 801 emprendimientos presentados de
            todo el país.</p>
            <p style="margin:0; color:var(--text-muted); font-size:0.9rem;">Chubut ya tiene talento
            emprendedor de nivel nacional — lo que falta es la arquitectura institucional (registro +
            dirección + ley) que provincias como Mendoza ya consolidaron.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Fuente: relevamiento normativo propio sobre Boletines Oficiales provinciales y "
        "argentina.gob.ar (septiembre 2026). Verificar textos consolidados antes de citarlos "
        "en un documento normativo definitivo."
    )

# ===========================================================================
# SEGMENTO 5 — PROGRAMAS Y CAPACITACIONES
# ===========================================================================
with tab_programas:
    st.markdown('<p class="section-eyebrow">Potencial del registro</p>', unsafe_allow_html=True)
    st.subheader("Programas y capacitaciones que se potencian con el registro")
    st.caption(
        "Con masa crítica de emprendedores cargados, estos son los programas a los que se los "
        "puede direccionar o que pueden diseñarse a medida con los datos del registro."
    )

    programas = [
        ("Raíz Emprendedora", "Programa provincial vigente (Secretaría General de Gobierno). El registro "
         "sería su base de datos formal, hoy dispersa en planillas."),
        ("Chubut Emprende", "Aporte reintegrable de la Secretaría de Trabajo (hasta $5.000.000). El registro "
         "permite segmentar a quién ofrecérselo primero."),
        ("Emprendimiento Argentino (línea de crédito nacional)", "Créditos de $10-50M al 25% TNA a 5 años. "
         "Requiere Certificado MiPyME y aval de una incubadora — el registro ayuda a preparar esa documentación."),
        ("Red Nacional de Incubadoras / INCUBAR", "Registro nacional de incubadoras y aceleradoras. Chubut "
         "podría inscribir sus propios espacios de incubación usando el registro como base de postulantes."),
        ("NAVES Argentina (Banco Macro + IAE)", "Formación y mentoría para emprendedores en etapa de "
         "crecimiento — más de 15.900 personas capacitadas en ediciones previas a nivel nacional."),
        ("Emprender con Perspectiva de Género", "ANR con foco en mujeres emprendedoras (vía RUMP/EEAE) — "
         "coincide con el perfil mayoritario de \"Raíz Emprendedora\" (2.500+ emprendedoras capacitadas)."),
        ("Herramientas de IA para el Ámbito Laboral", "Curso dictado dentro del Ministerio de Producción — "
         "el campo \"¿Usa inteligencia artificial?\" del registro permite detectar a quién priorizar."),
    ]

    rows_html = "".join(
        f'<div class="program-row"><div class="program-title">{titulo}</div>'
        f'<div class="program-desc">{descripcion}</div></div>'
        for titulo, descripcion in programas
    )
    st.markdown(f'<div class="profile-card">{rows_html}</div>', unsafe_allow_html=True)

# ===========================================================================
# SEGMENTO 6 — METODOLOGÍA CFI Y DIAGNÓSTICO
# ===========================================================================
with tab_metodologia:
    st.markdown('<p class="section-eyebrow">Marco de trabajo</p>', unsafe_allow_html=True)
    st.subheader("Metodología (marco CFI) y diagnóstico del registro")

    st.markdown(
        """
        El diseño de los campos de este registro sigue el **Marco Metodológico para el Registro
        Único Provincial de Emprendedores del Chubut**, elaborado con apoyo del
        **Consejo Federal de Inversiones (CFI)**. Su lógica es la misma que ya usa el pipeline de
        datos de Raíz Emprendedora: cruzar cada CUIT/CUIL contra fuentes públicas (BCRA, ARCA/AFIP)
        para enriquecer el perfil de cada emprendedor/a con información de formalización, acceso a
        crédito y situación fiscal — sin pedirle al emprendedor datos que el Estado ya tiene.

        El objetivo del marco no es solo juntar datos, sino producir **diagnóstico accionable**:
        identificar quiénes están fuera del sistema financiero formal, qué barreras de
        formalización predominan por rubro o localidad, y dónde conviene priorizar
        capacitaciones o líneas de crédito.
        """
    )

    st.markdown("#### Diagnóstico automático de esta sesión")

    if st.session_state.registros:
        df = pd.DataFrame(st.session_state.registros)
        st.caption(f"Calculado sobre los {len(df)} registro(s) cargado(s) en \"01 · Inscripción\".")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Por localidad de residencia**")
            conteo_localidad = df["Localidad de residencia"].replace("", "Sin dato").value_counts()
            st.bar_chart(conteo_localidad, color="#D9691D")
        with col2:
            st.markdown("**Por nivel de digitalización**")
            conteo_digital = df["Nivel de digitalización"].replace("", "Sin dato").value_counts()
            st.bar_chart(conteo_digital, color="#0F7A73")

        st.markdown("**Por figura impositiva**")
        conteo_fiscal = df["Figura impositiva"].replace("", "Sin dato").value_counts()
        st.bar_chart(conteo_fiscal, color="#211C16")
    else:
        st.info(
            "Todavía no hay registros cargados en esta sesión — cargá al menos uno en "
            "\"01 · Inscripción\" para ver el diagnóstico automático (localidad, digitalización, "
            "situación fiscal) generado en vivo a partir de esos datos."
        )

    st.caption(
        "En producción, este mismo diagnóstico se calcularía sobre la base real (no la de sesión), "
        "incorporando además el cruce con BCRA/ARCA — tal como ya funciona en el pipeline de "
        "~1.700 CUITs de Herramientas Financieras Chubut."
    )
