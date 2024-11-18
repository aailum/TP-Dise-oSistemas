import pyodbc

def verificar_conexion():
    try:
        conn = pyodbc.connect('DRIVER={SQL Server};SERVER=192.168.0.236;DATABASE=Rescuelens;UID=rescuelens;PWD=bomberos')
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result:
            print("Conexión exitosa a la base de datos.")
        else:
            print("Conexión fallida a la base de datos.")
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")

verificar_conexion()


