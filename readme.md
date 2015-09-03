# Your title here... #
## Installation (Folder: BlenderAddon) ##


- install Blender (www.blender.org)
- copy the files from the folder BlenderAddon to:
    Linux: ~/.config/blender/[version]/scripts/addons/ 
    Windows: [blender directory]/[version]/scripts/addons/ 
    [version] should be the version of the installed Blender e.g. 2.71 
- enable the addon:
    Load up Blender, go to File>User Preferences>Addons>Import-Export and enable the "OGRE Clonk Exporter" addon.
    Then click on "Save User Settings".
    HINT: You can also use the search box to look for an addon containing "Clonk".
    
    
## Test the Exporter (TestBlenderFile) ##

- Open the Dice.blend tile
- Make sure the dice object is selected
- Go to File>Export>Ogre3D Clonk (.scene and .mesh)
- Select an export folder or just keep the folder as it is
- Click on the "Export Ogre" button in the right top corner

The files Graphics.mesh, Scene.material, Dice.png and Dice.skeleton should be created in your export directory.


## Test the Exported Mesh (MeshViewer.ocs) ##

- Copy MeshViewer.ocs into your OpenClonk directory
- Copy your exported files (Graphics.mesh, Scene.material, Dice.png, Dice.skeleton)
  into the folder MeshViewer.ocs/TestObject.ocd/
- Start OpenClonk with the Scenario MeshViewer.ocs
- Use WASD or mouse to rotate the mesh
- Type in the editor GetCursor()->SetAnimation("OpenCloseLid") to view the animation