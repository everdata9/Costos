import streamlit as st
import pymssql



# Función para conectar a SQL Server con pymssql
def conectar_bd():
    try:
        conn = pymssql.connect(server, username, password, database)
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
