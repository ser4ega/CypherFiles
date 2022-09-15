from PyQt5.QtWidgets import *
import sys
import sqlite3
from PyQt5.QtGui import *
from PyQt5 import Qt
import hashlib
from cryptography.fernet import Fernet
def createDB():
    try:
        sqlite_connection = sqlite3.connect('sqlite_python.db')
        query_check_exists = "SELECT name FROM sqlite_master WHERE type='table' AND name='Files_to_Hide';"
        sqlite_create_table_query = '''CREATE TABLE Files_to_Hide (
                                    id INTEGER PRIMARY KEY,
                                    Path TEXT NOT NULL UNIQUE,
                                    Password text NOT NULL,
                                    Key text NOT NULL
                                    );'''
        cursor = sqlite_connection.cursor()
        print("База данных подключена к SQLite")
        cursor.execute(query_check_exists)
        sqlite_connection.commit()
        result = cursor.fetchall()
        if len(result) == 0:
            cursor.execute(sqlite_create_table_query)
            sqlite_connection.commit()
            print("Таблица Files_to_Hide создана")
        else:
            print("Таблица Files_to_Hide существует")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)

    finally:
        if (sqlite_connection):
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")



def writeToDB(path, password):    
    try:
        password = hashlib.md5(password.encode()).hexdigest()
        # сперва зашифруем
        key = Fernet.generate_key().decode("utf-8") 
        res = True
        sqlite_connection = sqlite3.connect('sqlite_python.db')
        cursor = sqlite_connection.cursor()
        print("База данных подключена к SQLite")
        sqlite_insert_query = f"""INSERT INTO Files_to_Hide
                            (Path, Password, Key)  VALUES  ('{path}', '{password}', '{key}')"""
        count = cursor.execute(sqlite_insert_query)
        sqlite_connection.commit()
        print("Запись успешно вставлена ​​в таблицу sqlitedb_developers ", cursor.rowcount)
        cursor.close()
        encrypt(path, key)
        
    except sqlite3.Error as error:
        print("Не удалось вставить данные в таблицу sqlite")
        print("Класс исключения: ", error.__class__)
        print("Исключение", error.args)
        print("Печать подробноcтей исключения SQLite: ")
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(exc_type, exc_value, exc_tb)
        sqlite_connection.close()
        res = False
    finally:
        if (sqlite_connection):
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")
            return res

class MainWidget(QWidget):
    
    def __init__(self):
        super().__init__()
        QWidget.__init__(self)
        layout = QGridLayout()
        self.setLayout(layout)
        self.setWindowTitle("Drag and Drop")
        self.resize(720, 480)
        self.setAcceptDrops(True)
        self.listwidget = QListWidget()
        self.listwidget.addItems(self.fillListFromDB()) 
        self.listwidget.clicked.connect(self.clicked)
        layout.addWidget(self.listwidget) 

    def fillListFromDB(self)    :
        try:
            sqlite_connection = sqlite3.connect('sqlite_python.db')
            cursor = sqlite_connection.cursor()
            print("База данных подключена к SQLite")
            sqlite_insert_query = "SELECT Path FROM Files_to_Hide;"
            cursor.execute(sqlite_insert_query)
            sqlite_connection.commit()
            result = [item[0] for item in cursor.fetchall()]
            print(result)
            cursor.close()
            return result

        except sqlite3.Error as error:
            print("Не удалось найти запись в базе данных")
            print("Класс исключения: ", error.__class__)
            print("Исключение", error.args)
            print("Печать подробноcтей исключения SQLite: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(exc_type, exc_value, exc_tb)
        finally:
            if (sqlite_connection):
                sqlite_connection.close()
                print("Соединение с SQLite закрыто")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            print(f)
            self.showDialog(f)


    def showDialog(self,f):
        pass1, ok = QInputDialog.getText(self, 'Input Password',
            'Input Password:', QLineEdit.Password)
        if ok:
            pass2, ok = QInputDialog.getText(self, 'Input Password Again',
                'Input Password again:', QLineEdit.Password)
            if ok:
                if pass1!=pass2:
                    QMessageBox.question(self, 'Error', "Введенные пароли не совпадают", QMessageBox.Ok, QMessageBox.Ok)
                    self.showDialog(f)
                elif  pass1 == '':
                    QMessageBox.question(self, 'Error', "Пустой пароль недопустим", QMessageBox.Ok, QMessageBox.Ok)
                    self.showDialog(f)
                else:
                    resOk = writeToDB(f, pass1)
                    if resOk!=True:
                        QMessageBox.question(self, 'Error', "Повторное добавление объекта в БД недопустимо", QMessageBox.Ok, QMessageBox.Ok)
                    else:
                        self.listwidget.insertItem(self.listwidget.count(), f) 
                        QMessageBox.question(self, 'Done', f"Файл {f} зашифрован", QMessageBox.Ok, QMessageBox.Ok)    

    def clicked(self, qmodelindex):
        item = self.listwidget.currentItem()
        print(item.text())
        self.show_item(item.text())
    
    def show_item(self,f):
        pass1, ok = QInputDialog.getText(self, 'Input Password',
            'Input Password:', QLineEdit.Password)        
        passFromDB = selectPassHashFromDb(f)
        if ok:
            pass1 = hashlib.md5(pass1.encode()).hexdigest()
            if passFromDB is None:
                QMessageBox.question(self, 'Error', "Не удалось найти запись в базе данных", QMessageBox.Ok, QMessageBox.Ok)                    

            elif pass1!=passFromDB:
                QMessageBox.question(self, 'Error', "Пароли не совпадают", QMessageBox.Ok, QMessageBox.Ok)
                self.show_item(f)    
            else:
                decrypt(f, getKeyFromDB(f))  
                row = self.listwidget.findItems(f, Qt.Qt.MatchExactly)[0]
                self.listwidget.takeItem(self.listwidget.row(row))
                QMessageBox.question(self, 'Done', f"Файл {f} расшифрован", QMessageBox.Ok, QMessageBox.Ok)
def getKeyFromDB(Path):
    try:
        sqlite_connection = sqlite3.connect('sqlite_python.db')
        cursor = sqlite_connection.cursor()
        print("База данных подключена к SQLite")

        sqlite_insert_query = f"""SELECT Key
                        FROM Files_to_Hide
                        where Path = '{Path}';"""
        cursor.execute(sqlite_insert_query)
        sqlite_connection.commit()
        result = cursor.fetchone()[0]
        print(result)
        sqlite_insert_query = f"""DELETE
                        FROM Files_to_Hide
                        where Path = '{Path}';"""
        cursor.execute(sqlite_insert_query)
        sqlite_connection.commit()
        cursor.close()
        return result

    except sqlite3.Error as error:
        print("Не удалось найти запись в базе данных")
        print("Класс исключения: ", error.__class__)
        print("Исключение", error.args)
        print("Печать подробноcтей исключения SQLite: ")
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(exc_type, exc_value, exc_tb)
    finally:
        if (sqlite_connection):
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")

def selectPassHashFromDb(Path):
    try:
        sqlite_connection = sqlite3.connect('sqlite_python.db')
        cursor = sqlite_connection.cursor()
        print("База данных подключена к SQLite")
        sqlite_insert_query = f"""SELECT Password
                        FROM Files_to_Hide
                        where Path = '{Path}';"""        
        cursor.execute(sqlite_insert_query)
        sqlite_connection.commit()
        result = cursor.fetchone()[0]
        print(result)
        cursor.close()
        return result

    except sqlite3.Error as error:
        print("Не удалось найти запись в базе данных")
        print("Класс исключения: ", error.__class__)
        print("Исключение", error.args)
        print("Печать подробноcтей исключения SQLite: ")
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(exc_type, exc_value, exc_tb)
    finally:
        if (sqlite_connection):
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")            

def encrypt(filename, key):
# Зашифруем файл и записываем его
    f = Fernet(key)
    with open(filename, 'rb') as file:
        # прочитать все данные файла
        file_data = file.read()
        encrypted_data = f.encrypt(file_data)
    with open(filename, 'wb') as file:
        file.write(encrypted_data)

def decrypt(filename, key):
# Расшифруем файл и записываем его
    f = Fernet(key)
    with open(filename, 'rb') as file:
        # читать зашифрованные данные
        encrypted_data = file.read()
    # расшифровать данные
    decrypted_data = f.decrypt(encrypted_data)
    # записать оригинальный файл
    with open(filename, 'wb') as file:
        file.write(decrypted_data)

if __name__ == '__main__':
    createDB()
    app = QApplication(sys.argv)
    ui = MainWidget()
    ui.show()
    sys.exit(app.exec_())
    
    
