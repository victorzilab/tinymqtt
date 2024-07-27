import sys
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
                             QMessageBox, QMenuBar, QMenu, QAction, QDialog, QFormLayout)
from PyQt5.QtCore import QThread, pyqtSignal
import paho.mqtt.client as mqtt

CONFIG_FILE = 'config.json'


class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Configuration')
        self.setFixedSize(300, 250)

        layout = QFormLayout()

        self.broker_edit = QLineEdit()
        layout.addRow('Broker Address:', self.broker_edit)

        self.port_edit = QLineEdit()
        layout.addRow('Port:', self.port_edit)

        self.user_edit = QLineEdit()
        layout.addRow('User:', self.user_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addRow('Password:', self.password_edit)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.accept)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def get_config(self):
        return {
            'broker': self.broker_edit.text(),
            'port': int(self.port_edit.text()),
            'user': self.user_edit.text(),
            'password': self.password_edit.text()
        }

    def set_config(self, config):
        self.broker_edit.setText(config.get('broker', ''))
        self.port_edit.setText(str(config.get('port', '')))
        self.user_edit.setText(config.get('user', ''))
        self.password_edit.setText(config.get('password', ''))


class MQTTWorker(QThread):
    message_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    publish_signal = pyqtSignal(str, str)  # signal now includes topic and message
    connected_signal = pyqtSignal(bool)
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        self.broker = None
        self.port = None
        self.user = None
        self.password = None

    def run(self):
        if self.broker and self.port:
            try:
                if self.user and self.password:
                    self.client.username_pw_set(self.user, self.password)
                self.client.connect(self.broker, self.port, 60)
                self.client.loop_forever()
            except Exception as e:
                self.error_signal.emit(str(e))

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.status_signal.emit("Connected successfully")
            self.connected_signal.emit(True)
            self.client.subscribe(self.default_topic)
        else:
            self.status_signal.emit(f"Connect failed with reason code {reason_code}")
            self.connected_signal.emit(False)

    def on_disconnect(self, client, userdata, reason_code, properties):
        self.status_signal.emit("Disconnected")
        self.connected_signal.emit(False)

    def on_message(self, client, userdata, msg):
        message = f"Received message: {msg.topic} -> {msg.payload.decode()}"
        self.message_signal.emit(message)

    def on_publish(self, client, userdata, mid):
        self.publish_signal.emit(self.last_topic, self.last_message)  # emit topic and message

    def publish(self, topic, message):
        self.last_topic = topic  # store last topic
        self.last_message = message  # store last message
        self.client.publish(topic, message)

    def set_connection(self, broker, port, topic, user=None, password=None):
        self.broker = broker
        self.port = port
        self.default_topic = topic
        self.user = user
        self.password = password
        if self.isRunning():
            self.client.disconnect()
            self.quit()
            self.wait()
        self.start()

    def subscribe(self, topic):
        self.client.subscribe(topic)


class MQTTClient(QWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()

        self.initUI()

        # Initialize the MQTT worker
        self.mqtt_worker = MQTTWorker()
        self.mqtt_worker.message_signal.connect(self.append_message)
        self.mqtt_worker.status_signal.connect(self.update_status)
        self.mqtt_worker.publish_signal.connect(self.append_publish_message)  # connect to new slot
        self.mqtt_worker.connected_signal.connect(self.update_connect_button)
        self.mqtt_worker.error_signal.connect(self.display_error)

    def initUI(self):
        self.setWindowTitle('TinyMQTT')
        self.setStyleSheet("background-color: #f0f0f0;")
        self.setGeometry(100, 100, 500, 400)

        layout = QVBoxLayout()

        # Menu bar
        menubar = QMenuBar(self)
        menu = menubar.addMenu('Options')
        config_action = QAction('Config', self)
        config_action.triggered.connect(self.open_config_dialog)
        menu.addAction(config_action)
        layout.setMenuBar(menubar)

        self.status_label = QLabel('Disconnected')
        layout.addWidget(self.status_label)

        self.topic_edit = QLineEdit('test/topic')
        layout.addWidget(self.topic_edit)

        button_layout = QHBoxLayout()

        self.connect_button = QPushButton('Connect')
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.connect_button.clicked.connect(self.connect_to_broker)
        button_layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton('Disconnect')
        self.disconnect_button.setStyleSheet("background-color: #f44336; color: white;")
        self.disconnect_button.clicked.connect(self.disconnect_from_broker)
        button_layout.addWidget(self.disconnect_button)

        layout.addLayout(button_layout)

        self.message_edit = QLineEdit()
        layout.addWidget(self.message_edit)

        self.publish_button = QPushButton('Publish')
        self.publish_button.setStyleSheet("background-color: #2196F3; color: white;")
        self.publish_button.clicked.connect(self.publish_message)
        layout.addWidget(self.publish_button)

        self.subscribe_button = QPushButton('Subscribe')
        self.subscribe_button.setStyleSheet("background-color: #FF9800; color: white;")
        self.subscribe_button.clicked.connect(self.subscribe_to_topic)
        layout.addWidget(self.subscribe_button)

        predefined_layout = QHBoxLayout()

        self.qos0_0_button = QPushButton('Publish qos0: 0')
        self.qos0_0_button.clicked.connect(lambda: self.publish_predefined('qos0', '0'))
        predefined_layout.addWidget(self.qos0_0_button)

        self.qos0_1_button = QPushButton('Publish qos0: 1')
        self.qos0_1_button.clicked.connect(lambda: self.publish_predefined('qos0', '1'))
        predefined_layout.addWidget(self.qos0_1_button)

        self.qos1_0_button = QPushButton('Publish qos1: 0')
        self.qos1_0_button.clicked.connect(lambda: self.publish_predefined('qos1', '0'))
        predefined_layout.addWidget(self.qos1_0_button)

        self.qos1_1_button = QPushButton('Publish qos1: 1')
        self.qos1_1_button.clicked.connect(lambda: self.publish_predefined('qos1', '1'))
        predefined_layout.addWidget(self.qos1_1_button)

        layout.addLayout(predefined_layout)

        self.clear_log_button = QPushButton('Clear Log')
        self.clear_log_button.setStyleSheet("background-color: #9E9E9E; color: white;")
        self.clear_log_button.clicked.connect(self.clear_message_log)
        layout.addWidget(self.clear_log_button)

        self.message_log = QTextEdit()
        self.message_log.setReadOnly(True)
        layout.addWidget(self.message_log)

        self.setLayout(layout)

    def append_message(self, message):
        self.message_log.append(message)

    def update_status(self, status):
        self.status_label.setText(status)

    def update_connect_button(self, connected):
        self.connect_button.setEnabled(not connected)
        self.disconnect_button.setEnabled(connected)

    def connect_to_broker(self):
        broker = self.config['broker']
        port = self.config['port']
        topic = self.topic_edit.text()
        user = self.config.get('user', None)
        password = self.config.get('password', None)
        self.mqtt_worker.set_connection(broker, port, topic, user, password)

    def disconnect_from_broker(self):
        self.mqtt_worker.client.disconnect()

    def publish_message(self):
        topic = self.topic_edit.text()
        message = self.message_edit.text()
        self.mqtt_worker.publish(topic, message)
        self.message_edit.clear()

    def publish_predefined(self, topic, message):
        self.mqtt_worker.publish(topic, message)

    def subscribe_to_topic(self):
        topic = self.topic_edit.text()
        self.mqtt_worker.subscribe(topic)

    def clear_message_log(self):
        self.message_log.clear()

    def append_publish_message(self, topic, message):
        self.append_message(f"Published message: {message} to topic: {topic}")

    def display_error(self, error_message):
        QMessageBox.critical(self, "Connection Error", f"Failed to connect to broker: {error_message}")

    def open_config_dialog(self):
        dialog = ConfigDialog()
        dialog.set_config(self.config)
        if dialog.exec_():
            self.config = dialog.get_config()
            self.save_config()

    def save_config(self):
        with open(CONFIG_FILE, 'w') as file:
            json.dump(self.config, file)

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {
                'broker': '',
                'port': 1883,
                'user': '',
                'password': ''
            }

    def closeEvent(self, event):
        self.mqtt_worker.terminate()
        self.mqtt_worker.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mqtt_client = MQTTClient()
    mqtt_client.show()
    sys.exit(app.exec_())
