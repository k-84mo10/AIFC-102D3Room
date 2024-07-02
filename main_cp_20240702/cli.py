from main_cp_20240702 import SerialCommunication, TakeImage, MachineLearning
import configparser
import os
import threading
import ast
from datetime import datetime


# 現在時刻の取得
def get_time():
    now = datetime.now()
    formatted_now = now.strftime("%Y%m%dT%H%M%S")
    return formatted_now


# シリアル通信を読むスレッド
def read_serial(serial_communication):
    while True:
        read_data = serial_communication.read()
        if read_data:
            serial_communication.record_read_state(read_data)


# 画像を撮り推論等を行うスレッド
def main_process(
    take_image, serial_communication, machine_learning, start_time, state_list
):            
    while True:
        timestamp = get_time()
        if serial_communication.is_manual():
            take_image.capture_image(timestamp, 95)
            state = serial_communication.get_state()
            if state != "----":
                take_image.copy_image_to_other_directory(timestamp, state, "train")
        else:
            if int(timestamp[-2:]) % 5 == 0:
                take_image.capture_image(timestamp, 95)
                image_path = "main_cp_20240702/data/image/raw/{}/{}.jpg".format(
                    start_time, timestamp
                )
                state = state_list[machine_learning.inference(image_path)]
                take_image.copy_image_to_other_directory(timestamp, state, "result")
                serial_communication.write_state(state)


# シリアル通信を送るスレッド
def write_serial(serial_communication):
    previous_time = get_time()
    while True:
        current_time = get_time()
        if current_time != previous_time:
            serial_communication.write()
            previous_time = current_time


def main():
    """
    メインの処理
    """

    config_path = os.path.join(os.path.dirname(__file__), "configs", "config.ini")
    config = configparser.ConfigParser()
    config.read(config_path)

    camera_id = config.getint("device", "camera_id")
    serial_port = config.get("serial", "serial_port")
    sereal_baudrate = config.getint("serial", "serial_baudrate")
    model_path = config.get("machine_learning", "model_path")
    model_type = config.get("machine_learning", "model_type")
    state_list = ast.literal_eval(config.get("machine_learning", "state_list"))

    # 現在時刻の取得
    start_time = get_time()

    # ディレクトリ・ファイルの作成
    os.makedirs("main_cp_20240702/data/image/raw/{}".format(start_time), exist_ok=True)
    os.makedirs(
        "main_cp_20240702/data/image/train/{}".format(start_time), exist_ok=True
    )
    os.makedirs(
        "main_cp_20240702/data/image/result/{}".format(start_time), exist_ok=True
    )
    os.makedirs("main_cp_20240702/data/csv/{}".format(start_time), exist_ok=True)
    with open(
        "main_cp_20240702/data/csv/{}/read_state.csv".format(start_time), "w"
    ) as file:
        pass
    with open(
        "main_cp_20240702/data/csv/{}/write_state.csv".format(start_time), "w"
    ) as file:
        pass

    # クラスのインスタンス化
    serial_communication = SerialCommunication(serial_port, sereal_baudrate, start_time)
    take_image = TakeImage(start_time, camera_id)
    machine_learning = MachineLearning(model_path, model_type)

    # シリアル通信の開始
    serial_communication.start()

    # シリアル通信を読むスレッドの起動
    read_serial_thread = threading.Thread(
        target=read_serial, args=(serial_communication,)
    )
    read_serial_thread.daemon = True
    read_serial_thread.start()

    # 画像を撮り推論等を行うスレッドの起動
    main_process_thread = threading.Thread(
        target=main_process,
        args=(
            take_image,
            serial_communication,
            machine_learning,
            start_time,
            state_list,
        ),
    )
    main_process_thread.daemon = True
    main_process_thread.start()

    # シリアル通信を送るスレッドの起動
    write_serial_thread = threading.Thread(
        target=write_serial, args=(serial_communication,)
    )
    write_serial_thread.daemon = True
    write_serial_thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        take_image.release()
        serial_communication.stop()
        print("Exiting main thread")
