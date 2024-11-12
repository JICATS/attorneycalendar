from flask import Flask, render_template, request, redirect, url_for,session,jsonify
import pymysql.cursors
import stripe

app = Flask(__name__)
app.secret_key = '1234'  # Cambia esto por una clave más segura

# Configura los detalles de la conexión a la base de datos
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Qq240419$',  # Cambia esto por tu contraseña real
    database='reservas_db',
    cursorclass=pymysql.cursors.DictCursor
)

# Configura tu clave secreta de Stripe
stripe.api_key = 'sk_test_51QHPbtL1y4d5B8Baiuunm5wsMfaciXRcsw5Yub3yfjdb7yaEcYsF6hR5JPZOH4RqPUnEZltcmIXYIhjjPBkvPtUd00UwRn6qzE'

@app.route('/', methods=['GET', 'POST'])
def index():
    horarios = []  # Inicialmente no hay horarios

    with connection.cursor() as cursor:
        

        # Obtener todas las fechas disponibles
        cursor.execute("SELECT DISTINCT fecha FROM horarios WHERE disponible = 1")
        fechas_disponibles = cursor.fetchall()
        
         
    
    return render_template('cita.html', fechas_disponibles=fechas_disponibles, horarios=horarios)

from datetime import timedelta

@app.route('/obtener_horarios', methods=['POST'])
def obtener_horarios():
    fecha_seleccionada = request.form['fecha']
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT hora FROM horarios WHERE fecha = %s AND disponible = 1", (fecha_seleccionada,))
        horarios = cursor.fetchall()

        # Imprimir el resultado de la consulta para ver la estructura
        print("Horarios obtenidos:", horarios)
        
        # Formatear las horas adecuadamente
        horarios_formateados = []
        for horario in horarios:
            # 'horario' es un diccionario con la clave 'hora' que tiene un valor tipo timedelta
            print("Contenido de horario:", horario)  # Imprimir el diccionario de cada horario

            # Obtener el valor de la clave 'hora', que es un objeto timedelta
            hora_timedelta = horario['hora']
            
            # Si 'hora_timedelta' es un objeto timedelta, convertirlo en una cadena de tiempo 'HH:MM:SS'
            total_seconds = int(hora_timedelta.total_seconds())  # Obtiene el total de segundos de timedelta
            horas = total_seconds // 3600  # Obtiene las horas
            minutos = (total_seconds % 3600) // 60  # Obtiene los minutos
            segundos = total_seconds % 60  # Obtiene los segundos
            horario_str = f"{horas:02}:{minutos:02}:{segundos:02}"  # Formato 'HH:MM:SS'

            horarios_formateados.append(horario_str)

        # Retornar la respuesta en formato JSON
        return jsonify({'horarios': horarios_formateados})






@app.route('/agendar', methods=['POST'])
def agendar():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        fecha = request.form['fecha']
        hora = request.form['hora']

        # Crear la sesión de pago con Stripe
        session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Cita de Abogado',
                    },
                    'unit_amount': 2000,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('pago_exitoso', _external=True, nombre=nombre, email=email, telefono=telefono, fecha=fecha, hora=hora),
            cancel_url=url_for('index', _external=True)
        )

        # Redirigir al cliente a la página de pago de Stripe
        return redirect(session.url, code=303)

@app.route('/pago_exitoso')
def pago_exitoso():
    # Aquí se obtienen los datos del cliente de la URL
    nombre = request.args.get('nombre')
    email = request.args.get('email')
    telefono = request.args.get('telefono')
    fecha = request.args.get('fecha')
    hora = request.args.get('hora')

    # Guardar los datos en la base de datos después de confirmar el pago
    with connection.cursor() as cursor:
        sql = 'INSERT INTO citas (nombre, email, telefono, fecha, hora) VALUES (%s, %s, %s, %s, %s)'
        cursor.execute(sql, (nombre, email, telefono, fecha, hora))
        # Actualizar el horario en la base de datos para marcarlo como no disponible
        cursor.execute("UPDATE horarios SET disponible = FALSE WHERE fecha = %s AND hora = %s", (fecha, hora))
        connection.commit()
    connection.commit()

    return render_template('success.html')
    

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Verifica si el usuario está autenticado
    if 'user' not in session:  # Cambiar 'logged_in' a 'user'
        return redirect(url_for('login'))  # Redirigir a la página de login
    
    if request.method == 'POST':
        fecha = request.form['fecha']
        hora = request.form['hora']
        
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO horarios (fecha, hora) VALUES (%s, %s)", (fecha, hora))
        connection.commit()

    # Obtener los horarios actuales
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM horarios where disponible= 1")
        horarios = cursor.fetchall()

    return render_template('admin.html', horarios=horarios)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validación sencilla de credenciales
        if username == 'attornyyield' and password == '123456':  # Cambia esto por tus credenciales
            session['user'] = username  # Cambiar 'logged_in' a 'user'
            return redirect(url_for('admin'))
        else:
            return "Credenciales incorrectas", 403

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(debug=True)
