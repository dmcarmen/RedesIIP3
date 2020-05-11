from appJar import gui
from PIL import Image, ImageTk
import cv2
import users
import control
import threading


class VideoClient(object):

    descubrimiento = None
    control = None
    video = None

    # Informacion del usuario
    nick = "usuario1"  # "usuario2"
    ip_address = "127.0.0.1"
    tcp_port = 49152  # 49154
    udp_port = 49153  # 49155
    password = "kk"
    protocols = "V0"

    # Informacion del destino
    dst_ip = None
    dst_port = None

    # Flags para saber si en llamada o en pausa
    flag_en_llamada = False
    flag_pause = False

    # Resolucion
    resol = None

    # Para parar de escuchar comandos de control
    thread = None
    stop_listening = False


    def __init__(self, window_size):
        """
            Nombre: __init__
            Descripcion: Constructor de la clase.
            Argumentos:
                -window_size: tamaño de la ventana
            Retorno: objecto VideoClient
        """

        # Creamos una variable que contenga el GUI principal
        self.app = gui("Redes2 - P2P", window_size)
        self.app.setGuiPadding(10)

        # Preparacion del interfaz
        self.app.addLabel("title", "Cliente Multimedia P2P - Redes2 ")
        self.app.addImage("video", "imgs/webcam.gif")

        # Registramos la funcion de captura de video
        # Esta misma funcion tambien sirve para enviar un video
        self.cap = cv2.VideoCapture(0)
        self.app.setPollTime(20)
        self.app.registerEvent(self.capturaVideo)

        # La ventana del otro video
        self.app.startSubWindow("Llamada")
        self.app.addImage("Llamada", "imgs/webcam.gif")
        self.app.stopSubWindow()
        self.app.hideSubWindow("Llamada")

        # Añadir los botones
        self.app.addButtons(["Conectar", "Pausar/Reanudar", "Colgar", "Salir"], self.buttonsCallback)

        # Barra de estado
        # Debe actualizarse con informacion util sobre la llamada (duracion, FPS, etc...)
        self.app.addStatusbar(fields=2)

        self.resol = '640x480'  # empezamos con la maxima por defecto

        # Creamos el servidor de descubrimiento y el objeto Control
        self.descubrimiento = users.UsersDescubrimiento()
        self.descubrimiento.register(self.nick, self.ip_address, self.tcp_port, self.password, self.protocols)
        self.control = control.Control(self, self.descubrimiento, self.tcp_port, self.udp_port)
        # Creamos el hilo para escuchar los comandos de control
        self.thread = threading.Thread(target=self.control.listening)
        self.thread.start()

    def start(self):
        """
            Nombre: start
            Descripcion: Funcion que inicializa la app.
            Argumentos: Ninguno
            Retorno: Ninguno
        """
        self.app.go()

    def capturaVideo(self):
        """
            Nombre: capturaVideo
            Descripcion: Funcion que captura el frame a mostrar en cada momento.
            Argumentos: Ninguno
            Retorno: Ninguno
        """
        # Capturamos un frame de la camara o del video
        ret, frame = self.cap.read()
        if ret is True:
            try:
                frame_ver = cv2.resize(frame, (640, 480))
                cv2_im = cv2.cvtColor(frame_ver, cv2.COLOR_BGR2RGB)
                img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))
                # Lo mostramos en el GUI
                self.app.setImageData("video", img_tk, fmt='PhotoImage')
            except:
                pass
            # Si estamos enviando video, enviamos el frame
            if self.video is not None and not self.flag_pause:
                self.video.enviar_frame(frame)
        # Si estamos reproduciendo un video y ya ha acabado, mostramos
        # y enviamos la foto inicial
        else:
            frame = cv2.imread("imgs/webcam.jpeg")
            photo = ImageTk.PhotoImage(Image.open("imgs/webcam.jpeg"))
            self.app.setImageData("video", photo, fmt='PhotoImage')

            if self.video is not None and not self.flag_pause:
                self.video.enviar_frame(frame)

    def setImageResolution(self, resolution):
        """
            Nombre: setImageResolution
            Descripcion: Funcion que establece la resolucion de la imagen capturada.
            Argumentos:
                -resolution: resolucion de la imagen
            Retorno: Ninguno
        """
        # Se establece la resolucion de captura de la webcam
        # Puede añadirse algun valor superior si la camara lo permite
        # pero no modificar estos
        if resolution == "LOW" and self.resol != "160x120":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
            self.resol = "160x120"
        elif resolution == "MEDIUM" and self.resol != "320x240":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            self.resol = "320x240"
        elif resolution == "HIGH" and self.resol != "640x480":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.resol = "640x480"

    def buttonsCallback(self, button):
        """
            Nombre: buttonsCallback
            Descripcion: Funcion que gestiona los callbacks de los botones.
            Argumentos:
                -button: boton pulsado
            Retorno: Ninguno
        """

        if button == "Salir":
            self.stop_listening = True
            # Salimos de la aplicacion
            self.app.stop()
        elif button == "Conectar":
            # Entrada del nick del usuario a conectar
            nick = self.app.textBox("Conexión",
                                    "Introduce el nick del usuario a buscar")
            info = self.descubrimiento.query(nick)
            self.dst_ip = info[1]
            self.dst_port = info[2]
            self.control.calling(nick, info[1], info[2])

        elif button == "Colgar":
            # Si nos encontramos en llamada, se finaliza
            if self.flag_en_llamada:
                self.control.call_end(self.nick, self.dst_ip, self.dst_port)
                self.dst_ip = None
                self.dst_port = None
        elif button == "Pausar/Reanudar":
            # Se comprueba que nos encontramos en llamada
            if self.flag_en_llamada:
                # Si esta en pausa, se reanuda la llamada
                if self.flag_pause:
                    self.control.call_resume(self.nick, self.dst_ip, self.dst_port)
                # Si no, se pausa la llamada
                else:
                    self.control.call_hold(self.nick, self.dst_ip, self.dst_port)


if __name__ == '__main__':
    vc = VideoClient("640x520")

    # Lanza el bucle principal del GUI
    # El control ya NO vuelve de esta funcion, por lo que todas las
    # acciones deberan ser gestionadas desde callbacks y threads
    vc.start()
