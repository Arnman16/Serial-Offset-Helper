from PyQt5 import QtWidgets, uic
from mailmerge import MailMerge
import pandas as pd
import sys
import xlrd

# default values
file_location = ("LISTOFVEHICLES.xls")
insured_name_cell = (0, 8)
policy_number_cell = (0, 17)
skiprows = 11

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('main.ui', self) # Load the .ui file
        self.table = self.findChild(QtWidgets.QTableWidget, 'tableWidget')
        self.button = self.findChild(QtWidgets.QPushButton, 'makeCards')
        self.insurer_name = self.findChild(QtWidgets.QLineEdit, 'insurer_name')
        self.policy_number = self.findChild(QtWidgets.QLineEdit, 'policy_number')
        self.insured_address = self.findChild(QtWidgets.QTextEdit, 'insured_address')
        self.insured_name = self.findChild(QtWidgets.QLineEdit, 'insured_name')
        self.effective_date = self.findChild(QtWidgets.QDateEdit, 'effective_date')
        self.expiry_date = self.findChild(QtWidgets.QDateEdit, 'expiry_date')
        self.excelFile = self.findChild(QtWidgets.QLineEdit, 'excel_file')
        self.loadButton = self.findChild(QtWidgets.QPushButton, 'load_button')
        self.file_button = self.findChild(QtWidgets.QToolButton, 'file_button')
        self.excelFile.setText(file_location)
        self.button.clicked.connect(self.make_cards)
        self.file_button.clicked.connect(self.file_browser)
        self.loadButton.clicked.connect(self.load_file)
        for x in range(self.table.rowCount()):
            item = QtWidgets.QTableWidgetItem()
            self.table.setItem(x, 0, item)
        self.show() # Show the GUI

    def load_file(self):
        # To open Workbook 
        wb = xlrd.open_workbook(file_location) 
        sheet = wb.sheet_by_index(0)
        # For row 0 and column 0 
        insured_name = sheet.cell_value(insured_name_cell[0], insured_name_cell[1])
        policy_number = sheet.cell_value(policy_number_cell[0], policy_number_cell[1])
        self.insured_name.setText(insured_name)
        self.policy_number.setText(policy_number)
        excel_data_df = pd.read_excel('LISTOFVEHICLES.xls', usecols=['No.', 'Year', 'Trade Name', 'Body', 'Serial No. '], skiprows=skiprows).dropna()
        excel_data_dict = excel_data_df.to_dict(orient='record')
        for index, row in enumerate(excel_data_dict):
            self.table.insertRow(self.table.rowCount())
            print(row['Year'])
            year = QtWidgets.QTableWidgetItem()
            year.setText(str(row['Year']))
            trade_name = QtWidgets.QTableWidgetItem()
            trade_name.setText(str(row['Trade Name']))
            serial = QtWidgets.QTableWidgetItem()
            serial.setText(str(row['Serial No. ']))
            self.table.setItem(index, 0, year)
            self.table.setItem(index, 1, trade_name)
            self.table.setItem(index, 2, serial)

    def file_browser(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', 
            'c:\\',"Excel files (*.xls *.gif)")
        print(fname)
        self.excelFile.setText(fname[0])
            
    def make_cards(self):
        for row in range(self.table.rowCount()):
            try:
                year = self.table.item(row, 0).text()
                trade_name = self.table.item(row, 1).text()
                serial_number = self.table.item(row, 2).text()
                policy_number = self.policy_number.text()
                insurer_name = self.insurer_name.text()
                insured_address = self.insured_address.toPlainText()
                insured_name = self.insured_name.text()
                effective_date = self.effective_date.text()
                expiry_date = self.expiry_date.text()
                with MailMerge('LiabilityCard2020.docx') as document:
                    document.merge(
                        Policy_Number1=policy_number,
                        Insured_Address1=insured_address,
                        Insured1=insured_name,
                        Year1=year,
                        Insurer1=insurer_name,
                        Trade_Name1=trade_name,
                        Effective_Date1=effective_date,
                        Expiry_Date1=expiry_date,
                        Serial_Number1=serial_number,
                        Broker1="STEERS INSURANCE LIMITED"
                    )
                    document.write('test-output.docx')
                    # print(document.get_merge_fields())
                # {'Policy_Number1', 'Insured_Address1', 'Insured1', 'Year1', 'Insurer1', 'Trade_Name1', 'Effective_Date1', 'Broker1', 'Expiry_Date1', 'Serial_Number1'}
            except AttributeError as e:
                print(e)
                pass

app = QtWidgets.QApplication(sys.argv) # Create an instance of QtWidgets.QApplication
window = Ui() # Create an instance of our class
app.exec_() # Start the application