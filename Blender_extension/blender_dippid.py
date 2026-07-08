import mathutils  # blender math utils
import math
import json
import socket
import time
import bpy  # blender python api

bl_info = {
    "name": "DIPPID 6DOF Phone Controller",
    "author": "Daniel, Marcel",
    "version": (1, 2),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > DIPPID",
    "description": "Enables movement and rotation of selected objects using DIPPID phone sensor data.",
    "category": "3D View",
}


class DIPPID_Controller(bpy.types.Operator):
    """Start listening to DIPPID sensor data to move or rotate selected blender objects"""
    bl_idname = "view3d.dippid_start"
    bl_label = "Start DIPPID Controller"

    _timer = None
    _sock = None
    _last_tick_time = None

    # Tuning variables
    UDP_PORT = 5700
    TIMER_INTERVAL = 0.016  # seconds, ~60Hz - just how often we poll, NOT
    # used as dt anymore (see _last_tick_time)

    # 1.0 = true 1:1 scaling: rotating the phone by X degrees rotates the
    # object by exactly X degrees. Change only if you deliberately want a
    # gain (e.g. 2.0 to rotate the object twice as fast as the phone).
    SENSITIVITY = 1.0

    # clutch: object only rotates while this is True (button_1 held on
    # the phone), same idea as lifting a physical mouse to reposition it
    # without moving the cursor.
    rot_clutch_engaged = False
    mov_clutch_engaged = False

    acc_x = 0
    acc_y = 0
    acc_z = 0

    grav_x = 0
    grav_y = 0
    grav_z = 0

    gyro_x = 0
    gyro_y = 0
    gyro_z = 0

    def modal(self, context, event):
        # Stop the script if the user presses ESC
        if event.type in {'ESC'}:
            self.cancel(context)
            self.report({'INFO'}, "DIPPID Controller Stopped")
            return {'CANCELLED'}

        # Triggered every time the timer fires
        if event.type == 'TIMER':
            now = time.time()
            # dt = the ACTUAL time since the last tick, not the nominal
            # timer interval. Blender's timer isn't perfectly exact, and
            # for genuine 1:1 scaling the integration needs to match real
            # elapsed time, not an assumed constant.
            dt = (
                now - self._last_tick_time) if self._last_tick_time else self.TIMER_INTERVAL
            self._last_tick_time = now

            # Drain ALL pending packets this tick, not just one. DIPPID can
            # easily send accelerometer + gyroscope updates faster than our
            # 60Hz timer, so reading only one per tick lets a backlog build
            # up and the rotation lags further and further behind reality.
            while True:
                try:
                    data, addr = self._sock.recvfrom(1024)
                except BlockingIOError:
                    break

                try:
                    payload = json.loads(data.decode('utf-8'))
                except json.JSONDecodeError:
                    continue

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

                # button_1 is the clutch: held = rotate, released = frozen.
                # DIPPID sends 0 (released) or 1 (pressed).
                if "button_1" in payload:
                    self.rot_clutch_engaged = bool(payload["button_1"])

                if "button_2" in payload:
                    self.mov_clutch_engaged = bool(payload["button_2"])

            # Only integrate/apply rotation while the clutch is held. While
            # released we still drain and update sensor values above (so
            # there's no backlog/jump when re-engaging), we just don't
            # apply them to the object.

            if self.rot_clutch_engaged:
                self.rotate_selected_objects(
                    context, dt, self.gyro_x, self.gyro_y, self.gyro_z
                )

            if self.mov_clutch_engaged:
                self.move_selected_objects(
                    context, dt, self.gyro_x, self.gyro_y, self.gyro_z
                )

        # Let normal Blender events (like regular mouse clicks) pass through
        return {'PASS_THROUGH'}

    def rotate_selected_objects(self, context, dt, x=0, y=0, z=0):
        if context.area.type != 'VIEW_3D' or not context.selected_objects:
            return

        # Get Viewport Direction
        rv3d = context.space_data.region_3d
        view = rv3d.view_rotation  # this is a quaternion

        ROT_THRESHHOLD = 0.05
        if abs(x) < ROT_THRESHHOLD:
            x = 0
        if abs(y) < ROT_THRESHHOLD:
            y = 0
        if abs(z) < ROT_THRESHHOLD:
            z = 0

        view_angular_velocity = mathutils.Vector((x, z, -y)) * self.SENSITIVITY
        # interpret sensor change only as view coordinate system change
        # this means changes are dependent on view direction

        world_angular_velocity = view @ view_angular_velocity
        # convert to world coordnates with view quaternion

        angle = world_angular_velocity.length * dt

        # nothing to do this frame - and normalizing a zero vector would
        # raise an error, so bail out early
        if angle == 0:
            return

        axis = world_angular_velocity.normalized()
        # incremental rotation for JUST this frame's worth of angular
        # velocity - this is what actually gets integrated/accumulated
        # over time, instead of re-deriving an absolute target rotation
        # from instantaneous (velocity, not orientation!) gyro values.
        delta_rotation = mathutils.Quaternion(axis, angle)

        # print(f"DEBUG: gyro=({x:.2f}, {y:.2f}, {z:.2f})  delta_angle(deg)={angle * 57.2958:.2f}")

        for obj in context.selected_objects:
            obj.rotation_mode = 'QUATERNION'
            # compose the incremental rotation onto the EXISTING rotation,
            # rather than lerping toward a target derived from velocity.
            # This is what makes rotation persist once the phone stops
            # moving, instead of relaxing back toward identity.
            obj.rotation_quaternion = delta_rotation @ obj.rotation_quaternion

    def move_selected_objects(self, context, dt, x, y, z):
        if context.area.type != 'VIEW_3D' or not context.selected_objects:
            return

        # different mapping here for more inuitive controls

        MOV_THRESHHOLD = 0.05
        if abs(x) < MOV_THRESHHOLD:
            x = 0
        if abs(y) < MOV_THRESHHOLD:
            y = 0
        if abs(z) < MOV_THRESHHOLD:
            z = 0

        MOV_SENSITIVITY = 0.2
        view_angular_velocity = mathutils.Vector((-z, x, -y)) * MOV_SENSITIVITY

        # Get Viewport Direction
        rv3d = context.space_data.region_3d
        view = rv3d.view_rotation  # this is a quaternion

        world_angular_velocity = view @ view_angular_velocity
        # convert to world coordnates with view quaternion
        VELOCITY = 50
        movement = world_angular_velocity * dt * VELOCITY

        if movement.length == 0:
            return

        for obj in context.selected_objects:
            obj.location += movement

    def invoke(self, context, event):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Magic setting: allows the socket to re-bind immediately after a crash
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self._sock.bind(('0.0.0.0', self.UDP_PORT))
        except OSError as e:
            self.report(
                {'ERROR'}, f"Port {self.UDP_PORT} in use! Restart Blender.")
            return {'CANCELLED'}

        self._sock.setblocking(False)
        self._last_tick_time = None
        self.rot_clutch_engaged = False

        wm = context.window_manager
        self._timer = wm.event_timer_add(
            self.TIMER_INTERVAL, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        """Cleanup function when the script stops"""
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self._timer = None
        if self._sock:
            self._sock.close()
            self._sock = None


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


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


def register():
    # --- PORT CLEANUP AT STARTUP ---
    # Attempt to close any lingering sockets on port 5700 from a previous
    # run that didn't shut down correctly.
    try:
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        temp_sock.bind(('0.0.0.0', 5700))
        temp_sock.close()
    except Exception as e:
        print(f"Port 5700 check: {e}")

    for cls in classes:
        bpy.utils.register_class(cls)


if __name__ == "__main__":
    register()
