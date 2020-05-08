import socket
import time

class Video:
    # Info general
    gui = None
    ext_ip = None
    socket_send = None
    socket_listen = None
    local_port = None
    ext_port = None
    n_orden = None

    # Constantes
    local_ip = "127.0.0.1"
    buffer_tam = 2048 #TODO no se que tam

    def __init__(self, gui, ip, local_port, ext_port):
        self.gui = gui
        self.ext_ip = ip
        self.local_port = local_port
        self.ext_port = ext_port
        self.n_orden = 0

        self.socket_send = self.create_sending_socket(ip, ext_port)

        self.socket_listen = self.create_sending_socket(local_ip, local_port)
        #self.socketListen.recvfrom()


    def create_socket(self, ip, port_udp):
        """
            Nombre: create_listen_socket
            Descripcion: Funcion
            Argumentos:
            Retorno:
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print("Socket UDP para enviar creado")
        except socket.error as err:
            print("La creación del socket UDP para enviar falló: error {}".format(err))
            return None

        s.bind((ip, port_udp)) #TODO ctrl errores y mirar si enviando too
        return s

    # Funciones para enviar mensajes
    def enviar_frame(self, frame, resol, fps):

        msg = '{}#{}#{}#{}#{}'.format(self.n_orden, time.time(), resol, fps,frame)
        #sendto
        self.socket_send.sendto(bytes(msg, 'utf-8'), (self.ext_ip, self.ext_port_udp)) #TODO maybe to_bytes el frame jaj
        self.n_orden += 1

    # Funciones para recibir mensajes
    def listening(self):
        while 1:  # TODO cuando acabar
            self.recibir_frame()

    def recibir_frame(self):
        msg = self.socket_listen.recvfrom(buffer_tam)
        msg = msg.split('#')


        encimg = msg[4].decode('utf-8')

        # Descompresión de los datos, una vez recibidos
        decimg = cv2.imdecode(np.frombuffer(encimg,np.uint8), 1)

        # Conversión de formato para su uso en el GUI
        cv2_im = cv2.cvtColor(decimg,cv2.COLOR_BGR2RGB)
        img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))
