# Implementation

## Sensing Pipeline Prototype

- First we wanted to check if the DIPPID + phone sensor pipeline even works the way we want it to, so we didn't have to debug DIPPID, the sensor mapping and the output program all together at once. We wrote a quick standalone Python script ([`dippid_mouse.py`](../first_attempts/dippid_mouse_simple.py)) that just moves the OS mouse cursor with the phone.
- Like in [Klompmaker et al.](https://link.springer.com/chapter/10.1007/978-3-642-36632-1_6) we tilted the phone away from a neutral position and mapped that to cursor movement, not to an absolute position. So tilting further = cursor moves faster, not further.
- We also quickly tried it the other way round, where actually moving the phone through the air moves the cursor 1:1. This drifted like crazy, even standing still the cursor slowly wandered off (a threshold could have solved this). So we dropped that idea and stuck with tilt, which is also closer to what the paper does anyway.
- Once the cursor moved the way we expected we were confident enough in the pipeline to move on to a real 3D app.

## FreeCAD Prototype

- Since FreeCAD was the app we originally considered, we first tried getting it working there. FreeCAD doesn't have anything like Blender's Python API for controlling the viewport directly (at least nothing we found quickly), so instead of doing it "properly" we just faked keyboard/mouse input with `pyautogui`: holding `button_1` on the phone presses down Shift + Right Click (FreeCAD's default orbit shortcut in "CAD" navigation mode) and then we move the OS mouse based on gyro x/z while it's held.
- It actually mostly worked, holding the button and sweeping the phone did orbit the model. But it felt pretty hacky: we're not actually talking to FreeCAD at all, just pretending to be a mouse+keyboard, so we're stuck with whatever shortcut FreeCAD happens to bind to orbiting, can't easily do movement/panning the same way without finding another shortcut to fake, and it would break immediately if the navigation style or shortcuts were different (had to specifically tell FreeCAD to use "CAD" navigation style for this to work).
- We decided against going further down this path and to properly get it working we would have had to fake input for every single gesture (rotate, move, zoom) or dig into FreeCAD's own source/scripting to do it properly instead of faking OS-level input, which felt like a lot of extra work for not much gain, especially compared to Blender.

## Pivot to Blender

- Aside from FreeCAD being more annoying to control, we also just thought Blender would be more interesting to build for since way more people use/care about it (bigger addressable market, more people who'd actually be interested in trying our demo).
- The add-on ([`dippid_blender_addon.py`](../Blender_extension/blender_dippid.py)) is a Blender modal operator. On start it opens a UDP socket and sets up a timer that fires about 60 times a second, and each time it fires it reads out however many DIPPID packets are waiting (not just one, because the phone sends faster than 60Hz and otherwise stuff piles up and everything gets laggy) and updates the object.

## Rotation Bug

- First version just built a quaternion straight from the gyroscope values every frame and smoothly rotated toward that. Looked ok for a second but then we noticed as soon as you stop moving the phone the object snaps back to almost no rotation, since gyro values go back to 0 when you stop and our target rotation basically went back to "no rotation" too.
- Fixed it by not building an absolute target rotation anymore. Instead each frame we take the current gyro reading, turn it into a tiny rotation for just that frame (based on how fast + which direction it's spinning), and stack that on top of whatever rotation the object already has. That way it actually keeps turning instead of snapping back.

## Clutch Buttons

- The paper uses one button that switches between moving and rotating, reusing the same gestures for both. We just used two separate buttons instead, one for rotate and one for move, so we can turn either on/off independently (or even both at once).
- Mainly did it this way because it was easier to test each one on its own while building it. Works basically like lifting up a real mouse, while you're not holding the button nothing moves, but we still keep reading the sensor in the background so there's no jump when you press it again.

## 1:1 Scaling

- Wanted turning the phone by some angle to turn the object by exactly that angle.
- Just setting the gain to 1 wasn't quite enough, we also had to use the actual real time between two timer ticks instead of just assuming a fixed 60Hz, since Blender's timer isn't 100% exact and that was throwing the scaling off slightly.
- Also DIPPID (at least in testing has wierd drops between packets that are anoying)
```bash  
Moving: X=0, Y=-9 (Packet Gap: 0.01s)
Moving: X=0, Y=-9 (Packet Gap: 0.01s)
Moving: X=0, Y=-151 (Packet Gap: 0.28s)
Moving: X=0, Y=-8 (Packet Gap: 0.00s)
Moving: X=2, Y=-9 (Packet Gap: 0.00s)
Moving: X=0, Y=-8 (Packet Gap: 0.00s) 
```

## Rotation Rate for Movement Too

- Movement was originally based on acceleration, same as the first mouse test. Switched it to use the gyroscope instead, so now rotating the phone moves the object (same view-relative thing as rotation, just applied as movement instead).
- Did this because accelerometer data is just a lot noisier.

## View-Relative Mapping

- Instead of mapping phone axes straight onto Blender's world axes, we first treat the input as if it's relative to whatever direction you're currently looking at in the viewport, and only then convert that into world space. So tilting the phone "up" always moves/rotates things "up" on your screen no matter which way you're currently looking at the scene, instead of always being tied to a fixed world direction.

## Axis Calibration

- Phone axes (x = right side of phone, y = out the top, z = out of the screen) don't automatically match up with how Blender's view is set up, and it also depends on how you're holding the phone.
- Instead of trying to figure it out on paper we just tested it by hand. Rotate the phone around one axis at a time, watch the debug print of the gyro values and see what actually happens in Blender. Found two things to fix:
  - Rotation: y (out the top) and z (out of the screen) were swapped, so we just swapped them back, left x alone.
  - Movement: z (out of the screen) was inverted, so we just flipped the sign on that one.
- Took a couple of tries since swapping the wrong two axes can look like it half-fixes things while actually just breaking something else.