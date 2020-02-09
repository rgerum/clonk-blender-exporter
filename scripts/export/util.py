import time
import mathutils
import subprocess
import os, sys
import bpy
from pathlib import Path

def xml_convert(infile, has_uvs=False):
    # test if the converter exists in the path
    try:
        if subprocess.call("OgreXMLConverter") == 0:
            cmd = ["OgreXMLConverter"]
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        # maybe it is directly next to the .blend file
        filename = Path(bpy.data.filepath).parent / "OgreXMLConverter.exe"
        if not filename.exists():
            # or in a subfolder?
            filename = Path(bpy.data.filepath).parent / "scripts/xml_converter/OgreXMLConverter.exe"
        cmd = [filename]
        # if we are on Linux, try to call it with wine
        if sys.platform.startswith("linux"):
            cmd.insert(0, "wine")
    
    cmd.append(infile)
    try:
        subprocess.call(cmd)
    except FileNotFoundError as err:
        print("FileNotFoundError", err)

def material_name( mat, clean = False, prefix='' ):
    """
    returns the material name.

    materials from a library might be exported several times for multiple objects.
    there is no need to have those textures + material scripts several times. thus
    library materials are prefixed with the material filename. (e.g. test.blend + diffuse
    should result in "test_diffuse". special chars are converted to underscore.

    clean: deprecated. do not use!
    """
    if type(mat) is str:
        return prefix + clean_object_name(mat)
    name = clean_object_name(mat.name)
    if mat.library:
        _, filename = split(mat.library.filepath)
        prefix, _ = splitext(filename)
        return prefix + "_" + name
    else:
        return prefix + name

invalid_chars = '\/:*?"<>|'

def clean_object_name(value):
    global invalid_chars
    for invalid_char in invalid_chars:
        value = value.replace(invalid_char, '_')
    value = value.replace(' ', '_')
    return value

def swap(vec):
    #swap_axis = config.get('SWAP_AXIS')
    swap_axis = 'xz-y'
    if swap_axis == 'xyz': return vec
    elif swap_axis == 'xzy':
        if len(vec) == 3: return mathutils.Vector( [vec.x, vec.z, vec.y] )
        elif len(vec) == 4: return mathutils.Quaternion( [ vec.w, vec.x, vec.z, vec.y] )
    elif swap_axis == '-xzy':
        if len(vec) == 3: return mathutils.Vector( [-vec.x, vec.z, vec.y] )
        elif len(vec) == 4: return mathutils.Quaternion( [ vec.w, -vec.x, vec.z, vec.y] )
    elif swap_axis == 'xz-y':
        if len(vec) == 3: return mathutils.Vector( [vec.x, vec.z, -vec.y] )
        elif len(vec) == 4: return mathutils.Quaternion( [ vec.w, vec.x, vec.z, -vec.y] )
    else:
        logging.warn( 'unknown swap axis mode %s', swap_axis )
        assert 0

def timer_diff_str(start):
    return "%0.2f" % (time.time()-start)