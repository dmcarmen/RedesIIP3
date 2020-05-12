import socket


class UsersDescubrimiento:
    # Informacion general
    socket = None

    # Constantes
    url = 'vega.ii.uam.es'
    puerto = 8000
    buffer_tam = 2048

    def __init__(self):
        """
            Nombre: __init__
            Descripcion: Constructor de la clase. Crea una conexion con el DS.
            Argumentos:
            Retorno: objecto Users_descubrimiento
        """
        self.socket = self.create_socket_tcp()

    def create_socket_tcp(self):
        """
            Nombre: create_socket_TCP
            Descripcion: Funcion para crear un socket TCP.
            Argumentos:
            Retorno: el socket si todo va bien, None si no
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Socket de comunicación con DS creado")
        except socket.error as err:
            print("La creación del socket falló: error {}".format(err))
            return None

        s.connect((self.url, self.puerto))
        return s

    def send_recv(self, msg):
        """
            Nombre: send_recv
            Descripcion: Funcion para enviar un mensaje al DS y recibir su respuesta.
            Argumentos:
                - msg: mensaje a enviar
            Retorno: mensaje recibido decodificado, None si falla
        """
        try:
            self.socket.send(bytes(msg, 'utf-8'))
            msg = self.socket.recv(self.buffer_tam)
            msg = msg.decode('utf-8')
        except Exception as e:
            print("Error de conexion: ", e)
            return None
        if msg == None:
            print('Error al recibir el mensaje')
        return msg

    def quit(self):
        """
            Nombre: quit
            Descripcion: Funcion para terminar la conexion con el DS.
            Argumentos:
            Retorno:
        """
        msg = self.send_recv('QUIT')
        if msg is not None:
            print(msg)
            self.socket.close()

    def register(self, nick, ip_address, port, password, protocols):
        """
            Nombre: register
            Descripcion: Funcion que regista/inicia sesión de un usuario
            Argumentos:
                -nick: nick del usuario.
                -ip_address: IP del usuario.
                -port: puerto UDP del usuario.
                -password: contraseña.
                -protocols: protocolos que soporta.
            Retorno: mensaje recibido
        """
        msg = "REGISTER {} {} {} {} {}".format(nick, ip_address, port, password, protocols)

        msg = self.send_recv(msg)
        if msg:
            print(msg)
            return msg

    def query(self, nick):
        """
            Nombre: query
            Descripcion: Funcion que pregunta por un usuario al DS.
            Argumentos:
                -nick: nick del usuario.
            Retorno: lista con nick, ip_address, port y protocols del usuario buscado
        """
        msg = "QUERY {}".format(nick)
        msg = self.send_recv(msg)
        if msg:
            print(msg)
            user_info = msg.split(' ')
            user_info[4] = int(user_info[4])  # guardamos el puerto como int
            return user_info[2:]

    def list_users(self):
        """
            Nombre: list_users
            Descripcion: Funcion que pide la lista de usuarios del DS.
            Argumentos:
            Retorno: diccionario cuyas keys son los usuarios y los valores
                otro diccionario con la ip y el puerto
        """
        msg = self.send_recv("LIST_USERS")
        if msg == 'NOK USER_UNKNOWN' or None:
            print(msg)
        else:
            # Vemos el numero de usuarios totales para seguir leyendo o no
            n_users = int(msg.split(' ')[2])
            users = msg.split('#')
            # Si hay menos users hay que seguir pidiendo datos
            while len(users) - 1 < n_users or msg[-1] != '#':
                msg = msg + self.socket.recv(self.buffer_tam).decode('utf-8')
                users = msg.split('#')

            print('Lista de {} usuarios:'.format(n_users))
            d = {}
            # Quitamos la primera parte del mensaje para obtener el primer usuario
            user1 = users[0].split(' ')[3:]
            d[user1[0]] = {'ip': user1[1], 'puerto': user1[2]}
            print(' '.join(user1))
            # El resto aparecen normal
            for u in users[1:]:
                print(u)
                u2 =u.split(' ')
                if len(u2) == 4:
                    d[u2[0]] = {'ip': u2[1], 'puerto': u2[2] }
            return d
