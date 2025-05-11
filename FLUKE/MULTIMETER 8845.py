import serial
import time
import sympy as sp


__author__ ="Juan Cruz Noya"
__mail__ = "juancruznoya@mi.unc.edu.ar"
__status__ = "in building"
class Fluke8845:
    def __init__(self,port,baudrate,fetch_trouble = False):
        self.COM = port
        self.baudrate = baudrate
        self.timeout = 0.1
        self.resistance = 0
        self.AC_DC = "DC"
        self.current = 0
        self.voltage = 0
        self.frequency = 0
        self.temperature = 0
        self.scale = "standard"
        self.range = ":AUTO ON"
        self.delay = 100
        self.mA = True
        self.four_wire = False
        self.ser = serial.Serial(self.COM, self.baudrate, timeout=self.timeout, parity = "N", stopbits = 1, bytesize = 8)
        self.error = None
        self.measurementUnit = {"standard":1,"kilo":1000,"mega":1000000,"mili":0.001,"micro":0.000001}
        self.fetch_trouble =fetch_trouble
        self.diodehighvoltage = 0
        self.diodelowcurrent = 0
        self.diode = 0


    def send_scpi_command(self,comando,delay=100):
        time.sleep(delay/1000) if "FETCh" in comando else time.sleep(0.2)
        self.ser.write(comando.encode())
        time.sleep(0.1)
        if comando == "*OPC?\r\n": #wait until *OPC? complete
            while self.ser.read(1024).decode() == "":
                pass
            return 0
        elif "FETCh" in comando:
            try:
                if self.fetch_trouble:
                    r =self.ser.readline().decode()
                    r = r.split(",")
                    r = float(r[-1])
                else:
                    r = self.ser.read(1024).decode()
                return float(sp.sympify(r))
            except:
                return -101 #for a future error list
        else:
            return 0

    def Measurementscale(self,value,unit="standard"):
        return value/self.measurementUnit[unit.lower()]

    def resistance_measure(self):
        
        if self.fetch_trouble:
            fetch = "FETCh?"
        else:
            fetch = "FETCh3?"

        if self.range != ":AUTO ON":
            self.range = f" 1E{int(self.range) + 1}" #el rangeo 1 seria 1E2 y asi .....

        command_type = "FRES" if self.four_wire else "RES"
        scpiCommands =["*CLS\r\n",
                       f"CONF:{command_type}\r\n",
                       f"{command_type}:NPLC 1\r\n",
                       f"{command_type}:RANG{self.range}\r\n",
                       #"trig:sour imm\r\n",
                       "INIT\r\n",
                       "*OPC?\r\n",
                       f'{fetch}\r\n']

        for comando in scpiCommands:

            self.resistance = self.send_scpi_command(comando,delay=self.delay)

        self.resistance = self.Measurementscale(self.resistance, self.scale)

    def diode_measure(self):
        if self.fetch_trouble:
            fetch = "FETCh?"
        else:
            fetch = "FETCh3?"

        if self.range != ":AUTO ON":
            self.range = f" 1E{int(self.range) + 1}"

        scpiCommands = ["*CLS\r\n",
                        f"CONF:DIOD {self.diodelowcurrent},{self.diodehighvoltage} \r\n",
                        f"CONF:DIOD:NPLC 10\r\n",
                        #"trig:sour imm\r\n",
                        "INIT\r\n",
                        "*OPC?\r\n",
                        f'{fetch}\r\n']

        for command in scpiCommands:
            self.diode = self.send_scpi_command(command,delay=self.delay)

        self.diode = self.Measurementscale(value=self.diode, unit=self.scale)         



    def freq_measure(self):

        if self.fetch_trouble:
            fetch = "FETCh?"
        else:
            fetch = "FETCh3?"
        if self.range != ":AUTO ON":
            self.range = f" 1E{int(self.range) + 1}" #el rangeo 1 seria 1E2 y asi .....

        scpiCommands =["*CLS\r\n",
                       f"CONF:FREQ\r\n",
                       f"FREQ:NPLC 10\r\n",
                       f"FREQ:RANG{self.range}\r\n",
                       #"trig:sour imm\r\n",
                       #"INIT\r\n",
                       "*OPC?\r\n",
                       f'{fetch}\r\n']

        for comando in scpiCommands:

            self.frequency = self.send_scpi_command(comando,delay=self.delay)

        self.frequency = self.Measurementscale(self.frequency, self.scale)

    def voltage_measure(self):

        if self.fetch_trouble:
            fetch = "FETCh?"
        else:
            fetch = "FETCh3?"
        if self.range != ":AUTO ON":
            self.range = f" 1E{int(self.range) + 1}" #el rangeo 1 seria 1E2 y asi .....

        scpiCommands = ["*CLS\r\n",
                        f"CONF:VOLT:{self.AC_DC}\r\n",
                        f"VOLT:{self.AC_DC}:NPLC 10\r\n",
                        f"VOLT:{self.AC_DC}:RANG{self.range}\r\n",
                        #"trig:sour imm\r\n",
                        #"INIT\r\n",
                        "*OPC?\r\n",
                        f'{fetch}\r\n']

        for command in scpiCommands:
            self.voltage = self.send_scpi_command(command,delay=self.delay)

        self.voltage = self.Measurementscale(value=self.voltage, unit=self.scale)


    def current_measure(self,unit ="standard",delay=1000):

        if self.fetch_trouble:
            fetch = "FETCh?"
        else:
            fetch = "FETCh3?"

        if self.range != ":AUTO ON":
            self.range = f" 1E{int(self.range) + 1}" #el rangeo 1 seria 1E2 y asi .....

        range = 1 if self.mA else 0.1
        scpiCommands =["*CLS\r\n",
                       f"CONF:CURR:{self.AC_DC} {range}\r\n",
                       f"CURR:{self.AC_DC}:NPLC 10\r\n",
                       f"CURR:{self.AC_DC}:RANG{self.range}\r\n",
                       #"trig:sour imm\r\n",
                       #"INIT\r\n",
                       "*OPC?\r\n",
                       f'{fetch}\r\n']

        for command in scpiCommands:
            self.current = self.send_scpi_command(command,delay=self.delay)
        self.current = self.Measurementscale(self.current,unit=self.scale)
        
    def temperature_measure(self,delay = 1000):


        if self.fetch_trouble:
            fetch = "FETCh?"
        else:
            fetch = "FETCh3?"

        scpiCommands =["*CLS\r\n",
                       f"CONF:TEMP\r\n",
                       f"TEMP:NPLC 10\r\n",
                       f"TEMP:RANG:AUTO ON\r\n",
                       #"trig:sour imm\r\n",
                       #"INIT\r\n",
                       "*OPC?\r\n",
                       f'{fetch}\r\n']
        for command in scpiCommands:
            self.temperature = self.send_scpi_command(command,delay = 2000)
        self.temperature = self.Measurementscale(value=self.temperature,unit = "standard")
        
    
    def stop(self):
        self.ser.close()
    def enable_four_wire(self):
        self.four_wire =True

    def DC_to_AC(self):
        self.AC_DC = "AC" if self.AC_DC == "DC" else "DC"

    def AC_to_DC(self):
        self.AC_DC = "DC" if self.AC_DC == "AC" else "AC"

    def enable_10mA(self):
        self.mA = False
    def None_function(self):
        return 0

class Fluke45:
    def __init__(self,port,baudrate):
        self.port = port
        self.baudrate = baudrate
        self.ser = serial.Serial(self.port, baudrate=baudrate,parity = "N", stopbits = 1, bytesize = 8,timeout=0.5)
        self.voltage = 0
        self.resistance = 0
        self.current = 0
        self.frequency = 0
        self.scale = "standard"
        self.delay = 1
        self.diode = 0
        self.AC_DC = "DC"
        self.four_wire = False
        self.measurementUnit = {"standard":1,"kilo":1000,"mega":1000000,"mili":0.001,"micro":0.000001}
        self.mA = True

    def send_queries_command(self,command,delay=100):
        time.sleep(delay/1000.0) if "VAL" in command else time.sleep(0.1)
        self.ser.write(command.encode())

        if command == "*OPC?\r\n": #wait until *OPC? complete
            while self.ser.read(1024).decode() == False:
                pass
            return 0
        if "VAL" in command :
            #print(command)
            r =self.ser.readline().decode()
            #print(r)
            try:
                return float(sp.sympify(r))
            except:
                return 0.0
        elif "AUTO" in command:
            time.sleep(0.1)
            r = self.ser.readline().decode()

            #print(f"-{r}")
            try:
                return 0
            except:
                return 0.1
        elif "*CLS in commnad":
            time.sleep(1)
            r = self.ser.readline().decode()

            #print(f"-{r}")
            try:

                return 0
            except:
                return 0.2
        
        else:
            time.sleep(0.1)
            r = self.ser.readline().decode()

            #print(f"-{r}")
            try:
                return 0
        
            except:
                return 0.3
    def Measurementscale(self,value,unit="standard"):
        return value/self.measurementUnit[unit.lower()]
    def resistance_measure(self):
        queries_command = ["*CLS\r\n",
                           "OHMS\r\n",
                           "AUTO\r\n",
                           "TRIGGER 1\r\n",
                           "VAL1?\r\n"]

        for command in queries_command:
            if "AUTO" in command:
                time.sleep(0.5)
            else:
                pass

            self.resistance = self.send_queries_command(command=command, delay=self.delay)

        self.resistance = self.Measurementscale(value=self.resistance,unit=self.scale)
    def voltage_measure(self):
        AC_DC_ = "VDC" if self.AC_DC == "DC" else "VAC"
        queries_command = ["*CLS\r\n",
                           f"{AC_DC_}\r\n",
                           "AUTO\r\n",
                           #"TRIGGER 1\r\n",
                           "VAL1?\r\n"]
        for command in queries_command:
            if "AUTO" in command:
                time.sleep(0.5)
            else:
                pass
            self.voltage = self.send_queries_command(command=command, delay=self.delay)

        self.voltage = self.Measurementscale(value=self.voltage,unit=self.scale)

    def current_measure(self):
        AC_DC_ = "ADC" if self.AC_DC == "DC" else "AAC"
        queries_command = ["*CLS\r\n",
                            "TRIGGER 1\r\n",
                            f"{AC_DC_}\r\n",
                           #"AUTO\r\n",
                           #"RANGE 3\r\n"

                           #"*OPC?\r\n",
                           "MEAS?\r\n",
]
        for command in queries_command:
            if "AUTO" in command:
                time.sleep(0.5)
            else:
                pass
            self.current = self.send_queries_command(command=command,delay=self.delay)

        self.current = self.Measurementscale(value=self.current,unit=self.scale)

    def freq_measure(self):
        queries_command = ["*CLS\r\n",
                           "FREQ\r\n",
                           "AUTO\r\n",

                           "VAL1?\r\n"]

        for command in queries_command:
            if "AUTO" in command:
                time.sleep(0.5)
            else:
                pass
            self.frequency = self.send_queries_command(command=command, delay=self.delay)

        self.frequency = self.Measurementscale(value=self.frequency, unit=self.scale)
    def stop(self):
        self.ser.close()
    def enable_four_wire(self):
        self.four_wire =True

    def DC_to_AC(self):
        self.AC_DC = "AC" if self.AC_DC == "DC" else "DC"

    def AC_to_DC(self):
        self.AC_DC = "DC" if self.AC_DC == "AC" else "AC"

    def enable_10mA(self):
        self.mA = False

    def None_function(self):
        return 0
        
        
if __name__ =="__main__":

    MUL  = Fluke8845(port="COM8",baudrate=9600)
    
    print(MUL.diode_measure())

    print(MUL.diode)