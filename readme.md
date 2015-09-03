# Blender Exporter #
Download newest repository version: [download](bitbucket.org/randrian/clonkblenderogreexporter/get/tip.zip)

## Installation (Folder: BlenderAddon) ##


- install Blender (www.blender.org)
- copy the files from the folder BlenderAddon to:

    Linux: `~/.config/blender/[version]/scripts/addons/`

    Windows: `[blender directory]/[version]/scripts/addons/`

    `[version]` should be the version of the installed Blender e.g. 2.71 
- enable the addon:
    Load up Blender, go to `File`>`User Preferences`>`Addons`>`Import-Export` and enable the `OGRE Clonk Exporter` addon.
    Then click on "Save User Settings".
    HINT: You can also use the search box to look for an addon containing `"Clonk"`.
    
    
## Test the Exporter (TestBlenderFile) ##

- Open the Dice.blend tile
- Make sure the dice object is selected
- Go to `File`>`Export`>`Ogre3D Clonk (.scene and .mesh)`
- Select an export folder or just keep the folder as it is
- Click on the `"Export Ogre"` button in the right top corner

The files Graphics.mesh, Scene.material, Dice.png and Dice.skeleton should be created in your export directory.


## Test the Exported Mesh (MeshViewer.ocs) ##

- Copy MeshViewer.ocs into your OpenClonk directory
- Copy your exported files (`Graphics.mesh`, `Scene.material`, `Dice.png`, `Dice.skeleton`)
  into the folder MeshViewer.ocs/TestObject.ocd/
- Start OpenClonk with the Scenario MeshViewer.ocs
- Use WASD or mouse to rotate the mesh, Space to reset view
- use Q/E to cycle through the animations

## Animation Export ##

The default is to export all animations (see a Window with Editor Type `"Dope Sheet"` and Mode `"Action Editor"`). Only animation with start with "_" are excluded.
A Actions.txt file in the same folder as the .blend file can specify a more detailed animation export:

Actions.txt files include a block for each animation:
~~~~
[Action]
Name=Walk
Group=NoHands
ExportName=Walk
Start=1
End=25`
~~~~
Only the `Name` attribute is mandatory and specifies the name as seen in Blender. `ExportName` specifies how the animation should be called in Clonk, fallback is the same name as in Blender. `Start` and `End` specify the start and end frame of the animation. If omitted 0 and the last frame with a keyframe are used. `Group` specifies which bones should be exported. Therefore groups can be defined:

~~~~
[Group]
Name=UpperBody
Exclude=skeleton_leg*
Exclude=skeleton_foot*

[Group]
Name=Eyelids
Include=eye_lid.R
Include=eye_lid.L
~~~~
The groups can either `Exclude` some bones with specified names (wildcards can be used) or `Include` only specific bones. This can be used to define animations which affect only a part of the object and thus make it easy to overlay multiple animations in Clonk when different parts of the objects should be animated differently at the same time, e.g. the legs of the Clonk should walk while the upper body should load a bow.