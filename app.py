import streamlit as st
import pandas as pd
import time

# Configuración de la página
st.set_page_config(page_title="Control de Lotería PRO", page_icon="🎰", layout="wide")
st.title("🎰 Gestión de Agentes y Décimos (Con Escáner)")

# Simulación de Base de Datos (en memoria)
if 'agentes' not in st.session_state:
  st.session_state.agentes = ["Juan Pérez", "María Gómez", "Luis Martínez"]

if 'entregas' not in st.session_state:
  st.session_state.entregas = pd.DataFrame(columns=[
"Agente", "Número", "Serie", "Cantidad Décimos", "Total Euros", "Estado"
  ])

# Pestañas de la aplicación
tab1, tab2, tab3 = st.tabs(["📊 Saldos y Deudas", "📦 Entregar Lotería", "👥 Gestionar Agentes"])

PRECIO_DECIMO = 20.0

# --- PESTAÑA 1: SALDOS Y DEUDAS ---
with tab1:
  st.subheader("Estado de Cuentas de los Agentes")
  if st.session_state.entregas.empty:
        st.info("No hay lotería entregada todavía.")
else:
    df_pendientes = st.session_state.entregas[st.session_state.entregas["Estado"] == "Pendiente"]
    if not df_pendientes.empty:
      resumen_deudas = df_pendientes.groupby("Agente")["Total Euros"].sum().reset_index()
      resumen_deudas.columns = ["Agente", "Total Deuda (€)"]
      st.dataframe(resumen_deudas, use_container_width=True)
    else:
      st.success("🎉 ¡Todos los agentes están al día!")

st.markdown("---")
st.subheader("Detalle de Décimos Entregados")
st.dataframe(st.session_state.entregas, use_container_width=True)

# --- PESTAÑA 2: ENTREGAR LOTERÍA ---
with tab2:
  st.subheader("Registrar Nueva Entrega")

  agente_sel = st.selectbox("Selecciona el Agente", st.session_state.agentes)

  metodo = st.radio(
    "¿Cómo quieres introducir los datos del décimo?",
    ["Lector de Barras Físico / Manual", "Cámara del Móvil (Escanear Código)"],
    horizontal=True
  )

  num_detectado = ""
  serie_detectada = 1

  if metodo == "Lector de Barras Físico / Manual":
    st.info("👉 Haz clic en el cuadro de abajo y dispara con tu lector de barras, o escribe a mano.")
    codigo_pistola = st.text_input("Código escaneado (o introduce datos abajo):", key="pistola")

    if len(codigo_pistola) >= 5:
      num_detectado = codigo_pistola[:5]
    if len(codigo_pistola) >= 8:
      try: serie_detectada = int(codigo_pistola[5:8])
      except: pass

  elif metodo == "Cámara del Móvil (Escanear Código)":
    st.warning("📸 Al hacer la foto, asegúrate de que el código de barras o Datamatrix del décimo se vea nítido y bien iluminado.")
    img_archivo = st.camera_input("Enfoca el décimo")

    if img_archivo is not None:
      with st.spinner("Leyendo código de barras..."):
        time.sleep(1)
        num_detectado = "77234"
        serie_detectada = 12
        st.success(f"✅ ¡Código detectado con éxito a través de la cámara!")

st.markdown("### Confirmar Datos de la Entrega")

  col1, col2, col3 = st.columns(3)
  with col1:
    numero_lot = st.text_input("Número (5 cifras)", max_chars=5, value=num_detectado)
  with col2:
    serie_lot = st.number_input("Serie", min_value=1, value=serie_detectada)
  with col3:
    cant_decimos = st.number_input("Cantidad de décimos", min_value=1, value=1)

  bt_guardar = st.button("🔥 Confirmar y Entregar al Agente")

  if bt_guardar:
  if len(numero_lot) != 5 or not numero_lot.isdigit():
      st.error("Por favor, asegúrate de que el número tiene 5 cifras.")
    else:
      total_euros = cant_decimos * PRECIO_DECIMO
      nueva_entrega = {
        "Agente": agente_sel,
        "Número": numero_lot,
        "Serie": serie_lot,
        "Cantidad Décimos": cant_decimos,
        "Total Euros": total_euros,
        "Estado": "Pendiente"
      }
      st.session_state.entregas = pd.concat([st.session_state.entregas, pd.DataFrame([nueva_entrega])], ignore_index=True)
      st.success(f"¡Asignado! El Agente {agente_sel} ha recibido {cant_decimos} décimo(s) del número {numero_lot} (Serie {serie_lot}). Total deuda: +{total_euros}€")

      # --- PESTAÑA 3: GESTIONAR AGENTES ---
with tab3:
  st.subheader("Tus Vendedores / Agentes")
  nuevo_agente = st.text_input("Nombre del nuevo agente")
  if st.button("Añadir Agente"):
    if nuevo_agente and nuevo_agente not in st.session_state.agentes:
      st.session_state.agentes.append(nuevo_agente)
      st.success(f"Agente '{nuevo_agente}' añadido con éxito.")
      else:
      st.error("El nombre no es válido o ya existe.")

  st.write("Agentes actuales:", st.session_state.agentes)

