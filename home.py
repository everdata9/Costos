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
    return st.sidebar.radio("Seleccionar", ["💰 Registro de Gastos", "📈 Análisis por Tipo de Gasto"], index=0)
    #return st.sidebar.radio("Seleccionar", ["💰 Registro de Gastos"], index=0)
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
def analisis_por_tipo_gasto():
    """Análisis del comportamiento del gasto por categoría y tipo de gasto"""
    st.markdown("<h3 style='color:#4285F4; text-align:center;'>📊 Análisis por Categoría y Tipo de Gasto</h3>", unsafe_allow_html=True)

    conn = conectar_bd()
    if not conn:
        return
    
    cursor = conn.cursor()

    # Obtener las categorías de gasto disponibles
    cursor.execute("SELECT id_categoria, nombre_categoria FROM Gastos_Categorias WITH (NOLOCK)")
    categorias = cursor.fetchall()
    categorias_dict = {categoria[1]: categoria[0] for categoria in categorias}

    # Agregar "Todos" como opción
    categorias_dict = {"Todos": None, **categorias_dict}

    # Selección de categoría
    categoria_seleccionada = st.selectbox("Seleccionar Categoría", list(categorias_dict.keys()), index=0)
    id_categoria = categorias_dict[categoria_seleccionada]

    # Obtener tipos de gasto dentro de la categoría seleccionada
    tipos_dict = {}
    cursor.execute("""
        SELECT id_tipo_gasto, nombre_tipo 
        FROM Gastos_Tipos WITH (NOLOCK)
        WHERE id_categoria = %s
    """, (id_categoria,))
    tipos_gastos = cursor.fetchall()
    tipos_dict = {tipo[1]: tipo[0] for tipo in tipos_gastos}

    # Selección de tipo de gasto (opcional)
    tipo_seleccionado = st.selectbox("Seleccionar Tipo de Gasto", ["Todos"] + list(tipos_dict.keys()), index=0)
    id_tipo_gasto = tipos_dict.get(tipo_seleccionado, None)

    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio", key='fecha_inicio')
    with col2:
        fecha_fin = st.date_input("Fecha de fin", key='fecha_fin')
    with col3:
        frecuencia = st.selectbox("Frecuencia", ["Semanal", "Mensual", "Anual"], index=2)

    # Determinar cómo agrupar los datos en SQL
    if frecuencia == "Semanal":
        # Usamos CONCAT con zero-padding en la semana para que quede YYYY-WW
        group_by = "CONCAT(YEAR(fecha), '-', FORMAT(DATEPART(WEEK, fecha), '00'))"
        label_x = "Semana"
    elif frecuencia == "Mensual":
        group_by = "FORMAT(fecha, 'yyyy-MM')"
        label_x = "Mes"
    else:  # Anual
        group_by = "YEAR(fecha)"
        label_x = "Año"

    # Construcción de la consulta SQL dinámicamente
    query = f"""
        SELECT {group_by} AS periodo, SUM(CAST(monto AS FLOAT)) AS total_gasto
        FROM Gastos_Registro GR
        JOIN Gastos_Tipos GT ON GR.id_tipo_gasto = GT.id_tipo_gasto
        JOIN Gastos_Categorias GC ON GT.id_categoria = GC.id_categoria
        WHERE GR.fecha BETWEEN %s AND %s
    """
    params = [fecha_inicio, fecha_fin]

    # Si se elige "Todos", excluimos "Entrada". De lo contrario, filtramos por la categoría
    if categoria_seleccionada == "Todos":
        query += " AND GC.nombre_categoria != 'Entrada'"
    else:
        query += " AND GC.id_categoria = %s"
        params.append(id_categoria)

    # Si se seleccionó un tipo de gasto específico
    if id_tipo_gasto:
        query += " AND GR.id_tipo_gasto = %s"
        params.append(id_tipo_gasto)

    query += f" GROUP BY {group_by} ORDER BY {group_by}"

    cursor.execute(query, tuple(params))
    datos = cursor.fetchall()

    # Si la categoría es "Entrada" y la frecuencia es "Anual", obtener la suma de todas las categorías por año
    total_general = {}
    if categoria_seleccionada == "Entrada" and frecuencia == "Anual":
        query_total = f"""
            SELECT {group_by} AS periodo, SUM(CAST(monto AS FLOAT)) AS total_general
            FROM Gastos_Registro
            WHERE fecha BETWEEN %s AND %s
            GROUP BY {group_by}
            ORDER BY {group_by}
        """
        cursor.execute(query_total, (fecha_inicio, fecha_fin))
        total_general = dict(cursor.fetchall())  # Convertir a diccionario {periodo: total_general}

    conn.close()

    if not datos:
        st.warning("⚠ No hay datos disponibles para este rango de fechas.")
        return

    # Convertir a DataFrame
    df = pd.DataFrame(datos, columns=["Fecha", "Total Gasto"])
    df["Total Gasto"] = df["Total Gasto"].astype(float)

    # Si es "Entrada" y "Anual", agregar total general y porcentaje
    if categoria_seleccionada == "Entrada" and frecuencia == "Anual":
        df["Total General"] = df["Fecha"].map(total_general).astype(float)  # Convertir total general a float
        df["Porcentaje"] = ((df["Total Gasto"] / df["Total General"]) * 100).fillna(0).round(2)

    # Convertir Fecha en formato correcto según la frecuencia
    if frecuencia == "Semanal":
        # Convertir "YYYY-WW" en una fecha real (lunes de esa semana)
        df["Fecha"] = pd.to_datetime(df["Fecha"] + "-1", format="%Y-%W-%w", errors="coerce")
    elif frecuencia == "Mensual":
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    else:  # Anual
        df["Fecha"] = df["Fecha"].astype(int)  # El año como entero

    # Ordenar los datos por fecha
    df = df.sort_values(by="Fecha")

    # Formatear la columna de gasto (con separadores de miles)
    df["Total Gasto"] = df["Total Gasto"].apply(lambda x: f"{x:,.0f}")
    if "Total General" in df.columns:
        df["Total General"] = df["Total General"].apply(lambda x: f"{x:,.0f}")
        df["Porcentaje"] = df["Porcentaje"].apply(lambda x: f"{x:.2f}%")

    # Mostrar la tabla
    st.dataframe(df, use_container_width=True)

    # Gráfico de evolución del gasto
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(
        df["Fecha"],
        df["Total Gasto"].str.replace(",", "").astype(float),
        marker="o", linestyle="-", color="blue", label="Total Gasto"
    )

    # Si hay columna de Total General, graficar también
    if "Total General" in df.columns:
        ax.plot(
            df["Fecha"],
            df["Total General"].str.replace(",", "").astype(float),
            marker="o", linestyle="--", color="red", label="Total General"
        )

    ax.set_xlabel(label_x)
    ax.set_ylabel("Monto en colones")
    ax.set_title(f"Evolución del Gasto: {categoria_seleccionada}")
    ax.grid(True)
    ax.legend()

    st.pyplot(fig)
# Navegación entre secciones
opcion = menu_lateral()
if opcion == "💰 Registro de Gastos":
    registrar_gastos()
elif opcion == "📈 Análisis por Tipo de Gasto":
    analisis_por_tipo_gasto()