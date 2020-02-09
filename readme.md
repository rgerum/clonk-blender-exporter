# Blender Exporter
Download newest repository version: [download](https://github.com/rgerum/clonk-blender-exporter/archive/master.zip)


## Getting started
Open the file `object.blend`. It is the default setting of Blender equipped with the current version of the exporter.

When you open the file, Blender will ask you:

    For security reasons, automatic execution of Python scripts in this file was disabled.
    
If you click on `Allow Execution`, Blender will directly set up the export script.

<img src="https://github.com/rgerum/clonk-blender-exporter/blob/master/docs/allow_execute.png">


## Exporting
When the exporter is loaded and a mesh object is selected in Blender, an options menu will show up in the 3D view (if it is hidden press `N` and select the `Misc` tab). In this menu you can export the mesh with the button `Export Mesh` or export the skeleton (e.g. Armature with animations) with the button `Export Skeleton`.

You can specify an `Export Mesh Name` which is as default `Graphics` as OpenClonk expects .mesh files to be called `Graphics.mesh`. And you can specify an `Export Skeleton Name`, which is the name for the .skeleton file.

<img src="https://github.com/rgerum/clonk-blender-exporter/blob/master/docs/export_button.png">


## Exporting Animations
For your mesh to feature animations, you need an armature linked with the object (hold `Shift`, select object and armature and press `Ctrl+P` and selection `Armature Deform`). Then your mesh needs to assign the vertices to vertex groups with the bone names.

For more information on Armature see https://docs.blender.org/manual/en/2.81/animation/armatures/skinning/parenting.html

To create animations, use the `Dope Sheet` window (e.g. `Shift+F12`) and select the mode `Action Editor` (the default is `Dope Sheet` so this is displayed in the dropdown menu). There you can create an Action for each animation you want to export. Actions are composed of key frames which you add at different time points.

https://docs.blender.org/manual/en/2.81/editors/dope_sheet/action.html

The exporter tries to export all of these Actions. The frame range is defined by the key frames.

To overwrite the defaults, in the 3D Viewport window right next to the `Export Mesh` button, there is a menu to define the properties of the current Action, wether to export it, if it should be exported using a different name or a different range of frames.

*Note: if you have multiple actions, you have to tell Blender not to discard when saving the currently unused actions. Therefore, you have to activate the button with the savety pin right next to the actions name.*

<img src="https://github.com/rgerum/clonk-blender-exporter/blob/master/docs/animation.png">


## Material files
The exporter only uses material properties defined in the panel "Clonk Material" in the Material menu. Therefore, it is best to not tought the other material properties that Blender offerst, as these do not have any effect on the exported material. When you select a texture image, you can use the "UV Editor" to define on which parts of the mesh the texture is mapped.

*Note: as material names share a global namespace in OpenClonk, ensure that your material name is unique, e.g. by prefixing it with the object's name.*

<img src="https://github.com/rgerum/clonk-blender-exporter/blob/master/docs/define_material.png">


## Mesh Viewer
The exporter comes with simple MeshViewer to test quickly if the object shows up correctly in OpenClonk.

Therefore, copy your files in the folder`MeshViewer.ocs/TestObject.ocd` (the `DefCore.txt` should always stay there, the other files should be only there for the current mesh). Then you can start the scenario `MeshViewer.ocs` (e.g. wih the command `openclonk MeshViewer.ocs`).

Over a gray background your mesh should now be displayed. You can use the `WASD` keys to rotate the mesh, the mouse wheel to zoom in and the keys `Q` and `E` to cycle through all the animation. Hit `SPACE` to reset the view.


## XML Converter
There are two types of mesh files .mesh.xml and .mesh. What is the difference?

The exporter writes directly .mesh.xml files as these are just plain text files which can be easily generated. But for loading in Clonk they are unfortunately inefficient as they would take a long time to load. Therefore, they are converted to the binary .mesh format using the OgreXMLConverter.

The exporter comes with a Windows binary of this software to allow for an easy setup of the exporter. The exporter first tries to look for an installed version of the converter. If it does not find one, it looks in the subfolder `scripts/xml_converter` for the file (the default location from the repository). If you want to move youre .blend file you can also store a copy of the xml converter directly next to your .blend file.

If you use Linux, the exporter will try to call the xml converter using wine, which should work fine, too.

