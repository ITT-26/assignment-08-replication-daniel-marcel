bl_info = {
    "name": "DIPPID 6DOF Viewport Controller",
    "author": "Your Team",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > DIPPID",
    "description": "Orbits the 3D viewport using DIPPID phone sensor data over UDP.",
    "category": "3D View",
}

import bpy
import socket
import json
import mathutils

class DIPPID_OT_controller(bpy.types.Operator):
    """Start listening to DIPPID UDP data to control the viewport"""
    bl_idname = "view3d.dippid_start"
    bl_label = "Start DIPPID Controller"

    _timer = None
    _sock = None

    # Tuning variables
    UDP_PORT = 5700
    DEADZONE = 0.05
    SENSITIVITY = 0.02  # Rotation speed multiplier

    def modal(self, context, event):
        # Stop the script if the user presses ESC
        if event.type in {'ESC'}:
            self.cancel(context)
            self.report({'INFO'}, "DIPPID Controller Stopped")
            return {'CANCELLED'}

        # Triggered every time the timer fires
        if event.type == 'TIMER':
            try:
                # Receive data non-blockingly
                data, addr = self._sock.recvfrom(1024)
                payload = json.loads(data.decode('utf-8'))

                # DIPPID payload example: {"gyroscope": {"x": 0.5, "y": -0.1, "z": 0.0}}
                if "gyroscope" in payload:
                    gyro = payload["gyroscope"]
                    gx = gyro.get("x", 0)
                    gz = gyro.get("z", 0)

                    # Apply deadzone
                    if abs(gx) > self.DEADZONE or abs(gz) > self.DEADZONE:
                        self.orbit_viewport(context, gx, gz)

            except BlockingIOError:
                # No data arrived yet, just pass through smoothly
                pass
            except Exception as e:
                print(f"DIPPID Error: {e}")

        # Let normal Blender events (like regular mouse clicks) pass through
        return {'PASS_THROUGH'}

    def orbit_viewport(self, context, gyro_x, gyro_z):
        """Mathematically rotates the Blender 3D Viewport Camera"""
        # Ensure we are in a 3D viewport
        if context.area.type != 'VIEW_3D':
            return
            
        rv3d = context.space_data.region_3d
        if not rv3d:
            return

        # Calculate rotation angles based on sensitivity
        # Note: You may need to invert these (e.g. -gyro_x) depending on your phone orientation
        rot_up_down = gyro_x * self.SENSITIVITY
        rot_left_right = gyro_z * self.SENSITIVITY

        # Create Quaternion rotations
        # X-axis rotates pitch (up/down)
        quat_x = mathutils.Quaternion((1.0, 0.0, 0.0), rot_up_down)
        # Z-axis rotates yaw (left/right)
        quat_z = mathutils.Quaternion((0.0, 0.0, 1.0), rot_left_right)

        # Apply rotation to the viewport's current matrix
        # Z rotation is applied globally, X rotation is applied locally to the camera
        rv3d.view_rotation = quat_z @ rv3d.view_rotation @ quat_x

    def invoke(self, context, event):
        # 1. Setup a NON-BLOCKING UDP Socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(('0.0.0.0', self.UDP_PORT))
        self._sock.setblocking(False)

        # 2. Setup the background timer (runs 60 times a second)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.016, window=context.window)
        wm.modal_handler_add(self)
        
        self.report({'INFO'}, f"DIPPID Controller Running on Port {self.UDP_PORT}. Press ESC to stop.")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        """Cleanup function when the script stops"""
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        if self._sock:
            self._sock.close()

# A simple UI Panel so you can click a button to start it
class DIPPID_PT_panel(bpy.types.Panel):
    bl_label = "DIPPID Setup"
    bl_idname = "DIPPID_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DIPPID'

    def draw(self, context):
        layout = self.layout
        layout.operator(DIPPID_OT_controller.bl_idname, text="Start Viewport Control", icon='PLAY')
        layout.label(text="Press ESC to stop.")

# Register classes into Blender
classes = (DIPPID_OT_controller, DIPPID_PT_panel)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()