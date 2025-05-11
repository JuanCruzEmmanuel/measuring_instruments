import serial
from time import sleep
import re

__version__ = "1.4.2"
__autor__ = "Juan Cruz Noya & Julian Font"
__propietario__ = "Feas Electronica"

"""
Version 1.2.3   Se elimina una linea de self.serial.decode() en mainAppliedParts(). Se busca corregir colgadas del puerto
Version 1.2.4   Se agregan tiempos de retardo entre comandos enviados al puerto serie y solicitudes de lectura
Version 1.3     Se agregan tiempos de timeout y write_timeout al abrir el puerto serie. Ambos de 20 segundos para evitar colgadas del puerto serie. Se eliminan tiempos de retardo introducidos en v1.2.4
Version 1.4     Se comienza a trabajar en el manejo de errores de comunicación. Se agrega el error -102 en enclosureLeakageCurrent(), patientLeakageCurrent(), mainAppliedParts() y patientAuxiliaryCurrent().
                Error -102: Este error indica que no se pudo convertir la respuesta del ESA620 de formato string a formato float.
Version 1.4.1   Se agrega el loop while para aceptar la lectura solo cuando la respuesta del ESA620 sea distinta de "*"
Version 1.4.2   Se agrega la funcion LOCAL(). Se implementará antes de cerrar el puerto en drivers.py esa620(). Se programa inicialmente los parametros en mainAppliedParts().
Version 1.4.3   Se agrega el error -103. Este error indica que no se pudo abrir y configurar el puerto serie.
"""

class ESA620:
    def __init__(self,port,baudrate=115200):
        self.port = port
        self.baudrate = baudrate

        try:   
            self.serial = serial.Serial(port=self.port,baudrate=self.baudrate,parity="N",stopbits=1,bytesize=8, timeout=20, write_timeout=20)
        except:
            return "-103"

        self._ident = None

        self.leads = 10
        self.electrodes = ["RA","LL","LA","RL","V1", "V2", "V3", "V4", "V5", "V6"]
        self.polarity = "N"
        self.earth = "C"
        self.neutral = "C"
        self.test = "ENCL"





    #Seteo del ESA620 en modo remoto
    def REMOTE(self):
        """
        CONECTA EL EQUIPO EN MODO REMOTO
        """

        self.serial.write("REMOTE\r".encode())
        self.serial.readline().decode()
        self.serial.write("RPTIME=2\r".encode())
        self.serial.readline().decode()
        self.serial.write("STD=NONE\r".encode())
        self.serial.readline().decode()
        sleep(1)

    def LOCAL(self):
        """
        Equipo en modo local
        """
        self.serial.write("LOCAL\r".encode())
        self.serial.readline().decode()


    #Encendido y apagado de equipo bajo ensayo desde ESA620
    def powerON(self):
        self.serial.write("REMOTE\r".encode())
        self.serial.readline().decode()
        self.serial.write("PAT\r".encode())
        self.serial.readline().decode()
        sleep(1)
        self.serial.write("POL=N\r".encode())
        self.serial.readline().decode()
    def powerOFF(self):
        self.serial.write("REMOTE\r".encode())
        self.serial.readline().decode()
        self.serial.write("PAT\r".encode())
        self.serial.readline().decode()
        sleep(1)
        self.serial.write("POL=OFF\r".encode())
        self.serial.readline().decode()     
    
    def setTest(self,value):
        """
        SETEA UN AUXILIAR DE ENSAYO
        :param value: va a setear el tipo de ensayo que se va a realizar 
        """

        TEST = {
            # Live to Neutral
            "LIVE_TO_NEUTRAL": "L1-L2",
            "live_to_neutral": "L1-L2",
            "VIVO_A_NEUTRO": "L1-L2",
            "L_N": "L1-L2",

            # Live to Earth
            "LIVE_TO_EARTH": "L1-GND",
            "VIVO_A_TIERRA": "L1-GND",
            "L_GND": "L1-GND",

            # Neutral to Earth
            "NEUTRO_TO_EARTH": "L2-GND",
            "NEUTRAL_TO_EARTH": "L2-GND",
            "NEUTRO_A_TIERRA": "L2-GND",
            "N_GND": "L2-GND",
            "NEUTRO_TO_GND": "L2-GND",

            # Mains to Protective Earth
            "MAINS-PE": "INSB",
            "MAINS_TO_PROTECTIVE_EARTH": "INSB",
            "PRINCIPAL_A_TIERRA": "INSB",
            "MAIN_PROTECTIVE_EARTH": "INSB",
            "MAIN-PE": "INSB",

            # Applied Parts to Protective Earth
            "A.P-PE": "INSD",
            "AP-PE":"INSD",
            "APPLIED_PARTS_PROTECTIVE_EARTH": "INSD",
            "ACTIVO_A_TIERRA": "INSD",

            # Main to Applied Parts
            "MAIN-A.P": "INSE",
            "PRINCIAPAL_A_ACTIVO": "INSE",
        }
        self.test = TEST[value]
    
    #Llamado por el comando --SET_ATRIBUTO leads. 3,5 o 10
    def setLeads(self,value):
        """
        
        :param leads: Cantidad de derivaciones
        """

        self.leads = int(value)
        
        match self.leads:
            case 5:
                self.electrodes = ["RA","LL","LA","RL","V1"]
            case 3:
                self.electrodes = ["RA","LL","LA"]
            case 10:
                self.electrodes = ["RA","LL","LA","RL","V1", "V2", "V3", "V4", "V5", "V6"]
            case _:
                raise Exception(f"Error: Cantidad de electrodos ingresada incorrecta, ingrese 3, 5 o 10")
        
    #Llamado por el comando --SET_ATRIBUTO polarity. Normal
    def setPolarity(self,value):
        POL = {
            "N":"N",
            "NORM":"N",
            "NORMAL":"N",
            "normal":"N",
            "1":"N",
            "DIRECTA":"N",
            "DIR":"N",
            "APAGADO":"OFF",
            "0":"OFF",
            "OFF":"OFF",
            "R":"R",
            "r":"R",
            "REVERSE":"R",
            "reverse":"R",
            "INVERTIDA":"R",
            "-1":"R"

        }
        self.polarity = POL[value]
    def setNeutral(self,value):
        """
        
        se debe poder setear si queremos que el nuetro cierre o abra su circuito hacia el toma corrientes
        """
        NEUT ={
            "O":"O",
            "OPEN":"O",
            "o":"O",
            "A":"O",
            "ABIERTO":"O",
            "C":"C",
            "CERRADO":"C",
            "CERRADA":"C",
            "Cerrada":"C",
            "CLOSED":"C",
            "CLOSE":"C",
            "c":"C"

        }

        self.neutral = NEUT[value]
    def setEarth(self,value):
        """
        Setea la confuracion de la tierra respecto al toma corriente
        
        """
        EARTH ={
            "O":"O",
            "OPEN":"O",
            "o":"O",
            "A":"O",
            "ABIERTO":"O",
            "C":"C",
            "CERRADO":"C",
            "CERRADA":"C",
            "Cerrada":"C",
            "CLOSED":"C",
            "CLOSE":"C",
            "c":"C"

        }


        self.earth = EARTH[value]
    def setElectrodes(self):

        """
        Selecciona una lista con la configuracion de electrodos en funcion a la cantidad elegida de estos
        
        """
        match self.leads:
            case 5:
                self.electrodes = ["RA","LL","LA","RL","V1"]
            case 3:
                self.electrodes = ["RA","LL","LA"]
            case 10:
                self.electrodes = ["RA","LL","LA","RL","V1", "V2", "V3", "V4", "V5", "V6"]
            case _:
                raise Exception(f"Error: Cantidad de electrodos ingresada incorrecta, ingrese 3, 5 o 10")
 
    def setESAMeasure(self):
        
        self.serial.write(f"{self.test}\r".encode())
        self.serial.readline().decode()
        self.serial.write(f"POL=OFF\r".encode())
        self.serial.readline().decode()
        self.serial.write(f"POL=N\r".encode())
        self.serial.readline().decode()
        self.serial.write(f"EARTH=C\r".encode())
        self.serial.readline().decode()
        self.serial.write(f"NEUT=C\r".encode())
        self.serial.readline().decode()
        self.serial.write(f"MODE=ACDC\r".encode())
        self.serial.readline().decode()
    def ensureResponse(self):
            respuesta = self.serial.readline().decode().strip()
            if respuesta != "*":
                raise Exception(f"Error: {respuesta}")

    def ident(self):

        """
        Identifica el equipo
        """

        self.serial.write("REMOTE\r".encode())

        self.serial.readline().decode()

        self.serial.write("IDENT\r".encode())

        self._ident=self.serial.readline().decode()

    #Llamados por el comando --run del Driver
    def protectiveEarthResistance(self):

        """
        
        Funcion para el ensayo de la resistencia de tierra
        """

        self.serial.write("REMOTE\r".encode())

        self.serial.readline().decode()
        self.serial.write("ERES = LOW\r".encode())
        self.serial.readline().decode()
        self.serial.write("RWIRE=2\r".encode())

        self.serial.readline().decode()
        self.serial.write("READ\r".encode())

        resistencia = self.serial.readline().decode()

        return resistencia.split(" ")[0]
    def voltMeasure(self):
        """
        Devuelve el valor medido en el ensayo de voltaje
        """
        self.serial.write("REMOTE\r".encode())

        self.serial.readline().decode()
        self.serial.write(f"MAINS={self.test}\r".encode())

        self.serial.readline().decode()
        self.serial.write("READ\r".encode())
        value = self.serial.readline().decode()
        return value.split(" ")[0]
    def insulationResistance(self,ensayo = 1):
        """
        Medicion de Insultaion resistance test
        """
        self.REMOTE()
        
        cmd = {
            1:"INSB",
            2:"INSD",
            3:"INSE"
        }
        self.serial.write(f"MINS\r".encode())
        self.serial.readline().decode()
        self.serial.write(f"INS=HIGH\r".encode())
        self.serial.readline().decode()
        self.serial.write(f"{self.test}\r".encode())

        self.serial.readline().decode()

        self.serial.write("READ\r".encode())
        r = self.serial.readline().decode()
        if "!21" in r:
            r="99999 MOHMS"
        else:
            pass

        return r.split(" ")[0]
    def equipmentCurrent(self):
        """
        Enciende el equipo para medicion de consumo

        :return: corriente alterna de consumo en Amperes
        """
        self.REMOTE()


        
        self.serial.write(f"EQCURR\r".encode())
        self.serial.readline().decode()
        self.serial.write("READ\r".encode())
        r = self.serial.readline().decode().split(" ")[0]
        return r
    def leakageEarth(self):
        """
        Funcion que configura el equipo para distintos ensayos de corrientes de fuga.
        return: corriente de fuga en uAAC+DC
        """
 
        self.REMOTE() #SET MODO REMOTO
        self.serial.write(f"EARTHL\r".encode()) #CONFIGURA EN MODO TIERRA O CARCASA
        self.serial.readline().decode()
        self.serial.write(f"POL={self.polarity}\r".encode()) #CONFIGURA LA POLARIDAD
        self.serial.readline().decode()
        self.serial.write(f"NEUT={self.neutral}\r".encode()) #CONFIGURA EL NEUTRO
        self.serial.readline().decode()
        self.serial.write(f"MODE=ACDC\r".encode()) #CONFIGURA EN MEDICION DE CORRIENTE DE FUGA DE PACIENTE
        self.serial.readline().decode()
        sleep(0.5)
        self.serial.write("READ\r".encode())#TOMA LA MEDICION
        r = self.serial.readline().decode().split(" ")[0]
        return r
    def enclosureLeakageCurrent(self):
        """
        Funcion que controla el ensayo de corriente por la carcasa
        
        """
        self.REMOTE()

        self.serial.write(f"ENCL\r".encode())
        self.serial.readline().decode()
        self.serial.write(f"AP=//OPEN\r".encode())
        self.serial.readline().decode()
        self.serial.write(f"MDUAL=OFF\r".encode())
        self.serial.readline().decode()
        self.serial.write(f"POL={self.polarity}\r".encode())
        self.serial.readline().decode()
        self.serial.write(f"EARTH={self.earth}\r".encode())
        self.serial.readline().decode()
        self.serial.write(f"NEUT={self.neutral}\r".encode())
        self.serial.readline().decode()
        sleep(0.5)
        self.serial.write(f"MREAD\r".encode())
        m = self.serial.readline().decode()
        while "*" in str(m):
            sleep(0.5)
            m = self.serial.readline().decode()
        self.serial.write(bytes([0x1B, 0x0D, 0x0A]))
        self.serial.readline().decode()
        try:
            value = float(m.replace(" uA", ""))
            return str(value)
        except ValueError:
            return "-102"
        
    def patientLeakageCurrent(self):

        """
        Funcion que controla el ensayo de fuga de corriente a paciente
        """

        self.REMOTE()
        
        max_current = 0
        for electrode in self.electrodes:
            gndElectrodes = ",".join([g for g in self.electrodes if g != electrode])
            self.serial.write("STD=NONE\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"PAT\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"POL={self.polarity}\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"EARTH={self.earth}\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"NEUT={self.neutral}\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"MODE=ACDC\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"AP={electrode}//\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"GRP={gndElectrodes}\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"MDUAL=OFF\r".encode())
            self.serial.readline().decode()
            sleep(0.5)
            self.serial.write(f"MREAD\r".encode())
            m = self.serial.readline().decode()
            while "*" in str(m):
                sleep(0.5)
                m = self.serial.readline().decode()
            self.serial.write(bytes([0x1B, 0x0D, 0x0A]))
            self.serial.readline().decode()
        try:
            current_value = float(m.replace(" uA", ""))
            if current_value > max_current:
                max_current = current_value
        except ValueError:
            return "-102"

        return str(max_current) 
    def mainAppliedParts(self):

        """
        Funcion que controla el ensayo de corriente en partes aplicables
        """

        self.REMOTE()

        max_current = 0
        for electrode in self.electrodes:
            gndElectrodes = ",".join([g for g in self.electrodes if g != electrode])
            self.serial.write(bytes([0x1B, 0x0D, 0x0A]))
            self.serial.readline().decode()
            self.serial.write("STD=NONE\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"MAP\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"MAP=LOW\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"EARTH=C\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"NEUT=C\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"MAP=NORM\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"POL={self.polarity}\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"AP={electrode}//\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"GRP={gndElectrodes}\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"MODE=ACDC\r".encode())
            self.serial.readline().decode()
            self.serial.write(f"MDUAL=OFF\r".encode())
            self.serial.readline().decode()
            sleep(0.5)
            self.serial.write(f"MREAD\r".encode())
            m = self.serial.readline().decode()
            while "*" in str(m):
                sleep(0.5)
                m = self.serial.readline().decode()
            self.serial.write(bytes([0x1B, 0x0D, 0x0A]))
            self.serial.readline().decode()
            try:
                current_value = float(m.replace(" uA", ""))
                if current_value > max_current:
                    max_current = current_value
            except ValueError:
                return "-102"
            
        return str(max_current)  
    def patientAuxiliaryCurrent(self):
        
        """
        Funcion que controla el ensayo de corriente auxiliar
        """
        self.REMOTE()

        max_current = 0
        for electrode in self.electrodes:
                gndElectrodes = ",".join([g for g in self.electrodes if g != electrode])

                self.serial.write(f"STD=NONE\r".encode())
                self.serial.readline().decode()
                self.serial.write(f"AUX\r".encode())
                self.serial.readline().decode()
                self.serial.write(f"POL={self.polarity}\r".encode())
                self.serial.readline().decode()
                self.serial.write(f"EARTH={self.earth}\r".encode())
                self.serial.readline().decode()
                self.serial.write(f"NEUT={self.neutral}\r".encode())
                self.serial.readline().decode()
                self.serial.write(f"MODE=ACDC\r".encode())
                self.serial.readline().decode()
                self.serial.write(f"AP={electrode}/{gndElectrodes}/\r".encode()) #CONFIGURA EN MEDICION DE CORRIENTE DE FUGA DE PACIENTE
                self.serial.readline().decode()
                self.serial.write(f"MDUAL=OFF\r".encode())
                self.serial.readline().decode()
                sleep(0.5)
                self.serial.write("MREAD\r".encode())#TOMA LA MEDICION
                m = self.serial.readline().decode()
                while "*" in str(m):
                    sleep(0.5)
                    m = self.serial.readline().decode()
                self.serial.write(bytes([0x1B, 0x0D, 0x0A]))
                self.serial.readline().decode()

                try:
                    current_value = float(m.replace(" uA", ""))
                    if current_value > max_current:
                        max_current = current_value  # Convertir el valor numérico a flotante
                except ValueError:
                    return "-102"

        return str(max_current)

    def close(self):
        self.serial.close()


class ESA620HELP:
    
    def __init__(self):
        
        self.COMANDOS ={
            "REMOTE":"COLOCA EL EQUIPO EN MODO REMOTO",
            "IDENT":"DEVUELVE LA INFORMACION DEL EQUIPO",
            "LOCAL":"COLOCA EL EQUIPO EN MODO LOCAL",
            "MAINS":"MEDICION DE VOLTAJE"
            }
   
