import mathutils  # blender math utils
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

    last_acc_x = None
    last_acc_y = None
    last_acc_z = None

    # Tuning variables
    UDP_PORT = 5700

    SENSITIVITY = 1  # Rotation speed multiplier

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

                if "accelerometer" in payload:
                    acc = payload["accelerometer"]
                    acc_x = acc.get("x", 0)
                    acc_y = acc.get("y", 0)
                    acc_z = acc.get("z", 0)

                if not (self.last_acc_x is None or self.last_acc_y is None or self.last_acc_z is None):
                    self.rotate_selected_object(
                        context, acc_x - self.last_acc_x, acc_y - self.last_acc_y, acc_z - self.last_acc_z)
                self.last_acc_x = acc_x
                self.last_acc_y = acc_y
                self.last_acc_z = acc_z

            except BlockingIOError:
                # No data arrived yet, just pass through smoothly
                pass
            except Exception as e:
                print(f"DIPPID Error: {e}")

        # Let normal Blender events (like regular mouse clicks) pass through
        return {'PASS_THROUGH'}

    def rotate_selected_object(self, context, acc_x, acc_y, acc_z):
        # Ensure we are in a 3D viewport
        if context.area.type != 'VIEW_3D':
            return

        rv3d = context.space_data.region_3d
        if not rv3d:
            return

        # self.report({'INFO'}, f"Selected Objects: {context.selected_objects}")

        if context.selected_objects:
            for obj in context.selected_objects:
                obj.rotation_euler.x += acc_x * self.SENSITIVITY
                obj.rotation_euler.y += acc_y * self.SENSITIVITY
                obj.rotation_euler.z += acc_z * self.SENSITIVITY

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
