import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QVBoxLayout, QWidget, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QStackedWidget, QComboBox
)
from PyQt6.QtCore import Qt


# Создание базы данных
def initialize_database():
    conn = sqlite3.connect('delivery_orders.db')
    cursor = conn.cursor()

    # Таблица заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            delivery_address TEXT NOT NULL,
            order_date TEXT NOT NULL,
            delivery_status TEXT NOT NULL DEFAULT 'Ожидается'
        )
    ''')

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Добавление администратора, если его еще нет
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES ('admin', 'admin123', 'admin')
    ''')

    conn.commit()
    conn.close()


# Окно входа и регистрации
class LoginWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Поля для входа
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Поле для выбора роли
        self.role_input = QComboBox()
        self.role_input.addItems(["user", "admin"])

        # Поле для пароля подтверждения роли админа
        self.admin_password_input = QLineEdit()
        self.admin_password_input.setPlaceholderText("Пароль для роли администратора")
        self.admin_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.admin_password_input.setVisible(False)

        # Событие выбора роли
        self.role_input.currentIndexChanged.connect(self.toggle_admin_password_field)

        # Кнопки
        login_btn = QPushButton("Войти")
        register_btn = QPushButton("Зарегистрироваться")
        login_btn.clicked.connect(self.login)
        register_btn.clicked.connect(self.register)

        layout.addWidget(QLabel("Авторизация"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(QLabel("Выберите роль"))
        layout.addWidget(self.role_input)
        layout.addWidget(self.admin_password_input)
        layout.addWidget(login_btn)
        layout.addWidget(register_btn)

    def toggle_admin_password_field(self):
        if self.role_input.currentText() == "admin":
            self.admin_password_input.setVisible(True)
        else:
            self.admin_password_input.setVisible(False)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        conn = sqlite3.connect('delivery_orders.db')
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM users WHERE username=? AND password=?', (username, password))
        result = cursor.fetchone()
        conn.close()

        if result:
            role = result[0]
            if role == "admin":
                self.parent.setCurrentWidget(self.parent.admin_window)
            elif role == "user":
                self.parent.user_window.set_user(username)
                self.parent.setCurrentWidget(self.parent.user_window)
        else:
            QMessageBox.warning(self, "Ошибка", "Неверное имя пользователя или пароль!")

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        role = self.role_input.currentText()

        if not all([username, password]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        if role == "admin":
            admin_password = self.admin_password_input.text()
            if admin_password != "secure_admin_password":
                QMessageBox.warning(self, "Ошибка", "Неверный пароль для роли администратора!")
                return

        conn = sqlite3.connect('delivery_orders.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
            conn.commit()
            QMessageBox.information(self, "Успех", "Регистрация успешна!")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Имя пользователя уже существует!")
        finally:
            conn.close()


# Окно администратора
class AdminWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Имя клиента")
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Адрес доставки")
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("Дата заказа (ГГГГ-ММ-ДД)")
        self.status_input = QLineEdit()
        self.status_input.setPlaceholderText("Статус доставки")

        add_order_btn = QPushButton("Добавить заказ")
        add_order_btn.clicked.connect(self.add_order)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Имя клиента", "Адрес", "Дата заказа", "Статус"])

        refresh_btn = QPushButton("Обновить заказы")
        refresh_btn.clicked.connect(self.load_orders)

        self.delete_id_input = QLineEdit()
        self.delete_id_input.setPlaceholderText("Введите ID заказа для удаления")
        delete_order_btn = QPushButton("Удалить заказ")
        delete_order_btn.clicked.connect(self.delete_order)

        back_btn = QPushButton("Выйти")
        back_btn.clicked.connect(lambda: self.parent.setCurrentWidget(self.parent.login_window))

        layout.addWidget(QLabel("Добавление заказа"))
        layout.addWidget(self.name_input)
        layout.addWidget(self.address_input)
        layout.addWidget(self.date_input)
        layout.addWidget(self.status_input)
        layout.addWidget(add_order_btn)
        layout.addWidget(QLabel("Список заказов"))
        layout.addWidget(self.table)
        layout.addWidget(refresh_btn)
        layout.addWidget(QLabel("Удаление заказа"))
        layout.addWidget(self.delete_id_input)
        layout.addWidget(delete_order_btn)
        layout.addWidget(back_btn)

        self.setLayout(layout)
        self.load_orders()

    def add_order(self):
        name = self.name_input.text()
        address = self.address_input.text()
        order_date = self.date_input.text()
        status = self.status_input.text()

        if not all([name, address, order_date, status]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        conn = sqlite3.connect('delivery_orders.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (customer_name, delivery_address, order_date, delivery_status)
            VALUES (?, ?, ?, ?)
        ''', (name, address, order_date, status))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Успех", "Заказ добавлен!")
        self.clear_inputs()
        self.load_orders()

    def load_orders(self):
        conn = sqlite3.connect('delivery_orders.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders')
        orders = cursor.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for row_number, row_data in enumerate(orders):
            self.table.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.table.setItem(row_number, column_number, QTableWidgetItem(str(data)))

    def delete_order(self):
        order_id = self.delete_id_input.text()

        if not order_id:
            QMessageBox.warning(self, "Ошибка", "Введите ID заказа!")
            return

        conn = sqlite3.connect('delivery_orders.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM orders WHERE id=?', (order_id,))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Успех", "Заказ удалён!")
        self.delete_id_input.clear()
        self.load_orders()

    def clear_inputs(self):
        self.name_input.clear()
        self.address_input.clear()
        self.date_input.clear()
        self.status_input.clear()


# Окно пользователя
class UserWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.username = None  # Имя текущего пользователя
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ваше имя")
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Адрес доставки")
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("Дата заказа (ГГГГ-ММ-ДД)")

        create_order_btn = QPushButton("Создать заказ")
        create_order_btn.clicked.connect(self.create_order)

        back_btn = QPushButton("Выйти")
        back_btn.clicked.connect(lambda: self.parent.setCurrentWidget(self.parent.login_window))

        layout.addWidget(QLabel("Создание заказа"))
        layout.addWidget(self.name_input)
        layout.addWidget(self.address_input)
        layout.addWidget(self.date_input)
        layout.addWidget(create_order_btn)
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def set_user(self, username):
        self.username = username
        self.name_input.setText(username)

    def create_order(self):
        name = self.name_input.text()
        address = self.address_input.text()
        order_date = self.date_input.text()

        if not all([name, address, order_date]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        conn = sqlite3.connect('delivery_orders.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (customer_name, delivery_address, order_date, delivery_status)
            VALUES (?, ?, ?, 'Ожидается')
        ''', (name, address, order_date))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Успех", "Заказ создан!")
        self.clear_inputs()

    def clear_inputs(self):
        self.address_input.clear()
        self.date_input.clear()


# Главный стек окон
class MainApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система управления доставкой")
        self.setGeometry(200, 200, 800, 600)

        self.login_window = LoginWindow(self)
        self.admin_window = AdminWindow(self)
        self.user_window = UserWindow(self)

        self.addWidget(self.login_window)
        self.addWidget(self.admin_window)
        self.addWidget(self.user_window)

        self.setCurrentWidget(self.login_window)


# Инициализация приложения
if __name__ == "__main__":
    initialize_database()
    app = QApplication([])
    main_app = MainApp()
    main_app.show()
    app.exec()
