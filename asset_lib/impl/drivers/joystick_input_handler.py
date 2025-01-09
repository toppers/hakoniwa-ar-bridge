import pygame

from asset_lib.impl.drivers.rc_utils import StickMonitor
from asset_lib.impl.local.sync_manager_local import SyncManager
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

    def reset_position(self):
        self.position = [0, 0, 0]
        self.rotation = [0, 0, 0]

    def handle_input_position(self, config):
        temp_position = [0, 0, 0]
        temp_rotation = [0, 0, 0]
        yaw_value = 0
        vertical_value = 0
        horizontal_value = 0
        forward_backward_value = 0

        # 軸の数を取得
        num_axes = self.joystick.get_numaxes()

        # 各軸の値を取得
        for axis in range(num_axes):
            axis_value = self.joystick.get_axis(axis)
            #print(f"軸 {axis} の値: {axis_value:.2f}")
            op_index = self.stick_monitor.rc_config.get_op_index(axis)
            if op_index is None:
                continue
            stick_value = self.stick_monitor.stick_value(axis, axis_value)
            if op_index == self.stick_monitor.rc_config.STICK_TURN_LR:
                yaw_value = stick_value * 1.0
            elif op_index == self.stick_monitor.rc_config.STICK_UP_DOWN:
                vertical_value = stick_value * 0.01
            elif op_index == self.stick_monitor.rc_config.STICK_MOVE_LR:
                horizontal_value = -stick_value * 0.01
            elif op_index == self.stick_monitor.rc_config.STICK_MOVE_FB:
                forward_backward_value = stick_value * 0.01

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
        #print("Position: ", pos)
        return pos, rot

    def handle_input(self, config):
        running = True
        while running:
            if self.sync_manager.get_sync_status() != "POSITIONING":
                return False

            # joystick event
            pygame.event.pump()  # イベントキューを更新
            pos, rot = self.handle_input_position(config)
            self.sync_manager.update_position(pos, rot)
            self.save_to_json(self.position, self.rotation)

            for event in pygame.event.get([pygame.JOYBUTTONUP]):  # 必要なイベントのみ取得
                event_op_index = self.stick_monitor.rc_config.get_event_op_index(event.button)
                print(f"INFO: Event for button {event.button} ==> END.")
                if event_op_index is not None and event_op_index == self.stick_monitor.rc_config.SWITCH_GRAB_BAGGAGE:
                    print("Confirmation button pressed.")
                    running = False
                elif event_op_index is not None and event_op_index == self.stick_monitor.rc_config.SWITCH_RETURN_HOME:
                    print("RTH button pressed.")
                    self.reset_position()

            pygame.time.wait(10)
        pygame.event.clear()
        return True
