import streamlit as st
import pymssql
import pandas as pd

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

# Estilos personalizados inspirados en Google Material Design
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
        .stCard {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
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

# Menú lateral con diseño moderno
def menu_lateral():
    st.sidebar.markdown("""
        <div class="sidebar-content">
            <h3>📌 Menú</h3>
        </div>
    """, unsafe_allow_html=True)
    return st.sidebar.radio("Seleccionar", ["📂 Categorías", "📑 Tipos de Gastos", "💰 Registro de Gastos"], index=0)

# Sección de contenido
def gestionar_categorias():
    st.markdown("""<div class="stHeader">📂 Gestión de Categorías</div>""", unsafe_allow_html=True)
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Gastos_Categorias")
        categorias = cursor.fetchall()
        df = pd.DataFrame(categorias, columns=["ID", "Nombre"])
        st.dataframe(df, use_container_width=True)
        
        nueva_categoria = st.text_input("Nueva Categoría")
        if st.button("Agregar Categoría"):
            cursor.execute("INSERT INTO Gastos_Categorias (nombre_categoria) VALUES (%s)", (nueva_categoria,))
            conn.commit()
            st.rerun()
        conn.close()

def gestionar_tipos_gastos():
    st.markdown("""<div class="stHeader">📑 Gestión de Tipos de Gastos</div>""", unsafe_allow_html=True)
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Gastos_Tipos")
        tipos = cursor.fetchall()
        df = pd.DataFrame(tipos, columns=["ID", "ID Categoría", "Nombre"])
        st.dataframe(df, use_container_width=True)
        conn.close()

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
        
        cursor.execute("SELECT G.nombre_tipo, FORMAT(R.fecha, 'dd/MM/yyyy') AS fecha, R.monto, R.cantidad, R.costo_por_unidad FROM Gastos_Registro R JOIN Gastos_Tipos G ON R.id_tipo_gasto = G.id_tipo_gasto")
        gastos = cursor.fetchall()
        df = pd.DataFrame(gastos, columns=["Tipo", "Fecha", "Monto", "Cantidad", "Costo Unitario"])
        st.dataframe(df, use_container_width=True)
        conn.close()

# Navegación entre secciones
opcion = menu_lateral()
if opcion == "📂 Categorías":
    gestionar_categorias()
elif opcion == "📑 Tipos de Gastos":
    gestionar_tipos_gastos()
elif opcion == "💰 Registro de Gastos":
    registrar_gastos()
