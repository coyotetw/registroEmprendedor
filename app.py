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

        /* ---------- Tabs como navegación por pasos (con scroll horizontal en celular) ---------- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            border-bottom: 1px solid var(--border);
            overflow-x: auto !important;
            overflow-y: hidden;
            flex-wrap: nowrap !important;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: thin;
        }
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { height: 5px; }
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {
            background-color: var(--accent-soft);
            border-radius: 999px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 0;
            font-family: var(--font-body);
            font-weight: 600;
            font-size: 0.88rem;
            color: var(--text-muted);
            padding: 10px 16px;
            flex-shrink: 0;
            white-space: nowrap;
        }
        .stTabs [aria-selected="true"] {
            background-color: transparent !important;
            color: var(--text) !important;
            box-shadow: inset 0 -3px 0 var(--accent);
        }
        .stTabs [aria-selected="true"] p { color: var(--text) !important; font-weight: 700; }
        .stTabs [data-baseweb="tab-highlight"] { background-color: var(--accent); }
        .stTabs [data-baseweb="tab-border"] { display: none; }

        .scroll-hint {
            display: none;
            color: var(--teal);
            font-size: 0.76rem;
            font-weight: 600;
            margin: 0 0 4px 0;
        }

        /* ---------- Ajustes para pantallas de celular ---------- */
        @media (max-width: 640px) {
            .topbar h1 { font-size: 1.25rem; }
            .stTabs [data-baseweb="tab"] { font-size: 0.8rem; padding: 9px 12px; }
            div[data-testid="stForm"] { padding: 16px 14px; }
            .kv-grid { grid-template-columns: 1fr; }
            .program-row { flex-direction: column; gap: 4px; }
            .program-title { min-width: 0; }
            .scroll-hint { display: block; }
        }

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
FIGURAS_YA_FORMALIZADO = ["Monotributo", "Monotributo Social", "Responsable Inscripto"]
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
ETAPA_DESARROLLO = [
    "Idea o proyecto (aún sin actividad)",
    "Puesta en marcha (despegue)",
    "Consolidación (crecimiento y expansión)",
]

# ---------------------------------------------------------------------------
# Estado de sesión ("base" que se borra sola al reiniciar la app)
# Se guarda como diccionario {DNI: registro} para poder completar la ficha
# en un segundo paso sin duplicar a la persona.
# ---------------------------------------------------------------------------
if "registros" not in st.session_state:
    st.session_state.registros = {}


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


def dnis_registrados():
    return sorted(st.session_state.registros.keys())


# ---------------------------------------------------------------------------
# Barra superior
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="topbar">
        <div class="topbar-id">
            <h1>Registro de Emprendedores</h1>
        </div>
        <span class="status-pill">Prototipo</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="scroll-hint">← Deslizá para ver las 6 secciones: Inscripción, Base de datos, '
    'Ejemplo, Otras provincias, Programas, Metodología →</p>',
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
        "02 · Base",
        "03 · Ejemplo",
        "04 · Provincias",
        "05 · Programas",
        "06 · Metodología",
    ]
)

# ===========================================================================
# SEGMENTO 1 — INSCRIPCIÓN (todo en una pantalla: obligatorios + opcionales)
# ===========================================================================
with tab_inscripcion:
    st.markdown('<p class="section-eyebrow">Alta de emprendedores</p>', unsafe_allow_html=True)
    st.subheader("Formulario de inscripción")
    st.caption(
        "Los campos marcados con * son obligatorios para quedar inscripto/a. El resto es "
        "opcional y se puede completar ahora o corregir más adelante volviendo a cargar el "
        "mismo DNI (no duplica a la persona, actualiza su ficha)."
    )

    sub_datos, sub_trayectoria, sub_emprendimiento = st.tabs(
        ["Datos personales", "Trayectoria emprendedora", "Emprendimiento"]
    )

    # Figura impositiva se pregunta fuera del formulario para poder reaccionar en el momento:
    # si ya está formalizado/a, no le volvemos a preguntar por situación fiscal, estado de
    # formalización ni barreras de formalización (pedido de Maca: sacar preguntas redundantes).
    with sub_emprendimiento:
        st.markdown("**3. Emprendimiento**")
        st.caption("Objetivo: actualizar rubro, alcance, canales y datos principales del emprendimiento.")
        st.markdown("**Antes de empezar**")
        st.selectbox("Figura impositiva", ["Seleccionar..."] + FIGURA_IMPOSITIVA, key="figura_impositiva")
        st.caption(
            "Con esto ya sabemos si estás formalizado/a: si elegís Monotributo, Monotributo "
            "Social o Responsable Inscripto, más abajo no te preguntamos de nuevo por tu "
            "situación fiscal, tu estado de formalización ni por barreras de formalización."
        )

    ya_formalizado = val("figura_impositiva") in FIGURAS_YA_FORMALIZADO

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
                cuil = st.text_input("CUIL/CUIT", key="cuil")
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
                etapa_desarrollo = st.selectbox(
                    "Etapa de desarrollo", ["Seleccionar..."] + ETAPA_DESARROLLO, key="etapa_desarrollo"
                )
            with col2:
                antiguedad = st.selectbox("Antigüedad del emprendimiento", ["Seleccionar..."] + ANTIGUEDAD, key="antiguedad")
                localidades_alcance = st.multiselect("Localidades de alcance", LOCALIDADES_CHUBUT, key="localidades_alcance")

            st.markdown("---")
            st.markdown("**3.2 Formalización y aspectos fiscales**")
            st.caption(f"Figura impositiva: **{val('figura_impositiva') or 'sin definir todavía'}**.")
            col1, col2 = st.columns(2)
            with col1:
                personas_involucradas = st.selectbox(
                    "Personas involucradas en el emprendimiento", ["Seleccionar..."] + PERSONAS_INVOLUCRADAS, key="personas_involucradas"
                )
                emision_facturas = st.selectbox("Emisión de facturas", ["Seleccionar..."] + EMISION_FACTURAS, key="emision_facturas")
            with col2:
                acceso_regimenes = st.text_area("Acceso a regímenes", key="acceso_regimenes")

            if ya_formalizado:
                st.info(
                    f"Ya formalizado/a como **{val('figura_impositiva')}** — no hace falta "
                    "preguntar por situación fiscal, estado de formalización ni barreras de "
                    "formalización."
                )
            else:
                if st.session_state.get("barrera_formalizacion") not in ["Seleccionar..."] + BARRERA_FORMALIZACION:
                    st.session_state.pop("barrera_formalizacion", None)
                col1, col2 = st.columns(2)
                with col1:
                    barrera_formalizacion = st.selectbox(
                        "Barrera de formalización", ["Seleccionar..."] + BARRERA_FORMALIZACION, key="barrera_formalizacion"
                    )
                with col2:
                    barreras_formalizacion_detalle = st.text_area(
                        "Barreras de formalización (detalle)", key="barreras_formalizacion_detalle"
                    )

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
            dni_key = st.session_state.dni.strip()
            registro_previo = st.session_state.registros.get(dni_key, {})
            registro_previo.update({
                "Fecha de registro": registro_previo.get("Fecha de registro") or datetime.now().strftime("%d/%m/%Y %H:%M"),
                # 1. Datos personales
                "DNI": dni_key, "Nombre": val("nombre"), "Apellido": val("apellido"),
                "Fecha de nacimiento": str(val("fecha_nacimiento") or ""), "Email": val("email"),
                "Teléfono": val("telefono"), "Localidad de residencia": val("localidad_residencia"),
                # 2. Trayectoria emprendedora
                "CUIL/CUIT": val("cuil"), "WhatsApp": val("whatsapp_personal"),
                "Hijos/as": val("hijos"), "Personas a cargo": val("personas_a_cargo"),
                "¿Tiene discapacidad?": val("discapacidad"), "Nivel educativo": val("nivel_educativo"),
                "Situación laboral": val("situacion_laboral"),
                "¿Recibe ingresos extra?": val("recibe_ingresos_extra"),
                "Detalle ingresos extra": val("detalle_ingresos_extra"),
                # 3.1 Emprendimiento - datos generales
                "Nombre del emprendimiento": val("nombre_emprendimiento"),
                "Rubros": ", ".join(val("rubros") or []),
                "Descripción": val("descripcion"), "Tipo de actividad": val("tipo_actividad"),
                "Etapa de desarrollo": val("etapa_desarrollo"),
                "Antigüedad": val("antiguedad"), "Alcance territorial": val("alcance_territorial"),
                "Localidades de alcance": ", ".join(val("localidades_alcance") or []),
                # 3.2 Formalización y fiscal — situación fiscal y estado de formalización se
                # derivan de la figura impositiva, no se vuelven a preguntar (redundante).
                "Personas involucradas": val("personas_involucradas"),
                "Figura impositiva": val("figura_impositiva"),
                "Situación fiscal": "No" if val("figura_impositiva") in ("", "No inscripto/a") else "Sí",
                "Estado de formalización": val("figura_impositiva"),
                "Acceso a regímenes": val("acceso_regimenes"),
                "Barrera de formalización": "No aplica (ya formalizado/a)" if ya_formalizado else val("barrera_formalizacion"),
                "Barreras de formalización (detalle)": "" if ya_formalizado else val("barreras_formalizacion_detalle"),
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
                "Ficha completa": "Sí",
            })
            st.session_state.registros[dni_key] = registro_previo
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
        df = pd.DataFrame(list(st.session_state.registros.values()))
        st.caption(f"{len(df)} persona(s) inscripta(s) en esta sesión.")
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
                st.session_state.registros = {}
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
                <div><div class="kv-label">Etapa de desarrollo</div><div class="kv-value">Consolidación (crecimiento y expansión)</div></div>
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
        "Síntesis del relevamiento de registros y leyes de emprendedurismo en Argentina. No se "
        "mira solo la posibilidad de financiar al emprendedor, sino también de capacitarlo y "
        "acompañarlo — insumo para diseñar el marco legal del registro provincial de Chubut."
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
                "Provincia": "San Luis",
                "Norma": "Resoluciones del Ministerio de Desarrollo Productivo (sin ley específica)",
                "Qué crea": "Registro de Emprendedores, Artesanos y Pequeños Productores + paquete de 18 "
                            "instrumentos: \"Mi Próximo Paso\" (crédito hasta $4M), \"Mi Primer Emprendimiento\" "
                            "(jóvenes 18-30), \"Eco-Emprende\" (triple impacto) y la plataforma \"Compre San Luis\".",
                "Por qué es relevante": "El modelo con más peso en capacitación y acompañamiento, no solo "
                                        "crédito: exige un ciclo formativo obligatorio antes de financiar "
                                        "(\"rechazo al financiamiento ciego\"), con más de 15.800 visitas de "
                                        "seguimiento en territorio (>90% de los proyectos financiados en 2025) "
                                        "y la Universidad de La Punta como aceleradora institucional. Creció "
                                        "486,9% en proyectos financiados entre 2024 y 2025.",
            },
            {
                "Provincia": "Chubut",
                "Norma": "Sin ley específica",
                "Qué crea": "Programas administrativos: \"Raíz Emprendedora\" (Secretaría General de Gobierno) "
                            "y \"Chubut Emprende\" (Secretaría de Trabajo)",
                "Por qué es relevante": "Vacío institucional a resolver — este registro es un primer paso "
                                        "hacia un marco formal similar al de Mendoza, sumando la capacitación "
                                        "y el acompañamiento territorial que muestra San Luis.",
            },
        ]
    )
    st.dataframe(df_provincias, use_container_width=True, hide_index=True)

    st.markdown(
        """
        <div class="callout">
            <p class="section-eyebrow">Caso destacado</p>
            <p style="margin:0 0 6px 0;"><b>Erisea (Chubut)</b> ganó la categoría "Crecimiento y Expansión"
            del Concurso Nacional Emprendimiento Argentino 2025, frente a 801 emprendimientos
            presentados de todo el país.</p>
            <p style="margin:0; color:var(--text-muted); font-size:0.9rem;">Chubut ya tiene talento
            emprendedor de nivel nacional — lo que falta es la arquitectura institucional (registro +
            dirección + ley) que provincias como Mendoza ya consolidaron.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Fuente: relevamiento normativo propio sobre Boletines Oficiales y sitios oficiales "
        "provinciales, y relevamiento del ecosistema emprendedor de San Luis (septiembre 2026). "
        "Verificar textos y cifras vigentes antes de citarlos en un documento normativo definitivo."
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
        ("Chubut Potencia", "Capacitaciones gratuitas del Ministerio de Producción y la Secretaría de Ciencia y "
         "Tecnología, en convenio con CAME, con un primer eje específico de emprendedurismo (modelos de negocio, "
         "comercialización, marketing digital, gestión). El registro permite convocar directamente a quienes "
         "ya están inscriptos como emprendedores."),
        ("INNOVA CFI", "Fondo de inversión en innovación del Consejo Federal de Inversiones para startups "
         "tecnológicas en etapa Pre-seed/Seed (deuda condicionada e instrumentos convertibles). El registro "
         "ayuda a identificar a los emprendimientos de base tecnológica de Chubut en condiciones de postularse."),
        ("Kit 4.0", "Programa nacional de transformación digital para PyMEs industriales: el Estado cubre "
         "hasta el 50% del valor de kits de digitalización (ciberseguridad, IoT, impresión 3D). Requiere "
         "personas jurídicas con Certificado MiPyME — el registro ayuda a detectar a quiénes les conviene dar "
         "ese salto de formalización primero."),
        ("Concurso Emprendimiento Argentino", "Ejemplo de cómo el registro sirve de excusa para hacer llegar "
         "este tipo de convocatorias a todo el entramado: concurso nacional anual (categorías Despegue "
         "Emprendedor y Crecimiento y Expansión) del que Erisea, de Chubut, salió ganador en 2025. Con el "
         "registro ya armado, avisar de este y de futuros concursos similares es tan simple como filtrar por "
         "rubro o etapa de desarrollo y escribirles."),
    ]

    rows_html = "".join(
        f'<div class="program-row"><div class="program-title">{titulo}</div>'
        f'<div class="program-desc">{descripcion}</div></div>'
        for titulo, descripcion in programas
    )
    st.markdown(f'<div class="profile-card">{rows_html}</div>', unsafe_allow_html=True)
    st.caption(
        "Lista no exhaustiva: además de estos, hay otras líneas provinciales y nacionales que se "
        "van sumando (nuevos programas del Ministerio de Producción, convocatorias del CFI, etc.) "
        "y que el registro permitiría mapear a medida que aparecen."
    )

# ===========================================================================
# SEGMENTO 6 — METODOLOGÍA CFI Y DIAGNÓSTICO
# ===========================================================================
with tab_metodologia:
    st.markdown('<p class="section-eyebrow">Marco de trabajo</p>', unsafe_allow_html=True)
    st.subheader("Metodología (árbol de problemas/soluciones CFI) y diagnóstico del registro")

    st.markdown(
        """
        Este registro no nace de un capricho de diseño: es uno de los **medios directos** del
        **Árbol de Soluciones** construido con la metodología de planificación del
        **Consejo Federal de Inversiones (CFI)** para justificar la creación de una
        **Dirección de Emprendedurismo** dentro del Ministerio de Producción del Chubut.
        """
    )

    col_prob, col_sol = st.columns(2)
    with col_prob:
        st.markdown(
            """
            <div class="callout">
                <p class="section-eyebrow">Árbol de Problemas</p>
                <p style="margin:0 0 8px 0;"><b>Problema central:</b> ausencia de una Dirección o
                Programa formal de Emprendedurismo en el Ministerio de Producción de Chubut.</p>
                <p style="margin:0 0 4px 0; font-size:0.88rem;"><b>Causas directas:</b></p>
                <ul style="margin:0 0 8px 18px; font-size:0.88rem; color:var(--text-muted);">
                    <li>Sin estructura orgánica ni presupuesto propio</li>
                    <li>Falta de un Registro Único de Emprendedores provincial</li>
                    <li>Sin líneas de financiamiento articuladas con el Banco del Chubut</li>
                    <li>Iniciativas dispersas entre organismos, sin conducción unificada</li>
                </ul>
                <p style="margin:0; font-size:0.88rem; color:var(--text-muted);"><b>Efectos:</b>
                Chubut rezagada frente a otras provincias y a la Secretaría PyME de la Nación en el
                diseño de políticas de emprendedurismo; emprendedores sin financiamiento adaptado a
                su etapa; menor incidencia en políticas nacionales; más informalidad y mortalidad
                temprana de emprendimientos.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_sol:
        st.markdown(
            """
            <div class="callout">
                <p class="section-eyebrow">Árbol de Soluciones</p>
                <p style="margin:0 0 8px 0;"><b>Objetivo central:</b> crear una Dirección o Programa
                de Emprendedurismo en el Ministerio de Producción de Chubut.</p>
                <p style="margin:0 0 4px 0; font-size:0.88rem;"><b>Medios directos:</b></p>
                <ul style="margin:0 0 8px 18px; font-size:0.88rem; color:var(--text-muted);">
                    <li>Estructura orgánica y presupuesto propio</li>
                    <li><b>Implementar un Registro Único de Emprendedores</b> (este prototipo)</li>
                    <li>Líneas de financiamiento articuladas con el Banco del Chubut</li>
                    <li>Unificar bajo una conducción provincial las iniciativas dispersas</li>
                </ul>
                <p style="margin:0; font-size:0.88rem; color:var(--text-muted);"><b>Fines:</b>
                Chubut activa frente a otras provincias y a la Secretaría PyME de la Nación en el
                diseño de políticas de emprendedurismo; financiamiento adaptado a cada etapa; más
                incidencia nacional; menor informalidad y mayor sostenibilidad.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        #### Del árbol al Registro: qué define el Marco Metodológico

        El **Marco Metodológico y Propuesta de Contenidos del Registro Único Provincial de
        Emprendedores** (Dirección de Promoción de Inversiones) traduce ese medio directo en una
        propuesta concreta. Los puntos que ya están reflejados en este prototipo:

        - **2.2 Perfil poblacional** — el universo del Registro es toda persona que emprende o
          quiere emprender en Chubut, segmentada en distintos ejes para poder diseñar política
          diferenciada: género (Raíz Emprendedora ya capacita a más de 2.500 emprendedoras; el
          registro municipal de Puerto Madryn releva mayoritariamente proyectos liderados por
          mujeres), juventud, personas con discapacidad (dato que el Registro ya releva de forma
          obligatoria), localización (rural/urbana, según la localidad de residencia y de alcance
          del emprendimiento) y etapa de desarrollo. La ley puede sumar otros ejes a medida que el
          propio Registro muestre qué segmentos están sub-representados.
        - **2.3 Creación del Registro** — carácter voluntario, gratuito y digital; alta con DNI y
          declaración jurada de actividad (el CUIT/CUIL se suma al completar la ficha, para no
          excluir a quien todavía no formalizó); segmentación por etapa de desarrollo y por
          pertenencia a los grupos prioritarios.
        - **2.4 Vinculación con sellos y registros preexistentes** — reconocimiento simplificado
          para quienes ya tengan el Sello Origen Chubut o estén en Raíz Emprendedora/Chubut
          Emprende, e interoperabilidad con los sellos municipales (Puerto Madryn, "Hecho en
          Esquel", Comodoro Conocimiento) para no pedir dos veces el mismo dato.

        Puntos del Marco que todavía **no** están instrumentados en este prototipo (son de
        política, no de formulario) y que necesitan una norma o un convenio para activarse:

        - **2.5 – 2.8** Beneficios impositivos en Ingresos Brutos, convenio de crédito preferencial
          con el Banco del Chubut, priorización en el Fondo de Garantías (lógica FOGARÍO de Río
          Negro) y una línea de microcréditos para etapa inicial.
        - **2.9 – 2.11** Capacitación canalizada con organismos existentes, mesa de articulación
          interinstitucional voluntaria, y gobernanza del Registro a cargo del Ministerio de
          Producción, reglamentada por decreto.
        """
    )

    st.markdown("#### Diagnóstico automático de esta sesión")
    st.caption(
        "Este panel es la instrumentación concreta del medio directo \"Implementar un Registro "
        "Único de Emprendedores\" del Árbol de Soluciones: mientras se resuelve la ley, ya permite "
        "ver quién se está inscribiendo y con qué características."
    )

    if st.session_state.registros:
        df = pd.DataFrame(list(st.session_state.registros.values()))
        st.caption(f"Calculado sobre los {len(df)} registro(s) cargado(s) en \"01 · Inscripción\".")

        def columna_o_vacia(nombre):
            if nombre in df.columns:
                return df[nombre].fillna("").replace("", "Sin dato")
            return pd.Series(["Sin dato"] * len(df))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Por localidad de residencia**")
            st.bar_chart(columna_o_vacia("Localidad de residencia").value_counts(), color="#D9691D")
        with col2:
            st.markdown("**Por nivel de digitalización**")
            st.bar_chart(columna_o_vacia("Nivel de digitalización").value_counts(), color="#0F7A73")

        st.markdown("**Por figura impositiva**")
        st.bar_chart(columna_o_vacia("Figura impositiva").value_counts(), color="#211C16")
    else:
        st.info(
            "Todavía no hay registros cargados en esta sesión — cargá al menos uno en "
            "\"01 · Inscripción\" para ver el diagnóstico automático (localidad, digitalización, "
            "situación fiscal) generado en vivo a partir de esos datos."
        )

    st.caption(
        "En producción, este mismo diagnóstico se calcularía sobre la base real del Registro "
        "(no la de sesión), lo que permitiría medir en el tiempo el avance de los medios directos "
        "del Árbol de Soluciones — por ejemplo, cuánta gente inscripta pertenece a los grupos "
        "prioritarios del punto 2.2 del Marco Metodológico."
    )
