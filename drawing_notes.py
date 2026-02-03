import streamlit as st
import pandas as pd
import pyperclip

# Configuración de la página
st.set_page_config(page_title="Drawing Notes Generator", page_icon="📐", layout="wide")

# Título
st.title("📐 Generador de Notas de Plano")
st.markdown("---")

# Cargar datos
@st.cache_data
def load_data():
    return pd.read_csv('Drawing-notes-294b36afa8f88077a5afcbf62c6e2997_all.csv', encoding='utf-8-sig')

df = load_data()

# Crear selector por tipo
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Selección de Tipo")

    # Obtener tipos únicos
    tipos = df['Type'].unique().tolist()
    tipos.sort()

    # Selector de tipo
    tipo_seleccionado = st.selectbox(
        "Tipo de pieza/conjunto:",
        options=["Todos"] + tipos,
        index=0
    )

    # Filtrar notas según tipo
    if tipo_seleccionado == "Todos":
        notas_filtradas = df
    else:
        notas_filtradas = df[df['Type'] == tipo_seleccionado]

    st.info(f"**{len(notas_filtradas)}** notas disponibles")

with col2:
    st.subheader("Seleccionar Notas")

    # Mostrar checkboxes para cada nota
    notas_seleccionadas = []

    for idx, row in notas_filtradas.iterrows():
        if st.checkbox(f"**{row['Name']}** ({row['Type']})", key=f"check_{idx}"):
            notas_seleccionadas.append(row['Text'])

st.markdown("---")

# Generar texto final
if notas_seleccionadas:
    st.subheader("📝 Notas Generadas")

    # Combinar todas las notas seleccionadas
    texto_final = "\n\n".join(notas_seleccionadas)

    # Mostrar el texto en un área de texto
    st.text_area(
        "Texto generado:",
        value=texto_final,
        height=300,
        disabled=False
    )

    # Botón para copiar al portapapeles
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

    with col_btn1:
        if st.button("📋 Copiar al Portapapeles", type="primary", use_container_width=True):
            try:
                pyperclip.copy(texto_final)
                st.success("✅ ¡Copiado!")
            except Exception as e:
                st.error(f"Error al copiar: {e}")
                st.info("Copia manual el texto del área de arriba")

    with col_btn2:
        # Botón de descarga
        st.download_button(
            label="💾 Descargar TXT",
            data=texto_final,
            file_name="drawing_notes.txt",
            mime="text/plain",
            use_container_width=True
        )

else:
    st.info("👈 Selecciona al menos una nota de la izquierda para generar el texto")

# Footer
st.markdown("---")
st.caption("🔧 Atlantis Prototyping - Drawing Notes Generator")
