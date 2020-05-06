import requests
import utils as u

urlIni = 'https://vega.ii.uam.es:8080/'


def register(nick, ip_address, port, password, protocols):
    """
        Nombre: register
        Descripcion: Funcion
        Argumentos:
            -nick:
        Retorno:
    """
    # Enviamos la peticion al servidor
    url = urlIni + 'register'
    args = {'nick': nick, 'ip_address': ip_address, 'port': port, 'password': password, 'protocols': protocols}
    try:
        r = requests.post(url, json=args)
    except requests.ConnectionError:
        print("Error de conexion")
        return

    # Si la peticion es correcta guardamos la clave privada del usuario e imprimimos su ID
    if r.status_code == requests.codes.ok:
        answer = r.json()
        nick = answer.get('nick')
        ts = answer.get('ts') # TODO que hacer con esto
        #print(r) #TODO te dan esto ya???
        print("S->C: OK WELCOME {} {}".format(nick, ts))
    else:
        u.error(r)


def query(nick):
    """
        Nombre: query
        Descripcion:
        Argumentos:
            -nick: nick del usuario.
        Retorno:
    """

    # Enviamos la peticion a la API
    url = urlIni + 'query'
    args = {'nick': nick} #TODO maybe es name?
    try:
        r = requests.post(url, json=args)
    except requests.ConnectionError:
        print("Error de conexion")
        return
    # Si es correcta imprimimos todas las coincidencias devueltas
    if r.status_code == requests.codes.ok:
        answers = r.json()
        nick = answer.get('nick')
        ip_address = answer.get('ip_address')
        port = answer.get('port')
        protocols = answer.get('protocols')
        print("{} {} {} {}:".format(nick, ip_address, port, protocols))
    else:
        u.error(r)


def list_users():
    """
        Nombre: list_users
        Descripcion:
        Argumentos: Ninguno
        Retorno:
    """

    # Envia la peticion a la API
    url = urlIni + 'list_users'
    try:
        r = requests.post(url)
    except requests.ConnectionError:
        print("Error de conexion")
        return

    # Si la peticion es correcta imprimimos el ID eliminado
    if r.status_code == requests.codes.ok:
        answers = r.json()
        i = 0
        for answer in answers:
            print("[{}] {} {} {} {}".format(i + 1, nick, ip_address, port, protocols))
            i += 1
    else:
        u.error(r)


def quit():
    """
        Nombre: quit
        Descripcion:
        Argumentos: Ninguno
        Retorno:
    """

    # Enviamos la peticion a la API
    url = urlIni + 'quit'#TODO check que esto funcione asi y en general
    args = {'userID': user_id}
    try:
        r = requests.post(url)
    except requests.ConnectionError:
        print("Error de conexion")
        return None

    if r.status_code == requests.codes.ok:
        print("oki")#TODO print lo que sea
    else:
        u.error(r)
        return None
