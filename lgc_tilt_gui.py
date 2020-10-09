from PyQt5 import QtWidgets, QtCore, QtGui
from layout import Ui_MainWindow
import traceback, sys
import serial
import serial.tools.list_ports
from serial import SerialException, portNotOpenError
import time
import math


class MySerial(object):

    ##    These are the Items you will Change
    ##    *********************************
    PitchCorrect=0.419     #Sign convention: corrected pitch = raw - PitchCorrect
    RollCorrect=0.307     #Sign convention: corrected roll = raw -RollCorrect
    inPORT='COM13'
    inBAUD=9600
    outPORT='COM7'
    outBAUD=9600
    ##    *********************************

    FusionPort = serial.Serial()
    DMonPort = serial.Serial()

    def __init__(self, com_in, com_out, baud_in, baud_out, pitch_correction, roll_correction):
        print(self.inPORT)
        self.PitchCorrect = pitch_correction
        self.RollCorrect = roll_correction
        self.inPORT = com_in
        self.outPORT = com_out
        self.inBAUD = baud_in
        self.outBAUD = baud_out
        print(self.inPORT)


    def tst_serial(self):
        try:
            self.FusionPort.port = self.inPORT
            self.FusionPort.baudrate = self.inBAUD
            self.FusionPort.close()
            self.FusionPort.open()
            self.FusionPort.write(str.encode("run\n\r"))
            self.DMonPort.port = self.outPORT
            self.DMonPort.baudrate = self.outBAUD
            self.DMonPort.close()
            self.DMonPort.open()
            return True, "Ports initialized"
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            error = str(value).split('(')[0]
            print(value)
            return False, (exctype, value, traceback.format_exc())


    def read_port(self):
        if self.FusionPort.isOpen():
            string_in = self.FusionPort.readline()
            return string_in
        

    def write_port(self, stringin):
        try:
            outstring = stringin
            outstring = (outstring+"\n").encode('utf-8')
            if self.DMonPort.isOpen():
                string_out = self.DMonPort.write(outstring)
            return outstring
        except Exception as e:
            print(e)
            return "".encode('utf-8')

    def close_it(self):
        print('SERIAL PORTS CLOSED')
        self.FusionPort.close()
        self.DMonPort.close()

    def doincout(self, instring):
        try:
            holder = instring.split(",")
            pitch = float(holder[7].split("*")[0])
            head, roll = float(holder[5]), float(holder[6])
            pitch = pitch - self.PitchCorrect
            roll = roll - self.RollCorrect
            tilt = math.sqrt(pitch**2 + roll**2)
            rollr = math.radians(roll)
            pitchr = math.radians(pitch)
            y1 = -math.sin(pitchr)
            z1 = math.cos(pitchr)
            x2 = z1 * math.sin(rollr)
            dir = math.degrees(math.atan2(x2, y1))
            dir = (dir + head) % 360       ##This is relative to north
            #dir=(dir)%360       ##This is relative to LGC fwd
            outstring = ("$HRPTD,%.3f,%.3f,%.3f,%.3f,%.3f"%(head,roll,pitch,tilt,dir))
            return outstring
            print(outstring)
        except IndexError as e:
            print(e)


class WorkerSignals(QtCore.QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data
    
    error
        `tuple` (exctype, value, traceback.format_exc() )
    
    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress 

    '''
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)
    message = QtCore.pyqtSignal(object)
    data_in = QtCore.pyqtSignal(object)
    data_out = QtCore.pyqtSignal(object)
    progress = QtCore.pyqtSignal(int)


class Worker(QtCore.QRunnable):
    def __init__(self, serial_object):
        super(Worker, self).__init__()
        self.serial_object = serial_object
        self.signals = WorkerSignals() 
        self.power = True

    def on(self):
        self.power = True

    def off(self):
        self.power = False
    '''
    Worker thread
    '''
    @QtCore.pyqtSlot()
    def run(self):
        try:
            t = self.serial_object
            is_good, msg = t.tst_serial()
            if is_good:
                self.signals.message.emit(msg)
            else:
                self.signals.error.emit(msg)
            while self.power:
                mystring = t.read_port()
                if mystring:
                    mystring = mystring.decode('utf-8')
                    inclout = t.doincout(mystring)
                    newstring=t.write_port(inclout)
                    # print ((time.strftime("%H:%M:%S")),' <INCOMING> ' + mystring.rstrip(),' <OUTGOING> ' + newstring.decode('utf-8'))              
                    self.signals.data_out.emit('<b>' + time.strftime("%H:%M:%S") + '</b> - ' + newstring.decode('utf-8').rstrip())
                    self.signals.data_in.emit('<b>' + time.strftime("%H:%M:%S") + '</b> - ' + mystring.rstrip())
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            print(exctype, value, traceback.format_exc())
            error = str(value).split('(')[0]
            # self.signals.message.emit(error)
            self.signals.error.emit((exctype, value, traceback.format_exc()))


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setStyleSheet("QMainWindow {background: '#f0f0f0';}")
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        self.pushButton = self.ui.pushButton
        self.com_in = self.ui.com_in
        self.com_out = self.ui.com_out
        self.baud_in = self.ui.baud_in
        self.baud_out = self.ui.baud_out
        self.pitch_correction = self.ui.pitch_correction
        self.roll_correction = self.ui.roll_correction
        self.console_out = self.ui.console_out
        self.console_in = self.ui.console_in
        self.menubar = self.ui.menubar


        self.pushButton.clicked.connect(self.start)
        self.flag = True
        self.setWindowTitle('LGC TILT')
        self.pushButton.setStyleSheet('QPushButton {background-color: #E7F1E1; border:  none}')
        com_list = []
        for i in serial.tools.list_ports.comports():
            com_list.append(str(i).split(" ")[0])
        sorted_list = []
        for i in range(300):
            this_com = ("COM" + str(i))
            if this_com in com_list:
                sorted_list.append(this_com)
        self.com_in.addItems(sorted_list)
        self.com_out.addItems(sorted_list)
        self.threadpool = QtCore.QThreadPool()
        self.serial_object = None
        self.settings = QtCore.QSettings(self.objectName())
        self.com_in.setCurrentIndex(self.settings.value('com_in', 0))
        self.com_out.setCurrentIndex(self.settings.value('com_out', 1))
        self.baud_in.setCurrentIndex(self.settings.value('baud_in', 2))
        self.baud_out.setCurrentIndex(self.settings.value('baud_out', 2))
        self.pitch_correction.setText(self.settings.value('pitch_correction', '0'))
        self.roll_correction.setText(self.settings.value('roll_correction', '0'))
        self.restoreGeometry(self.settings.value('geo', self.saveGeometry()))
        self.settings.setValue('com_in', self.com_in.currentIndex())
        self.worker = None
        self.menubar.setHidden(True)
        self.show() # Show the GUI
    
    def append_output(self, s):
        if len(self.console_out.toPlainText().split('\n')) > 100:
            self.console_out.setHtml(self.console_out.toHtml().split('</p>', 1)[1] + s)
            self.console_out.verticalScrollBar().setValue(self.console_out.verticalScrollBar().maximum())
        else:
            self.console_out.append(s)

    def append_input(self, s):
        if len(self.console_in.toPlainText().split('\n')) > 100:
            self.console_in.setHtml(self.console_in.toHtml().split('</p>', 1)[1] + s)
            self.console_in.verticalScrollBar().setValue(self.console_in.verticalScrollBar().maximum())
        else:
            self.console_in.append(s)
        print(s)
    
    def show_message(self, e):
        self.statusBar.showMessage(str(e))
    
    def start(self):
        if self.flag:
            com_in = self.com_in.currentText()
            com_out = self.com_out.currentText()
            baud_in = int(self.baud_in.currentText())
            baud_out = int(self.baud_out.currentText())
            pitch_correction = float(self.pitch_correction.text())
            roll_correction = float(self.roll_correction.text())
            self.serial_object = MySerial(com_in, com_out, baud_in, baud_out, pitch_correction, roll_correction)
            self.worker = Worker(self.serial_object)
            # self.worker.on()
            self.threadpool.start(self.worker)
            self.worker.signals.data_in.connect(self.append_input)
            self.worker.signals.data_out.connect(self.append_output)
            self.worker.signals.message.connect(self.show_message)
            self.worker.signals.error.connect(self.error)
            self.off()
        else:
            self.on()

    def error(self, e):
        self.on()
        print(str(e[1]).split('(')[0])
        self.statusBar.showMessage(str(e[1]).split('(')[0])

    def on(self):
        self.worker.off()
        self.statusBar.showMessage('Ports Closed')
        self.pushButton.setText('START')
        self.com_in.setEnabled(True)
        self.com_out.setEnabled(True)
        self.baud_in.setEnabled(True)
        self.baud_out.setEnabled(True)
        self.pitch_correction.setEnabled(True)
        self.roll_correction.setEnabled(True)
        self.pushButton.setStyleSheet('QPushButton {background-color: #E7F1E1; border:  none}')
        self.flag = True

    def off(self):
        self.pushButton.setText('STOP')
        self.flag = False
        self.com_in.setEnabled(False)
        self.com_out.setEnabled(False)
        self.baud_in.setEnabled(False)
        self.baud_out.setEnabled(False)
        self.pitch_correction.setEnabled(False)
        self.roll_correction.setEnabled(False)
        self.pushButton.setStyleSheet('QPushButton {background-color: red; border:  none}')


    def closeEvent(self, event):
        self.settings.setValue('com_in', self.com_in.currentIndex())
        self.settings.setValue('com_out', self.com_out.currentIndex())
        self.settings.setValue('baud_in', self.baud_in.currentIndex())
        self.settings.setValue('baud_out', self.baud_out.currentIndex())
        self.settings.setValue('pitch_correction', self.pitch_correction.text())
        self.settings.setValue('roll_correction', self.roll_correction.text())
        self.settings.setValue('geo', self.saveGeometry())
        if self.worker:
            self.worker.off()
        if self.serial_object:
            self.serial_object.close_it()
        self.close()
        

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv) # Create an instance of QtWidgets.QApplication
    app.setWindowIcon(QtGui.QIcon('icon.ico'))
    window = Ui() # Create an instance of our class
    app.exec_() # Start the application