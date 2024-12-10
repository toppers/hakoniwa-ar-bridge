import pygame

from asset_lib.impl.drivers.rc_utils import StickMonitor
from asset_lib.impl.sync_manager import SyncManager
from asset_lib.impl.drivers.input_handler import InputHandler
import time

class JoystickInputHandler(InputHandler):
    def __init__(self, position, rotation, sync_manager: SyncManager, save_to_json, stick_monitor: StickMonitor):
        self.position = position
        self.rotation = rotation
        self.sync_manager = sync_manager
        self.save_to_json = save_to_json
        self.stick_monitor = stick_monitor

        pygame.init()
        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

    def handle_input_position(self, event, config):
        temp_position = [0, 0, 0]
        temp_rotation = [0, 0, 0]
        op_index = self.stick_monitor.rc_config.get_op_index(event.axis)
        stick_value = self.stick_monitor.stick_value(event.axis, event.value)

        yaw_value = 0
        vertical_value = 0
        horizontal_value = 0
        forward_backward_value = 0
        if op_index == self.stick_monitor.rc_config.STICK_TURN_LR:
            yaw_value = stick_value * 1.0
        elif op_index == self.stick_monitor.rc_config.STICK_UP_DOWN:
            vertical_value = stick_value * 0.1
        elif op_index == self.stick_monitor.rc_config.STICK_MOVE_LR:
            horizontal_value = stick_value * 0.1
        elif op_index == self.stick_monitor.rc_config.STICK_MOVE_FB:
            forward_backward_value = stick_value * 0.1

        # スティックの値が変わった場合のみ更新
        if yaw_value != 0 or vertical_value != 0 or horizontal_value != 0 or forward_backward_value != 0:
            temp_rotation[1] = yaw_value * config["adjustments"]["yaw"]
            temp_position[1] = vertical_value * config["adjustments"]["vertical"]
            temp_position[0] = horizontal_value * config["adjustments"]["horizontal"]
            temp_position[2] = forward_backward_value * config["adjustments"]["forward_and_back"]

            self.position[0] += temp_position[0]
            self.position[1] += temp_position[1]
            self.position[2] += temp_position[2]
            self.rotation[1] += temp_rotation[1]

        pos = {
            "x": self.position[0],
            "y": self.position[1],
            "z": self.position[2]
        }
        rot = {
            "x": 0.0,
            "y": self.rotation[1],
            "z": 0.0
        }
        return pos, rot

    def handle_input(self, config):
        running = True
        last_sent_time = 0
        send_interval = 0.1

        while running:
            if self.sync_manager.get_sync_status() != "POSITIONING":
                running = False
                return False
            current_time = time.time()  # ループの先頭で時間を取得
            pygame.event.pump()  # イベントキューを更新
            for event in pygame.event.get([pygame.JOYAXISMOTION, pygame.JOYBUTTONDOWN]):  # 必要なイベントのみ取得
                if event.type == pygame.JOYAXISMOTION:
                    pos, rot = self.handle_input_position(event, config)
                    if current_time - last_sent_time >= send_interval:
                        self.sync_manager.update_position(pos, rot)
                        self.save_to_json(self.position, self.rotation)
                        last_sent_time = current_time  # 最後に送信した時間を更新
                elif event.type == pygame.JOYBUTTONDOWN:
                    event_op_index = self.stick_monitor.rc_config.get_event_op_index(event.button)
                    if event_op_index is not None and event_op_index == self.stick_monitor.rc_config.SWITCH_GRAB_BAGGAGE:
                        event_triggered = self.stick_monitor.switch_event(event.button, (event.type == pygame.JOYBUTTONDOWN))
                        if event_triggered:  # 確認ボタン
                            print("Confirmation button pressed.")
                            running = False
            pygame.time.wait(10)

        return True
