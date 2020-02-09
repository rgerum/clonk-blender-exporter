import bpy
from pathlib import Path
import shutil


class Block:
    def __init__(self, name, fp):
        self.name = name
        self.fp = fp
        
    def __enter__(self):
        self.fp.write(self.name+"\n")
        self.fp.write("{\n")
        self.fp_old_write = self.fp.write
        def write(text):
            self.fp_old_write("        "+text)
        self.fp.write = write
        
    def __exit__(self, *args):
        self.fp.write = self.fp_old_write
        self.fp.write("}\n")
        
    
def printValues(*args):
    all_values = []
    for arg in args:
        try:
            all_values += list(arg)
        except TypeError:
            all_values += list([arg])
    return " ".join(["%.2f" % val for val in all_values])


def writeMaterials(filename, mats):
    file = Path(filename)
    print(file)
    working_directory = Path(bpy.data.filepath).parent
    with file.open("w") as fp:
        for mat_name in mats:
            mat = bpy.data.materials[mat_name]
            with Block("material "+mat_name, fp):
                if mat.clonkReceiveShadows:
                    fp.write("receive_shadows on\n")
                with Block("technique", fp):
                    with Block("pass", fp):
                        fp.write("ambient "+printValues(mat.clonkAmbient)+"\n")
                        fp.write("diffuse "+printValues(mat.clonkDiffuse)+"\n")
                        fp.write("specular "+printValues(mat.clonkSpecular, mat.clonkSpecularSize)+"\n")
                        fp.write("emissive "+printValues(mat.clonkEmissive)+"\n")
                        if mat.clonkTexture is not None:
                            image = mat.clonkTexture
                            with Block("texture_unit", fp):
                                fp.write(f"texture {image.name}\n")
                                fp.write("tex_address_mode wrap\n")
                                fp.write("filtering trilinear\n")
                                shutil.copy(image.filepath.replace("//", str(working_directory)+"/"),
                                                file.parent / image.name)
				
