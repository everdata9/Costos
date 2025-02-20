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
                st.error("❌ Usuario o cGit status -s Contraseña incorrectos")
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
        /* Contenedor de la tabla */
        [data-testid="stTable"] {
            border-radius: 12px;
            border: 2px solid #4285F4;
            overflow: hidden;
        }

        /* Cabecera con azul Google */
        thead tr {
            background: linear-gradient(90deg, #4285F4, #34A853);
            color: white !important;
            font-weight: bold;
            text-transform: uppercase;
            text-align: center;
            font-size: 14px;
        }

        /* Filas alternadas */
        tbody tr:nth-child(even) {
            background-color: #F1F3F4 !important;
        }

        /* Celdas con espaciado */
        tbody td {
            padding: 12px;
            text-align: center;
            font-size: 15px;
        }

        /* Hover en amarillo Google */
        tbody tr:hover {
            background-color: #FBBC05 !important;
            transition: 0.3s;
        }

        /* Botón moderno en rojo Google */
        .stButton>button {
            background-color: #EA4335 !important;
            color: white !important;
            font-weight: bold;
            border-radius: 8px;
            padding: 10px 20px;
            transition: 0.3s;
            border: none;
        }
        .stButton>button:hover {
            background-color: #C5221F !important;
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
    #return st.sidebar.radio("Seleccionar", ["💰 Registro de Gastos", "📊 Análisis de Costos"], index=0)
    return st.sidebar.radio("Seleccionar", ["💰 Registro de Gastos"], index=0)

def registrar_gastos():
    """Función para registrar y editar gastos con un diseño moderno"""
    st.markdown("<h3 style='color:#4285F4; text-align:center;'> Registro y Edición de Gastos </h3>", unsafe_allow_html=True)

    conn = conectar_bd()
    if conn:
        try:
            cursor = conn.cursor()

            # Obtener categorías de gastos
            cursor.execute("SELECT id_categoria, nombre_categoria FROM Gastos_Categorias WITH (NOLOCK)")
            categorias = cursor.fetchall()
            categoria_dict = {categoria[1]: categoria[0] for categoria in categorias}

            # Selección de categoría
            categoria_seleccionada = st.selectbox("Seleccionar Categoría", list(categoria_dict.keys()))
            id_categoria = categoria_dict[categoria_seleccionada]

            # Obtener tipos de gastos
            cursor.execute("SELECT id_tipo_gasto, nombre_tipo FROM Gastos_Tipos WITH (NOLOCK) WHERE id_categoria = %s", (id_categoria,))
            tipos_gastos = cursor.fetchall()
            tipos_dict = {tipo[1]: tipo[0] for tipo in tipos_gastos}

            # Selección de tipo de gasto
            tipo_seleccionado = st.selectbox("Seleccionar Tipo de Gasto", list(tipos_dict.keys()))
            id_tipo_gasto = tipos_dict[tipo_seleccionado]

            # Entrada de datos
            fecha = st.date_input("Fecha del gasto", key='fecha_gasto').strftime('%Y-%m-%d')
            monto = st.number_input("Monto", min_value=0.0, format="%.2f")
            cantidad = st.number_input("Cantidad", min_value=0.0, format="%.2f")

            if st.button("Registrar Gasto"):
                try:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM Gastos_Registro WITH (NOLOCK)
                        WHERE id_tipo_gasto = %s AND fecha = %s
                    """, (id_tipo_gasto, fecha))

                    existe = cursor.fetchone()[0]
                    if existe > 0:
                        st.error("❌ No puedes registrar el mismo tipo de gasto en la misma fecha.")
                    else:
                        cursor.execute("""
                            INSERT INTO Gastos_Registro (id_tipo_gasto, fecha, monto, cantidad) 
                            VALUES (%s, %s, %s, %s)
                        """, (id_tipo_gasto, fecha, monto, cantidad))
                        conn.commit()
                        st.success("✅ Gasto registrado exitosamente")
                        st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Error al registrar gasto: {e}")

            # Obtener registros actuales
            cursor.execute("""
                SELECT R.id_gasto, G.nombre_tipo, CONVERT(VARCHAR, R.fecha, 23) AS fecha, R.monto, R.cantidad 
                FROM Gastos_Registro R WITH (NOLOCK)
                JOIN Gastos_Tipos G WITH (NOLOCK) ON R.id_tipo_gasto = G.id_tipo_gasto 
                ORDER BY fecha DESC
            """)
            gastos = cursor.fetchall()

            if gastos:
                df_original = pd.DataFrame(gastos, columns=["ID", "Tipo", "Fecha", "Monto", "Cantidad"])
                st.subheader("✏️ Editar Gastos")
                df_editado = st.data_editor(df_original.copy(), num_rows="dynamic")

                if st.button("Guardar Cambios"):
                    try:
                        cambios_realizados = False

                        for index, row in df_editado.iterrows():
                            id_gasto = row["ID"]
                            nuevo_monto = row["Monto"]
                            nueva_cantidad = row["Cantidad"]
                            nueva_fecha = row["Fecha"]

                            fila_original = df_original[df_original["ID"] == id_gasto]
                            if not fila_original.empty:
                                original_monto = fila_original.iloc[0]["Monto"]
                                original_cantidad = fila_original.iloc[0]["Cantidad"]
                                original_fecha = fila_original.iloc[0]["Fecha"]

                                if (
                                    nuevo_monto != original_monto or
                                    nueva_cantidad != original_cantidad or
                                    nueva_fecha != original_fecha
                                ):
                                    cursor.execute("""
                                        UPDATE Gastos_Registro 
                                        SET monto=%s, cantidad=%s, fecha=%s 
                                        WHERE id_gasto=%s
                                    """, (nuevo_monto, nueva_cantidad, nueva_fecha, id_gasto))
                                    cambios_realizados = True

                        if cambios_realizados:
                            conn.commit()
                            st.success("✅ Cambios guardados exitosamente")
                            st.rerun()
                        else:
                            st.info("ℹ No se detectaron cambios en los datos.")

                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Error al guardar cambios: {e}")
            else:
                st.warning("ℹ No hay registros disponibles.")

        finally:
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
#elif opcion == "📊 Análisis de Costos":
#    analisis_costos()
