# hakoniwa-ar-bridge
A bridge connecting AR applications with real-world positional and sensor data. This repository aligns AR devices with physical coordinates via the Hakoniwa simulation hub, enabling AR users to view real-world data in AR space and feed AR data back to reality, creating an interactive mixed-reality experience.

## Architecture

![image](https://github.com/user-attachments/assets/5de2f38b-1acd-4c2f-b386-d9edc2073b80)



## Data Packet Structure

The data packet system enables real-time data exchange between AR devices and the Hakoniwa simulation hub. Each packet is transmitted as a JSON object, with a unified structure for consistent data communication. This structure supports various types of data, each designed for a specific function within the AR bridge. Below is the packet structure overview and the specific purposes of each packet type:

- **Base Packet Structure**: All packets share a fundamental structure that includes:
  - **`type`**: Defines the packet’s primary category, either `"data"` or `"event"`.
  - **`data_type`**: Specifies the data category when `type` is `"data"` (e.g., `"heartbeat_request"` or `"position"`).
  - **`event_type`**: Specifies the event type when `type` is `"event"` (e.g., `"play_start"` or `"reset"`).
  - **`data`**: Holds additional information relevant to the packet type, such as positional data, IP addresses, and status indicators.

- **Packet Types and Functions**:
  - **HeartBeatRequest**: A periodic packet sent from the Hakoniwa Asset to the AR device to verify connectivity. The AR device should respond with a HeartBeatResponse. This packet also includes the Web Server IP address in the `data` field.
  
    ```json
    {
      "type": "data",
      "data_type": "heartbeat_request",
      "data": {
        "ip_address": "192.168.1.10"
      }
    }
    ```
  - **HeartBeatResponse**: Sent from the AR device to the Hakoniwa Asset in response to a HeartBeatRequest. It communicates the AR device’s current status, which can be either "positioning" or "play".

    ```json
    {
      "type": "data",
      "data_type": "heartbeat_response",
      "data": {
        "status": "play"
      }
    }
    ```


  - **EventRequest**: This packet allows the Hakoniwa Asset to instruct the AR device to start or reset its actions. The `event_type` specifies the action, which can be either `"play_start"` or `"reset"`, indicating the desired action for the AR device.

    ```json
    {
      "type": "event",
      "event_type": "play_start"
    }
    ```

  - **PositioningRequest**: Sent periodically by the Hakoniwa Asset to communicate its current position and orientation. This packet includes a `frame_type` (e.g., `"unity"`), `position` (x, y, z coordinates), and `orientation` (x, y, z angles in degrees) within the `data` field. The PositioningRequest ensures the simulation hub accurately represents the device’s real-time movement.



    ```json
    {
      "type": "data",
      "data_type": "position",
      "data": {
        "frame_type": "unity",
        "position": {
          "x": 1.0,
          "y": 2.0,
          "z": 3.0
        },
        "orientation": {
          "x": 0.0,
          "y": 0.0,
          "z": 90.0
        }
      }
    }
    ```

Each packet type is essential for ensuring seamless interactions between AR applications and the real-world environment via the simulation hub. The unified JSON structure enables scalable, modular communication, supporting both state synchronization and event handling within an interactive mixed-reality experience.
