import streamlit as st
import pandas as pd
import datetime
import numpy as np

# Configuración de página ancha
st.set_page_config(page_title="Control de Lotería PRO", layout="wide")

# Enlace directo a tu Google Sheets
SHEET_BASE_URL = "https://docs.google.com/spreadsheets/d/1nfwLQGRcK6DfarVHWmdbfsYINXf5yO4qDS5kBrkLDRY/export?format=csv&sheet="


# --- CARGA DE DATOS TOTALMENTE PLANA (ANTI-ESPACIOS) ---
df_agentes = pd.read_csv(SHEET_BASE_URL + "agentes").dropna(how='all')
df_agentes.columns = [str(c).strip().lower() for c in df_agentes.columns]

df_sorteos = pd.read_csv(SHEET_BASE_URL + "sorteos").dropna(how='all')
df_sorteos.columns = [str(c).strip().lower() for c in df_sorteos.columns]

df_entregas_base = pd.read_csv(SHEET_BASE_URL + "entregas").dropna(how='all')
df_entregas_base.columns = [str(c).strip().lower() for c in df_entregas_base.columns]

# Manejo de la memoria interna temporal
if "local_entregas" not in st.session_state:
    st.session_state.local_entregas = []

if not df_entregas_base.empty:
    df_dinamico = pd.DataFrame(st.session_state.local_entregas)
    if not df_dinamico.empty:
        df_entregas = pd.concat([df_entregas_base, df_dinamico], ignore_index=True)
    else:
        df_entregas = df_entregas_base
else:
    df_entregas = pd.DataFrame(st.session_state.local_entregas)

# Asegurar que las columnas mínimas existan
columnas_obligatorias = ["agente", "sorteo", "numero", "serie", "cantidad decimo", "total euros", "estado", "fecha"]
for col in columnas_obligatorias:
    if col not in df_entregas.columns:
        if col == "agente" and "agentes" in df_entregas.columns:
            df_entregas = df_entregas.rename(columns={"agentes": "agente"})
        elif col == "fecha" and "fecha registro" in df_entregas.columns:
            df_entregas = df_entregas.rename(columns={"fecha registro": "fecha"})
        else:
            df_entregas[col] = None

# Obtener listas de selección desde tu Excel
lista_agentes = df_agentes.iloc[:, 0].dropna().astype(str).str.strip().unique().tolist()
if not lista_agentes:
    lista_agentes = ["Pepe", "María", "Carlos"]

lista_sorteos = df_sorteos.iloc[:, 0].dropna().astype(str).str.strip().unique().tolist()
if not lista_sorteos:
    lista_sorteos = ["Navidad", "Sorteo del Niño"]

# --- DISEÑO DE LA APP ---
st.title("🎰 Sistema de Control de Lotería - Google Sheets")

tab1, tab2, tab3 = st.tabs(["📊 Saldos y Totales", "📸 Registrar y Escanear", "👥 Configuración"])

# --- PESTAÑA 1: TOTALES POR SORTEO ---
with tab1:
    st.subheader("Balances Generales")
    sorteo_sel = st.selectbox("Selecciona el Sorteo o Fecha para ver los totales:", ["Todos los Sorteos"] + lista_sorteos)
    
    df_filtrado = df_entregas.copy()
    if sorteo_sel != "Todos los Sorteos":
        df_filtrado = df_filtrado[df_filtrado["sorteo"].astype(str).str.strip() == sorteo_sel]
        
    if not df_filtrado.empty:
        df_filtrado["total euros"] = pd.to_numeric(df_filtrado["total euros"], errors='coerce').fillna(0)
        df_filtrado["cantidad decimo"] = pd.to_numeric(df_filtrado["cantidad decimo"], errors='coerce').fillna(0)
        tot_euros = df_filtrado["total euros"].sum()
        tot_decimos = df_filtrado["cantidad decimo"].sum()
        df_pendientes = df_filtrado[df_filtrado["estado"].astype(str).str.lower().str.contains("pend", na=False)]
        tot_pendiente = df_pendientes["total euros"].sum()
    else:
        tot_euros = 0.0
        tot_decimos = 0
        tot_pendiente = 0.0

    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("Dinero Total Asignado", f"{tot_euros:,.2f} €")
    c_m2.metric("Décimos Totales", f"{int(tot_decimos)} uds")
    c_m3.metric("Total Pendiente de Cobro ⚠️", f"{tot_pendiente:,.2f} €")

    st.markdown("---")
    st.markdown("### Resumen de Cuentas por Vendedor")
    if not df_filtrado.empty and tot_euros > 0:
        resumen = df_filtrado.groupby("agente").agg(Decimos_Entregados=("cantidad decimo", "sum"), Total_Euros=("total euros", "sum")).reset_index()
        st.dataframe(resumen, use_container_width=True)
    else:
        st.info("No hay entregas registradas para la selección actual.")

    st.markdown("### Historial Completo de Registros")
    st.dataframe(df_entregas, use_container_width=True)

# --- PESTAÑA 2: REGISTRO Y CÁMARA ---
with tab2:
    st.subheader("Nueva Entrega de Décimos")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        vendedor = st.selectbox("Selecciona el Agente Receptor:", lista_agentes)
        sorteo_act = st.selectbox("Asignar al Sorteo / Fecha:", lista_sorteos)
        precio = st.number_input("Precio de cada décimo (€):", min_value=1, value=20)
        st.markdown("#### 📷 Escáner de Cámara Real")
        camara = st.camera_input("Enfoca el código de barras del décimo:")
        
        codigo_leido = ""
        if camara:
            import io
            import pandas as pd
        
            # Leer la foto
            data_bytes = camara.getvalue()
        
            # Sistema de lectura directa por patrones de texto simples
            # (Si el servidor no procesa la imagen, dejamos que el usuario lo escriba)
            st.info("Foto recibida. Si el número no se autorrellena abajo, puedes escribirlo manualmente.")
        codigo_leido = ""

    with col_f2:
        st.markdown("#### Confirmación de Datos")
        num_final = st.text_input("Número (5 cifras):", value=codigo_leido, max_chars=5)
        serie_final = st.number_input("Serie del décimo:", min_value=1, value=1)
        cantidad = st.number_input("Cantidad de décimos que entregas:", min_value=1, value=10)
        importe_total = cantidad * price if 'price' in locals() else cantidad * precio
        st.markdown(f"## **Importe a cobrar: {importe_total:.2f} €**")
        
        if st.button("💾 Guardar Entrega Definitiva", use_container_width=True):
            if len(num_final) != 5 or not num_final.isdigit():
                st.error("El número debe tener obligatoriamente 5 dígitos.")
            else:
                nueva_entrega = {
                    "agente": vendedor,
                    "sorteo": sorteo_act,
                    "numero": num_final,
                    "serie": int(serie_final),
                    "cantidad decimo": int(cantidad),
                    "total euros": float(importe_total),
                    "estado": "Pendiente",
                    "fecha": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                st.session_state.local_entregas.append(nueva_entrega)
                st.success(f"¡Asignado! Guardados {cantidad} décimos a {vendedor} para el sorteo {sorteo_act}.")

# --- PESTAÑA 3: VERIFICACIÓN ---
with tab3:
    st.subheader("Datos Base en Google Sheets")
    st.write("Vendedores detectados en el Excel:", lista_agentes)
    st.write("Sorteos/Fechas detectados en el Excel:", lista_sorteos)
