import pyautogui
from time import sleep
import socket
from DIPPID import SensorUDP

# Disable PyAutoGUI's internal delay for maximum speed
pyautogui.PAUSE = 0

UDP_PORT = 5700  # Default DIPPID port [cite: 89]
DEADZONE = 0.05  # Low deadzone so tiny movements are registered
SENSITIVITY = 12 # Higher sensitivity to make the cursor move across the screen easily

def on_gyroscope_change(data):
    """
    Using the 'gyroscope' key to measure rotation velocity.
    Sweeping the phone across the table creates a rotational velocity 
    around the Z or X/Y axes depending on how you hold it.
    """
    if not isinstance(data, dict):
        return

    # Extract angular momentum data 
    # In a flat table position, pivoting left/right maps to 'z' 
    # and pushing forward/backward maps to 'x' or 'y'
    gyro_x = -data.get('x', 0)
    gyro_z = data.get('z', 0)

    move_x = 0
    move_y = 0

    # Apply deadzone and multiply by our sensitivity factor
    if abs(gyro_z) > DEADZONE:
        # Turning left/right swings the Z axis
        move_x = -gyro_z * SENSITIVITY  

    if abs(gyro_x) > DEADZONE:
        # Pushing forward/backward tilts/swings the X axis
        move_y = gyro_x * SENSITIVITY

    if move_x != 0 or move_y != 0:
        try:
            # Shift the cursor relatively
            pyautogui.move(int(move_x), int(move_y))
        except Exception as e:
            pass

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
    print(f" DIPPID Gyro-Mouse Prototype")
    print(f" -> Phone IP: {my_ip}")
    print(f" -> Phone Port: {UDP_PORT}")
    print("==================================================")
    print("Place the phone flat on the table and slide/pivot it like a mouse.")
    print("Press Ctrl+C to exit.")

    phone_sensor = SensorUDP(port=UDP_PORT)
    
    # Registering to 'gyroscope' for active movement tracking 
    phone_sensor.register_callback("gyroscope", on_gyroscope_change)

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down cleanly...")
        phone_sensor.disconnect()

if __name__ == "__main__":
    main()