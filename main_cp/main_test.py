import cv2
import os
import serial
import threading
import re
from datetime import datetime

class SerialCommunication:
    """
    シリアル通信を行うためのクラス
    """
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate

    def start(self):
        self.ser = serial.Serial(self.port, self.baudrate)

    def read(self):
        if self.ser.in_waiting > 0:
            read_data = self.ser.readline().decode().strip()
            return read_data

    def write(self):
        user_input = input("Enter data to send: ")
        self.ser.write(user_input.encode() + b'\r\n')

    def stop(self):
        self.ser.close()

class StateManagement:
    """
    状態を読み書きするためのクラス
    """
    def __init__(self):
        self.filename = 'state.csv'
        with open(self.filename, 'w'):
            pass

    def record_state(self, data):
        if self.is_valid_format(data):
            with open(self.filename, 'a') as file:
                file.write(data + '\n')

    def get_state(self):
        with open(self.filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()   
            if lines:         
                latest_line = lines[-1].strip()
                state = latest_line[1:5]
            else:
                state = "0000"
        return state

    def is_valid_format(self, data):
        pattern = r'^S\d{7}'
        if re.match(pattern, str(data)):
            return True
        else:
            return False
        
class Camera:
    """
    カメラを操作するためのクラス
    """
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Unable to access camera")

    def capture_image(self, timestamp, quality):
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to capture image")
            return
        filename = "raw/{}.jpg".format(timestamp)
        cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])

    def release(self):
        self.cap.release()

class PhotoNameManeger:
    """
    写真の名前を管理するためのクラス
    """
    def __init__(self, photoname):
        self.photoname = photoname
    
    def change_photoname(self, state):
        old_picture_name = 'raw/{}.jpg'.format(self.photoname)
        new_picture_name = 'raw/{}_{}.jpg'.format(self.photoname, state)
        os.rename(old_picture_name, new_picture_name)
        self.photoname = "{}_{}".format(self.photoname, state)

class Main:
    def __init__(self):
        self.serial_communication = SerialCommunication('/dev/ttyACM0', 9600)
        self.state_management = StateManagement()
        self.camera = Camera()
        self.serial_communication.start()

    def get_time(self):
        now = datetime.now()
        formatted_now = now.strftime('%Y%m%dT%H%M%S')
        return formatted_now

    def state_acuire(self):
        try:
            while True:
                data = self.serial_communication.read()
                self.state_management.record_state(data)
        except KeyboardInterrupt:
            print("Exiting state acuirement")
    
    def take_picture(self):
        try:
            while True:
                timestamp = self.get_time()
                self.camera.capture_image(timestamp, 95)
                state = self.state_management.get_state()
                self.photo_name_maneger = PhotoNameManeger(timestamp)
                self.photo_name_maneger.change_photoname(state)
        except KeyboardInterrupt:
            print("Exiting take picture")

    def send_state(self):
        try:
            while True:
                self.serial_communication.write()
        except KeyboardInterrupt:
            print("Exiting sent state")

    def run(self):
        read_serial_thread = threading.Thread(target=self.state_acuire)
        read_serial_thread.daemon = True
        read_serial_thread.start()

        take_picture_thread = threading.Thread(target=self.take_picture)
        take_picture_thread.daemon = True
        take_picture_thread.start()

        send_serial_thread = threading.Thread(target=self.send_state)
        send_serial_thread.daemon = True
        send_serial_thread.start()

        try:
            while True:
                pass
        except KeyboardInterrupt:
            self.camera.release()
            print("Exiting main thread")

if __name__ == '__main__':
    main = Main()
    main.run()