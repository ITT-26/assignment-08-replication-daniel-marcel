import socket
from time import sleep
from dippid import SensorUDP
from pynput.mouse import Controller

# Initialize the pynput mouse controller
mouse = Controller()

UDP_PORT = 5700
DEADZONE = 0.05
SENSITIVITY = 15

def on_gyroscope_change(data):
    """
    Standard 2D mouse movement using pynput (no buttons required).
    """
    if not isinstance(data, dict):
        return

    gyro_x = -data.get('x', 0)
    gyro_z = data.get('z', 0)

    move_x = 0
    move_y = 0

    if abs(gyro_z) > DEADZONE:
        move_x = -gyro_z * SENSITIVITY  

    if abs(gyro_x) > DEADZONE:
        move_y = gyro_x * SENSITIVITY

    if move_x != 0 or move_y != 0:
        try:
            # pynput relative movement
            mouse.move(int(move_x), int(move_y))
        except Exception as e:
            print(f"Movement error: {e}")

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

def main():
    my_ip = get_local_ip()
    print("==================================================")
    print(f" Pure pynput 2D Mouse Test")
    print(f" -> Phone IP: {my_ip}")
    print(f" -> Phone Port: {UDP_PORT}")
    print("==================================================")
    print("Move the phone to move the cursor. Press Ctrl+C to exit.")

    phone_sensor = SensorUDP(port=UDP_PORT)
    
    # Register only the gyroscope
    phone_sensor.register_callback("gyroscope", on_gyroscope_change)

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down cleanly...")
        phone_sensor.disconnect()

if __name__ == "__main__":
    main()