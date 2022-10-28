import sys
import chardet
import sqlite3
import os
from pdfminer.high_level import extract_text
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QWidget, QPushButton
from PyQt5.QtGui import QFont, QCloseEvent

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

        self.btn_load.clicked.connect(self.load)
        self.btn_del.clicked.connect(self.delete)
        self.btn_read.clicked.connect(self.read)
        self.btn_search.clicked.connect(self.search)

        self.read_win = ReadWindow()

        self.con = sqlite3.connect('Books_db.sqlite')
        self.cur = self.con.cursor()

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
                self.listWidget.takeItem(self.listWidget.row(self.listWidget.selectedItems()[0]))
                CUR.execute("""DELETE FROM Books
                                WHERE book_name == ?""",
                            (self.selected(),))
        except SelectedElementError:
            pass
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
                self.read_win.show()
        except SelectedElementError:
            pass

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
        self.remark = RemarkWindow()
        self.flag = True
        self.format = True
        self.current_page = 1
        self.pages = 0
        self.sym = 0
        self.text = ''
        self.btn_next = QPushButton('->', self)
        self.btn_next.setGeometry(510, 670, 30, 20)
        self.btn_previous = QPushButton('<-', self)
        self.btn_previous.setGeometry(20, 670, 30, 20)

        self.btn_font.clicked.connect(self.change_font)
        self.btn_remark.clicked.connect(self.open_remark)
        self.btn_form.clicked.connect(self.change_format)
        self.btn_previous.clicked.connect(self.previous_next)
        self.btn_next.clicked.connect(self.previous_next)
        self.textEdit.setReadOnly(True)

    def change_font(self) -> None:
        self.textEdit.setCurrentFont(QFont('MS Shell Dlg 2', int(self.comboBox.currentText())))

    def open_remark(self) -> None:
        self.remark.show()

    def change_format(self) -> None:
        if self.flag:
            self.text = self.textEdit.toPlainText()
            self.flag = False

        if int(self.comboBox.currentText()) == 8:
            self.pages = len(self.text) // 2400 + 1
            self.sym = 2400
        elif int(self.comboBox.currentText()) == 6:
            self.pages = len(self.text) // 4200 + 1
            self.sym = 4200
        elif int(self.comboBox.currentText()) == 7:
            self.pages = len(self.text) // 3300 + 1
            self.sym = 3300
        elif int(self.comboBox.currentText()) == 9:
            self.pages = len(self.text) // 2000 + 1
            self.sym = 2000
        elif int(self.comboBox.currentText()) == 10:
            self.pages = len(self.text) // 1500 + 1
            self.sym = 1500
        elif int(self.comboBox.currentText()) == 11:
            self.pages = len(self.text) // 1000 + 1
            self.sym = 1000
        elif int(self.comboBox.currentText()) == 12:
            self.pages = len(self.text) // 800 + 1
            self.sym = 800
        elif int(self.comboBox.currentText()) == 14:
            self.pages = len(self.text) // 400 + 1
            self.sym = 400

        if self.format:
            self.textEdit.setText(self.text[:self.sym])
            self.format = False
        else:
            self.textEdit.setText(self.text)
            self.format = True

    def previous_next(self):
        if self.current_page >= self.pages and self.sender().text() == '->' and not self.format:
            self.textEdit.setText('END')
        elif self.current_page >= self.pages and self.sender().text() == '<-' and not self.format:
            self.current_page = self.pages
            self.textEdit.setText(self.text[self.sym * (self.current_page - 1):self.sym * self.current_page])
        elif self.current_page == 1 and self.sender().text() == '<-' and not self.format:
            self.textEdit.setText(self.text[:self.sym])
        elif self.sender().text() == '->' and not self.format and self.current_page:
            self.current_page += 1
            self.textEdit.setText(self.text[self.sym * (self.current_page - 1):self.sym * self.current_page])
        elif self.sender().text() == '<-' and not self.format and self.current_page:
            self.current_page -= 1
            self.textEdit.setText(self.text[self.sym * (self.current_page - 1):self.sym * self.current_page])

    def closeEvent(self, a0: QCloseEvent) -> None:
        main_win.show()
        self.flag = True
        self.format = True


class RemarkWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi('Remark_win.ui', self)

    def closeEvent(self, a0: QCloseEvent) -> None:
        book_path = CUR.execute("""SELECT Book_path FROM Books
                                    WHERE Book_name = ?""",
                                (main_win.selected(),)).fetchone()
        en = encoding(book_path[0])
        r = self.remark_bd()
        if r:
            with open(r[0][0], 'w', encoding=en) as remark:
                remark.write(self.textEdit.toPlainText())
        else:
            with open('remark' + main_win.selected(), 'w+', encoding=en) as remark:
                remark.write(self.textEdit.toPlainText())
                CUR.execute("""UPDATE Books
                               SET remark = ?""",
                            (os.path.basename(remark.name),))
        CON.commit()

    def remark_bd(self) -> list:
        remark_file = 'remark' + main_win.selected()
        remark = CUR.execute("""SELECT remark FROM Books
                                    WHERE remark = ?""",
                             (remark_file,)).fetchall()
        return remark


def encoding(path) -> str:
    with open(path, 'rb') as f:
        return chardet.detect(bytes(f.read()))['encoding']


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
