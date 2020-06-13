import sys
import sqlite3
from PyQt5.QtWidgets import QWidget, QApplication, QPushButton, QGridLayout, QColorDialog
from PyQt5.QtWidgets import QInputDialog, QHBoxLayout, QLabel, QVBoxLayout, QDialog
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QSize, QTimer, QUrl, Qt
from PyQt5 import QtMultimedia
from PyQt5.Qt import Qt
from random import randint
from time import time

levels = {'Новичок': (9, 9, 10),
          'Любитель': (16, 16, 40),
          'Профессионал': (16, 30, 99)}


class Square(QPushButton):
    def __init__(self, x, y, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initUI(x, y)

    def initUI(self, x, y):

        self.setFixedSize(QSize(20, 20))
        self.is_mine = False
        self.with_flag = False
        self.opened = False
        self.number = 0
        self.setStyleSheet("""QPushButton{
                        background-color: #9098ab;
                        border: 2px solid lightgrey;
                        }
                    """)
        self.x = x
        self.y = y

    def open(self):
        if not self.with_flag and not self.opened:
            if self.parentWidget().no_mines:
                for _ in range(self.parentWidget().num_of_mines):
                    while True:
                        row, col = randint(0, len(self.parentWidget().field) - 1),\
                                   randint(0, len(self.parentWidget().field[0]) - 1)
                        if (not self.parentWidget().field[row][col].is_mine
                            and self.x not in range(col - 1, col + 2)
                                and self.y not in range(row - 1, row + 2)):
                            self.parentWidget().field[row][col].is_mine = True
                            for i in range(-1, 2):
                                for j in range(-1, 2):
                                    if (0 <= row + i < len(self.parentWidget().field) and
                                            0 <= col + j < len(self.parentWidget().field[0])):
                                        self.parentWidget().field[row + i][col + j].number += 1
                            break
                self.parentWidget().no_mines = False
            self.opened = True
            self.setStyleSheet("""QPushButton{
                                background-color: #ffffff;
                                border: 1px solid lightgrey;
                            }
                            """)
            self.setIcon(QIcon(None))
            if self.number and not self.is_mine:
                self.setText(str(self.number))

            elif self.is_mine:
                self.setIcon(QIcon('my_mine.png'))
                self.parentWidget().lose()
            else:
                for a in range(-1, 2):
                    for b in range(-1, 2):
                        if (len(self.parentWidget().field) > self.y + a >= 0
                                and len(self.parentWidget().field[0]) > b + self.x >= 0):
                            square_nearby = self.parentWidget().field[self.y + a][self.x + b]
                            if not square_nearby.opened:
                                square_nearby.open()

    def set_or_remove_flag(self):
        if not self.opened:
            if not self.with_flag:
                self.setIcon(QIcon('my_flag.png'))
                self.setIconSize(QSize(19, 19))
                self.parentWidget().num_of_flags -= 1
                self.with_flag = True
            else:
                self.setIcon(QIcon(None))
                self.parentWidget().num_of_flags += 1
                self.with_flag = False
            if self.parentWidget().sounds_allowed:
                self.play_sounds()
        self.parentWidget().flags.setText(str(self.parentWidget().num_of_flags))

    def restart(self):
        self.is_mine = False
        self.with_flag = False
        self.opened = False
        self.number = 0
        self.setStyleSheet("""QPushButton{
                        background-color: #9098ab;
                        border: 1px solid lightgrey;
                        
                        }
                    """)
        self.setText('')
        self.setIcon(QIcon(None))

    def mousePressEvent(self, event):
        if self.parentWidget().new:
            self.parentWidget().begin_timer()
            self.parentWidget().new = False
        button = event.button()
        if not self.parentWidget().blocked:
            if self.parentWidget().sounds_allowed and not self.with_flag and not self.opened:
                self.play_sounds()
            if button == Qt.RightButton:
                self.set_or_remove_flag()

            elif button == Qt.LeftButton:

                self.open()

            if self.parentWidget().check():
                self.parentWidget().win()

        return QPushButton.mousePressEvent(self, event)

    def play_sounds(self):

        def load_mp3(filename):
            media = QUrl.fromLocalFile(filename)
            content = QtMultimedia.QMediaContent(media)
            self.player = QtMultimedia.QMediaPlayer()
            self.player.setMedia(content)

        load_mp3('snap.wav')
        self.player.play()


class MainWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_game = True
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Сапер')
        self.new = True
        self.blocked = False
        self.lost = False
        self.sounds_allowed = False

        self.field = None

        self.no_mines = True

        self.main_layout = QGridLayout(self)

        self.layout_field = QGridLayout(self)
        self.layout_field.setSpacing(0)

        self.upper_layout = QHBoxLayout(self)
        self.upper_layout.setSpacing(1)
        self.main_layout.addLayout(self.upper_layout, 0, 0)
        self.main_layout.addLayout(self.layout_field, 1, 0)

        clock = QLabel()
        clock.setPixmap(QPixmap('my_clock.png'))
        self.upper_layout.addWidget(clock)

        self.height = 0
        self.width = 0
        self.name = ''
        self.num_of_mines = 0
        self.num_of_flags = 0
        self.no_mines = True

        self.timer = QTimer()
        self.timer.timeout.connect(self.change_time)
        self.timer.start(1000)

        self.time = QLabel(self)
        self.time.setText('000')

        self.low_layout = QVBoxLayout(self)

        self.restart = QPushButton('Начать заново')
        self.restart.clicked.connect(self.nullify)
        self.low_layout.addWidget(self.restart)

        self.statistic = QPushButton('Статистика')
        self.statistic.clicked.connect(self.show_records)
        self.low_layout.addWidget(self.statistic)

        self.resBtn = QPushButton('Мои результаты')
        self.resBtn.clicked.connect(self.show_myresults)
        self.low_layout.addWidget(self.resBtn)

        self.settingsBtn = QPushButton('Настройки')
        self.settingsBtn.clicked.connect(self.show_settings)
        self.low_layout.addWidget(self.settingsBtn)

        self.main_layout.addLayout(self.low_layout, 2, 0)

        if self.first_game:
            self.registration()
        self.field = [[Square(i, j) for i in range(self.width)] for j in range(self.height)]
        for i in range(self.height):
            for j in range(self.width):
                self.layout_field.addWidget(self.field[i][j], i, j)
        self.flags = QLabel(self)
        self.flags.setText(str(self.num_of_flags))
        f = self.flags.font()
        f.setPointSize(20)
        self.flags.setFont(f)
        self.time.setFont(f)
        self.upper_layout.addWidget(self.time)

        flag = QLabel()
        flag.resize(QSize(20, 20))
        flag.setPixmap(QPixmap('my_flag.png'))

        self.upper_layout.addWidget(flag)
        self.upper_layout.addWidget(self.flags)

        self.left_layout = QVBoxLayout(self)

        self.message = QLabel(self)
        self.show()

    def change_time(self):
        if not self.new and not self.blocked:
            self.time.setText(str((time() - self.beginning_time) // 1)[:-2:].rjust(3, '0'))

    def begin_timer(self):
        self.beginning_time = int(time())

    def lose(self):
        if not self.lost:
            self.blocked = True
            self.lost = True
            for row in self.field:
                for sq in row:
                    sq.open()
            self.add_to_db(0)
            self.show_endgame(0)

    def win(self):
        self.blocked = True
        self.add_to_db(1)
        self.show_endgame(1)

    def add_to_db(self, status):
        self.ending_time = int((time() - self.beginning_time) // 1)
        con = sqlite3.connect("games.db")
        cur = con.cursor()
        if not cur.execute("""SELECT id from Gamers WHERE name = ?""", (self.name,)).fetchone():
            cur.execute("""INSERT INTO 
                    Gamers (name)
                     VALUES(?)""", (self.name,))
        cur.execute("""INSERT INTO
        Records (duration,gamer,level,result)
         VALUES(?,?,?,?)""",
                    (self.ending_time,
                     cur.execute("""SELECT id from Gamers
                     WHERE name = ?""", (self.name,)).fetchone()[0],
                     list(levels.keys()).index(self.level) + 1,
                     status))
        con.commit()

    def check(self):
        for row in self.field:
            for sq in row:
                if (not sq.opened and not sq.is_mine)\
                        or self.lost:
                    return False
        return True

    def registration(self):
        name, okBtnPressed = QInputDialog.getText(self, "Регистрация",
                                               "Введите имя:")
        if okBtnPressed:
            self.name = name
            self.level, okBtnPressed = QInputDialog.getItem(self, "Сложность",
                                                       f'Добро пожаловать, {name}!\n'
                                                       f'Выберите уровень:',
                                                       ("Новичок", "Любитель", "Профессионал"),
                                                       0, False)
            if okBtnPressed:
                self.height, self.width, self.num_of_mines = levels[self.level]
                self.num_of_flags = self.num_of_mines
            else:
                sys.exit(0)

        else:
            sys.exit(0)

    def nullify(self):
        self.new = True
        self.blocked = False
        self.lost = False
        self.no_mines = True
        self.time.setText('000')
        self.num_of_flags = self.num_of_mines
        self.flags.setText(str(self.num_of_flags))
        for row in self.field:
            for square in row:
                square.restart()

    def show_records(self):
        s = Statistics()
        s.exec_()

    def show_settings(self):
        n = Settings(self)
        n.exec_()

    def show_endgame(self, number):
        e = Endgame(number, self)
        e.exec_()

    def show_myresults(self):
        e = MyResults(self)
        e.exec_()


class MyResults(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Ваши результаты')
        con = sqlite3.connect("games.db")
        cur = con.cursor()
        num = cur.execute("""SELECT id
            FROM Gamers WHERE name = ?""", (self.parentWidget().name,)).fetchone()
        if num:
            info = cur.execute("""SELECT duration, result, level
                FROM Records WHERE gamer = ?""", num).fetchall()
        else:
            info = []
        con.commit()

        self.lay = QHBoxLayout(self)
        self.lay.setSpacing(50)
        for difficulty in range(len(list(levels.keys()))):
            self.text = QLabel(self)
            message = str(list(levels.keys())[difficulty]) + '\n'
            print([info[i] for i in range(len(info)) if info[i][2] == difficulty + 1])
            if [info[i] for i in range(len(info)) if info[i][2] == difficulty + 1]:
                if [info[i][0] for i in range(len(info))
                        if info[i][1] == 1 and info[i][2] == difficulty + 1]:
                    min_time = min([info[i][0] for i in range(len(info))
                                    if info[i][1] == 1 and info[i][2] == difficulty + 1])
                else:
                    min_time = 'нет данных'
                message += f'Лучшее время:' \
                           f' {min_time}\n'
                wins = len([info[i] for i in range(len(info))
                            if info[i][1] and info[i][2] == difficulty + 1])
                message += f'Побед: {wins}\n'
                fails = len([info[i] for i in range(len(info)) if not info[i][1] and info[i][2] == difficulty + 1])
                message += f'Поражений: {fails}\n'
                message += f'Процент побед: {int(wins / (wins + fails) * 100 // 1)}%'
            else:
                message += 'Нет данных'
            self.text.setText(message)
            self.lay.addWidget(self.text)


class Statistics(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Статистика')

        def get_best_5(level):
            con = sqlite3.connect("games.db")
            cur = con.cursor()
            top = sorted(list(cur.execute("""SELECT gamer, duration
            FROM Records WHERE level = ? and result = ?""", (level, 1)).fetchall()), key=lambda x: x[1])[:5:]
            gamers = [cur.execute("""SELECT name from Gamers WHERE id = ?""",
                                  (i,)).fetchone() for i in [i[0] for i in top]]
            results = [[gamers[i][0], top[i][1]] for i in range(len(top))]
            con.commit()
            return results

        self.lay = QHBoxLayout(self)
        self.lay.setSpacing(50)
        for difficulty in range(len(list(levels.keys()))):
            self.text = QLabel(self)
            message = str(list(levels.keys())[difficulty])
            if get_best_5(difficulty + 1):
                for point in get_best_5(difficulty + 1):
                    message += '\n' + "\t".join(map(str, point))
            else:
                message += '\n' + 'Нет данных'
            self.text.setText(message)
            self.lay.addWidget(self.text)


class Settings(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Настройки')
        self.setFixedSize(200, 30)
        redb = QCheckBox('Включить/выключить звук ', self)
        if self.parentWidget().sounds_allowed:
            redb.setCheckState(Qt.Checked)
        else:
            redb.setCheckState(Qt.Unchecked)
        redb.clicked[bool].connect(self.sounds_change)

    def sounds_change(self, state):
        if state:
            self.parentWidget().sounds_allowed = True
        else:
            self.parentWidget().sounds_allowed = False


class Endgame(QDialog):
    def __init__(self, result, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = result
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Игра окончена')
        message = QLabel(self)
        self.lay = QHBoxLayout(self)
        text = ''
        if self.result:
            text += 'Вы выиграли!\n'
        else:
            text += 'Вы проиграли!\n'
        text += f'Время: {self.parentWidget().ending_time} сек.\n'
        f = message.font()
        f.setPointSize(20)
        message.setFont(f)
        message.setText(text)
        self.lay.addWidget(message)


if __name__ == '__main__':
    app = QApplication([])
    w = MainWidget()
    sys.exit(app.exec())
