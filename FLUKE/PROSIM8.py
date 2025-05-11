"""
  _____  _____   ____   _____ _____ __  __    ___           _____  _____  _______      ________ _____  
 |  __ \|  __ \ / __ \ / ____|_   _|  \/  |  / _ \         |  __ \|  __ \|_   _\ \    / /  ____|  __ \ 
 | |__) | |__) | |  | | (___   | | | \  / | | (_) |        | |  | | |__) | | |  \ \  / /| |__  | |__) |
 |  ___/|  _  /| |  | |\___ \  | | | |\/| |  > _ <         | |  | |  _  /  | |   \ \/ / |  __| |  _  / 
 | |    | | \ \| |__| |____) |_| |_| |  | | | (_) |        | |__| | | \ \ _| |_   \  /  | |____| | \ \ 
 |_|    |_|  \_\\____/|_____/|_____|_|  |_|  \___/         |_____/|_|  \_\_____|   \/   |______|_|  \_\
                                                                                                                                                                                                                                                                                                                                                                             
prosim8.py - Driver para control remoto de ProSim 8 (Fluke Biomedical)
Versión 1.2.0

Este módulo implementa la clase PROSIM8 para gestionar la comunicación
con un simulador de paciente ProSim 8 a través de un puerto serie USB.
Permite poner el equipo en modo remoto, configurar parámetros fisiológicos
(ECG, NIBP, SpO₂, ritmo cardíaco, arritmias, estimulación, etc.), y
manejar la conexión de forma robusta con timeouts y reintentos básicos.
"""
import serial
from typing import Optional
import numpy
from time import sleep

__company__ = "Feas Electronica"
__author__ = "Juan Cruz Noya & Julian Font"
__version__ = "1.2.0"
__country__ = "Argentina"

class PROSIM8:
    """
    Clase para controlar el simulador ProSim 8 vía puerto serie.

    Métodos principales:
    - Abrir/cerrar conexión serial:                     connect()/disconnect()
    - Cambiar entre modo remoto y local:                remote()/local(): 
    - Configurar ritmo sinusal:                         setHeartRate(), NormalRate()
    - Ajustar señales ECG:                              setDeviation(), setECGAmplitude(), setArtifact(), etc.
    - Métodos de arritmias:                             setPreVentricularArrhythmia(), setSupArrhythmia(), VentricularArrhythmia(), ConductionArrythmia().
    - Métodos de marcapasos:                            setPacerPolarity(), setPacerAmplitude(), setPacerWidth(), setPacerChamber(), setPacerPulse().
    - Simular fibrilación y taquicardia ventricular:    setFibrilation(), setMonovtach()

    Ejemplo de uso básico:
        ps8 = PROSIM8(port="COM11")
        ps8.connect()
        ps8.setHeartRate(70)
        ps8.NormalRate()
        ...
        ps8.disconnect()
    """
    def __init__(self,port,debug=False,baudrate=115200):
        
        self.port = port
        self.baudrate = baudrate
        self.debug = debug
        self.HEARTRATE = 60
        self.MODE = "ADULTO"
        self.LEAD_ARTIFACT = "ALL"
        self.LEAD_SIZE = "025"
        self.SIDE = "Left"
        self.PACER_POLARITY = "P"
        self.PACER_AMP = "010"
        self.PACER_WIDTH = "1.0"
        self.PACER_CHAMBER = "A"
        self.FIB_GRANULARITY = "COARSE"
        self.con: Optional[serial.Serial] = None
    def connect(self):
        """
        CONECTA PROSIM8 CON PUERTO SERIE\n
        DATOS:\n
        serial.STOPBITS_ONE = 1\n
        serial.PARITY_NONE = 'None'\n
        """
        if self.con is not None and self.con.is_open:
            return
        try:
            self.con = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                bytesize=8,
                xonxoff=False,
                timeout=1
            )
            self.remote()
        except serial.SerialException as e:
            self.con = None
            raise ConnectionError(f"Error de conexión: {e}")
        
    def remote(self):
        self.sendCommand(cmd="REMOTE")


    def disconnect(self):
        """
        DESCONECTA PROSIM8 CON PUERTO SERIE\n
        """
        if self.con is not None:
            if self.con.is_open:
                self.con.close()
            self.con = None

    def _format_int(self, value, width= 3):
        try:
            iv = int(value)
            return str(iv).zfill(width)
        except (ValueError, TypeError):
            return str(value)

    def _format_decimal(self, value, int_digits=2, dec_digits=2):
        """
        Formatea un número decimal con dígitos fijos antes y después del punto.
        """
        try:
            fv = float(value)
            fmt = f"{{:0{int_digits + 1 + dec_digits}.{dec_digits}f}}"
            return fmt.format(fv)
        except (ValueError, TypeError):
            return str(value)
        
    
    def sendCommand(self, cmd):
        if self.con is None or not self.con.is_open:
            raise serial.SerialException("Puerto serie no está conectado")
        
        # Formatear número a 3 dígitos si el comando contiene un "="
        if '=' in cmd:
            key, value = cmd.split('=', 1)
            if '.' in value:
                value = self._format_decimal(value, int_digits=2, dec_digits=2)
            elif value.isdigit():
                value = self._format_int(value, width=3)
            cmd = f"{key}={value}"
        
        cmd = cmd + "\r"
        self.con.write(cmd.encode('utf-8'))  # type: ignore
        if self.debug:
            print(f"Comando enviado: {cmd}")

        if self.con is None or not self.con.is_open:
            raise serial.SerialException("Puerto serie no está conectado")
        raw = self.con.readline()  # type: ignore
        try:
            if self.debug:
                print(f"Status recibido: {raw.decode('utf-8').strip()}")
            return
        except UnicodeDecodeError:
            if self.debug:
                print(f"Status recibido: {raw.decode('latin1').strip()}")
            return




#*****************************************************************ECG**********************************************************************
    def setPacerPolarity(self,polarity):
        self.PACER_POLARITY = polarity
    
    def setPacerAmplitude(self,ampl):

        self.PACER_AMP = ampl

    def setPacerWidth(self,width):
        self.PACER_WIDTH = width

    def setHeartRate(self,rate):
        """
        SETEA LA FRECUENCIA DE LATIDOS\n
        :rate: 10 - 360\n
        """
        if int(rate)<10:
            print("Valor por debajo del limite")
            self.HEARTRATE=10
        elif int(rate)>360:
            print("Valor por encima del limite")
            self.HEARTRATE = 360
        else:
            print(f"Se setea el valor frecuencia cardiaca en: {int(rate)}")
            self.HEARTRATE = int(rate)

    def setMode(self,mode):
        """
        SETEA EL MODO\n
        :mode: ADULTO, NEO,.... y los que sean necesarios\n
        """

        self.MODE =mode

    def NormalRate(self):
        """
        Se encarga de enviar el comando para configurar el control normal de la señal cardiaca\n
        """
        cmd = f"NSRA={self.HEARTRATE}"
        self.sendCommand(cmd)


    def truncar_dos_decimales(self,valor):
        return int(valor * 100) / 100

    def setDeviation(self,param="0.00"):
        """
        Setea desviacion de la linea base\n
        :param:
        param: valor que puede ir desde:\n
        ± 0.00 a 0.05 a 0.01mV de paso\n
        ± 0.10 a 0.80 a 0.10mV de paso
        """ 
        #En este caso particular como es un valor "numerico" puedo determinar si el valor ingresado tiene forma de valor flotante
        
        _float_param = float(param)
        try:
            if -0.05<=_float_param<= 0.05:
                _float_param = self.truncar_dos_decimales(valor=_float_param)
                param = str(_float_param)
            elif (0.10 <= _float_param <= 0.80 or -0.80 <= _float_param <= -0.10):
                # Solo aceptar si es múltiplo de 0.10 exacto
                if round(_float_param % 0.10, 8) == 0:
                    param = str(_float_param)
            else:
                print("ERR-150")
                print("El formato ingresado es incorrecto")
                param = "0.00"
        except:
            print("ERR-151")
            print("El formato ingresado es incorrecto")
            param = "0.00"

        cmd=f"STDEV={param}"
        self.sendCommand(cmd)
    
    def setECGAmplitude(self,param="1.00"):
        """
        Setea la amplitud del ECG\n
        
        """
        #No me voy a gastar en esta instancia en poner la amplitud correcta, se hace muy largo;
        #Se tiene que saber que entre 0.05 a 0.45; saltos de 0.05mV;
        #Saltos de 0.50 a 5.00 saltos de 0.25mV
        cmd=f"ECGAMPL={param}"
        self.sendCommand(cmd)
    
    def setArtifact(self,param="OFF"):
        """
        Funcion que setea el tipo de artefacto\n
        :param:
        DIC: El diccionario va a tener una cantidad de posibles valores para que la funcion tenga un accionar correcto\n
        """

        dic_artifact={
            "50":"50",
            "60": "60",
            "50HZ":"50",
            "50Hz":"50",
            "60HZ": "60",
            "60Hz": "60",
            "60hz": "60",
            "50hz": "50",
            "Musc": "MSC",
            "MUSC": "MSC",
            "musc": "MSC",
            "MUSCULAR": "MSC",
            "muscular": "MSC",
            "MSC": "MSC",
            "WANDERING": "WAND",
            "BASELINE": "WAND",
            "wandering": "WAND",
            "wand": "WAND",
            "base": "WAND",
            "wanderingBaseline":"WAND",
            "WanderingBaseline":"WAND",
            "RESP":"RESP",
            "resp":"RESP",
            "Resp":"RESP",
            "RESPIRATORIA":"RESP",
            "respiratoria":"RESP"
        }

        try:
            param = dic_artifact[param]
        except:
            param = param
        
        #configura
        cmd = f"EART={param}"
        self.sendCommand(cmd)



    def setArtifactLead(self,lead):

        self.LEAD_ARTIFACT = "LEAD"
        cmd = f"EARTLD={self.LEAD_ARTIFACT}"
        self.sendCommand(cmd)

    def SetArtifactSize(self,size):
        if int(size)<25:
            size = "25"
        elif int(size)>100:
            size = "100"
        if len(str(size))==2:
            self.LEAD_SIZE =f"0{size}"
        else:
            self.LEAD_SIZE = "100"

        cmd = f"EARTSZ={self.LEAD_SIZE}"
        self.sendCommand(cmd)

    def setSide(self,param):

        _side_dic = {

            "Izquierda":"Left",
            "IZQ": "Left",
            "I":"Left",
            "L":"Left",
            "Left":"Left",
            "izq":"Left",
            "izquierda":"Left",
            "DER":"Right",
            "der":"Right",
            "D":"Right",
            "R":"Right",
            "Right":"Right",
            "Derecha":"Right",
            "derecha":"Right"
        }

        self.SIDE = _side_dic[param] #Selecciona el lado donde se va a realizar la arrimia


    def setPreVentricularArrhythmia(self,param):

        _pre_ventricular_arrhythmia_dic = {
            "prematureatrialcontraction":"PAC",
            "PrematureAtrialContraction":"PAC",
            "PAC":"PAC",
            "AtrialContraction":"PAC",
            "ACONTRACTION":"PAC",
            "prematurenodalcontraction":"PNC",
            "PrematureNodalContraction":"PNC",
            "PNC":"PNC",
            "NodalContraction":"PNC",
            "NCONTRACTION":"PNC",
            "ContraccionVentricular": "PVC1",
            "PVC":"PVC1",
            "VentricularContraction":"PVC1",
            "Early":"PVC1E",
            "early":"PVC1E",
            "Temprana":"PVC1E",
            "temprana":"PVC1E",
            "ContraccionTemprana":"PVC1E",
            "RenT":"PVC1R",
            "RonT":"PVC1R",
            "ContraccionRenT":"PVC1R",
            "ContraccionRT":"PVC1R",
            "RTContraction":"PVC1R",
            "RT":"PVC1R",
        }
        try:
            arrh = _pre_ventricular_arrhythmia_dic[param]
        except:
            arrh = "PAC" #Para que no se detenga la ejecucion.....
        if not self.SIDE=="Left":
            if "1" in arrh:
                arrh = arrh.replace("1","2") #Cambio el 1 por el 2, ya que eso simboliza que el pvc se realiza a la derecha
        
        cmd = f"PREWAVE={arrh}"
        self.sendCommand(cmd)

    def setSupArrhythmia(self,param):
        """
        ***GLOSARIO***:\n
        **AFL**: Atrial Flutter\n
        **SNA**: Sinus Arrhythmia\n
        **MB80**: Missed Beat at 80 BPM\n
        **MB120**: Missed Beat at 120 BPM\n
        **ATC**: Atrial Tachycaria\n
        **PAT**: Paroxismal Atrial Tachycardia\n
        **NOD**: Nodal Rhythm\n
        **SVT**: Supraventricual Tachycardia 
        
        """
        supra_ventricular_arrhythmia_dic = {
            "Flutter": "AFL",
            "AtrialFlutter": "AFL",
            "flutter": "AFL",
            "AFL":"AFL",
            "Sinus":"SNA",
            "sinus":"SNA",
            "SNA":"SNA",
            "Sinusal":"SNA",
            "ArritmiaSinusal":"SNA",
            "SinusArrhythmia":"SNA",
            "80BPM" :"MB80",
            "80":"MB80",
            "80LPM":"MB80",
            "120BPM":"MB120",
            "120":"MB120",
            "120LPM":"MB120",
            "SupraventricularTachycardia":"SVT",
            "TaquicardiaSupraventricular":"SVT",
            "SupTaquicardia":"SVT",
            "SVT":"SVT",
            "SupTachycardia":"SVT",
            "Nodal":"NOD",
            "NOD":"NOD",
            "Paraox": "PAT",
            "PAT":"PAT",
            "Paroxismal":"PAT",
            "Paroxysmal":"PAT",
            "TaquicardiaAtrialParoxismal":"PAT",
            "ParoxysmalAtrialTachycardia":"PAT",
            "TaquicardiaAtrial":"ATC",
            "ATC":"ATC",
            "Taquicardia":"ATC",
            "Tachycardia":"ATC",
            "TaquicardiaAtrial":"ATC",
            "AtrialTachycardia":"ATC"
        }

        try:
            arrh = supra_ventricular_arrhythmia_dic[param]
        except:
            arrh = "AFL" #Para que no se detenga la ejecucion.....
        cmd=f"SPVWAVE={arrh}"
        self.sendCommand(cmd)
    def VentricularArrhythmia(self,param):

        _ventricular_arrhythmia_dic = {
            "6":"PVC6M",
            "6min":"PVC6M",
            "PVC6M":"PVC6M",
            "12":"PVC12M",
            "12min":"PVC12M",
            "PVC12M":"PVC12M",
            "24":"PVC24M",
            "24min":"PVC24M",
            "PVC24M":"PVC24M",
            "MultiFocal":"FMF",
            "Multi":"FMF",
            "FrequentMultiFocal":"FMF",
            "Trigeminismo":"TRIG",
            "Trigeminy":"TRIG",
            "TRIG":"TRIG",
            "Trig":"TRIG",
            "Bigeminismo":"BIG",
            "Bigeminy":"BIG",
            "BIG":"BIG",
            "Big":"BIG",
            "PAIR":"PAIR",
            "PAR":"PAIR",
            "5": "RUN5",
            "11":"RUN11"
        }
    
        try:
            arrh = _ventricular_arrhythmia_dic[param]
        except:
            arrh = "FMF" #Para que no se detenga la ejecucion.....
        cmd = f"VNTWAVE={arrh}"
        self.sendCommand(cmd)


    def RunAsistolia(self):
        cmd=f"VNTWAVE=ASYS"
        self.sendCommand(cmd)

    def ConductionArrythmia(self,param): #El alias puede ser bloqueo

        
        _conduction_arrythmia_dic = {
            "PrimerBloqueo":"1DB",
            "PrimerGrado":"1DB",
            "FirstDegeeBlock":"1DB",
            "BloqueoAV":"1DB",
            "Wenck":"2DB1",
            "Wenckebach":"2DB1",
            "SegundoGrade":"2DB2",
            "SecondDegree":"2DB2",
            "Tipo2":"2DB2",
            "2DG":"2DB2",
            "TercerGrado":"3DB",
            "ThirdDegree":"3DB",
            "BloqueoTercerGrado":"3DB",
            "RamaDerecha":"RBBB",
            "RightBundleBranchBlock":"RBBB",
            "RightBranch":"RBBB",
            "RamaIzquierda":"LBBB",
            "LeftBranch":"LBBB",
            "LeftBundleBranchBlock":"LBBB"
        }
        try:
            arrh = _conduction_arrythmia_dic[param]
        except:
            arrh = "1DB"

        cmd = f"CNDWAVE={arrh}"
        self.sendCommand(cmd)

    def setPacerChamber(self,chamber):

        self.PACER_CHAMBER = chamber

    def setPacerPulse(self,wave):

        tvp_wave_dic = {
            "Atrial":"ATR",
            "atrial":"ATR",
            "ATR":"ATR",
            "Asincronica":"ASY",
            "asincronica":"ASY",
            "Asincronico":"ASY",
            "asincronico":"ASY",
            "ASIN":"ASY",
            "ASI":"ASY",
            "Asynchronous":"ASY",
            "ASY":"ASY",
            "Frecuente":"DFS",
            "Frequent":"DFS",
            "DFS":"DFS",
            "Ocasional":"DOS",
            "Occasional":"DOS",
            "DOS":"DOS",
            "AtrioVentricular":"AVS",
            "Atrio-Ventricular":"AVS",
            "SinCaputra":"NCP",
            "Sin-Captura":"NPC",
            "NonCapture":"NPC",
            "Non-Capture":"NPC",
            "NPC":"NPC",
            "Sin-Funcion":"NFN",
            "Non-Function":"NFN"
        }

        try:
            wave_selected = tvp_wave_dic[wave]
        except:
            wave_selected = "ATR"
            print("ERROR-502")


        #Setea polaridad
        cmd = f"TVPPOL={self.PACER_CHAMBER},{self.PACER_POLARITY}"
        self.sendCommand(cmd)
        #Setea Amplitud
        cmd = f"TVPAMPL={self.PACER_CHAMBER},{self.PACER_AMP}"
        self.sendCommand(cmd)
        #Setea Ancho de pulso
        cmd = f"TVPWID={self.PACER_CHAMBER},{self.PACER_WIDTH}"
        self.sendCommand(cmd)

        #######################################
        #Setea el tipo de onda
        cmd = f"TVPWAVE={wave_selected}"
        self.sendCommand(cmd)

    def setGranularity(self,param):
        _granularity_dic = {
            "fino":"FINE",
            "Fino":"FINE",
            "Fine":"FINE",
            "FINE":"FINE",
            "fine":"FINE",
            "Grueso":"COARSE",
            "grueso":"COARSE",
            "COARSE":"COARSE",
            "Coarse":"COARSE",
            "coarse":"COARSE"
        }
        try:
            self.FIB_GRANULARITY = _granularity_dic[param]
        except:
            self.FIB_GRANULARITY = "COARSE"
            print("ERROR-503")

    def setFibrilation(self,param):
        """
        Setea la fibrilacion, puede ser de atrio, o ventricular
        """
        _fibrilation_dic = {
            "Atrio":"ATRIAL",
            "Atrial":"ATRIAL",
            "ATRIO":"ATRIAL",
            "atrio":"ATRIAL",
            "atrial":"ATRIAL",
            "A":"ATRIAL",
            "V":"VENTRICULAR",
            "Ventricular":"VENTRICULAR",
            "VENTRICULAR":"VENTRICULAR",
            "ventricular":"VENTRICULAR",
            "VENTRICULO":"VENTRICULAR",
            "ventriculo":"VENTRICULAR",
            "Ventriculo":"VENTRICULAR"

        }
        try:
            switcher = _fibrilation_dic[param]
        except:
            switcher = "VENTRICULAR"
        
        if switcher=="ATRIAL":
            cmd = f"AFIB={self.FIB_GRANULARITY}"
            self.sendCommand(cmd)
        else:
            cmd = f"VFIB={self.FIB_GRANULARITY}"
            self.sendCommand(cmd)

    def setMonovtach(self):
        """
        SOLO FUNCIONA SI HEARTRATE >120
        """
        """try:
            if int(param)<120:
                _rate = "120"
            elif int(param)>300:
                _rate = "300"
            else:
                _rate = str(int(param))
        except:
            print("ERROR-505")
            _rate = "120"
        """
        cmd = f"MONOVTACH={self.HEARTRATE}"
        self.sendCommand(cmd)

    #*****************************************************************SpO2**********************************************************************
    def set_SpO2_saturacion(self, SATURATION):
        cmd = f"SAT={SATURATION}"
        self.sendCommand(cmd)
    
    def set_SpO2_perfusion(self, PERFUSION):
        cmd = f"PERF={PERFUSION}"
        self.sendCommand(cmd)

    def set_SpO2_ppm(self, PERFUSION):
        cmd = f"PERF={PERFUSION}"
        self.sendCommand(cmd)
 
    def set_SpO2_Sensor(self,sensor):
        """
        Setea el tipo de sensor de oximetría.

        Args:
            sensor (str): Tipo de sensor a configurar.

        Returns:
            str: "OK" si la configuración fue exitosa.
        """
        sensor_type_dic = {
            "NELCOR":"NELCR",
            "NELCR":"NELCR",
            "MASIMO":"MASIM",
            "MASIM":"MASIM",
            "MASIMORAD":"MASIMR",
            "MASIMOR":"MASIMR",
            "MASIMR":"MASIMR",
            "NONIN":"NONIN",
            "OHMED":"OHMED",
            "PHIL":"PHIL",
            "NIHON":"NIHON",
            "MINDRAY":"MINDR",
            "MINDR":"MINDR",
            "BCI":"BCI"
        }

        try:
            selected_sensor = sensor_type_dic[sensor]
        except:
            selected_sensor="BCI"
        
        self.sendCommand(cmd=f"SPO2TYPE={selected_sensor}")

    #*****************************************************************RESPIRATORIO**********************************************************************

    def RespCurveOn(self):
        """
        Inicia la curva de respiratoria
        """
        self.sendCommand(cmd="RESPRUN=TRUE")

    def RespCurveOff(self):
        """
        Finaliza la curva de respiratoria
        """
        self.sendCommand(cmd="RESPRUN=FALSE")

if __name__=="__main__":
    ps8 = PROSIM8(port="COM11", debug = True)
    ps8.connect()

    ps8.set_SpO2_perfusion(0.2)



""" 
Ejemplos de uso:

    Primero conectar el PS8 y crear el objeto:
        ps8 = PROSIM8(port="COM11")
        ps8.connect()
    

    Configurar en PS8 curva ECG de 100ppm:
        ps8.setHeartRate(100)
        ps8.NormalRate()

    Configurar en PS8 curva pletismografica en 85%:
        ps8.set_SpO2_saturacion(85)
    
"""


