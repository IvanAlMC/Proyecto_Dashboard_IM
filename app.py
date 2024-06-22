from flask import Flask, render_template, request
from fpreprocesamiento import preprocesamiento # type: ignore
import matplotlib.pyplot as plt
import pandas as pd
import cx_Oracle

app = Flask(__name__)

# Configuración de la conexión a la base de datos Oracle
username = 'pedidos'
password = 'pedidos'
host_ngrok = 'localhost'
puerto = '1521'
servicio = 'ORCL'  # O SID

dsn = cx_Oracle.makedsn(host_ngrok, puerto, service_name=servicio)

#Controler
df_emp = preprocesamiento.lee_archivo()
cuenta_job_id = preprocesamiento.cuenta_job_id(df_emp)
cantidad_max_job = cuenta_job_id.loc[0]['Cantidad']

#Obtener otros datos del dataframe empleados:

cant_empleados = preprocesamiento.numero_total_empleados(df_emp)
cant_dep = preprocesamiento.numero_total_departamentos(df_emp)
sal_prom = preprocesamiento.promedio_salario_empleados(df_emp)

# Luego puedes definir tus rutas
@app.route('/')
@app.route('/index.html')
def index():

    # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)

    # Consultas SQL
    consultas = [
        "SELECT COUNT(*) AS total_pedidos FROM PEDIDOS",
        "SELECT Nombre_Producto FROM PRODUCTOS WHERE Precio_por_Unidad = (SELECT MAX(Precio_por_Unidad) FROM PRODUCTOS)",
        "SELECT p.Nombre_Producto FROM PRODUCTOS p JOIN DETALLES_PEDIDOS dp ON p.Id_Producto = dp.Id_Producto GROUP BY p.Nombre_Producto ORDER BY SUM(dp.Cantidad) DESC FETCH FIRST 1 ROW ONLY",
        "SELECT c.nombre_compania FROM CLIENTES c JOIN PEDIDOS p ON c.Id_Cliente = p.Id_Cliente GROUP BY c.nombre_compania ORDER BY COUNT(p.Id_Pedido) DESC FETCH FIRST 1 ROW ONLY",
        "SELECT SUM(dp.Cantidad * dp.Precio_Unidad) AS Total_Ingresos FROM DETALLES_PEDIDOS dp",
        "SELECT ROUND(AVG(Precio_por_Unidad), 2) AS Promedio_Precio_Unidad FROM PRODUCTOS",
        "SELECT p.Nombre_Compania AS Proveedor FROM PROVEEDORES p JOIN PRODUCTOS pr ON p.Id_Proveedor = pr.Id_Proveedor GROUP BY p.Nombre_Compania ORDER BY COUNT(*) DESC FETCH FIRST 1 ROW ONLY",
        "SELECT c.Nombre_Compania AS Cliente FROM CLIENTES c JOIN PEDIDOS p ON c.Id_Cliente = p.Id_Cliente GROUP BY c.Nombre_Compania ORDER BY MAX(p.Valor_Envio) DESC FETCH FIRST 1 ROW ONLY",
        "SELECT COUNT(*) AS Total_Clientes FROM CLIENTES",
        "SELECT COUNT(*) AS Total_Proveedores FROM PROVEEDORES",
        "SELECT TO_CHAR(MAX(Fecha_Pedido), 'DD/MM/YYYY') AS Ultimo_Pedido FROM PEDIDOS",
        "SELECT Nombre_Producto FROM PRODUCTOS GROUP BY Nombre_Producto ORDER BY MAX(Unidades_en_Existencia) DESC FETCH FIRST 1 ROW ONLY",
        "SELECT Nombre_Producto FROM PRODUCTOS GROUP BY Nombre_Producto ORDER BY MIN(Unidades_en_Existencia) ASC FETCH FIRST 1 ROW ONLY",
        "SELECT COUNT(*) AS cant_pedidos_sin_representante FROM PEDIDOS WHERE employee_id IS NULL"
    ]

    # Ejecutar las consultas y obtener los resultados
    resultados = []
    for consulta in consultas:
        cursor = connection.cursor()
        cursor.execute(consulta)
        resultado = cursor.fetchone()[0]
        resultados.append(resultado)
        cursor.close()

    # Cerrar la conexión a la base de datos
    connection.close()

    return render_template('index.html', cantidad_max_job=cantidad_max_job, cant_empleados=cant_empleados,
                           cant_dep=cant_dep, sal_prom=sal_prom, resultados=resultados)

@app.route('/tables.html')
def tables():

     # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)

    try:
        with connection.cursor() as cursor:
            sql = "SELECT nombre_producto, cantidad_vendida FROM ( SELECT nombre_producto, SUM(cantidad) AS cantidad_vendida, ROW_NUMBER() OVER (ORDER BY SUM(cantidad) DESC) AS ranking FROM detalles_pedidos dp JOIN productos p ON dp.id_producto = p.id_producto GROUP BY nombre_producto) WHERE ranking <= 10"
            cursor.execute(sql)
            productos_vendidos = cursor.fetchall()
    except Exception as e:
        # Manejo de errores en caso de que la consulta falle
        print("Error al ejecutar la consulta:", e)
        productos_vendidos = []

    try:
        with connection.cursor() as cursor:
            sql = "SELECT nombre_producto, cantidad_vendida FROM (SELECT nombre_producto, COUNT(*) AS cantidad_vendida, ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS ranking FROM detalles_pedidos dp JOIN productos p ON dp.id_producto = p.id_producto GROUP BY nombre_producto) WHERE ranking <= 10"
            cursor.execute(sql)
            productos_mas_solicitados = cursor.fetchall()
    except Exception as e:
        # Manejo de errores en caso de que la consulta falle
        print("Error al ejecutar la consulta:", e)
        productos_mas_solicitados = []

    try:
        with connection.cursor() as cursor:
            sql = "SELECT nombre_producto, cantidad_vendida FROM (SELECT nombre_producto, COUNT(*) AS cantidad_vendida, ROW_NUMBER() OVER (ORDER BY COUNT(*) ASC) AS ranking FROM detalles_pedidos dp JOIN productos p ON dp.id_producto = p.id_producto GROUP BY nombre_producto) WHERE ranking <= 10"
            cursor.execute(sql)
            productos_menos_solicitados = cursor.fetchall()
    except Exception as e:
        # Manejo de errores en caso de que la consulta falle
        print("Error al ejecutar la consulta:", e)
        productos_menos_solicitados = []

    try:
        with connection.cursor() as cursor:
            sql = "SELECT c.nombre_compania AS nombre_cliente, COUNT(p.id_pedido) AS cantidad_pedidos FROM clientes c JOIN pedidos p ON c.id_cliente = p.id_cliente GROUP BY c.nombre_compania ORDER BY cantidad_pedidos DESC"
            cursor.execute(sql)
            clientes_pedidos = cursor.fetchall()
    except Exception as e:
        # Manejo de errores en caso de que la consulta falle
        print("Error al ejecutar la consulta:", e)
        clientes_pedidos = []

    try:
        with connection.cursor() as cursor:
            sql = "SELECT CASE WHEN forma_pago = 'E' THEN 'EFECTIVO' WHEN forma_pago = 'C' THEN 'CREDITO' ELSE 'OTRO' END AS forma_pago, COUNT(*) AS cantidad_pedidos FROM pedidos GROUP BY forma_pago"
            cursor.execute(sql)
            forma_pago = cursor.fetchall()
    except Exception as e:
        # Manejo de errores en caso de que la consulta falle
        print("Error al ejecutar la consulta:", e)
        forma_pago = []

    try:
        with connection.cursor() as cursor:
            sql = "SELECT TO_CHAR(fecha_pedido, 'YYYY') AS anio, COUNT(id_pedido) AS cantidad_pedidos FROM pedidos GROUP BY TO_CHAR(fecha_pedido, 'YYYY') ORDER BY TO_CHAR(fecha_pedido, 'YYYY')"
            cursor.execute(sql)
            pedidos_anio = cursor.fetchall()
    except Exception as e:
        # Manejo de errores en caso de que la consulta falle
        print("Error al ejecutar la consulta:", e)
        pedidos_anio = []

    try:
        with connection.cursor() as cursor:
            sql = "SELECT p.nombre_producto, COALESCE(COUNT(dp.id_pedido), 0) AS cantidad_pedidos FROM productos p LEFT JOIN detalles_pedidos dp ON p.id_producto = dp.id_producto GROUP BY p.nombre_producto"
            cursor.execute(sql)
            pedidos_producto = cursor.fetchall()
    except Exception as e:
        # Manejo de errores en caso de que la consulta falle
        print("Error al ejecutar la consulta:", e)
        pedidos_producto = []

    try:
        with connection.cursor() as cursor:
            sql = "SELECT c.nombre_categoria, SUM(dp.cantidad) AS cantidad_vendida FROM detalles_pedidos dp JOIN productos p ON dp.id_producto = p.id_producto JOIN categorias c ON p.id_categoria = c.id_categoria GROUP BY c.nombre_categoria"
            cursor.execute(sql)
            productos_categoria = cursor.fetchall()
    except Exception as e:
        # Manejo de errores en caso de que la consulta falle
        print("Error al ejecutar la consulta:", e)
        productos_categoria = []

    #Cantidad de pedidos por cliente en el año 2021
    try:
        with connection.cursor() as cursor:
            sql = "SELECT c.nombre_compania AS nombre_cliente, COUNT(p.id_pedido) AS cantidad_pedidos FROM pedidos p JOIN clientes c ON p.id_cliente = c.id_cliente WHERE EXTRACT(YEAR FROM p.fecha_pedido) = 2021 GROUP BY c.nombre_compania ORDER BY cantidad_pedidos DESC"
            cursor.execute(sql)
            pedidos_cliente_2021 = cursor.fetchall()
    except Exception as e:
        # Manejo de errores en caso de que la consulta falle
        print("Error al ejecutar la consulta:", e)
        pedidos_cliente_2021 = []

    #Cantidad de productos en inventario por proveedor
    try:
        with connection.cursor() as cursor:
            sql = "SELECT pr.nombre_compania AS nombre_proveedor, COUNT(p.id_producto) AS cantidad_productos FROM productos p JOIN proveedores pr ON p.id_proveedor = pr.id_proveedor GROUP BY pr.nombre_compania ORDER BY cantidad_productos DESC"
            cursor.execute(sql)
            productos_proveedor = cursor.fetchall()
    except Exception as e:
        # Manejo de errores en caso de que la consulta falle
        print("Error al ejecutar la consulta:", e)
        productos_proveedor = []

    #Total de ventas por mes en el año actual
    try:
        with connection.cursor() as cursor:
            sql = "SELECT TO_CHAR(p.fecha_pedido, 'Month') AS nombre_mes, SUM(dp.cantidad * dp.precio_unidad) AS total_ventas FROM detalles_pedidos dp JOIN pedidos p ON dp.id_pedido = p.id_pedido WHERE EXTRACT(YEAR FROM p.fecha_pedido) = 2021 GROUP BY TO_CHAR(p.fecha_pedido, 'Month')"
            cursor.execute(sql)
            ventas_mes = cursor.fetchall()
    except Exception as e:
        # Manejo de errores en caso de que la consulta falle
        print("Error al ejecutar la consulta:", e)
        ventas_mes = []
    
    return render_template('tables.html', df_emp=df_emp, columns_emp=df_emp.columns, productos_vendidos=productos_vendidos, 
                           productos_menos_solicitados=productos_menos_solicitados, productos_mas_solicitados=productos_mas_solicitados,
                           clientes_pedidos=clientes_pedidos, forma_pago=forma_pago, pedidos_anio=pedidos_anio,
                           pedidos_producto=pedidos_producto, productos_categoria=productos_categoria,
                           pedidos_cliente_2021=pedidos_cliente_2021, productos_proveedor=productos_proveedor, ventas_mes=ventas_mes)

@app.route('/charts.html')
def charts():
    #Obtener grafico
    pie_chart = generate_pie_chart_principal()
    bar_chart = generate_bar_chart_job()
    lineal_chart = generate_lineal_chart_job()
    top10mas = generate_graph_top10_most()
    top10massoli = generate_graph_top10_most_solicited()
    top10menossoli = generate_graph_top10_lees_solicited()
    pedidos_mes = generate_graph_pedidos_mes()
    forma_pago = generate_graph_forma_pago()
    pedidos_anio = generate_graph_pedidos_anio()
    pedidos_productos = generate_graph_productos_pedidos()
    categorias_ventas = generate_graph_categoria_ventas()
    clientes_pedidos = generate_graph_clientes_pedidos()
    proveedor_productos = generate_graph_proveedores_productos()
    ventas_mes = generate_graph_ventas_mes()

    return render_template('charts.html', pie_chart=pie_chart, bar_chart=bar_chart, lineal_chart=lineal_chart,
                           top10mas=top10mas, top10massoli=top10massoli, top10menossoli=top10menossoli,
                           pedidos_mes=pedidos_mes, forma_pago=forma_pago, pedidos_anio=pedidos_anio,
                           pedidos_productos=pedidos_productos, categorias_ventas=categorias_ventas,
                           clientes_pedidos=clientes_pedidos, proveedor_productos=proveedor_productos,
                           ventas_mes=ventas_mes)

def generate_pie_chart_principal():
    plt.switch_backend('Agg')

    conteo_job_id = df_emp['JOB_ID'].value_counts().nlargest(4)

    plt.figure(figsize=(4, 8))
    plt.pie(conteo_job_id, labels=conteo_job_id.index, autopct='%1.1f%%', startangle=90,
            colors=['skyblue', 'lightgreen', 'lightcoral', 'lightsalmon'])
    plt.title('Distribución de Empleados por cargo')

    # Ajustar el diseño para evitar que los nombres estén entrecortados
    plt.tight_layout()

    # Guardar el gráfico como un archivo PNG en el servidor
    image_path = "../static/img/grafica1.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path


def generate_bar_chart_job():
    plt.switch_backend('Agg')

    conteo_job_id = df_emp['JOB_ID'].value_counts().nlargest(4)

    plt.figure(figsize=(10,6))
    ax = conteo_job_id.plot(kind='bar', color=['skyblue', 'lightgreen', 'lightcoral', 'lightsalmon'])
    plt.title('Distribucion de cargos de los empleados')
    plt.xlabel('Cargos')
    plt.ylabel('Cantidad de empleados')

    #Agreando el numero de empleados a cada barra
    for i, v in enumerate(conteo_job_id):
        ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontsize=8)
    
    #Ajustar el diseño para evitar nombres entrecortados
    plt.tight_layout()

    # Guardar el gráfico como un archivo PNG en el servidor
    image_path = "../static/img/grafica2.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path

def generate_lineal_chart_job():
    #establecer tamaño figura
    plt.figure(figsize=(10,6))

    #sumar empleados por cargo    
    conteo_job_id = df_emp['JOB_ID'].value_counts().nlargest(4)

    #trazar linea de cargos
    plt.plot(['SA_REP', 'ST_CLERK', 'SH_CLERK', 'IT_PROG'], conteo_job_id, marker='o', label='Cargos Empleados')

    #ajustar etiquetas y titutlo
    plt.title('Empleados por cargos')
    plt.xlabel('Cargos')
    plt.ylabel('Cantidad de empleados')

    #Mostrar la leyenda
    plt.legend()

    #Ajustar el diseño
    plt.tight_layout()

    #Guardando la imagen para usuarla luego
    image_path = "../static/img/grafica3.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path


def generate_graph_top10_most():
     # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)
    sql_query = "SELECT nombre_producto, cantidad_vendida FROM ( SELECT nombre_producto, SUM(cantidad) AS cantidad_vendida, ROW_NUMBER() OVER (ORDER BY SUM(cantidad) DESC) AS ranking FROM detalles_pedidos dp JOIN productos p ON dp.id_producto = p.id_producto GROUP BY nombre_producto) WHERE ranking <= 10"
    # Cerrar la conexión a la base de datos

    # Ejecutar la consulta y cargar los resultados en un DataFrame de Pandas
    df = pd.read_sql(sql_query, connection)

    connection.close()

    plt.switch_backend('Agg')

    # Crear el gráfico de barras
    plt.figure(figsize=(10,6))
    ax = plt.bar(df['NOMBRE_PRODUCTO'], df['CANTIDAD_VENDIDA'], color='skyblue')
    plt.title('Top 10 Productos Más Vendidos')
    plt.xlabel('Producto')
    plt.ylabel('Cantidad Vendida')

    # Agregar las etiquetas de cantidad a cada barra
    for i, v in enumerate(df['CANTIDAD_VENDIDA']):
        plt.text(i, v + 0.1, str(v), ha='center', va='bottom', fontsize=8)
    
    # Ajustar el diseño para evitar nombres entrecortados
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Guardar el gráfico como un archivo PNG
    image_path = "../static/img/grafica_t10mas.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path

def generate_graph_top10_most_solicited():
     # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)
    sql_query = "SELECT nombre_producto, cantidad_vendida FROM ( SELECT nombre_producto, COUNT(*) AS cantidad_vendida, ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS ranking FROM detalles_pedidos dp JOIN productos p ON dp.id_producto = p.id_producto GROUP BY nombre_producto) WHERE ranking <= 10"
    # Cerrar la conexión a la base de datos

    # Ejecutar la consulta y cargar los resultados en un DataFrame de Pandas
    df = pd.read_sql(sql_query, connection)

    connection.close()

    plt.switch_backend('Agg')

    # Crear el gráfico de barras
    plt.figure(figsize=(10,6))
    ax = plt.bar(df['NOMBRE_PRODUCTO'], df['CANTIDAD_VENDIDA'], color='skyblue')
    plt.title('Top 10 Productos Más Solicitados')
    plt.xlabel('Producto')
    plt.ylabel('Cantidad Vendida')

    # Agregar las etiquetas de cantidad a cada barra
    for i, v in enumerate(df['CANTIDAD_VENDIDA']):
        plt.text(i, v + 0.1, str(v), ha='center', va='bottom', fontsize=8)
    
    # Ajustar el diseño para evitar nombres entrecortados
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Guardar el gráfico como un archivo PNG
    image_path = "../static/img/grafica_t10massoli.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path


def generate_graph_top10_lees_solicited():
     # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)
    sql_query = "SELECT nombre_producto, cantidad_vendida FROM ( SELECT nombre_producto, COUNT(*) AS cantidad_vendida, ROW_NUMBER() OVER (ORDER BY COUNT(*) ASC) AS ranking FROM detalles_pedidos dp JOIN productos p ON dp.id_producto = p.id_producto GROUP BY nombre_producto) WHERE ranking <= 10"
    # Cerrar la conexión a la base de datos

    # Ejecutar la consulta y cargar los resultados en un DataFrame de Pandas
    df = pd.read_sql(sql_query, connection)

    connection.close()

    plt.switch_backend('Agg')

    # Crear el gráfico de barras
    plt.figure(figsize=(10,6))
    ax = plt.bar(df['NOMBRE_PRODUCTO'], df['CANTIDAD_VENDIDA'], color='skyblue')
    plt.title('Top 10 Productos Menos Solicitados')
    plt.xlabel('Producto')
    plt.ylabel('Cantidad Vendida')

    # Agregar las etiquetas de cantidad a cada barra
    for i, v in enumerate(df['CANTIDAD_VENDIDA']):
        plt.text(i, v + 0.1, str(v), ha='center', va='bottom', fontsize=8)
    
    # Ajustar el diseño para evitar nombres entrecortados
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Guardar el gráfico como un archivo PNG
    image_path = "../static/img/grafica_t10memossoli.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path

def generate_graph_pedidos_mes():
    # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)
    
    # Consulta SQL para obtener la cantidad de pedidos por mes del año 2020
    sql_query = "SELECT TO_CHAR(fecha_pedido, 'Month') AS nombre_mes, COUNT(id_pedido) AS cantidad_pedidos FROM pedidos WHERE TO_CHAR(fecha_pedido, 'YYYY') = '2020' GROUP BY TO_CHAR(fecha_pedido, 'Month') ORDER BY TO_DATE(TO_CHAR(fecha_pedido, 'Month'), 'Month')"
    
    # Ejecutar la consulta y cargar los resultados en un DataFrame de Pandas
    df = pd.read_sql(sql_query, connection)

    connection.close()

    # Establecer tamaño de la figura
    plt.figure(figsize=(10,6))

    # Trazar la línea de cantidad de pedidos por mes
    plt.plot(df['NOMBRE_MES'], df['CANTIDAD_PEDIDOS'], marker='o', label='Cantidad de Pedidos')

    # Ajustar etiquetas y título
    plt.title('Cantidad de Pedidos por Mes en el Año 2020')
    plt.xlabel('Mes')
    plt.ylabel('Cantidad de Pedidos')

    # Mostrar la leyenda
    plt.legend()

    # Ajustar el diseño
    plt.tight_layout()

    # Guardar la imagen para usarla luego
    image_path = "../static/img/grafica_pedidos_por_mes_2020.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path

def generate_graph_forma_pago():
     # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)
    sql_query = "SELECT CASE WHEN forma_pago = 'E' THEN 'EFECTIVO' WHEN forma_pago = 'C' THEN 'CREDITO' ELSE 'OTRO' END AS forma_pago, COUNT(*) AS cantidad_pedidos FROM pedidos GROUP BY forma_pago"
    # Cerrar la conexión a la base de datos

    # Ejecutar la consulta y cargar los resultados en un DataFrame de Pandas
    df = pd.read_sql(sql_query, connection)

    connection.close()

    plt.switch_backend('Agg')

    # Crear el gráfico de barras
    plt.figure(figsize=(10,6))
    ax = plt.bar(df['FORMA_PAGO'], df['CANTIDAD_PEDIDOS'], color='skyblue')
    plt.title('Pedidos por forma de pago')
    plt.xlabel('Forma de Pago')
    plt.ylabel('Cantidad de Pedidos')

    # Agregar las etiquetas de cantidad a cada barra
    for i, v in enumerate(df['CANTIDAD_PEDIDOS']):
        plt.text(i, v + 0.1, str(v), ha='center', va='bottom', fontsize=8)
    
    # Ajustar el diseño para evitar nombres entrecortados
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Guardar el gráfico como un archivo PNG
    image_path = "../static/img/grafica_forma_pago.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path

def generate_graph_pedidos_anio():
    # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)
    
    # Consulta SQL para obtener la cantidad de pedidos por año
    sql_query = "SELECT TO_CHAR(fecha_pedido, 'YYYY') AS anio, COUNT(id_pedido) AS cantidad_pedidos FROM pedidos GROUP BY TO_CHAR(fecha_pedido, 'YYYY') ORDER BY TO_CHAR(fecha_pedido, 'YYYY')"
    
    # Ejecutar la consulta y cargar los resultados en un DataFrame de Pandas
    df = pd.read_sql(sql_query, connection)

    connection.close()

    # Establecer los datos para el diagrama de pastel
    labels = df['ANIO']
    sizes = df['CANTIDAD_PEDIDOS']
    colors = ['skyblue', 'lightgreen', 'lightcoral', 'lightsalmon']

    # Crear el diagrama de pastel
    plt.switch_backend('Agg')
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
    plt.title('Distribución de Pedidos por Año')

    # Ajustar el diseño
    plt.tight_layout()

    # Guardar el gráfico como un archivo PNG
    image_path = "../static/img/grafica_pedidos_anio.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path

def generate_graph_productos_pedidos():
    # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)
    
    # Consulta SQL para obtener la cantidad de pedidos por producto
    sql_query = "SELECT p.nombre_producto, COALESCE(COUNT(dp.id_pedido), 0) AS cantidad_pedidos FROM productos p LEFT JOIN detalles_pedidos dp ON p.id_producto = dp.id_producto GROUP BY p.nombre_producto"
    
    # Ejecutar la consulta y cargar los resultados en un DataFrame de Pandas
    df = pd.read_sql(sql_query, connection)

    connection.close()

    # Ordenar el DataFrame por la cantidad de pedidos
    df = df.sort_values(by='CANTIDAD_PEDIDOS', ascending=False)

    # Filtrar los primeros cinco y los últimos cinco productos
    df_top_bottom = pd.concat([df.head(5), df.tail(5)])

    # Establecer tamaño de la figura
    plt.figure(figsize=(20,10))

    # Crear el gráfico de barras
    ax = df_top_bottom.plot(kind='bar', x='NOMBRE_PRODUCTO', y='CANTIDAD_PEDIDOS', color='skyblue')
    plt.title('Cantidad de Pedidos por Producto')
    plt.xlabel('Producto')
    plt.ylabel('Cantidad de Pedidos')

    plt.tight_layout()

    # Guardar el gráfico como un archivo PNG
    image_path = "../static/img/grafica_pedidos_por_producto.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path

def generate_graph_categoria_ventas():
   # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)
    
    # Consulta SQL para obtener la cantidad de productos vendidos por categoría
    sql_query = "SELECT c.nombre_categoria, SUM(dp.cantidad) AS cantidad_vendida FROM detalles_pedidos dp JOIN productos p ON dp.id_producto = p.id_producto JOIN categorias c ON p.id_categoria = c.id_categoria GROUP BY c.nombre_categoria"
    
    # Ejecutar la consulta y cargar los resultados en un DataFrame de Pandas
    df = pd.read_sql(sql_query, connection)

    connection.close()

    # Establecer los datos para el diagrama de pastel
    labels = df['NOMBRE_CATEGORIA']
    sizes = df['CANTIDAD_VENDIDA']
    colors = ['skyblue', 'lightgreen', 'lightcoral', 'lightsalmon']

    # Crear el diagrama de pastel
    plt.switch_backend('Agg')
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
    plt.title('Distribución de Productos Vendidos por Categoría')

    # Ajustar el diseño
    plt.tight_layout()

    # Guardar el gráfico como un archivo PNG
    image_path = "../static/img/grafica_productos_por_categoria.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path

def generate_graph_clientes_pedidos():
    # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)
    
    # Consulta SQL para obtener la cantidad de pedidos por cliente en el año actual
    sql_query = "SELECT c.nombre_compania AS nombre_cliente, COUNT(p.id_pedido) AS cantidad_pedidos FROM pedidos p JOIN clientes c ON p.id_cliente = c.id_cliente WHERE EXTRACT(YEAR FROM p.fecha_pedido) = 2021 GROUP BY c.nombre_compania ORDER BY cantidad_pedidos DESC"
    
    # Ejecutar la consulta y cargar los resultados en un DataFrame de Pandas
    df = pd.read_sql(sql_query, connection)

    connection.close()

    # Ordenar el DataFrame por la cantidad de pedidos
    df = df.sort_values(by='CANTIDAD_PEDIDOS', ascending=False)

    # Filtrar los primeros cinco y los últimos cinco productos
    df_top_bottom = pd.concat([df.head(5), df.tail(5)])


    # Establecer tamaño de la figura
    plt.figure(figsize=(10,6))

    # Crear el gráfico de barras
    ax = df_top_bottom.plot(kind='bar', x='NOMBRE_CLIENTE', y='CANTIDAD_PEDIDOS', color='skyblue')
    plt.title('Cantidad de Pedidos por Cliente en el Año Actual')
    plt.xlabel('Cliente')
    plt.ylabel('Cantidad de Pedidos')

    # Ajustar el diseño
    plt.tight_layout()

    # Guardar el gráfico como un archivo PNG
    image_path = "../static/img/grafica_pedidos_por_cliente.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path

def generate_graph_proveedores_productos():
    # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)
    
    # Consulta SQL para obtener la cantidad de pedidos por cliente en el año actual
    sql_query = "SELECT c.nombre_compania AS nombre_proveedor, COUNT(p.id_pedido) AS cantidad_productos FROM pedidos p JOIN clientes c ON p.id_cliente = c.id_cliente WHERE EXTRACT(YEAR FROM p.fecha_pedido) = 2021 GROUP BY c.nombre_compania ORDER BY cantidad_productos DESC"
    
    # Ejecutar la consulta y cargar los resultados en un DataFrame de Pandas
    df = pd.read_sql(sql_query, connection)

    connection.close()

    # Ordenar el DataFrame por la cantidad de pedidos
    df = df.sort_values(by='CANTIDAD_PRODUCTOS', ascending=False)

    # Filtrar los primeros cinco y los últimos cinco productos
    df_top = pd.concat([df.head(7)])


    # Establecer los datos para el diagrama de pastel
    labels = df_top['NOMBRE_PROVEEDOR']
    sizes = df_top['CANTIDAD_PRODUCTOS']
    colors = ['skyblue', 'lightgreen', 'lightcoral', 'lightsalmon']

    # Crear el diagrama de pastel
    plt.switch_backend('Agg')
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
    plt.title('Distribución de Productos en Inventario por Proveedor')

    # Ajustar el diseño
    plt.tight_layout()

    # Guardar el gráfico como un archivo PNG
    image_path = "../static/img/grafica_productos_por_proveedor.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path

def generate_graph_ventas_mes():
    # Conexión a la base de datos
    connection = cx_Oracle.connect(username, password, dsn)
    
    # Consulta SQL para obtener el total de ventas por mes en el año actual
    sql_query = "SELECT TO_CHAR(p.fecha_pedido, 'Month') AS nombre_mes, SUM(dp.cantidad * dp.precio_unidad) AS total_ventas FROM detalles_pedidos dp JOIN pedidos p ON dp.id_pedido = p.id_pedido WHERE EXTRACT(YEAR FROM p.fecha_pedido) = 2021 GROUP BY TO_CHAR(p.fecha_pedido, 'Month')"
    
    # Ejecutar la consulta y cargar los resultados en un DataFrame de Pandas
    df = pd.read_sql(sql_query, connection)

    connection.close()

    # Establecer tamaño de la figura
    plt.figure(figsize=(10,6))

    # Crear el gráfico de líneas
    plt.plot(df['NOMBRE_MES'], df['TOTAL_VENTAS'], marker='o', color='skyblue')
    plt.title('Total de Ventas por Mes en el Año Actual')
    plt.xlabel('Mes')
    plt.ylabel('Total de Ventas')

    # Ajustar el diseño
    plt.tight_layout()

    # Guardar el gráfico como un archivo PNG
    image_path = "../static/img/grafica_ventas_por_mes.png"
    plt.savefig(image_path, format='png', bbox_inches='tight')
    plt.close()
    return image_path

if __name__ == '__main__':
    app.run(debug=True)