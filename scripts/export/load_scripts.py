import bpy

filenames = [
    "config.py",
    "material.py",
    "mesh.py",
    "report.py",
    "skeleton.py",
    "ui.py",
    "util.py",
    "xml_simple.py",
    "load_scripts.py",
]

def getPath(file):
    if file == "ui.py":
        return "//scripts/"+file
    else:
        return "//scripts/export/"+file    

# iterate over all filenames
for file in filenames:
    # remove the file if it exits
    if file in bpy.data.texts:
        bpy.data.texts.remove(bpy.data.texts[file])
    # and open it from the provided path
    bpy.ops.text.open(filepath=getPath(file))
    text = bpy.data.texts[file]
    text.filepath = getPath(file)

# register the ui.py text as a module (it gets called on load of the .blend file)
bpy.data.texts["ui.py"].use_module = True
bpy.context.space_data.text = bpy.data.texts["ui.py"]
bpy.ops.text.run_script()
bpy.context.space_data.text = bpy.data.texts["load_scripts.py"]
