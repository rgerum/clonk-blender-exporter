config = {
    'MESH' : True,
    'SCENE' : True,
    'COPY_SHADER_PROGRAMS' : True,
    'MAX_TEXTURE_SIZE' : 4096,
    'SWAP_AXIS' : 'xz-y', # ogre standard is 'xz-y', but swapping is currently broken
    'SEP_MATS' : True,
    'SELONLY' : True,
    'EXPORT_HIDDEN' : True,
    'FORCE_CAMERA' : True,
    'FORCE_LAMPS' : True,
    'MESH_OVERWRITE' : True,
    'ONLY_DEFORMABLE_BONES' : False,
    'ONLY_KEYFRAMED_BONES' : False,
    'OGRE_INHERIT_SCALE' : False,
    'FORCE_IMAGE_FORMAT' : 'NONE',
    'TOUCH_TEXTURES' : True,
    'ARM_ANIM' : True,
    'SHAPE_ANIM' : True,
    'ARRAY' : True,
    'MATERIALS' : True,
    'DDS_MIPS' : True,
    'TRIM_BONE_WEIGHTS' : 0.01,
    'TUNDRA_STREAMING' : True,
    'lodLevels' : 0,
    'lodDistance' : 300,
    'lodPercent' : 40,
    'nuextremityPoints' : 0,
    'generateEdgeLists' : False,
    'generateTangents' : True, # this is now safe - ignored if mesh is missing UVs
    'tangentSemantic' : 'tangent', # used to default to "uvw" but that doesn't seem to work with anything and breaks shaders
    'tangentUseParity' : 4,
    'tangentSplitMirrored' : False,
    'tangentSplitRotated' : False,
    'reorganiseBuffers' : True,
    'optimiseAnimations' : True,
    'interface_toggle': False,
}
