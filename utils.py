import os
import configparser

# Variables globales
token = ""
path_archivos = ""
headers = {}


def config_ini():
    """
        Nombre: config_ini
        Descripcion: Realiza la configuración inicial necesaria.
            Lee de ini.conf el token del usuario y el path para guardar archivos.
        Argumentos: Ninguno
        Retorno: Ninguno
    """
    global token, path_archivos

    # Leemos token.txt y lo guardamos en la variable global token
    config = configparser.ConfigParser()
    config.read('ini.conf')
    if 'token' in config['DEFAULT']:
        token = config['DEFAULT']['token']
    else:
        return

    # Guardamos el path de archivos y si no ponemos uno por defecto
    if 'path_archivos' in config['DEFAULT']:
        path_archivos = config['DEFAULT']['path_archivos']
    else:
        path_archivos = "Archivos/"

    # Si no existe path_archivos creamos la carpeta
    basedir = os.path.dirname(path_archivos)
    if not os.path.exists(basedir):
        os.makedirs(basedir)


def error(request):
    """
        Nombre: error
        Descripcion: Imprime el mensaje de error correspodiente recibido por una
            request.
        Argumentos:
            - request: respuesta de la peticion al servidor.
        Retorno: Ninguno
    """
    json = request.json()

    # Si el error esta definido imprimimos la informacion completa
    if "error_code" in json:
        print("Error {}: {} -> {}".format(json.get("http_error_code"), json.get("error_code"), json.get("description")))
    else:
        print("Error {}".format(request.status_code))
