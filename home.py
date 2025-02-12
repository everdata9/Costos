import streamlit as st
import pyodbc

server = "SQL5054.site4now.net"  # Asegúrate de usar el servidor correcto
database = "DB_A362A0_losCipresesElCedro"  # Base de datos encontrada
username = "DB_A362A0_losCipresesElCedro_admin"  # Usuario asociado
password = "cbd123456"  # Verifica que esta contraseña sea correcta

# Función para conectarse a SQL Server
def conectar_bd():
    try:
        conn = pyodbc.connect(
            f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
        st.success("Conexión exitosa a la base de datos")
        return conn
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# Interfaz en Streamlit
st.title("Conexión a SQL Server desde Streamlit")

if st.button("Conectar a la base de datos"):
    conn = conectar_bd()
    if conn:
        st.write("¡Conectado exitosamente!")