import os, time, sys, logging
import bpy
Report = bpy.data.texts["report.py"].as_module().Report
xml = bpy.data.texts["xml_simple.py"].as_module()
util = bpy.data.texts["util.py"].as_module()
config = bpy.data.texts["config.py"].as_module()


def dot_mesh(ob, path, force_name=None, **kwargs):
    """
    export the vertices of an object into a .mesh file

    ob: the blender object
    path: the path to save the .mesh file to. path MUST exist
    force_name: force a different name for this .mesh
    kwargs:
      * material_prefix - string. (optional)
      * overwrite - bool. (optional) default False
    """
    obj_name = force_name or ob.clonkExportName
    obj_name = util.clean_object_name(obj_name)
    target_file = os.path.join(path, '%s.mesh.xml' % obj_name)
    print("target_file", target_file)

    material_prefix = kwargs.get('material_prefix', '')
    overwrite = kwargs.get('overwrite', False)

    if os.path.isfile(target_file) and not overwrite:
        return []

    if not os.path.isdir(path):
        os.makedirs(path)

    start = time.time()

    # blender per default does not calculate these. when querying the quads/tris
    # of the object blender would crash if calc_tessface was not updated
    ob.data.calc_loop_triangles()

    # add something to the report
    Report.meshes.append(obj_name)
    Report.faces += len(ob.data.loop_triangles)
    Report.orig_vertices += len(ob.data.vertices)

    cleanup = False
    # if the object has modifiers remove them and work on a copy
    if ob.modifiers:
        cleanup = True
        copy = ob.copy()
        # bpy.context.scene.objects.link(copy)
        rem = []
        for mod in copy.modifiers:  # remove armature and array modifiers before collapse
            if mod.type in 'ARMATURE ARRAY'.split(): rem.append(mod)
        for mod in rem: copy.modifiers.remove(mod)
        # bake mesh
        mesh = copy.to_mesh(bpy.context.depsgraph, apply_modifiers=True)  # collapse
        mesh.calc_loop_triangles()
    else:
        copy = ob
        mesh = ob.data

    # print status
    if logging:
        print('      - Generating:', '%s.mesh.xml' % obj_name)

    # try to open the target file
    try:
        with open(target_file, 'w') as f:
            f.flush()
    except Exception as e:
        print("Invalid mesh object name: " + obj_name)  # TODO was show_dialog
        return

    # open the target file
    with open(target_file, 'w') as f:
        # start an xml writer with a mesh tag
        doc = xml.SimpleSaxWriter(f, 'mesh', {})

        """ the sharedgeometry tag """
        # Very ugly, have to replace number of vertices later
        doc.start_tag('sharedgeometry', {'vertexcount': '__TO_BE_REPLACED_VERTEX_COUNT__'})

        if logging:
            print('      - Writing shared geometry')

        """ the vertexbuffer tag as a subtag of the sharedgeometry tag"""
        doc.start_tag('vertexbuffer', {
            'positions': 'true',
            'normals': 'true',
            'colours_diffuse': str(bool(mesh.vertex_colors)),
            'texture_coords': '%s' % len(mesh.uv_layers) #if mesh.uv_textures.active else '0'
        })

        # Vertex colors, note that you can define a vertex color
        # material. see 'vertex_color_materials' below!
        vcolors = None
        vcolors_alpha = None
        if len(mesh.vertex_colors):
            vcolors = mesh.vertex_colors[0]
            for bloc in mesh.vertex_colors:
                if bloc.name.lower().startswith('alpha'):
                    vcolors_alpha = bloc
                    break

        # Materials
        # saves tuples of material name and material obj (or None)
        materials = []
        # a material named 'vertex.color.<yourname>' will overwrite
        # the diffuse color in the mesh file!
        vertex_color_materials = []
        for mat in ob.data.materials:
            mat_name = "_missing_material_"
            if mat is not None:
                mat_name = mat.name
            mat_name = util.material_name(mat_name, prefix=material_prefix)
            extern = False
            if mat_name.startswith("extern."):
                mat_name = mat_name[len("extern."):]
                extern = True
            if mat:
                materials.append((mat_name, extern, mat))
            else:
                print('[WARNING:] Bad material data in', ob)
                materials.append(('_missing_material_', True, None))  # fixed dec22, keep proper index
        if not materials:
            materials.append(('_missing_material_', True, None))
        vertex_groups = {}
        material_faces = []
        for matidx, mat in enumerate(materials):
            material_faces.append([])

        # Textures
        dotextures = False
        uvcache = []  # should get a little speed boost by this cache
        if mesh.uv_layers.active:
        #if mesh.tessface_uv_textures.active:
            dotextures = True
            for uv_layer in mesh.uv_layers:
                uvs = []
                uvcache.append(uvs)  # layer contains: name, active, data
                for uv in uv_layer.data:
                    uvs.append(uv.uv)

            #for layer in mesh.tessface_uv_textures:
            #for layer in mesh.uv_layers:
            #    uvs = []
            #    uvcache.append(uvs)  # layer contains: name, active, data
            #    for uvface in layer.data:
            #        uvs.append((uvface.uv1, uvface.uv2, uvface.uv3, uvface.uv4))

        shared_vertices = {}
        _remap_verts_ = []
        numverts = 0

        print("***********************************************")
        print("***********************************************")
        print("\n\nEXPORT\n\n", mesh, len(mesh.loop_triangles))

        # iterate over all faces (meshTessFace objects)
        for tri in mesh.loop_triangles:
            print("tri", tri)
        #for tessface in mesh.tessfaces:

            #if dotextures:
            #    a = []
            #    b = []
            #    uvtris = [a, b]
            #    for layer in uvcache:
            #        uv1, uv2, uv3, uv4 = layer[tri.index]
            #        a.append((uv1, uv2, uv3))
            #        b.append((uv1, uv3, uv4))

            # iterate over triangles of the face
            face = []
            # iterate over the vertices of the triangle
            #for vidx, idx in enumerate(tri):
            for vidx, idx in enumerate(tri.vertices):
                # get the vertex
                vertex = mesh.vertices[idx]

                # get the normal
                if tri.use_smooth:
                    nx, ny, nz = util.swap(vertex.normal)  # fixed june 17th 2011
                else:
                    nx, ny, nz = util.swap(tri.normal)

                # get the color of the vertex
                export_vertex_color, color_tuple = extract_vertex_color(vcolors, vcolors_alpha, tri, idx)
                r, g, b, ra = color_tuple

                # Texture maps
                vert_uvs = []
                if dotextures:
                    for uv_layer in mesh.uv_layers:
                        loop_index = tri.loops[vidx]
                        vert_uvs.append(uv_layer.data[loop_index].uv)
                    #for layer in uvtris[tidx]:
                    #    vert_uvs.append(layer[vidx])

                ''' Check if we already exported that vertex with same normal, do not export in that case,
                    (flat shading in blender seems to work with face normals, so we copy each flat face'
                    vertices, if this vertex with same normals was already exported,
                    todo: maybe not best solution, check other ways (let blender do all the work, or only
                    support smooth shading, what about seems, smoothing groups, materials, ...)
                '''
                vert = VertexNoPos(numverts, nx, ny, nz, r, g, b, ra, vert_uvs)
                alreadyExported = False
                if idx in shared_vertices:
                    for vert2 in shared_vertices[idx]:
                        # does not compare ogre_vidx (and position at the moment)
                        if vert == vert2:
                            face.append(vert2.ogre_vidx)
                            alreadyExported = True
                            # print(idx,numverts, nx,ny,nz, r,g,b,ra, vert_uvs, "already exported")
                            break
                    if not alreadyExported:
                        face.append(vert.ogre_vidx)
                        shared_vertices[idx].append(vert)
                        # print(numverts, nx,ny,nz, r,g,b,ra, vert_uvs, "appended")
                else:
                    face.append(vert.ogre_vidx)
                    shared_vertices[idx] = [vert]
                    # print(idx, numverts, nx,ny,nz, r,g,b,ra, vert_uvs, "created")

                if alreadyExported:
                    continue

                numverts += 1
                _remap_verts_.append(vertex)

                x, y, z = util.swap(vertex.co)  # xz-y is correct!

                doc.start_tag('vertex', {})
                doc.leaf_tag('position', {
                    'x': '%6f' % x,
                    'y': '%6f' % y,
                    'z': '%6f' % z
                })

                doc.leaf_tag('normal', {
                    'x': '%6f' % nx,
                    'y': '%6f' % ny,
                    'z': '%6f' % nz
                })

                if export_vertex_color:
                    doc.leaf_tag('colour_diffuse', {'value': '%6f %6f %6f %6f' % (r, g, b, ra)})

                # Texture maps
                if dotextures:
                    for uv in vert_uvs:
                        doc.leaf_tag('texcoord', {
                            'u': '%6f' % uv[0],
                            'v': '%6f' % (1.0 - uv[1])
                        })

                doc.end_tag('vertex')

            append_triangle_in_vertex_group(mesh, ob, vertex_groups, face, [v for v in tri.vertices])
            faces = material_faces[tri.material_index]
            faces.append((face[0], face[1], face[2]))

        Report.vertices += numverts

        doc.end_tag('vertexbuffer')
        doc.end_tag('sharedgeometry')

        if logging:
            print('        Done at', util.timer_diff_str(start), "seconds")
            print('      - Writing submeshes')

        doc.start_tag('submeshes', {})
        for matidx, (mat_name, extern, mat) in enumerate(materials):
            if not len(material_faces[matidx]):
                Report.warnings.append(
                    'BAD SUBMESH "%s": material %r, has not been applied to any faces - not exporting as submesh.' % (
                    obj_name, mat_name))
                continue  # fixes corrupt unused materials

            submesh_attributes = {
                'usesharedvertices': 'true',
                # Maybe better look at index of all faces, if one over 65535 set to true;
                # Problem: we know it too late, postprocessing of file needed
                "use32bitindexes": str(bool(numverts > 65535)),
                "operationtype": "triangle_list"
            }
            if mat_name != "_missing_material_":
                submesh_attributes['material'] = mat_name

            doc.start_tag('submesh', submesh_attributes)
            doc.start_tag('faces', {
                'count': str(len(material_faces[matidx]))
            })
            for fidx, (v1, v2, v3) in enumerate(material_faces[matidx]):
                doc.leaf_tag('face', {
                    'v1': str(v1),
                    'v2': str(v2),
                    'v3': str(v3)
                })
            doc.end_tag('faces')
            doc.end_tag('submesh')
            Report.triangles += len(material_faces[matidx])

        for name, ogre_indices in vertex_groups.items():
            if len(ogre_indices) <= 0:
                continue
            submesh_attributes = {
                'usesharedvertices': 'true',
                "use32bitindexes": str(bool(numverts > 65535)),
                "operationtype": "triangle_list",
                "material": "none",
            }
            doc.start_tag('submesh', submesh_attributes)
            doc.start_tag('faces', {
                'count': len(ogre_indices)
            })
            for (v1, v2, v3) in ogre_indices:
                doc.leaf_tag('face', {
                    'v1': str(v1),
                    'v2': str(v2),
                    'v3': str(v3)
                })
            doc.end_tag('faces')
            doc.end_tag('submesh')

        del material_faces
        del shared_vertices
        doc.end_tag('submeshes')

        # Submesh names
        # todo: why is the submesh name taken from the material
        # when we have the blender object name available?
        doc.start_tag('submeshnames', {})
        for matidx, (mat_name, extern, mat) in enumerate(materials):
            doc.leaf_tag('submesh', {
                'name': mat_name,
                'index': str(matidx)
            })
        idx = len(materials)
        for name in vertex_groups.keys():
            name = name[len('ogre.vertex.group.'):]
            doc.leaf_tag('submesh', {'name': name, 'index': idx})
            idx += 1
        doc.end_tag('submeshnames')

        if logging:
            print('        Done at', util.timer_diff_str(start), "seconds")


        arm = ob.find_armature()
        if arm:
            doc.leaf_tag('skeletonlink', {
                'name': '%s.skeleton' % ob.clonkExportSkeletonName
            })
            doc.start_tag('boneassignments', {})
            boneOutputEnableFromName = {}
            boneIndexFromName = {}
            for bone in arm.pose.bones:
                boneOutputEnableFromName[bone.name] = True
                if config.get('ONLY_DEFORMABLE_BONES'):
                    # if we found a deformable bone,
                    if bone.bone.use_deform:
                        # visit all ancestor bones and mark them "output enabled"
                        parBone = bone.parent
                        while parBone:
                            boneOutputEnableFromName[parBone.name] = True
                            parBone = parBone.parent
                    else:
                        # non-deformable bone, no output
                        boneOutputEnableFromName[bone.name] = False
            boneIndex = 0
            for bone in arm.pose.bones:
                boneIndexFromName[bone.name] = boneIndex
                if boneOutputEnableFromName[bone.name]:
                    boneIndex += 1
            badverts = 0
            for vidx, v in enumerate(_remap_verts_):
                check = 0
                for vgroup in v.groups:
                    if vgroup.weight > config.get('TRIM_BONE_WEIGHTS'):
                        groupIndex = vgroup.group
                        if groupIndex < len(copy.vertex_groups):
                            vg = copy.vertex_groups[groupIndex]
                            if vg.name in boneIndexFromName:  # allows other vertex groups, not just armature vertex groups
                                bnidx = boneIndexFromName[vg.name]  # find_bone_index(copy,arm,vgroup.group)
                                doc.leaf_tag('vertexboneassignment', {
                                    'vertexindex': str(vidx),
                                    'boneindex': str(bnidx),
                                    'weight': '%6f' % vgroup.weight
                                })
                                check += 1
                        else:
                            print('WARNING: object vertex groups not in sync with armature', copy, arm, groupIndex)
                if check > 4:
                    badverts += 1
                    print(
                        'WARNING: vertex %s is in more than 4 vertex groups (bone weights)\n(this maybe Ogre incompatible)' % vidx)
            if badverts:
                Report.warnings.append(
                    '%s has %s vertices weighted to too many bones (Ogre limits a vertex to 4 bones)\n[try increaseing the Trim-Weights threshold option]' % (
                    mesh.name, badverts))
            doc.end_tag('boneassignments')

        ## Clean up and save
        # bpy.context.scene.meshes.unlink(mesh)
        if cleanup:
            # bpy.context.scene.objects.unlink(copy)
            copy.user_clear()
            bpy.data.objects.remove(copy)
            mesh.user_clear()
            bpy.data.meshes.remove(mesh)
            del copy
            del mesh
        del _remap_verts_
        del uvcache
        doc.close()  # reported by Reyn
        f.close()

        if logging:
            print('      - Created .mesh.xml at', util.timer_diff_str(start), "seconds")

    # todo: Very ugly, find better way
    def replaceInplace(f, searchExp, replaceExp):
        import fileinput
        for line in fileinput.input(f, inplace=1):
            if searchExp in line:
                line = line.replace(searchExp, replaceExp)
            sys.stdout.write(line)
        fileinput.close()  # reported by jakob

    replaceInplace(target_file, '__TO_BE_REPLACED_VERTEX_COUNT__' + '"', str(numverts) + '"')  # + ' ' * (ls - lr))
    del (replaceInplace)

    # Start .mesh.xml to .mesh convertion tool
    util.xml_convert(target_file, has_uvs=dotextures)

    # note that exporting the skeleton does not happen here anymore
    # it moved to the function dot_skeleton in its own module

    mats = []
    for mat_name, extern, mat in materials:
        # _missing_material_ is marked as extern
        if not extern:
            mats.append(mat_name)
        else:
            print("extern material", mat_name)

    logging.info('      - Created .mesh in total time %s seconds', util.timer_diff_str(start))

    return mats



def triangle_list_in_group(mesh, shared_vertices, group_index):
    faces = []
    for face in mesh.loop_triangles:
    #for face in mesh.data.tessfaces:
        vertices = [mesh.data.vertices[v] for v in face.vertices]
        match_group = lambda g, v: g in [x.group for x in v.groups]
        all_in_group = all([match_group(group_index, v) for v in vertices])
        if not all_in_group:
            continue
        assert len(face.vertices) == 3
        entry = [shared_vertices[v][0].ogre_vidx for v in face.vertices]
        faces.append(tuple(entry))
    return faces


def append_triangle_in_vertex_group(mesh, obj, vertex_groups, ogre_indices, blender_indices):
    vertices = [mesh.vertices[i] for i in blender_indices]
    names = set()
    for v in vertices:
        for g in v.groups:
            if g.group >= len(obj.vertex_groups):
                return
            group = obj.vertex_groups.items()[g.group][1]
            if not group.name.startswith("ogre.vertex.group."):
                return
            names.add(group.name)
    match_group = lambda name, v: name in [obj.vertex_groups[x.group].name for x in v.groups]
    for name in names:
        all_in_group = all([match_group(name, v) for v in vertices])
        if not all_in_group:
            continue
        if name not in vertex_groups:
            vertex_groups[name] = []
        vertex_groups[name].append(ogre_indices)


from math import isclose


class VertexNoPos(object):
    def __init__(self, ogre_vidx, nx, ny, nz, r, g, b, ra, vert_uvs):
        self.ogre_vidx = ogre_vidx
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.r = r
        self.g = g
        self.b = b
        self.ra = ra
        self.vert_uvs = vert_uvs

    '''does not compare ogre_vidx (and position at the moment) [ no need to compare position ]'''

    def __eq__(self, o):
        if not isclose(self.nx, o.nx): return False
        if not isclose(self.ny, o.ny): return False
        if not isclose(self.nz, o.nz): return False
        if not isclose(self.r, o.r): return False
        if not isclose(self.g, o.g): return False
        if not isclose(self.b, o.b): return False
        if not isclose(self.ra, o.ra): return False
        if len(self.vert_uvs) != len(o.vert_uvs): return False
        if self.vert_uvs:
            for i, uv1 in enumerate(self.vert_uvs):
                uv2 = o.vert_uvs[i]
                if uv1 != uv2: return False
        return True

    def __repr__(self):
        return 'vertex(%d)' % self.ogre_vidx


def extract_vertex_color(vcolors, vcolors_alpha, face, index):
    r = 1.0
    g = 1.0
    b = 1.0
    ra = 1.0
    export = False
    if vcolors:
        k = list(face.vertices).index(index)
        r, g, b = getattr(vcolors.data[face.index], 'color%s' % (k + 1))
        if vcolors_alpha:
            ra, ga, ba = getattr(vcolors_alpha.data[face.index], 'color%s' % (k + 1))
        else:
            ra = 1.0
        export = True
    return export, (r, g, b, ra)


if 0:
    import os
    print("Start")
    dot_mesh(bpy.data.objects["Clonk"], os.path.dirname(bpy.data.filepath)+"/scripts/test.mesh.xml", overwrite=True)
    print("End")
