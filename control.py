import socket
import video


class Control:
    # Informacion general
    video_client = None
    gui = None
    users_descubrimiento = None
    socket_listen = None
    udp_port = None

    # Constantes
    max_conexiones = 5

    def __init__(self, video_client, users_descubrimiento, tcp_port, udp_port):
        """
            Nombre: __init__
            Descripcion: Constructor de la clase.
            Argumentos:
                -video_client: objeto de la aplicacion
                -users_descubrimiento: objeto del server de descubrimiento
                -tcp_port: puerto tcp
                -udp_port: puerto udp
            Retorno: objecto Control
        """
        self.video_client = video_client
        self.gui = video_client.app
        self.users_descubrimiento = users_descubrimiento
        self.udp_port = udp_port

        # Creamos el socket para recibir mensajes del resto de usuarios
        self.socket_listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_listen.bind(("", tcp_port))
        self.socket_listen.listen(self.max_conexiones)

    def send_msg(self, msg, dst_ip, dst_port):
        """
            Nombre: send_msg
            Descripcion: Funcion que envia un mensaje a (dst_ip, dst_port).
            Argumentos:
                -msg: mensaje
                -dst_ip: ip destino
                -dst_port: puerto destino
            Retorno: Ninguno
        """
        socket_send = socket.socket()
        socket_send.connect((dst_ip, dst_port))
        socket_send.send(bytes(msg, 'utf-8'))
        socket_send.close()

    # FUNCIONES PARA ENVIAR MENSAJES DE CONTROL

    def calling(self, nick, dst_ip, dst_port):
        """
            Nombre: calling
            Descripcion: Funcion que envia un mensaje para establecer llamada.
            Argumentos:
                -nick: nick de tu usuario
                -dst_ip: ip destino
                -dst_port: puerto destino
            Retorno: Ninguno
        """
        self.gui.setStatusbar("Llamando a {}...".format(nick), 0)
        msg = "CALLING {} {}".format(self.video_client.nick, self.udp_port)
        self.send_msg(msg, dst_ip, dst_port)

    def call_hold(self, nick, dst_ip, dst_port):
        """
            Nombre: call_hold
            Descripcion: Funcion que envia un mensaje para parar la llamada.
            Argumentos:
                -nick: nick de tu usuario
                -dst_ip: ip destino
                -dst_port: puerto destino
            Retorno: Ninguno
        """
        msg = "CALL_HOLD {}".format(nick)
        self.send_msg(msg, dst_ip, dst_port)
        self.gui.setStatusbar("Llamada pausada.", 0)
        self.video_client.flag_pause = True

    def call_resume(self, nick, dst_ip, dst_port):
        """
            Nombre: call_resume
            Descripcion: Funcion que envia un mensaje para reanudar la llamada
            Argumentos:
                -nick: nick de tu usuario
                -dst_ip: ip destino
                -dst_port: puerto destino
            Retorno: Ninguno
        """
        msg = "CALL_RESUME {}".format(nick)
        self.send_msg(msg, dst_ip, dst_port)
        self.gui.setStatusbar("En llamada.", 0)
        self.video_client.flag_pause = False

    def call_end(self, nick, dst_ip, dst_port):
        """
            Nombre: call_end
            Descripcion: Funcion que envia un mensaje para terminar la llamada
            Argumentos:
                -nick: nick de tu usuario
                -dst_ip: ip destino
                -dst_port: puerto destino
            Retorno: Ninguno
        """
        msg = "CALL_END {}".format(nick)
        self.send_msg(msg, dst_ip, dst_port)
        self.gui.setStatusbar("Llamada finalizada.", 0)
        self.video_client.flag_en_llamada = False
        self.video_client.video = None

    # FUNCIONES PARA RECIBIR MENSAJES Y ACTUAR EN CONSECUENCIA

    def calling_handler(self, nick, dst_udp_port):
        """
            Nombre: calling_handler
            Descripcion: Funcion que responde a una solicitud de llamada.
            Argumentos:
                -nick: nick del usuario
                -dst_udp_port: puerto udp destino
            Retorno: Ninguno
        """
        # Hallamos la informacion del usuario
        user_info = self.users_descubrimiento.query(nick)
        dst_ip = user_info[1]
        dst_port = user_info[2]

        # Si no estamos en llamada
        if not self.video_client.flag_en_llamada:
            # Pregunta si quieres aceptar la llamada
            res = self.gui.yesNoBox("Llamada entrante", nick)
            if res:
                msg = "CALL_ACCEPTED {} {}".format(self.video_client.nick, self.udp_port)
                self.send_msg(msg, dst_ip, dst_port)
                self.gui.setStatusbar("En llamada.", 0)

                # Actualizamos la informacion necesaria en la app
                self.video_client.flag_en_llamada = True
                self.video_client.dst_ip = dst_ip
                self.video_client.dst_port = dst_port

                # Comenzamos la llamada
                self.video_client.video = video.Video(self.video_client, dst_ip,
                                                      int(self.udp_port), int(dst_udp_port))
                self.video_client.video.llamada()

            else:
                msg = "CALL_DENIED {}".format(nick)
                self.send_msg(msg, dst_ip, dst_port)

        else:
            msg = "CALL_BUSY"
            self.send_msg(msg, dst_ip, dst_port)

    def call_hold_handler(self):
        """
            Nombre: call_hold_handler
            Descripcion: Funcion que pausa la llamada.
            Argumentos: Ninguno
            Retorno: Ninguno
        """
        if self.video_client.flag_en_llamada:
            self.gui.setStatusbar("Llamada pausada.", 0)
            self.video_client.flag_pause = True

    def call_resume_handler(self):
        """
            Nombre: call_resume_handler
            Descripcion: Funcion que reanuda la llamada.
            Argumentos: Ninguno
            Retorno: Ninguno
        """
        if self.video_client.flag_en_llamada:
            self.gui.setStatusbar("En llamada.", 0)
            self.video_client.flag_pause = False

    def call_end_handler(self):
        """
            Nombre: call_end_handler
            Descripcion: Funcion que finaliza la llamada.
            Argumentos: Ninguno
            Retorno: Ninguno
        """
        if self.video_client.flag_en_llamada:
            self.gui.setStatusbar("Llamada finalizada.", 0)
            self.video_client.flag_en_llamada = False
            self.video_client.video = None

    def call_accepted_handler(self, nick, dst_udp_port):
        """
            Nombre: call_end_handler
            Descripcion: Funcion que comienza una llamada tras ser aceptada.
            Argumentos:
                -nick: nick del usuario
                -dst_udp_port: puerto udp destino
            Retorno: Ninguno
        """
        if not self.video_client.flag_en_llamada:
            user_info = self.users_descubrimiento.query(nick)
            dst_ip = user_info[1]

            self.gui.infoBox("Información de llamada", "{} ha aceptado tu llamada.".format(nick))
            self.gui.setStatusbar("En llamada.", 0)

            # Actualizamos la informacion necesaria en la app
            self.video_client.flag_en_llamada = True
            self.video_client.dst_ip = dst_ip
            self.video_client.dst_port = user_info[2]

            # Comenzamos la llamada
            self.video_client.video = video.Video(self.video_client, dst_ip, int(self.udp_port), int(dst_udp_port))
            self.video_client.video.llamada()

    def call_denied_handler(self, nick):
        """
            Nombre: call_denied_handler
            Descripcion: Funcion que informa de que la llamada ha sido rechazada.
            Argumentos:
                -nick: nick del usuario
            Retorno: Ninguno
        """
        self.gui.infoBox("Información de llamada", "{} no ha aceptado tu llamada.".format(nick))
        self.gui.setStatusbar("", 0)

    def call_busy_handler(self):
        """
            Nombre: call_busy_handler
            Descripcion: Funcion que informa de que el usuario ya esta en llamada.
            Argumentos: Ninguno
            Retorno: Ninguno
        """
        self.gui.infoBox("Información de llamada", "El usuario se encuentra en una llamada.")
        self.gui.setStatusbar("", 0)

    # FUNCIONES PARA RECIBIR Y PROCESAR PETICIONES

    def listening(self):
        """
            Nombre: listening
            Descripcion: Funcion que recibe mensajes de control.
            Argumentos: Ninguno
            Retorno: Ninguno
        """
        while 1:
            host, port = self.socket_listen.accept()
            msg = host.recv(1024)

            if msg:
                msg = msg.decode('utf-8')
                print("Mensaje recibido:" + msg)
                # Procesamos la peticion
                self.procesar_peticion(msg)

    def procesar_peticion(self, msg):
        """
            Nombre: procesar_peticion
            Descripcion: Funcion que procesa mensajes de control.
            Argumentos:
                -msg: mensaje a procesar
            Retorno: Ninguno
        """
        campos = msg.split(" ")
        comando = campos[0]

        # Buscamos el comando recibido y llamamos al handler correspondiente.
        if comando == "CALLING":
            if len(campos) == 3:
                self.calling_handler(campos[1], campos[2])
            else:
                print("Mensaje incorrecto")

        elif comando == "CALL_HOLD":
            if len(campos) == 2:
                self.call_hold_handler()
            else:
                print("Mensaje incorrecto")

        elif comando == "CALL_RESUME":
            if len(campos) == 2:
                self.call_resume_handler()
            else:
                print("Mensaje incorrecto")

        elif comando == "CALL_END":
            if len(campos) == 2:
                self.call_end_handler()
            else:
                print("Mensaje incorrecto")

        elif comando == "CALL_ACCEPTED":
            if len(campos) == 3:
                self.call_accepted_handler(campos[1], campos[2])
            else:
                print("Mensaje incorrecto")

        elif comando == "CALL_DENIED":
            if len(campos) == 2:
                self.call_denied_handler(campos[1])
            else:
                print("Mensaje incorrecto")

        elif comando == "CALL_BUSY":
            if len(campos) == 1:
                self.call_busy_handler()
            else:
                print("Mensaje incorrecto")
        else:
            print("Mensaje incorrecto")
