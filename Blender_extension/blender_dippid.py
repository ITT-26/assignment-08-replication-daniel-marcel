import mathutils  # blender math utils
import math
import json
import socket
import bpy  # blender python api
bl_info = {
    "name": "DIPPID 6DOF Phone Controller",
    "author": "Daniel, Marcel",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > DIPPID",
    "description": "Orbits the 3D viewport using DIPPID phone sensor data.",
    "category": "3D View",
}


class DIPPID_Controller(bpy.types.Operator):
    """Start listening to DIPPID sensor data to move or rotate selected blender object"""
    bl_idname = "view3d.dippid_start"
    bl_label = "Start DIPPID Controller"

    _timer = None
    _sock = None

    # Tuning variables
    UDP_PORT = 5700
    DEADZONE = 0.05
    SENSITIVITY = 5 # Rotation speed multiplier

    acc_x = 0
    acc_y = 0
    acc_z = 0

    grav_x = 0
    grav_y = 0
    grav_z = 0

    gyro_x = 0
    gyro_y = 0
    grav_z = 0

    pitch = 0
    roll = 0
    yaw = 0

    def modal(self, context, event):
        # Stop the script if the user presses ESC
        if event.type in {'ESC'}:
            self.cancel(context)
            self.report({'INFO'}, "DIPPID Controller Stopped")
            return {'CANCELLED'}

        # Triggered every time the timer fires
        if event.type == 'TIMER':
            dt = 0.016
            try:
                # Receive data non-blockingly
                data, addr = self._sock.recvfrom(1024)
                payload = json.loads(data.decode('utf-8'))

                if "accelerometer" in payload:
                    acc = payload["accelerometer"]
                    self.acc_x = acc.get("x", 0)
                    self.acc_y = acc.get("y", 0)
                    self.acc_z = acc.get("z", 0)

                if "gravity" in payload:
                    grav = payload["gravity"]
                    self.grav_x = grav.get("x", 0)
                    self.grav_y = grav.get("y", 0)
                    self.grav_z = grav.get("z", 0)

                if "gyroscope" in payload:
                    gyro = payload["gyroscope"]
                    self.gyro_x = gyro.get("x", 0)
                    self.gyro_y = gyro.get("y", 0)
                    self.gyro_z = gyro.get("z", 0)

                # self.report({'INFO'}, f"Sensors: {self.acc_z}, {self.grav_x}, {self.gyro_x}")
                self.pitch = math.atan2(self.grav_x, math.sqrt(
                    self.grav_y**2 + self.grav_z ** 2))
                
                self.roll = math.atan2(self.grav_y, math.sqrt(
                    self.grav_y**2 + self.grav_z ** 2))
                
                self.yaw += self.gyro_z * dt

                self.rotate_selected_objects(
                    context, self.pitch, self.roll, self.yaw)

            except BlockingIOError:
                # No data arrived yet, just pass through smoothly
                pass
            except Exception as e:
                print(f"DIPPID Error: {e}")

        # Let normal Blender events (like regular mouse clicks) pass through
        return {'PASS_THROUGH'}

    def rotate_selected_objects(self, context, pitch=0, roll=0, yaw=0):
        # Ensure we are in a 3D viewport
        if context.area.type != 'VIEW_3D':
            return

        rv3d = context.space_data.region_3d
        if not rv3d:
            return

        # self.report({'INFO'}, f"Selected Objects: {context.selected_objects}")

        if context.selected_objects:
            if abs(pitch) < self.DEADZONE:
                pitch = 0
            if abs(roll) < self.DEADZONE:
                roll = 0
            if abs(yaw) < self.DEADZONE or pitch > 0 and roll > 0:
                yaw = 0
            for obj in context.selected_objects:
                obj.rotation_mode = 'QUATERNION'
                euler_rotation = mathutils.Euler((roll * self.SENSITIVITY, pitch * self.SENSITIVITY, yaw), 'XYZ')
                quat_rotation = euler_rotation.to_quaternion()
                obj.rotation_quaternion = quat_rotation
                # rv3d.view_rotation  = quat_rotation

    def invoke(self, context, event):
        # 1. Setup a NON-BLOCKING UDP Socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(('0.0.0.0', self.UDP_PORT))
        self._sock.setblocking(False)

        # 2. Setup the background timer (runs 60 times a second)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.016, window=context.window)
        wm.modal_handler_add(self)

        self.report(
            {'INFO'}, f"DIPPID Controller Running on Port {self.UDP_PORT}. Press ESC to stop.")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        """Cleanup function when the script stops"""
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        if self._sock:
            self._sock.close()


class DIPPID_PT_panel(bpy.types.Panel):
    bl_label = "DIPPID Controller"
    bl_idname = "DIPPID_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DIPPID'

    def draw(self, context):
        layout = self.layout
        layout.operator(DIPPID_Controller.bl_idname,
                        text="Start DIPPID Control", icon='PLAY')
        layout.label(text="Press ESC to stop.")


# Register classes into Blender
classes = (DIPPID_Controller, DIPPID_PT_panel)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
