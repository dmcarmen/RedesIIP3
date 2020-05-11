import socket
import time
import queue
from PIL import Image, ImageTk
import numpy as np
import cv2
import threading


class Video:
    # Información general
    video_client = None
    gui = None
    socket_send = None
    socket_listen = None
    local_port = None
    ext_ip = None
    ext_port = None

    buffer_circ = None
    n_orden = None
    contador = None
    media = None

    # Constantes
    buffer_tam = 65536  # tamaño buffer recibir datos
    last_one = -1
    fps = 20

    def __init__(self, video_client, ip, local_port, ext_port):
        """
            Nombre: __init__
            Descripcion: Constructor de la clase.
            Argumentos:
                -video_client: objeto de la aplicación
                -ip: ip de la persona con la que contactamos
                -local_port: puerto udp propio
                -ext_port: puerto udp de la persona con la que contactamos
            Retorno: objecto Video
        """
        # Iniciamos las variables pasadas
        self.video_client = video_client
        self.gui = video_client.app
        self.ext_ip = ip
        self.local_port = local_port
        self.ext_port = ext_port

        #Iniciamos las variables propias de la clase
        self.n_orden = 0
        self.buffer_circ = queue.PriorityQueue(self.fps * 2)  # fps*2secs
        self.contador = 0
        self.media = 0

        # Iniciamos los sockets
        self.socket_send = self.create_socket()
        self.socket_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.socket_listen = self.create_socket()
        self.socket_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_listen.bind(('', local_port))


    def create_socket(self):
        """
            Nombre: create_listen_socket
            Descripcion: Funcion para crear un socket UDP.
            Argumentos:
            Retorno: socket si va bien, None si hay error
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print("Socket UDP creado")
        except socket.error as err:
            print("La creación del socket UDP para enviar falló: error {}".format(err))
            return None
        return s

    # Funciones para enviar mensajes
    def enviar_frame(self, frame):
        """
            Nombre: enviar_frame
            Descripcion: Funcion para enviar un frame al otro puerto de UDP.
            Argumentos:
                -frame: frame de foto a enviar (obtenido en la captura)
            Retorno:
        """
        # Compresión JPG al 50% de resolución (se puede variar)
        encode_param = [cv2.IMWRITE_JPEG_QUALITY, 50]
        result, encimg = cv2.imencode('.jpg', frame, encode_param)
        if result == False:
            print('Error al codificar imagen')
            return

        # Formamos el mensaje y lo enviamos
        msg = '{}#{}#{}#{}#'.format(self.n_orden, time.time(), self.video_client.resol, self.fps)
        msg = msg.encode() + encimg.tostring()
        self.socket_send.sendto(msg, (self.ext_ip, self.ext_port))
        self.n_orden += 1


    # Funciones para recibir mensajes
    def listening(self):
        """
            Nombre: listening
            Descripcion: Funcion que escucha en el puerto UDP hasta el fin de
                llamada. Al finalizar cierra los sockets.
            Argumentos:
            Retorno:
        """
        while not self.video_client.end_event:
            if not self.video_client.pause_event:
                self.recibir_frame()

        self.socket_listen.close()
        self.socket_send.close()

    def recibir_frame(self):
        """
            Nombre: recibir_frame
            Descripcion: Función que recibe un frame de la otra parte y lo guarda
                en el buffer circular.
            Argumentos:
            Retorno:
        """
        msg, ip = self.socket_listen.recvfrom(self.buffer_tam)

        # Dividimos el mensaje en las 5 partes (4 primeras el 'header' y última la img)
        msg = msg.split(b'#', 4)
        encimg = msg[4]
        # Descompresión de los datos, una vez recibidos
        decimg = cv2.imdecode(np.frombuffer(encimg, np.uint8), 1)

        # Conversión de formato para su uso en el GUI
        cv2_im = cv2.cvtColor(decimg, cv2.COLOR_BGR2RGB)
        img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

        # Aplicamos medidas de medidas de descongestión cada 100 mensajes
        ts = float(msg[1].decode())
        dif = time.time() - ts
        self.contador = 1 + self.contador
        self.media = self.media + dif
        if self.contador == 100:
            self.medidas_descongestion(self.media/100)
            self.contador = 0
            self.media = 0

        # Añadimos al buffer circular la imagen si es posterior a la ultima reproducida
        n = int(msg[0]) # número de orden del mensaje recibido
        if  self.last_one < n:
            self.last_one = n
            d = {'ts': ts, 'resol': msg[2].decode(), 'fps': int(msg[3].decode()), 'img_tk': img_tk}
            self.buffer_circ.put(n, d))

    def medidas_descongestion(self, media):
        """
            Nombre: medidas_descongestion
            Descripcion: Función que ajusta la resolución según el retraso de los
                paquetes.
            Argumentos:
                -media: media de retraso cada 100 paquetes
            Retorno:
        """
        if media < 2.0:
            self.video_client.setImageResolution('HIGH')
        elif media < 5.0:
            self.video_client.setImageResolution('MEDIUM')
        else:
            self.video_client.setImageResolution('LOW')

    def reproducir(self):
        """
            Nombre: reproducir
            Descripcion: Función que reproduce los frames del buffer circular
                cuando está en llamada.
            Argumentos:
            Retorno:
        """
        # No empezamos a reproducir hasta que al menos 1/4 del buffer esté lleno
        while self.buffer_circ.qsize() < self.fps//2:
            continue
        while not self.video_client.end_event:
            if not self.video_client.pause_event:
                # Si el buffer está vacío esperamos a que llegue algún frame
                if self.buffer_circ.empty():
                    continue

                # Cogemos el siguiente elemento de la cola
                d = self.buffer_circ.get()[1]
                img_tk = d.get('img_tk')

                # Cambiamos la resolución de la segunda pantalla a la de la img
                # y la mostramos
                resol = d.get('resol').split('x')
                self.gui.showSubWindow("2")
                self.gui.setImageSize("El otro", resol[0], resol[1])
                self.gui.setImageData("El otro", img_tk, fmt='PhotoImage')

        # Al terminar la llamada escondemos la segunda evntana
        photo = ImageTk.PhotoImage(Image.open("imgs/webcam.gif"))
        self.gui.setImageData("El otro", photo , fmt='PhotoImage')
        self.gui.hideSubWindow("2")

    def llamada(self):
        """
            Nombre: llamada
            Descripcion: Función que lanza el thread de escucha y reproduccion
                al empezar una llamada.
            Argumentos:
            Retorno:
        """
        thread_listen = threading.Thread(target=self.listening)
        thread_listen.start()

        thread_play = threading.Thread(target=self.reproducir)
        thread_play.start()
