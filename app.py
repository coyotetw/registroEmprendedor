"""
Registro de Emprendedores - Provincia del Chubut
--------------------------------------------------
Prototipo / demo en Streamlit que replica los campos de "Mi Espacio" del
Sistema de Gestión Raíz Emprendedora (documento provisto por Dani Calvo,
Raíz Emprendedora), pensado como punto de partida para el Registro Único
Provincial de Emprendedores.

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

# ---------------------------------------------------------------------------
# Paleta de colores (gobierno de Chubut / estilo Raíz Emprendedora)
# Ajustar estos hex a la guía de marca oficial si difieren.
# ---------------------------------------------------------------------------
COLOR_PRIMARIO = "#0B3D91"     # azul institucional
COLOR_SECUNDARIO = "#F2A93B"   # naranja (tono Raíz Emprendedora)
COLOR_FONDO_CLARO = "#F4F7FC"
COLOR_TEXTO = "#1A1A2E"

st.set_page_config(
    page_title="Registro de Emprendedores | Chubut",
    page_icon="🦖",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {COLOR_FONDO_CLARO};
        }}
        .header-bar {{
            background-color: {COLOR_PRIMARIO};
            padding: 18px 24px;
            border-radius: 10px;
            margin-bottom: 18px;
        }}
        .header-bar h1 {{
            color: white;
            font-size: 1.4rem;
            margin: 0;
        }}
        .header-bar p {{
            color: #D9E4F5;
            margin: 4px 0 0 0;
            font-size: 0.85rem;
        }}
        .badge-demo {{
            display: inline-block;
            background-color: {COLOR_SECUNDARIO};
            color: #3A2400;
            font-weight: 600;
            font-size: 0.7rem;
            padding: 2px 10px;
            border-radius: 999px;
            margin-left: 8px;
            vertical-align: middle;
        }}
        div[data-testid="stForm"] {{
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #E1E6EF;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: white;
            border-radius: 8px 8px 0 0;
        }}
        .stButton>button {{
            background-color: {COLOR_PRIMARIO};
            color: white;
            border-radius: 8px;
            border: none;
            font-weight: 600;
        }}
        .stButton>button:hover {{
            background-color: #082C6B;
            color: white;
        }}
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
# Encabezado
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="header-bar">
        <h1>🦖 Registro de Emprendedores &nbsp;<span class="badge-demo">PROTOTIPO / DEMO</span></h1>
        <p>Provincia del Chubut · Dirección de Promoción de Inversiones · basado en los campos de
        "Mi Espacio" (Raíz Emprendedora)</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "⚠️ Este es un simulacro de sistema de registro: lo que se carga acá vive solo en esta "
    "sesión y se borra automáticamente al reiniciar la app. No es la base real."
)

tab_datos, tab_trayectoria, tab_emprendimiento, tab_registros = st.tabs(
    ["1️⃣ Datos personales", "2️⃣ Trayectoria emprendedora", "3️⃣ Emprendimiento", "📋 Registros (demo)"]
)

# ---------------------------------------------------------------------------
# Formulario único (los tabs son visuales; el submit junta todo)
# ---------------------------------------------------------------------------
with st.form("form_registro", clear_on_submit=False):

    with tab_datos:
        st.subheader("1. Datos personales")
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

    with tab_trayectoria:
        st.subheader("2. Trayectoria emprendedora")
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

    with tab_emprendimiento:
        st.subheader("3. Emprendimiento")
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
    enviado = st.form_submit_button("✅ Registrarme", use_container_width=True)

# ---------------------------------------------------------------------------
# Procesamiento del envío
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Tab de registros (vista admin del demo)
# ---------------------------------------------------------------------------
with tab_registros:
    st.subheader("Registros cargados en esta sesión")
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
        st.download_button(
            "⬇️ Descargar registros cargados (Excel)",
            data=buffer.getvalue(),
            file_name="registros_emprendedores_demo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        if st.button("🗑️ Vaciar base ahora (simular borrado automático)"):
            st.session_state.registros = []
            st.rerun()
    else:
        st.info("Todavía no hay registros cargados en esta sesión.")
