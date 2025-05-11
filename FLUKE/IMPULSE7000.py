import serial
import time



class IMPULSE7000:
    def __init__(self,port:str):
        """
        :param port: set COM port
        :param baudrate: set baudrate for serial connection
        :return: Nothing
        """

        self.serial = serial.Serial(port=port,baudrate=115200,parity="N",bytesize=8,
                                    stopbits=1,rtscts=True, dsrdtr=True)
        self.energy = 0

    def read_energy(self):

        CMD = (
            'REMOTE\r', 
            'MODE=DEFIB\r',
            'Dready\r'
            )
        
        for comando in CMD:
            try:
                self.serial.write(comando.encode())
                time.sleep(0.1)
                respuesta = self.serial.readline().decode("utf-8")
                print(respuesta)
                
                if comando == 'REMOTE\r' and "!01" in respuesta:
                    self.serial.write("LOCAL\r".encode())
                    self.serial.readline().decode("utf-8")
                    time.sleep(0.1)
                    self.serial.write(comando.encode())
                    self.serial.readline().decode("utf-8")
                    time.sleep(0.1)
            except Exception as e:
                print(f"Error: {e}")
                return "Error"


        self.serial.write('Dready\r'.encode())
        try:
            self.energy = self.serial.readline().decode("utf-8")[2:7]
        except:
            return "Error en medicion"
        
        return self.energy
        
    def local_mode(self):
        """
        Return to local mode
        """
        cmd = "Local\r"
        self.serial.write(cmd.encode())
    
    def close(self):

        """
        Close serial COM
        """
        self.serial.close()

