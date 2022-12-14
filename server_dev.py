import socket
from select import select
import sqlite3
from datetime import datetime, date
import hashlib

tasks = []

to_read = {}
to_write = {}

clients_dict = {}
clients_count = {}
clients_name = {}
CHECKER = {}


class SQL_database:  # Класс базы данных, который отвечает за авторизацию и ведение логов
    def AddUser(self, login, password, secret_question,
                secret_answer):  # Функция добавления нового пользователя в базу данных
        with sqlite3.connect('Users.db') as db:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE login= ?;", (login,))
            ans = cursor.fetchall()
        if len(ans) != 0:
            return 'create user already exist'
        else:
            current_date = '.'.join(
                str(date(int(datetime.now().year), int(datetime.now().month), int(datetime.now().day))).split('-'))
            new_password = hashlib.md5(password.encode('utf-8')).hexdigest()
            new_secret_answer = hashlib.md5(secret_answer.encode('utf-8')).hexdigest()
            with sqlite3.connect('Users.db') as db:
                cursor = db.cursor()
                cursor.execute("""INSERT INTO users(login, password, secret_question, secret_answer, reg_date, win, lose)
                                VALUES(?, ?, ?, ?, ?, ?, ?);""",
                               (login, new_password, secret_question, new_secret_answer, current_date, 0, 0))
                return 'create 1'

    def Auth(self, login, password):  # Функция авторизации пользователя
        try:
            with sqlite3.connect('Users.db') as db:
                cursor = db.cursor()
                cursor.execute("SELECT password FROM users WHERE login=?;", (login,))
                ans_password = cursor.fetchall()[0][0]
                new_password = hashlib.md5(password.encode('utf-8')).hexdigest()
            if new_password == ans_password:
                return login
            else:
                return 'incorrect password'
        except Exception:
            return 'incorrect login'

    def Forgot_password_login_check(self,
                                    login):  # Когда пользователь забывает пароль, первым делом необходимо указать логин, эта функция его проверяет
        with sqlite3.connect('Users.db') as db:
            cursor = db.cursor()
            try:
                check = cursor.execute("SELECT secret_question FROM users WHERE login=?;", (login,)).fetchone()[0]
                return True
            except Exception:
                return False

    def Get_question(self,
                     login):  # После того, как логин был верно указан, пользователю возвращается секретный вопрос, на который необходимо ответить
        with sqlite3.connect('Users.db') as db:
            cursor = db.cursor()
            question = cursor.execute("SELECT secret_question FROM users WHERE login=?;", (login,)).fetchone()[0]
            return question

    def Send_answer(self, login,
                    answer):  # Сюда присылается секретный вопрос, он хешируется и сравнивается в сохраненным в бд хешем
        with sqlite3.connect('Users.db') as db:
            cursor = db.cursor()
            input_answer = hashlib.md5(answer.encode('utf-8')).hexdigest()
            cursor.execute("SELECT secret_answer FROM users WHERE login=?;", (login,))
            secret_answer = cursor.fetchall()[0][0]
            if secret_answer == input_answer:
                return True
            else:
                return False

    def get_info(self, login):  # функция, которая возвращает дату регистрации по логину пользователя
        with sqlite3.connect('users.db') as db:
            cursor = db.cursor()
            data = cursor.execute("SELECT reg_date, win, lose FROM users WHERE login=?;", (login,)).fetchone()
            result = f'{data[0]} {data[1]} {data[2]}'
            return result

    def New_password(self, login, new_password):  # Функция, которая перезаписывает хеш пароля в бд
        new_password_hash = hashlib.md5(new_password.encode('utf-8')).hexdigest()
        with sqlite3.connect('Users.db') as db:
            cursor = db.cursor()
            cursor.execute("UPDATE users SET password=? WHERE login=?;", (new_password_hash, login))
            cursor.execute('select * from users;')
            a = cursor.fetchall()

    def add_log(self, login, sign_in):  # Функция, которая добавляет новый лог при авторизации или при выходе
        with sqlite3.connect('Users.db') as db:
            cursor = db.cursor()
            current_date = datetime.now().strftime("%Y %m %d %H %M %S").split()
            date = '.'.join(current_date[:3])
            time = '.'.join(current_date[3:])
            datetime_for_log = date + '-' + time
            login_id = cursor.execute("""SELECT id FROM users WHERE login = ?""", (login,)).fetchall()[0][0]
            cursor.execute("""INSERT INTO logs(datetime, sign_in, fk_users_login_id) VALUES(?, ?, ?)""",
                           (datetime_for_log, sign_in, login_id))
            db.commit()

    def add_game_log(self, player1, player2, game_result):
        with sqlite3.connect('Users.db') as db:
            cursor = db.cursor()
            current_date = datetime.now().strftime("%Y %m %d %H %M %S").split()
            date = '.'.join(current_date[:3])
            time = '.'.join(current_date[3:])
            datetime_for_log = date + '-' + time
            player1_id = cursor.execute("""SELECT id FROM users WHERE login = ?""", (player1,)).fetchone()[0]
            player2_id = cursor.execute("""SELECT id FROM users WHERE login = ?""", (player2,)).fetchone()[0]
            cursor.execute("""INSERT INTO game_log(date, player_1, player_2, game_result) VALUES(?, ?, ?, ?)""",
                           (datetime_for_log, player1_id, player2_id, game_result))
            if game_result == 'WIN':
                cursor.execute("""UPDATE users SET win = win + 1 WHERE id = ?""", (player1_id,))
            elif game_result == 'LOSE':
                cursor.execute("""UPDATE users SET lose = lose + 1 WHERE id = ?""", (player1_id,))
            CHECKER[player1] = True
            db.commit()

    def Get_users_list(self, info, filter_info):  # Возвращает список пользователей, основанный на примененных фильтрах
        with sqlite3.connect('Users.db') as db:
            cursor = db.cursor()
            if len(info) != 0:
                if filter_info == 'login':
                    result = cursor.execute("SELECT id, login, reg_date FROM users WHERE login=?;", (info,)).fetchall()
                else:
                    result = cursor.execute("SELECT id, login, reg_date FROM users WHERE reg_date=?",
                                            (info,)).fetchall()
            else:
                result = cursor.execute("SELECT id, login, reg_date FROM users;").fetchall()
            return result


database = SQL_database()


def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('192.168.43.131', 5002))
    server_socket.listen(2)

    while True:
        yield ('read', server_socket)
        client_socket, addr = server_socket.accept()  # read
        clients_dict[client_socket] = addr
        clients_count[client_socket] = 0
        print('Connection from ', addr)
        tasks.append(client(client_socket))


def client(client_socket):
    while True:
        if all([CHECKER[i] for i in CHECKER]):
            for sock in clients_count:
                clients_count[sock] = 0
            for login in CHECKER:
                CHECKER[login] = False
        yield ('read', client_socket)
        request = client_socket.recv(4092)  # read

        if not request:
            break
        else:
            key = request.decode().split()[0]
            req_text = request.decode().split()[1:]
            if request.decode() == 'add_log':
                for sock in clients_name:
                    if sock != client_socket:
                        enemy_name = clients_name[sock]
                client_socket.send(f'end {enemy_name}'.encode())
                yield ('write', client_socket)
            elif key == 'game_log':  # получает результаты игры и логины игроков для записи лога
                database.add_game_log(req_text[0], req_text[1], req_text[2])
            elif key == 'get_info':
                client_socket.send(f'info {database.get_info(req_text[0])}'.encode())
                yield ('write', client_socket)
            elif key == 'gol':  # обрабатывает гол
                clients_count[client_socket] += 1
            elif key == 'autogol':  # обрабатывает автогол
                for sock in clients_count:
                    if sock != client_socket:
                        clients_count[sock] += 1
            elif key == 'auth':  # осуществляется попытка авторизации пользователя
                result = database.Auth(req_text[0], req_text[1])
                result1 = ''
                if result == req_text[0]:
                    clients_name[client_socket] = req_text[0]
                    CHECKER[req_text[0]] = False
                    database.add_log(req_text[0], 'entrance')
                    result1 = database.get_info(result)
                client_socket.send(f'auth {result} {result1}'.encode())
                yield ('write', client_socket)

            elif key == 'create':  # создание аккаунта
                if len(req_text) != 0:
                    result = database.AddUser(req_text[0], req_text[1], req_text[2], req_text[3])
                else:
                    result = 'Error'
                client_socket.send(result.encode())
                yield ('write', client_socket)

            elif key == 'rl':  # проверяется валидность логина при восстановлении пароля
                try:
                    result = database.Get_question(req_text[0])
                    result = f'rl {result}'
                except Exception:
                    result = 'rl Error'
                client_socket.send(result.encode())
                yield ('write', client_socket)

            elif key == 'ra':  # проверка на правильность ответа на секретный вопрос
                if database.Send_answer(req_text[0], ' '.join(req_text[1:])):
                    client_socket.send('ra True'.encode())
                else:
                    client_socket.send('ra False'.encode())
                yield ('write', client_socket)

            elif key == 'rp':  # запись нового пароля на аккаунта
                if len(req_text) != 0:
                    database.New_password(req_text[0], req_text[1])
                    client_socket.send('rp True'.encode())
                    yield ('write', client_socket)

            elif key == 'exit':  # выход из учетной записи пользователя и запись в лог
                database.add_log(req_text[0], req_text[1])
            elif key == 'stop':  # пакет, в котором говорится о том, что игра прекращена
                if req_text[0] == 'WIN':
                    client_socket.send('stop WIN'.encode())
                    yield ('write', client_socket)
                elif req_text[0] == 'LOSE':
                    client_socket.send('stop LOSE'.encode())
                    yield ('write', client_socket)
            elif all(i.isdigit() for i in
                     request.decode().split()):  # во время игры пользователи постоянно обмениваются координатами врага и шайбы
                for sock in clients_dict:
                    if sock != client_socket:
                        new_request = f'coords {request.decode("utf-8")} {str(clients_count[client_socket])} {str(clients_count[sock])}'
                        sock.send(new_request.encode())
                    yield ('write', sock)
    client_socket.close()


def event_loop():
    while any([tasks, to_read, to_write]):

        while not tasks:
            ready_to_read, ready_to_write, _ = select(to_read, to_write, [])

            for sock in ready_to_read:
                tasks.append(to_read.pop(sock))  # наполняем генераторами

            for sock in ready_to_write:
                tasks.append(to_write.pop(sock))

        try:
            task = tasks.pop(0)  # передаем генератор

            reason, sock = next(task)  # так как от генератора передается кортеж, нарприер ("read", client_socket)

            if reason == 'read':
                to_read[sock] = task
            if reason == 'write':
                to_write[sock] = task
        except StopIteration:
            print('Done!')


if __name__ == '__main__':
    tasks.append(server())
    event_loop()
