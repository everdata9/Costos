import streamlit as st
import pymssql
import pandas as pd
import matplotlib.pyplot as plt


def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔑 Iniciar Sesión")
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar"):
            if username == st.secrets["APP_USER"] and password == st.secrets["APP_PASSWORD"]:
                st.session_state["logged_in"] = True
                st.rerun()  # ✅ Esto es la nueva forma de recargar la app en Streamlit
            else:
                st.error("❌ Usuario o contraseña incorrectos")
        st.stop()

# Llamar la función para validar el login
check_login()

# Configuración de conexión a SQL Server
server = st.secrets["DB_SERVER"]
database = st.secrets["DB_NAME"]
username = st.secrets["DB_USER"]
password = st.secrets["DB_PASSWORD"]

def conectar_bd():
    try:
        return pymssql.connect(server, username, password, database)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# Configuración de la interfaz con diseño moderno
st.set_page_config(page_title="Gestión de Gastos", page_icon="💰", layout="wide")

# Estilos personalizados
st.markdown("""
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f4f4f4;
        }
        .sidebar-content {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        }
        .stApp {
            background-color: #f8f9fa;
        }
        .stButton>button {
            background-color: #ff4b4b;
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #d43f3f;
        }
        .stHeader {
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 10px;
            font-size: 22px;
            font-weight: bold;
            color: #2e7d32;
            display: flex;
            align-items: center;
        }
    </style>
""", unsafe_allow_html=True)

# Menú lateral
def menu_lateral():
    st.sidebar.markdown("""
        <div class="sidebar-content">
            <h3>📌 Menú</h3>
        </div>
    """, unsafe_allow_html=True)
    return st.sidebar.radio("Seleccionar", ["💰 Registro de Gastos", "📊 Análisis de Costos"], index=0)

def registrar_gastos():
    st.markdown("""<div class="stHeader">💰 Registro de Gastos</div>""", unsafe_allow_html=True)
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_categoria, nombre_categoria FROM Gastos_Categorias")
        categorias = cursor.fetchall()
        categoria_dict = {categoria[1]: categoria[0] for categoria in categorias}
        
        categoria_seleccionada = st.selectbox("Seleccionar Categoría", list(categoria_dict.keys()))
        cursor.execute("SELECT id_tipo_gasto, nombre_tipo FROM Gastos_Tipos WHERE id_categoria = %s", (categoria_dict[categoria_seleccionada],))
        tipos_gastos = cursor.fetchall()
        tipos_dict = {tipo[1]: tipo[0] for tipo in tipos_gastos}
        
        tipo_seleccionado = st.selectbox("Seleccionar Tipo de Gasto", list(tipos_dict.keys()))
        fecha = st.date_input("Fecha del gasto", key='fecha_gasto').strftime('%Y-%m-%d')
        monto = st.number_input("Monto", min_value=0.0, format="%.2f")
        cantidad = st.number_input("Cantidad", min_value=0.0, format="%.2f")
        
        if st.button("Registrar Gasto"):
            cursor.execute("INSERT INTO Gastos_Registro (id_tipo_gasto, fecha, monto, cantidad) VALUES (%s, %s, %s, %s)",
                           (tipos_dict[tipo_seleccionado], fecha, monto, cantidad))
            conn.commit()
            st.success("✅ Gasto registrado exitosamente")
            st.rerun()
        
        cursor.execute("SELECT id_gasto, G.nombre_tipo, FORMAT(R.fecha, 'yyyy-MM-dd') AS fecha, R.monto, R.cantidad FROM Gastos_Registro R JOIN Gastos_Tipos G ON R.id_tipo_gasto = G.id_tipo_gasto")
        gastos = cursor.fetchall()
        df = pd.DataFrame(gastos, columns=["ID", "Tipo", "Fecha", "Monto", "Cantidad"])
        
        # Permitir edición de los gastos
        st.subheader("Editar Gastos")
        df_editado = st.data_editor(df, num_rows="dynamic")
        
        if st.button("Guardar Cambios"):
            for index, row in df_editado.iterrows():
                cursor.execute("UPDATE Gastos_Registro SET monto=%s, cantidad=%s, fecha=%s WHERE id_gasto=%s",
                               (row["Monto"], row["Cantidad"], row["Fecha"], row["ID"]))
            conn.commit()
            st.success("✅ Cambios guardados exitosamente")
            st.rerun()
        
        conn.close()

def analisis_costos():
    """Módulo de análisis de costos basado en filtros."""
    st.markdown("""<div class="stHeader">📊 Análisis de Costos</div>""", unsafe_allow_html=True)
    
    conn = conectar_bd()
    if not conn:
        return

    cursor = conn.cursor()

    # Selección de tipo de análisis
    tipo_analisis = st.selectbox("Seleccionar tipo de análisis", [
        "Gasto por Categoría",
        "Distribución de Tipos de Gastos",
        "Tendencia de Gastos en el Tiempo",
        "Costo por Unidad de Gasto",
        "Comparación de Gastos en Diferentes Periodos"
    ])
    
    # Obtener categorías y tipos de gasto
    cursor.execute("SELECT DISTINCT nombre_categoria FROM Gastos_Categorias")
    categorias = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT nombre_tipo FROM Gastos_Tipos")
    tipos_gastos = [row[0] for row in cursor.fetchall()]
    
    # Filtros de categoría y fecha
    categoria_seleccionada = st.selectbox("Filtrar por Categoría", categorias)
    tipo_gasto_seleccionado = st.selectbox("Filtrar por Tipo de Gasto", ["Todos"] + tipos_gastos)
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio", key='fecha_inicio')
    with col2:
        fecha_fin = st.date_input("Fecha de fin", key='fecha_fin')
    
    # Consulta base con filtros
    query = """
        SELECT C.nombre_categoria, T.nombre_tipo, R.fecha, R.monto, R.costo_por_unidad
        FROM Gastos_Registro R
        JOIN Gastos_Tipos T ON R.id_tipo_gasto = T.id_tipo_gasto
        JOIN Gastos_Categorias C ON T.id_categoria = C.id_categoria
        WHERE C.nombre_categoria = %s AND R.fecha BETWEEN %s AND %s
    """
    params = [categoria_seleccionada, fecha_inicio, fecha_fin]
    
    if tipo_gasto_seleccionado != "Todos":
        query += " AND T.nombre_tipo = %s"
        params.append(tipo_gasto_seleccionado)
    
    cursor.execute(query, params)
    datos = cursor.fetchall()
    df = pd.DataFrame(datos, columns=["Categoría", "Tipo", "Fecha", "Monto", "Costo por Unidad"])
    df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce")
    df.dropna(subset=["Monto"], inplace=True)
    
    st.write(df)
    
    if not df.empty:
        if tipo_analisis == "Gasto por Categoría":
            st.subheader("Gasto por Categoría")
            fig, ax = plt.subplots()
            df.groupby("Tipo")["Monto"].sum().plot(kind="bar", ax=ax, color="green")
            ax.set_ylabel("Monto en colones")
            ax.set_xlabel("Tipo de Gasto")
            ax.set_title(f"Gastos en {categoria_seleccionada}")
            st.pyplot(fig)

        elif tipo_analisis == "Distribución de Tipos de Gastos":
            st.subheader("Distribución de Tipos de Gastos")
            fig, ax = plt.subplots()
            df.groupby("Tipo")["Monto"].sum().plot(kind="pie", ax=ax, autopct='%1.1f%%', startangle=90, cmap="viridis")
            ax.set_ylabel("")
            st.pyplot(fig)

        elif tipo_analisis == "Tendencia de Gastos en el Tiempo":
            st.subheader("Tendencia de Gastos en el Tiempo")
            df["Fecha"] = pd.to_datetime(df["Fecha"])
            df.set_index("Fecha", inplace=True)
            fig, ax = plt.subplots()
            df.resample('M')["Monto"].sum().plot(ax=ax, marker="o", linestyle="-")
            ax.set_ylabel("Monto en colones")
            ax.set_title("Tendencia de Gastos")
            st.pyplot(fig)

        elif tipo_analisis == "Costo por Unidad de Gasto":
            st.subheader("Costo por Unidad de Gasto")
            fig, ax = plt.subplots()
            df.groupby("Tipo")["Costo por Unidad"].mean().plot(kind="bar", ax=ax, color="blue")
            ax.set_ylabel("Costo Promedio por Unidad")
            ax.set_xlabel("Tipo de Gasto")
            ax.set_title("Costo Promedio por Unidad")
            st.pyplot(fig)

        elif tipo_analisis == "Comparación de Gastos en Diferentes Periodos":
            st.subheader("Comparación de Gastos en Diferentes Periodos")
            df["Mes"] = df["Fecha"].dt.to_period("M")
            fig, ax = plt.subplots()
            df.groupby("Mes")["Monto"].sum().plot(kind="bar", ax=ax, color="purple")
            ax.set_ylabel("Monto en colones")
            ax.set_xlabel("Mes")
            ax.set_title("Comparación de Gastos Mensuales")
            st.pyplot(fig)
    else:
        st.warning("No hay datos disponibles para el rango de fechas seleccionado.")
    
    conn.close()

# Navegación entre secciones
opcion = menu_lateral()
if opcion == "💰 Registro de Gastos":
    registrar_gastos()
elif opcion == "📊 Análisis de Costos":
    analisis_costos()
