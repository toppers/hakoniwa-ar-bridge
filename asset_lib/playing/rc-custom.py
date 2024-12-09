#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from asset_lib.impl.sync_manager import SyncManager
import hakosim
import pygame
import time
from asset_lib.playing.return_to_home import DroneController
from asset_lib.impl.drivers.rc_utils import RcConfig, StickMonitor
import os

def saveCameraImage(client):
    png_image = client.simGetImage("0", hakosim.ImageType.Scene)
    if png_image:
        with open("scene.png", "wb") as f:
            f.write(png_image)

def joystick_control(client: hakosim.MultirotorClient, stick_monitor: StickMonitor, sync_manager: SyncManager) -> int:
    try:
        while True:
            if sync_manager.get_sync_status() != "PLAYING":
                return -1
            data = client.getGameJoystickData()
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION:
                    if event.axis < 6:
                        op_index = stick_monitor.rc_config.get_op_index(event.axis)
                        stick_value = stick_monitor.stick_value(event.axis, event.value)
                        #if (abs(stick_value) > 0.1):
                        #    print(f"stick event: stick_index={event.axis} op_index={op_index} event.value={event.value} stick_value={stick_value}")
                        data['axis'] = list(data['axis'])
                        data['axis'][op_index] = stick_value
                    else:
                        pass
                        #print(f'ERROR: not supported axis index: {event.axis}')
                elif event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
                    if event.button < 16:
                        data['button'] = list(data['button'])
                        event_op_index = stick_monitor.rc_config.get_event_op_index(event.button)
                        if event_op_index is not None:
                            event_triggered = stick_monitor.switch_event(event.button, (event.type == pygame.JOYBUTTONDOWN))
                            print(f"button event: switch_index={event.button} event_op_index={event_op_index} down: {(event.type == pygame.JOYBUTTONDOWN)} event_triggered={event_triggered}")
                            data['button'][event_op_index] = event_triggered
                            if event_triggered:
                                if event_op_index == stick_monitor.rc_config.SWITCH_CAMERA_SHOT:
                                    time.sleep(0.5)
                                    saveCameraImage(client)
                                elif event_op_index == stick_monitor.rc_config.SWITCH_RETURN_HOME:
                                    controller = DroneController(client, default_drone_name=client.default_drone_name, height=2.0, power=0.5, yaw_power=0.8)
                                    controller.return_to_home()
                    else:
                        if event.type == pygame.JOYBUTTONDOWN:
                            return -1
                        else:
                            print(f'ERROR: not supported button index: {event.button}')
            client.putGameJoystickData(data)
    except KeyboardInterrupt:
        pygame.joystick.quit()
        pygame.quit()

def do_radio_control(sync_manager: SyncManager, custom_config_path: str, stick_monitor: StickMonitor) -> int:    
    if not os.path.exists(custom_config_path):
        print(f"ERROR: Config file not found at '{custom_config_path}'")
        return -1

    pygame.init()
    pygame.joystick.init()

    # 接続されているジョイスティックの数を取得
    joystick_count = pygame.joystick.get_count()
    print(f"Number of joysticks: {joystick_count}")
    try:
        # ジョイスティックのインスタンス生成
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f'ジョイスティックの名前: {joystick.get_name()}')
        print(f'ボタン数 : {joystick.get_numbuttons()}')
    except pygame.error:
        print('ジョイスティックが接続されていません')
        pygame.joystick.quit()
        pygame.quit()
        return -1
    # connect to the HakoSim simulator
    client = hakosim.MultirotorClient(custom_config_path)
    client.default_drone_name = "DroneTransporter"
    client.confirmConnection()
    client.enableApiControl(True)
    client.armDisarm(True)
    return joystick_control(client, stick_monitor, sync_manager)

