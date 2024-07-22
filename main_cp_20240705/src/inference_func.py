# src/inference.py
from main_cp_20240705.lib import MachineLearning, FileManage
import shutil


def inference_function(
    machine_learning: MachineLearning,
    start_time: str,
    state_list: list,
    take_image_time_file: FileManage,
    write_serial_file: FileManage,
    read_serial_file: FileManage,
) -> None:
    """
    Infers the state of the object in the image.

    Args:
        machine_learning (MachineLearning): The machine learning object.
    """
    while True:
        state = read_serial_file.read_last_line()
        if state == "":
            continue

        is_manual = state[5] == "0"
        if is_manual:
            continue

        nowest_image_time = take_image_time_file.read_last_line()
        if nowest_image_time == "":
            continue

        try:
            image_path = (
                f"main_cp_20240705/data/image/raw/{start_time}/{nowest_image_time}.jpg"
            )
            state_value = machine_learning.inference(image_path)
            if state_value == -1:
                continue

            inference_state = state_list[state_value]

            source_picture_name = (
                f"main_cp_20240705/data/image/raw/{start_time}/{nowest_image_time}.jpg"
            )
            copied_picture_name = f"main_cp_20240705/data/image/result/{start_time}/{nowest_image_time}_{inference_state}.jpg"
            shutil.copy(source_picture_name, copied_picture_name)

            write_serial_file.write_file(inference_state)
        except Exception as e:
            pass
