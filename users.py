import socket

class Users_descubrimiento:
    url = 'vega.ii.uam.es'
    puerto = 8000
    buffer_tam = 2048
    socket = None

    def __init__(self):
        self.socket = self.create_socket_TCP()

    def send_recv(self, msg):
        try:
            self.socket.send(bytes(msg, 'utf-8'))
            msg = self.socket.recv(self.buffer_tam)
            msg = msg.decode('utf-8')
        except:
            print("Error de conexion.")
            return None
        return msg

    def create_socket_TCP(self):
        """
            Nombre: create_socket_TCP
            Descripcion: Funcion
            Argumentos:
                -nick:
            Retorno:
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Socket creado")
        except socket.error as err:
            print("La creación del socket falló: error {}".format(err))
            return None

        s.connect((self.url, self.puerto)) #TODO ctrl errores
        return s

    def quit(self):
        """
            Nombre: quit
            Descripcion: Funcion
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
            Descripcion: Funcion
            Argumentos:
                -nick: nick del usuario.
            Retorno:
        """
        msg = "REGISTER {} {} {} {} {}".format(nick, ip_address, port, password, protocols)

        msg = self.send_recv(msg)
        if msg == 'NOK WRONG_PASS' or None:
            print(msg) #TODO control de errores
        else:
            print(msg)

    def query(self, nick):
        """
            Nombre: query
            Descripcion: Funcion
            Argumentos:
                -nick: nick del usuario.
            Retorno:
        """
        msg = "QUERY {}".format(nick)
        msg = self.send_recv(msg)
        if msg == 'NOK USER_UNKNOWN' or None:
            print(msg) #TODO control de errores
        else:
            print(msg)
            user_info = msg.split(' ')
            user_info[4] = int(user_info[4])
            return user_info[2:] #TODO ver cuando used

    def list_users(self):
        """
            Nombre: list_users
            Descripcion: Funcion
            Argumentos:
            Retorno:
        """
        msg = self.send_recv("LIST_USERS")
        if msg == 'NOK USER_UNKNOWN' or None:
            print(msg) #TODO control de errores
        else:
            #TODO ver si drama de no entran
            n_users = int(msg.split(' ')[2])
            users = msg.split('#')
            # Si hay menos users hay que seguir pidiendo datetes
            while len(users) - 1 < n_users or msg[-1] != '#':
                msg = msg + self.socket.recv(self.buffer_tam).decode('utf-8')
                users = msg.split('#')

            print('Lista de {} usuarios:'.format(n_users))
            # primer usuario
            user1 = users[0].split(' ')[3:]
            print(' '.join(user1))
            # resto
            for u in users[1:]:
                print(u)

def prueba():
    bicho = Users_descubrimiento()
 #   bicho.register('holi', 1, 2, 3, 4)
    bicho.list_users()
    query = bicho.query('usuario1')
    print(query)
   # bicho.register('holi', 1, 2, 3, 4)
    #bicho.register('holi', 1, 2, 4, 4)
    #bicho.quit()

#prueba()
