import sys
import chardet
import sqlite3
import os
from pdfminer.high_level import extract_text
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QWidget
from PyQt5.QtGui import QFont, QCloseEvent, QColor, QIcon

CON = sqlite3.connect('Books_db.sqlite')
CUR = CON.cursor()


class NameListError(Exception):
    pass


class SelectedElementError(Exception):
    pass


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi('Main_win.ui', self)
        self.setWindowTitle('Главное окно')
        self.setWindowIcon(QIcon('book_pic.png'))

        self.btn_load.clicked.connect(self.load)
        self.btn_del.clicked.connect(self.delete)
        self.btn_read.clicked.connect(self.read)
        self.btn_search.clicked.connect(self.search)

        self.read_win = read_win

        self.books_from_bd()

    def load(self) -> None:
        path = QFileDialog.getOpenFileName(self,
                                           'Выбрать текстовый файл', '', 'Текст (*.txt);;Текст (*.pdf)')[0]

        name = path.split('/')
        if name[-1][-4:] == '.pdf':
            with open(name[-1][:-4] + '.txt', 'w+') as new_name:
                new_name.write(extract_text(path))

        try:
            if self.file_in_list(name[-1]):
                if name[-1][-4:] == '.pdf':
                    with open(name[-1][:-4] + '.txt', 'w+') as new_name:
                        new_name.write(extract_text(path))
                        self.listWidget.addItem(name[-1])

                        CUR.execute("""INSERT INTO books(book_path, book_name) VALUES(?, ?)""",
                                    (name[-1][:-4] + '.txt', name[-1],))
                else:
                    self.listWidget.addItem(name[-1])

                    CUR.execute("""INSERT INTO books(book_path, book_name) VALUES(?, ?)""",
                                (path, name[-1],))
            CON.commit()
        except NameListError:
            pass

    def file_in_list(self, name: str) -> bool:
        for i in range(len(self.listWidget)):
            if name == self.listWidget.item(i).text():
                raise NameListError
        return True

    def books_from_bd(self) -> None:
        books_bd = CUR.execute("""SELECT book_name FROM Books""")
        for book in books_bd:
            self.listWidget.addItem(book[0])

    def delete(self) -> None:
        try:
            if self.is_selected():
                item = self.listWidget.selectedItems()[0]
                self.listWidget.takeItem(self.listWidget.row(item))
                CUR.execute("""DELETE FROM Books
                                WHERE book_name == ?""",
                            (item.text(),))
        except SelectedElementError:
            self.statusBar.showMessage('Пожалуйста выберите файл')
        CON.commit()

    def read(self) -> None:
        try:
            if self.is_selected():
                book_path = CUR.execute("""SELECT Book_path FROM Books
                                                    WHERE Book_name = ?""",
                                        (self.listWidget.selectedItems()[0].text(),)).fetchone()
                en = encoding(book_path[0])
                with open(book_path[0], encoding=en) as book:
                    self.read_win.textEdit.setText(book.read())
                self.hide()
                read_win.show()
                self.statusBar.showMessage('Ok')
        except SelectedElementError:
            self.statusBar.showMessage('Пожалуйста выберите файл')

    def search(self) -> None:
        self.listWidget.clear()
        if self.search_line.text():
            lines = CUR.execute("""SELECT book_name FROM Books
                                            WHERE book_name like ?""",
                                (f"%{self.search_line.text()}%",)).fetchall()
            for elem in lines:
                self.listWidget.addItem(elem[0])
        else:
            self.books_from_bd()

    def selected(self) -> str:
        return self.listWidget.selectedItems()[0].text()

    def is_selected(self):
        if self.listWidget.selectedItems():
            return True
        raise SelectedElementError

    def closeEvent(self, a0: QCloseEvent) -> None:
        CON.close()


class ReadWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi('Read_win.ui', self)
        self.textEdit.setReadOnly(True)

        self.setWindowTitle('Окно для чтения')
        self.setWindowIcon(QIcon('book_pic.png'))
        self.theme = 'original'

        self.win_style_sheet_white = """background-color: rgb(25, 25, 25);"""
        self.other_style_sheet_white = """
                        background-color: rgb(50, 50, 50);
                        color: rgb(255, 255, 255);
                        """
        self.win_style_sheet_black = """background-color: rgb(240, 240, 240);"""
        self.other_style_sheet_black = """
                                background-color: rgb(240, 240, 240);
                                color: rgb(0, 0, 0);
                                """
        self.win_style_sheet_original = """background-color: rgb(90, 49, 19);"""
        self.other_style_sheet_original = """background-color: rgb(232, 183, 128);
                                             color: rgb(0, 0, 0);
                                             """

        self.btn_font.clicked.connect(self.change_font)
        self.btn_remark.clicked.connect(self.open_remark)
        self.btn_size.clicked.connect(self.show_full_screen)
        self.btn_theme.clicked.connect(self.change_theme)

    def change_font(self) -> None:
        self.textEdit.selectAll()
        self.textEdit.setCurrentFont(QFont(self.fontComboBox.currentText(), int(self.comboBox.currentText())))

    def open_remark(self) -> None:
        remark_win.show()

    def change_theme(self):
        if self.theme == 'original':
            self.setStyleSheet(self.win_style_sheet_white)
            self.btn_font.setStyleSheet(self.other_style_sheet_white)
            self.btn_remark.setStyleSheet(self.other_style_sheet_white)
            self.btn_size.setStyleSheet(self.other_style_sheet_white)
            self.btn_theme.setStyleSheet(self.other_style_sheet_white)
            self.groupBox.setStyleSheet(self.other_style_sheet_white)
            self.groupBox_2.setStyleSheet(self.other_style_sheet_white)
            self.comboBox.setStyleSheet(self.other_style_sheet_white)
            self.fontComboBox.setStyleSheet(self.other_style_sheet_white)
            self.textEdit.setStyleSheet("""background-color: rgb(0,0,0)""")
            self.textEdit.selectAll()
            self.textEdit.setTextColor(QColor('white'))
            remark_win.change_theme()
            self.theme = 'black'
        elif self.theme == 'black':
            self.setStyleSheet(self.win_style_sheet_black)
            self.btn_font.setStyleSheet(self.other_style_sheet_black)
            self.btn_remark.setStyleSheet(self.other_style_sheet_black)
            self.btn_size.setStyleSheet(self.other_style_sheet_black)
            self.btn_theme.setStyleSheet(self.other_style_sheet_black)
            self.groupBox.setStyleSheet(self.other_style_sheet_black)
            self.groupBox_2.setStyleSheet(self.other_style_sheet_black)
            self.comboBox.setStyleSheet(self.other_style_sheet_black)
            self.fontComboBox.setStyleSheet(self.other_style_sheet_black)
            self.textEdit.setStyleSheet("""background-color: rgb(255,255,255)""")
            self.textEdit.selectAll()
            self.textEdit.setTextColor(QColor('black'))
            remark_win.change_theme()
            self.theme = 'white'
        else:
            self.setStyleSheet(self.win_style_sheet_original)
            self.btn_font.setStyleSheet(self.other_style_sheet_original)
            self.btn_remark.setStyleSheet(self.other_style_sheet_original)
            self.btn_size.setStyleSheet(self.other_style_sheet_original)
            self.btn_theme.setStyleSheet(self.other_style_sheet_original)
            self.groupBox.setStyleSheet(self.other_style_sheet_original)
            self.groupBox_2.setStyleSheet(self.other_style_sheet_original)
            self.comboBox.setStyleSheet(self.other_style_sheet_original)
            self.fontComboBox.setStyleSheet(self.other_style_sheet_original)
            self.textEdit.setStyleSheet("""background-color: rgb(232, 183, 128);""")
            self.textEdit.selectAll()
            self.textEdit.setTextColor(QColor(0, 0, 0))
            remark_win.change_theme()
            self.theme = 'original'

    def show_full_screen(self):
        read_full_screen.showFullScreen()
        read_full_screen.textEdit.setText(self.textEdit.toPlainText())
        self.hide()

    def closeEvent(self, a0: QCloseEvent) -> None:
        main_win.show()


class RemarkWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi('Remark_win.ui', self)

        self.setWindowTitle('Окно для заметок')
        self.setWindowIcon(QIcon('book_pic.png'))
        self.theme = 'original'

        self.win_style_sheet_white = """background-color: rgb(25, 25, 25);"""
        self.win_style_sheet_black = """background-color: rgb(240, 240, 240);"""
        self.win_style_sheet_original = """background-color: rgb(232, 183, 128)"""

    def closeEvent(self, a0: QCloseEvent) -> None:
        book_path = CUR.execute("""SELECT Book_path FROM Books
                                    WHERE Book_name = ?""",
                                (main_win.selected(),)).fetchone()
        en = encoding(book_path[0])
        r = self.remark_bd()
        if r:
            with open(os.path.split(os.path.abspath('main.py'))[0] + '/remarks' + r[0][0], 'w', encoding=en) as remark:
                remark.write(self.textEdit.toPlainText())
        else:
            with open(os.path.split(os.path.abspath('main.py'))[0] + '/remarks' + '/remark' + main_win.selected(), 'w+', encoding=en) as remark:
                remark.write(self.textEdit.toPlainText())
                CUR.execute("""UPDATE Books
                               SET remark = ?
                               WHERE Book_name = ?""",
                            (os.path.basename(remark.name), main_win.selected()))
        CON.commit()

    def change_theme(self):
        if self.theme == 'original':
            self.setStyleSheet(self.win_style_sheet_white)
            self.textEdit.setStyleSheet("""background-color: rgb(10,10,10)""")
            self.textEdit.selectAll()
            self.textEdit.setTextColor(QColor(255, 255, 255))
            self.theme = 'black'
        elif self.theme == 'black':
            self.setStyleSheet(self.win_style_sheet_black)
            self.textEdit.setStyleSheet("""background-color: rgb(250,250,250)""")
            self.textEdit.selectAll()
            self.textEdit.setTextColor(QColor(0, 0, 0))
            self.theme = 'white'
        else:
            self.setStyleSheet(self.win_style_sheet_original)
            self.textEdit.setStyleSheet("""background-color: rgb(232,183,128)""")
            self.textEdit.selectAll()
            self.textEdit.setTextColor(QColor(0, 0, 0))
            self.theme = 'white'

    def remark_bd(self) -> list:
        remark_file = 'remark' + main_win.selected()
        remark = CUR.execute("""SELECT remark FROM Books
                                    WHERE remark = ?""",
                             (remark_file,)).fetchall()
        return remark


class ReadFullScreenWin(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('Read_full_screen.ui', self)
        self.textEdit.setReadOnly(True)
        self.setWindowIcon(QIcon('book_pic.png'))
        self.theme = 'original'

        self.win_style_sheet_white = """background-color: rgb(25, 25, 25);"""
        self.other_style_sheet_white = """
                                background-color: rgb(50, 50, 50);
                                color: rgb(255, 255, 255);
                                """
        self.win_style_sheet_black = """background-color: rgb(240, 240, 240);"""
        self.other_style_sheet_black = """
                                        background-color: rgb(240, 240, 240);
                                        color: rgb(0, 0, 0);
                                        """

        self.win_style_sheet_original = """background-color: rgb(90, 49, 19);"""
        self.other_style_sheet_original = """background-color: rgb(232, 183, 128);
                                                color: rgb(0, 0, 0);
                                                """

        self.btn_close.clicked.connect(self.close)
        self.btn_remark.clicked.connect(self.open_remark)
        self.btn_font.clicked.connect(self.change_font)
        self.btn_theme.clicked.connect(self.change_theme)

    def change_font(self):
        self.textEdit.selectAll()
        self.textEdit.setCurrentFont(QFont(self.fontComboBox.currentText(), int(self.comboBox.currentText())))

    def change_theme(self):
        if self.theme == 'original':
            self.setStyleSheet(self.win_style_sheet_white)
            self.btn_font.setStyleSheet(self.other_style_sheet_white)
            self.btn_remark.setStyleSheet(self.other_style_sheet_white)
            self.btn_close.setStyleSheet(self.other_style_sheet_white)
            self.btn_theme.setStyleSheet(self.other_style_sheet_white)
            self.comboBox.setStyleSheet(self.other_style_sheet_white)
            self.fontComboBox.setStyleSheet(self.other_style_sheet_white)
            self.label.setStyleSheet("""color: rgb(255,255,255)""")
            self.textEdit.setStyleSheet("""background-color: rgb(0,0,0)""")
            self.textEdit.selectAll()
            self.textEdit.setTextColor(QColor('white'))
            remark_win.change_theme()
            self.theme = 'black'
        elif self.theme == 'black':
            self.setStyleSheet(self.win_style_sheet_black)
            self.btn_font.setStyleSheet(self.other_style_sheet_black)
            self.btn_remark.setStyleSheet(self.other_style_sheet_black)
            self.btn_close.setStyleSheet(self.other_style_sheet_black)
            self.btn_theme.setStyleSheet(self.other_style_sheet_black)
            self.comboBox.setStyleSheet(self.other_style_sheet_black)
            self.fontComboBox.setStyleSheet(self.other_style_sheet_black)
            self.label.setStyleSheet("""color: rgb(0,0,0)""")
            self.textEdit.setStyleSheet("""background-color: rgb(255,255,255)""")
            self.textEdit.selectAll()
            self.textEdit.setTextColor(QColor('black'))
            remark_win.change_theme()
            self.theme = 'white'
        else:
            self.setStyleSheet(self.win_style_sheet_original)
            self.btn_font.setStyleSheet(self.other_style_sheet_original)
            self.btn_remark.setStyleSheet(self.other_style_sheet_original)
            self.btn_close.setStyleSheet(self.other_style_sheet_original)
            self.btn_theme.setStyleSheet(self.other_style_sheet_original)
            self.comboBox.setStyleSheet(self.other_style_sheet_original)
            self.fontComboBox.setStyleSheet(self.other_style_sheet_original)
            self.label.setStyleSheet("""color: rgb(0,0,0)""")
            self.textEdit.setStyleSheet("""background-color: rgb(232, 183, 128);""")
            self.textEdit.selectAll()
            self.textEdit.setTextColor(QColor(0, 0, 0))
            remark_win.change_theme()
            self.theme = 'original'

    def open_remark(self):
        remark_win.show()

    def closeEvent(self, a0: QCloseEvent) -> None:
        read_win.show()


def encoding(path) -> str:
    with open(path, 'rb') as f:
        return chardet.detect(bytes(f.read()))['encoding']


if __name__ == '__main__':
    app = QApplication(sys.argv)
    read_win = ReadWindow()
    read_full_screen = ReadFullScreenWin()
    remark_win = RemarkWindow()
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
