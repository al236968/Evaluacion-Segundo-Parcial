from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory,
    Response
)

from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

import json
import csv
import io
from pathlib import Path


# =====================================================
# APLICACIÓN FLASK
# =====================================================

app = Flask(__name__)

app.secret_key = "seguridad_veterinaria_2026_clave_secreta"


# =====================================================
# USUARIOS
# =====================================================

USUARIOS = {

    "frida":
    "scrypt:32768:8:1$YhRRY24wjtNXEq4e$5febac1ad1f1b3b4ee94ed6e5793aa78c9ca58e3c2650083232c4ebd5a398887cff8f015f8e57ca18e27779274dc21c62ac1ac36b3274778822733e65966fa47",

    "empleado2":
    "scrypt:32768:8:1$nwuDhQ4VJtPH2RHX$1015fc453e2168ba489e1bac190b4c703f3a40ad5bf9e946b25f1f7e6ff52cdff62bb46b03518ec9563b28f5b90d27070316d4cb2097e2e33246d7c3fbb7f9f4"
}


# =====================================================
# CARPETAS Y ARCHIVOS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

FOTOS_DIR = BASE_DIR / "fotos"

PACIENTES_FILE = BASE_DIR / "pacientes.json"


# Crear carpeta de fotos si no existe

FOTOS_DIR.mkdir(exist_ok=True)


# =====================================================
# CARGAR PACIENTES
# =====================================================

def cargar_pacientes():

    if not PACIENTES_FILE.exists():

        return []

    try:

        with open(
            PACIENTES_FILE,
            "r",
            encoding="utf-8"
        ) as archivo:

            return json.load(archivo)

    except json.JSONDecodeError:

        return []


# =====================================================
# GUARDAR PACIENTES
# =====================================================

def guardar_pacientes(pacientes):

    with open(
        PACIENTES_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            pacientes,
            archivo,
            ensure_ascii=False,
            indent=4
        )


# =====================================================
# MOSTRAR FOTOGRAFÍAS
# =====================================================

@app.route("/fotos/<nombre>")
def foto(nombre):

    return send_from_directory(
        FOTOS_DIR,
        nombre
    )


# =====================================================
# LOGIN
# =====================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        usuario = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        # Buscar hash correspondiente al usuario

        hash_guardado = USUARIOS.get(
            usuario
        )


        # Verificar usuario y contraseña

        if (
            hash_guardado
            and check_password_hash(
                hash_guardado,
                password
            )
        ):

            session["logged_in"] = True

            session["usuario"] = usuario

            return redirect(
                url_for("index")
            )


        return render_template(
            "login.html",
            error="Usuario o contraseña incorrectos"
        )


    return render_template(
        "login.html",
        error=None
    )


# =====================================================
# PÁGINA PRINCIPAL
# =====================================================

@app.route("/")
def index():

    # Verificar que exista una sesión activa

    if not session.get("logged_in"):

        return redirect(
            url_for("login")
        )


    pacientes = cargar_pacientes()


    return render_template(
        "index.html",
        usuario=session.get("usuario"),
        pacientes=pacientes
    )


# =====================================================
# REGISTRAR NUEVO PACIENTE
# =====================================================

@app.route(
    "/nuevo_paciente",
    methods=["POST"]
)
def nuevo_paciente():

    # Verificar sesión

    if not session.get("logged_in"):

        return redirect(
            url_for("login")
        )


    pacientes = cargar_pacientes()


    # =================================================
    # DATOS DEL PACIENTE
    # =================================================

    nombre = request.form.get(
        "nombre",
        ""
    ).strip()


    tipo = request.form.get(
        "tipo",
        ""
    ).strip()


    servicio = request.form.get(
        "servicio",
        ""
    ).strip()


    fecha = request.form.get(
        "fecha",
        ""
    ).strip()


    hora = request.form.get(
        "hora",
        ""
    ).strip()


    costo = request.form.get(
        "costo",
        ""
    ).strip()


    # =================================================
    # VALIDACIÓN BÁSICA
    # =================================================

    if (
        not nombre
        or not tipo
        or not servicio
        or not fecha
        or not hora
        or not costo
    ):

        return redirect(
            url_for("index")
        )


    # =================================================
    # FOTOGRAFÍA
    # =================================================

    archivo = request.files.get(
        "foto"
    )

    nombre_foto = ""


    if archivo and archivo.filename:

        nombre_foto = secure_filename(
            archivo.filename
        )

        archivo.save(
            FOTOS_DIR / nombre_foto
        )


    # =================================================
    # CREAR REGISTRO
    # =================================================

    paciente = {

        "nombre": nombre,

        "tipo": tipo,

        "servicio": servicio,

        "fecha": fecha,

        "hora": hora,

        "costo": costo,

        "foto": nombre_foto

    }


    pacientes.append(
        paciente
    )


    guardar_pacientes(
        pacientes
    )


    return redirect(
        url_for("index")
    )


# =====================================================
# CONSULTAR FICHA DEL PACIENTE
# =====================================================

@app.route(
    "/paciente/<int:indice>"
)
def paciente(indice):

    # Verificar sesión

    if not session.get("logged_in"):

        return redirect(
            url_for("login")
        )


    pacientes = cargar_pacientes()


    # Verificar que el paciente exista

    if (
        indice < 0
        or indice >= len(pacientes)
    ):

        return redirect(
            url_for("index")
        )


    paciente_seleccionado = pacientes[
        indice
    ]


    return render_template(
        "paciente.html",
        paciente=paciente_seleccionado,
        indice=indice
    )


# =====================================================
# ELIMINAR PACIENTE
# =====================================================

@app.route(
    "/eliminar/<int:indice>",
    methods=["POST"]
)
def eliminar_paciente(indice):

    # Verificar sesión

    if not session.get("logged_in"):

        return redirect(
            url_for("login")
        )


    pacientes = cargar_pacientes()


    if (
        indice >= 0
        and indice < len(pacientes)
    ):

        pacientes.pop(
            indice
        )

        guardar_pacientes(
            pacientes
        )


    return redirect(
        url_for("index")
    )


# =====================================================
# EXPORTAR DATOS A CSV
# =====================================================

@app.route("/exportar")
def exportar():

    # Verificar sesión

    if not session.get("logged_in"):

        return redirect(
            url_for("login")
        )


    pacientes = cargar_pacientes()


    # Crear archivo CSV en memoria

    salida = io.StringIO()


    escritor = csv.writer(
        salida
    )


    # Encabezados

    escritor.writerow([
        "Nombre",
        "Tipo de animal",
        "Servicio",
        "Fecha",
        "Hora",
        "Costo",
        "Fotografía"
    ])


    # Datos

    for paciente in pacientes:

        escritor.writerow([

            paciente.get(
                "nombre",
                ""
            ),

            paciente.get(
                "tipo",
                ""
            ),

            paciente.get(
                "servicio",
                ""
            ),

            paciente.get(
                "fecha",
                ""
            ),

            paciente.get(
                "hora",
                ""
            ),

            paciente.get(
                "costo",
                ""
            ),

            paciente.get(
                "foto",
                ""
            )

        ])


    contenido = salida.getvalue()


    # BOM para que Excel reconozca correctamente
    # acentos y caracteres especiales

    contenido = "\ufeff" + contenido


    return Response(

        contenido,

        mimetype="text/csv",

        headers={

            "Content-Disposition":
            "attachment; filename=pacientes_veterinaria.csv"

        }

    )


# =====================================================
# CERRAR SESIÓN
# =====================================================

@app.route("/logout")
def logout():

    session.clear()


    return redirect(
        url_for("login")
    )


# =====================================================
# EJECUTAR FLASK
# =====================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )