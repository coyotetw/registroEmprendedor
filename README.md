# Registro de Emprendedores | Chubut (prototipo Streamlit)

Prototipo pedido por Dani (Raíz Emprendedora) para simular una plataforma
de registro de emprendedores con los colores del Gobierno del Chubut,
usando exactamente los campos del documento **"Mi espacio. Campos de
Registro de Raíz Emprendedora."**

## Cómo correrlo

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Se abre en `http://localhost:8501`.

## Qué incluye

- Los mismos campos que usa Raíz Emprendedora, organizados en 3 pasos:
  Datos personales, Trayectoria emprendedora, Emprendimiento.
- Paleta de colores institucional de Chubut (azul/naranja) + ícono 🦖
  como referencia al "dino" (reemplazable por el logo oficial si lo
  tienen en PNG/SVG).
- Pestaña "Registros (demo)" para ver lo cargado en la sesión y
  descargarlo como Excel.
- Botón "Vaciar base ahora" para simular el borrado manual, además del
  borrado automático.

## Sobre la "base que se borra automáticamente"

Los registros se guardan únicamente en `st.session_state`, en memoria
del proceso de Streamlit. Apenas se reinicia la app o el servidor
(o pasa el timeout de Streamlit Cloud por inactividad), **todo se
borra solo** — no hay ninguna base persistente detrás. Es la forma más
simple de cumplir literalmente con el pedido de Dani de "una base que
se borra automáticamente" para la demo del evento.

Para producción real (que los registros no se pierdan) habría que
reemplazar `st.session_state.registros` por una base persistente
(Postgres/SQLite en Render, como ya usan en Herramientas Financieras
Chubut), agregando además autenticación y validación de CUIT/DNI
contra AFIP/RENAPER.
