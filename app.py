from flask import Flask, request, redirect, url_for, render_template
import pyodbc
import os
from dotenv import load_dotenv
from jinja2 import ChoiceLoader, FileSystemLoader

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Configurar Flask para buscar plantillas en varias carpetas
template_dirs = [
    os.path.join(app.root_path, 'templates'),
    os.path.join(app.root_path, 'admin'),
    os.path.join(app.root_path, 'bomberos'),
    os.path.join(app.root_path, 'coordinadores')
]

app.jinja_loader = ChoiceLoader([FileSystemLoader(template_dirs)])

def validar_usuario(email, clave, rol_seleccionado):
    print(f"Validando usuario: email={email}, clave={clave}, rol_seleccionado={rol_seleccionado}")
    conn = pyodbc.connect(
        f"DRIVER={{SQL Server}};SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};UID={os.getenv('DB_USER')};PWD={os.getenv('DB_PASSWORD')}"
    )
    cursor = conn.cursor()
    
    # Mapear el rol seleccionado a un ID de rol
    roles = {'Administrador': 1, 'Coordinador': 2, 'Bombero': 3}
    rol_id = roles.get(rol_seleccionado)

    print(f"Rol mapeado: {rol_id}")
    
    # Consulta para validar usuario con el rol especificado
    query = """
    SELECT U.ID_Usuario, P.ID_Rol, U.Validado FROM Usuario U
    JOIN Persona P ON U.ID_Usuario = P.ID_Usuario
    WHERE LOWER(U.Mail) = LOWER(?) AND U.Clave = ? AND P.ID_Rol = ?
    """
    
    print(f"Ejecutando consulta SQL: {query} con parámetros: email={email}, clave={clave}, rol_id={rol_id}")
    cursor.execute(query, (email, clave, rol_id))
    row = cursor.fetchone()
    
    if row:
        usuario_id = row.ID_Usuario
        rol_id = row.ID_Rol
        validado = row.Validado
        print(f"Usuario encontrado: ID_Usuario={usuario_id}, ID_Rol={rol_id}, Validado={validado}")
        
        # Actualizar el estado de validación del usuario si no está validado
        if validado == 0:
            print(f"Actualizando estado de validación para usuario ID: {usuario_id}")
            update_query = "UPDATE Usuario SET Validado = 1 WHERE ID_Usuario = ?"
            cursor.execute(update_query, (usuario_id,))
            conn.commit()
            print(f"Estado de validación actualizado para el usuario {usuario_id}")
        
        return True, rol_id
    else:
        print("Usuario no encontrado o credenciales incorrectas.")
        return False, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validar_usuario', methods=['POST'])
def login():
    email = request.form.get('email')
    clave = request.form.get('clave')
    rol_seleccionado = request.form.get('rol')

    print(f"Datos recibidos: email={email}, clave={clave}, rol_seleccionado={rol_seleccionado}")
    
    validado, rol = validar_usuario(email, clave, rol_seleccionado)
    
    if validado:
        if rol == 1:  # Administrador
            return redirect(url_for('crear_usuario'))
        elif rol == 2:  # Coordinador
            return redirect(url_for('coord_principal'))
        elif rol == 3:  # Bombero
            return redirect(url_for('bombero_home'))
    else:
        return "Usuario no válido o credenciales incorrectas."

@app.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'POST':
        # Obtener todos los datos del formulario
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        dni = request.form.get('dni')
        fecha_nacimiento = request.form.get('date')
        correo = request.form.get('correo')
        password = request.form.get('password')
        genero = request.form.get('genero')
        rol = request.form.get('rol')
        tipo_sangre = request.form.get('sangre')
        peso = request.form.get('peso')
        altura = request.form.get('altura')
        historial = request.form.get('historial')
        
        # Mapear valores de genero y rol a sus IDs correspondientes
        generos = {'m': 1, 'f': 2, 'o': 3}
        roles = {'adm': 1, 'coord': 2, 'bomb': 3}
        tipos_sangre = {'ap': 1, 'an': 2, 'bp': 3, 'bn': 4, 'abp': 5, 'abn': 6, 'op': 7, 'on': 8}
        
        # Mapeo de los valores
        genero_id = generos.get(genero)
        rol_id = roles.get(rol)
        tipo_sangre_id = tipos_sangre.get(tipo_sangre)
        
        # Verificación de los valores obtenidos
        print(f"Valores recibidos: nombre={nombre}, apellido={apellido}, dni={dni}, fecha_nacimiento={fecha_nacimiento}, correo={correo}, password={password}, genero_id={genero_id}, rol_id={rol_id}, tipo_sangre_id={tipo_sangre_id}, peso={peso}, altura={altura}, historial={historial}")
        
        # Verifica que ninguno de los campos requeridos esté vacío 
        if not nombre or not apellido or not dni or not fecha_nacimiento or not correo or not password or not genero_id or not rol_id or not tipo_sangre_id or not peso or not altura:
            return "Todos los campos son obligatorios."


        # Conexión a la base de datos
        conn = pyodbc.connect(
            f"DRIVER={{SQL Server}};SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_NAME')};UID={os.getenv('DB_USER')};PWD={os.getenv('DB_PASSWORD')}"
        )
        cursor = conn.cursor()

        # Inserción en la tabla Usuario
        insert_usuario_query = """
        INSERT INTO Usuario (Mail, Clave, Validado)
        VALUES (?, ?, 0)
        """
        cursor.execute(insert_usuario_query, (correo, password))

        # Obtener el ID del usuario recién creado
        cursor.execute("SELECT @@IDENTITY AS ID_Usuario")
        usuario_id = cursor.fetchone()[0]

        # Inserción en la tabla Persona
        insert_persona_query = """
        INSERT INTO Persona (DNI, Nombre, Apellido, Peso, FechaNacimiento, Altura, ID_Genero, ID_Grupo, ID_Condicion, ID_Rol, ID_Usuario)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_persona_query, (dni, nombre, apellido, peso, fecha_nacimiento, altura, genero_id, tipo_sangre_id, None, rol_id, usuario_id))
        conn.commit()
        
        return "Usuario creado exitosamente"
    
    return render_template('admin/crearUsuario.html')

@app.route('/admin_home')
def admin_home():
    return render_template('admin/ingresoAdmin.html')

@app.route('/coord_principal')
def coord_principal():
    return render_template('coordinadores/coordPrincipal.html')

@app.route('/coordinador_ingreso')
def coordinador_ingreso():
    return render_template('coordinadores/ingresoCoordinador.html')

@app.route('/bombero_home')
def bombero_home():
    return render_template('bomberos/ingresoBombero.html')

@app.route('/bombero_principal')
def bombero_principal():
    return render_template('bomberos/bomberoPrincipal.html')

if __name__ == '__main__':
    app.run(debug=True)


