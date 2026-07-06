import pyautogui
from time import sleep
import socket
from dippid import SensorUDP

# Disable PyAutoGUI's internal delay for smooth movement
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

UDP_PORT = 5700
DEADZONE = 0.05

# --- TUNING CONSTANTS ---
# Adjust this to change how fast the camera spins in FreeCAD
SENSITIVITY = 18  

# Global state to track if we are currently orbiting
is_orbiting = False

def on_button_1(data):
    """
    Acts as our clutch.
    """
    global is_orbiting
    
    if data == 1 and not is_orbiting:
        print("🔒 Orbit clutch ENGAGED (Shift + Right Click)")
        is_orbiting = True
        # Press down the FreeCAD default orbit shortcut combination
        pyautogui.keyDown('shift')
        pyautogui.mouseDown(button='right')
        
    elif data == 0 and is_orbiting:
        print("🔓 Orbit clutch RELEASED")
        is_orbiting = False
        # Release the shortcut keys cleanly
        pyautogui.keyUp('shift')
        pyautogui.mouseUp(button='right')

def on_gyroscope_change(data):
    """
    Moves the mouse only while the clutch is held down.
    The lag multiplier has been removed to stop random viewport jumping.
    """
    global is_orbiting
    
    if not is_orbiting or not isinstance(data, dict):
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
    print(f" Production FreeCAD DIPPID Controller")
    print(f" -> Computer IP: {my_ip}")
    print("==================================================")
    print("1. Open FreeCAD (Set navigation style to 'CAD').")
    print("2. Hold Button 1 on your phone and sweep it to rotate the model.")
    print("Press Ctrl+C to exit safely.")

    phone_sensor = SensorUDP(port=UDP_PORT)
    phone_sensor.register_callback("button_1", on_button_1)
    phone_sensor.register_callback("gyroscope", on_gyroscope_change)

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down cleanly and releasing keys...")
        pyautogui.keyUp('shift')
        pyautogui.mouseUp(button='right')
        phone_sensor.disconnect()

if __name__ == "__main__":
    main()