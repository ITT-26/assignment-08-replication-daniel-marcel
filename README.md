[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/sPpq67Dc)


# Task 1 Finding a Suitable Paper

- We chose our interaction technique for this assignment from the following paper: [F. Klompmaker, K. Nebe and J. Eschenlohr, "Towards Multimodal 3D Tabletop Interaction Using Sensor Equipped Mobile Devices," in Mobile Computing, Applications,and Services, Springer, 2013, pp. 100-114.](https://link.springer.com/chapter/10.1007/978-3-642-36632-1_6).
- Documentation on the paper selection process can be found in [`paper_selection.md`](./documentation/paper_selection.md) in the [`documentation`](./documentation/) directory.


# Task 2 Implementation 

- As our final result we implemented an Add-on for Blender 3D.
- The code for the extension is in a single python file called [`blender_dippid`](./blender_extension/blender_dippid.py). 
- Documentation on the implementation is in [`implementation.md`](./documentation/implementation.md).
- The extension ist build for Blender 5, so the latest Blender version. 
- The python file can be opened in Blender's `Scripting` Tab. When opened, you can simply run the file and the `DIPPID` option will show up in the menu in the sidebar. 
- You can also add the extension permanently (not per project) to Blender via the `Preferences` options.
- For this go to `Edit` in the top left corner. Then choose `Preferences` and click on `Add-ons`. Click on the arrow in the top right corner there and choose `Install from disk...`. Then you can simply find the [`blender_dippid` file ](./blender_extension/blender_dippid.py) on your system and install the extension trough selecting it. Afterwards you should also have the `DIPPID` option in the menu on the sidebar.
- If there is no sidebar menu press `N` in the viewport so the menu is shown. `DIPPID` is the last option on the bottom. 
- You can simply start the DIPPID Controller with the button `Start DIPPID Control`. The extension then starts listening UDP Port 5700 for DIPPID data. 
- Simply connect your phone through entering the right IP and port in the DIPPID app and then you can start controlling the viewport or selected objects in `Object Mode`.
- You can use the checkbox `Move and Rotate Viewport` to enable the movement and rotation of the viewport instead of the movement and rotation of selected objects. 
- Then simply press Button 1 or Button 2 on your device to either move or rotate the viewport / the selected object. You can also select multiple objects and move or rotate them at the same time. You cannot move/rotate the viewport and objects at the same time. This is controlled by the checkbox. Object control only works if it is not checked.
- When the DIPPID Controller is running it also shows the time since the last DIPPID package was received. This way it is possible to determine if the connection between DIPPID device and Blender works.

# Task 3 Presentation 

- The entry in the GRIPS forum _Replicating Interaction Techniques_ with the demo video can be found [here](https://elearning.uni-regensburg.de/mod/forum/discuss.php?d=599197).