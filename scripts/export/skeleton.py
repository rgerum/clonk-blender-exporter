import bpy
import mathutils
Report = bpy.data.texts["report.py"].as_module().Report
RDocument = bpy.data.texts["xml_simple.py"].as_module().RDocument
util = bpy.data.texts["util.py"].as_module()
config = bpy.data.texts["config.py"].as_module().config
from os.path import join
import re


def dot_skeleton(obj, path, **kwargs):
    """
    create the .skeleton file for this object. This is only possible if the object
    has an armature attached.

    obj: the blender object
    path: the path where to save this to. Never None and must exist.
    kwargs:
      * force_name - string: force another name. default None
      * invoke_xml_converter - bool: invoke the xml to binary converter. default True

    returns None if there is no skeleton exported, or the filename on success
    """

    arm = obj.find_armature()
    if arm and config.get('ARM_ANIM'):
        skel = Skeleton(obj)
        name = kwargs.get('force_name') or obj.clonkExportSkeletonName
        name = util.clean_object_name(name)
        xmlfile = join(path, '%s.skeleton.xml' % name)
        with open(xmlfile, 'wb') as fd:
            fd.write(bytes(skel.to_xml(), 'utf-8'))

        if kwargs.get('invoke_xml_converter', True):
            util.xml_convert(xmlfile)
        return name + '.skeleton'

    return None


class Bone(object):

    def __init__(self, rbone, pbone, skeleton):
        #swap_axis = config.get('SWAP_AXIS')
        swap_axis = 'xz-y'
        if swap_axis == 'xyz':
            self.fixUpAxis = False
        else:
            self.fixUpAxis = True
            if swap_axis == '-xzy':  # Tundra 1.x
                self.flipMat = mathutils.Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
            elif swap_axis == 'xz-y':  # Tundra 2.x current generation
                # self.flipMat = mathutils.Matrix(((1,0,0,0),(0,0,1,0),(0,1,0,0),(0,0,0,1)))
                self.flipMat = mathutils.Matrix(
                    ((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))  # thanks to Waruck
            else:
                print('ERROR - TODO: axis swap mode not supported with armature animation')
                assert 0

        self.skeleton = skeleton
        self.name = pbone.name
        self.matrix = rbone.matrix_local.copy()  # armature space
        # self.matrix_local = rbone.matrix.copy() # space?

        self.bone = pbone  # safe to hold pointer to pose bone, not edit bone!
        self.shouldOutput = True
        if config.get('ONLY_DEFORMABLE_BONES') and not pbone.bone.use_deform:
            self.shouldOutput = False

        # todo: Test -> #if pbone.bone.use_inherit_scale: print('warning: bone <%s> is using inherit scaling, Ogre has no support for this' %self.name)
        self.parent = pbone.parent
        self.children = []

    def update(self):  # called on frame update
        pbone = self.bone
        pose = pbone.matrix.copy()
        self._inverse_total_trans_pose = pose.inverted()
        # calculate difference to parent bone
        if self.parent:
            pose = self.parent._inverse_total_trans_pose @ pose
        elif self.fixUpAxis:
            pose = self.flipMat @ pose
        else:
            pass

        self.pose_location = pose.to_translation() - self.ogre_rest_matrix.to_translation()
        pose = self.inverse_ogre_rest_matrix @ pose
        self.pose_rotation = pose.to_quaternion()

        # self.pose_location = pbone.location.copy()
        # self.pose_scale = pbone.scale.copy()
        # if pbone.rotation_mode == 'QUATERNION':
        #    self.pose_rotation = pbone.rotation_quaternion.copy()
        # else:
        #    self.pose_rotation = pbone.rotation_euler.to_quaternion()

        if config.get('OGRE_INHERIT_SCALE'):
            # special case workaround for broken Ogre nonuniform scaling:
            # Ogre can't deal with arbitrary nonuniform scaling, but it can handle certain special cases
            # The special case we are trying to handle here is when a bone has a nonuniform scale and it's
            # child bones are not inheriting the scale.  We should be able to do this without having to
            # do any extra setup in Ogre (like turning off "inherit scale" on the Ogre bones)
            # if Ogre is inheriting scale, we just output the scale relative to the parent
            self.pose_scale = pose.to_scale()
            self.ogreDerivedScale = self.pose_scale.copy()
            if self.parent:
                # this is how Ogre handles inheritance of scale
                self.ogreDerivedScale[0] *= self.parent.ogreDerivedScale[0]
                self.ogreDerivedScale[1] *= self.parent.ogreDerivedScale[1]
                self.ogreDerivedScale[2] *= self.parent.ogreDerivedScale[2]
                # if we don't want inherited scale,
                if not self.bone.bone.use_inherit_scale:
                    # cancel out the scale that Ogre will calculate
                    scl = self.parent.ogreDerivedScale
                    self.pose_scale = mathutils.Vector((1.0 / scl[0], 1.0 / scl[1], 1.0 / scl[2]))
                    self.ogreDerivedScale = mathutils.Vector((1.0, 1.0, 1.0))
        else:
            # if Ogre is not inheriting the scale,
            # just output the scale directly
            self.pose_scale = pbone.scale.copy()
            # however, if Blender is inheriting the scale,
            if self.parent and self.bone.bone.use_inherit_scale:
                # apply parent's scale (only works for uniform scaling)
                self.pose_scale[0] *= self.parent.pose_scale[0]
                self.pose_scale[1] *= self.parent.pose_scale[1]
                self.pose_scale[2] *= self.parent.pose_scale[2]

        for child in self.children:
            child.update()

    def clear_pose_transform(self):
        self.bone.location.zero()
        self.bone.scale.Fill(3, 1.0)
        self.bone.rotation_quaternion.identity()
        self.bone.rotation_euler.zero()
        # self.bone.rotation_axis_angle  #ignore axis angle mode

    def save_pose_transform(self):
        self.savedPoseLocation = self.bone.location.copy()
        self.savedPoseScale = self.bone.scale.copy()
        self.savedPoseRotationQ = self.bone.rotation_quaternion
        self.savedPoseRotationE = self.bone.rotation_euler
        # self.bone.rotation_axis_angle  #ignore axis angle mode

    def restore_pose_transform(self):
        self.bone.location = self.savedPoseLocation
        self.bone.scale = self.savedPoseScale
        self.bone.rotation_quaternion = self.savedPoseRotationQ
        self.bone.rotation_euler = self.savedPoseRotationE
        # self.bone.rotation_axis_angle  #ignore axis angle mode

    def rebuild_tree(self):  # called first on all bones
        if self.parent:
            self.parent = self.skeleton.get_bone(self.parent.name)
            self.parent.children.append(self)
            if self.shouldOutput and not self.parent.shouldOutput:
                # mark all ancestor bones as shouldOutput
                parent = self.parent
                while parent:
                    parent.shouldOutput = True
                    parent = parent.parent

    def compute_rest(self):  # called after rebuild_tree, recursive roots to leaves
        if self.parent:
            inverseParentMatrix = self.parent.inverse_total_trans
        elif self.fixUpAxis:
            inverseParentMatrix = self.flipMat
        else:
            inverseParentMatrix = mathutils.Matrix(((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))

        # self.ogre_rest_matrix = self.skeleton.object_space_transformation * self.matrix    # ALLOW ROTATION?
        self.ogre_rest_matrix = self.matrix.copy()
        # store total inverse transformation
        self.inverse_total_trans = self.ogre_rest_matrix.inverted()
        # relative to OGRE parent bone origin
        self.ogre_rest_matrix = inverseParentMatrix @ self.ogre_rest_matrix
        self.inverse_ogre_rest_matrix = self.ogre_rest_matrix.inverted()

        # recursion
        for child in self.children:
            child.compute_rest()


class Keyframe:
    def __init__(self, time, pos, rot, scale):
        self.time = time
        self.pos = pos.copy()
        self.rot = rot.copy()
        self.scale = scale.copy()

    def isTransIdentity(self):
        return self.pos.length < 0.0001

    def isRotIdentity(self):
        # if the angle is very close to zero
        if abs(self.rot.angle) < 0.0001:
            # treat it as a zero rotation
            return True
        return False

    def isScaleIdentity(self):
        scaleDiff = mathutils.Vector((1, 1, 1)) - self.scale
        return scaleDiff.length < 0.0001


# Bone_Track
# Encapsulates all of the key information for an individual bone within a single animation,
# and srores that information as XML.
class Bone_Track:
    def __init__(self, bone):
        self.bone = bone
        self.keyframes = []

    def is_pos_animated(self):
        # take note if any keyframe is anything other than the IDENTITY transform
        for kf in self.keyframes:
            if not kf.isTransIdentity():
                return True
        return False

    def is_rot_animated(self):
        # take note if any keyframe is anything other than the IDENTITY transform
        for kf in self.keyframes:
            if not kf.isRotIdentity():
                return True
        return False

    def is_scale_animated(self):
        # take note if any keyframe is anything other than the IDENTITY transform
        for kf in self.keyframes:
            if not kf.isScaleIdentity():
                return True
        return False

    def add_keyframe(self, time):
        bone = self.bone
        kf = Keyframe(time, bone.pose_location, bone.pose_rotation, bone.pose_scale)
        self.keyframes.append(kf)

    def write_track(self, doc, tracks_element):
        isPosAnimated = self.is_pos_animated()
        isRotAnimated = self.is_rot_animated()
        isScaleAnimated = self.is_scale_animated()
        if not isPosAnimated and not isRotAnimated and not isScaleAnimated:
            return
        track = doc.createElement('track')
        track.setAttribute('bone', self.bone.name)
        keyframes_element = doc.createElement('keyframes')
        track.appendChild(keyframes_element)
        for kf in self.keyframes:
            keyframe = doc.createElement('keyframe')
            keyframe.setAttribute('time', '%6f' % kf.time)
            if isPosAnimated:
                trans = doc.createElement('translate')
                keyframe.appendChild(trans)
                trans.setAttribute('x', '%6f' % kf.pos.x)
                trans.setAttribute('y', '%6f' % kf.pos.y)
                trans.setAttribute('z', '%6f' % kf.pos.z)

            if isRotAnimated:
                rotElement = doc.createElement('rotate')
                keyframe.appendChild(rotElement)
                angle = kf.rot.angle
                axis = kf.rot.axis
                # if angle is near zero or axis is not unit magnitude,
                if kf.isRotIdentity():
                    angle = 0.0  # avoid outputs like "-0.00000"
                    axis = mathutils.Vector((0, 0, 0))
                rotElement.setAttribute('angle', '%6f' % angle)
                axisElement = doc.createElement('axis')
                rotElement.appendChild(axisElement)
                axisElement.setAttribute('x', '%6f' % axis[0])
                axisElement.setAttribute('y', '%6f' % axis[1])
                axisElement.setAttribute('z', '%6f' % axis[2])

            if isScaleAnimated:
                scale = doc.createElement('scale')
                keyframe.appendChild(scale)
                x, y, z = kf.scale
                scale.setAttribute('x', '%6f' % x)
                scale.setAttribute('y', '%6f' % y)
                scale.setAttribute('z', '%6f' % z)
            keyframes_element.appendChild(keyframe)
        tracks_element.appendChild(track)


# Skeleton
def findArmature(ob):
    arm = ob.find_armature()
    # if this armature has no animation,
    if not arm.animation_data:
        # search for another armature that is a proxy for it
        for ob2 in bpy.data.objects:
            if ob2.type == 'ARMATURE' and ob2.proxy == arm:
                print("proxy armature %s found" % ob2.name)
                return ob2
    return arm


class Skeleton(object):
    def get_bone(self, name):
        for b in self.bones:
            if b.name == name:
                return b
        return None

    def __init__(self, ob):
        if ob.location.x != 0 or ob.location.y != 0 or ob.location.z != 0:
            Report.warnings.append('ERROR: Mesh (%s): is offset from Armature - zero transform is required' % ob.name)
        if ob.scale.x != 1 or ob.scale.y != 1 or ob.scale.z != 1:
            Report.warnings.append('ERROR: Mesh (%s): has been scaled - scale(1,1,1) is required' % ob.name)

        self.object = ob
        self.bones = []
        mats = {}
        self.arm = arm = findArmature(ob)
        print(arm)
        #arm.hide = False
        #self._restore_layers = list(arm.layers)
        # arm.layers = [True]*20      # can not have anything hidden - REQUIRED?

        # add all the bones for the skeleton
        for pbone in arm.pose.bones:
            mybone = Bone(arm.data.bones[pbone.name], pbone, self)
            self.bones.append(mybone)

        if arm.name not in Report.armatures:
            Report.armatures.append(arm.name)

        ## bad idea - allowing rotation of armature, means vertices must also be rotated,
        ## also a bug with applying the rotation, the Z rotation is lost
        # x,y,z = arm.matrix_local.copy().inverted().to_euler()
        # e = mathutils.Euler( (x,z,y) )
        # self.object_space_transformation = e.to_matrix().to_4x4()
        x, y, z = arm.matrix_local.to_euler()
        if x != 0 or y != 0 or z != 0:
            Report.warnings.append('ERROR: Armature: %s is rotated - (rotation is ignored)' % arm.name)

        ## setup bones for Ogre format ##
        for b in self.bones:
            b.rebuild_tree()
        ## walk bones, convert them ##
        self.roots = []
        ep = 0.0001
        for b in self.bones:
            if not b.parent:
                b.compute_rest()
                loc, rot, scl = b.ogre_rest_matrix.decompose()
                # if loc.x or loc.y or loc.z:
                #    Report.warnings.append('ERROR: root bone has non-zero transform (location offset)')
                # if rot.w > ep or rot.x > ep or rot.y > ep or rot.z < 1.0-ep:
                #    Report.warnings.append('ERROR: root bone has non-zero transform (rotation offset)')
                self.roots.append(b)

    def write_animation(self, arm, actionName, frameBegin, frameEnd, doc, parentElement):
        _fps = float(bpy.context.scene.render.fps)
        # boneNames = sorted( [bone.name for bone in arm.pose.bones] )
        bone_tracks = []
        for bone in self.bones:
            # bone = self.get_bone(boneName)
            if bone.shouldOutput:
                bone_tracks.append(Bone_Track(bone))
            bone.clear_pose_transform()  # clear out any leftover pose transforms in case this bone isn't keyframed
        for frame in range(int(frameBegin), int(frameEnd) + 1, bpy.context.scene.frame_step):  # thanks to Vesa
            bpy.context.scene.frame_set(frame)
            for bone in self.roots:
                bone.update()
            for track in bone_tracks:
                track.add_keyframe((frame - frameBegin) / _fps)
        # check to see if any animation tracks would be output
        animationFound = False
        for track in bone_tracks:
            if track.is_pos_animated() or track.is_rot_animated() or track.is_scale_animated():
                animationFound = True
                break
        if not animationFound:
            return
        anim = doc.createElement('animation')
        parentElement.appendChild(anim)
        tracks = doc.createElement('tracks')
        anim.appendChild(tracks)
        Report.armature_animations.append(
            '%s : %s [start frame=%s  end frame=%s]' % (arm.name, actionName, frameBegin, frameEnd))

        anim.setAttribute('name', actionName)  # USE the action name
        anim.setAttribute('length', '%6f' % ((frameEnd - frameBegin) / _fps))

        for track in bone_tracks:
            # will only write a track if there is some kind of animation there
            track.write_track(doc, tracks)

    def to_xml(self):
        # start xml file
        doc = RDocument()

        # add skeleton root tag
        root = doc.createElement('skeleton')
        doc.appendChild(root)

        # add a bones tag
        bones = doc.createElement('bones')
        root.appendChild(bones)

        # add a bone hierarchy tag
        bh = doc.createElement('bonehierarchy')
        root.appendChild(bh)

        # iterate over all bones
        boneId = 0
        for bone in self.bones:
            # ignore bones that should not be exported
            if not bone.shouldOutput:
                continue

            # create a bone tag
            b = doc.createElement('bone')
            b.setAttribute('name', bone.name)
            b.setAttribute('id', str(boneId))
            # add it to the bones tag
            bones.appendChild(b)

            # increase the bone index
            boneId = boneId + 1

            # if the bone has a parent, add this relation to the bonehierarchy tag
            if bone.parent:
                bp = doc.createElement('boneparent')
                bp.setAttribute('bone', bone.name)
                bp.setAttribute('parent', bone.parent.name)
                bh.appendChild(bp)

            # get the rest matrix
            mat = bone.ogre_rest_matrix.copy()

            # the position tag (subtag of bone)
            pos = doc.createElement('position')
            b.appendChild(pos)
            # add the translation
            x, y, z = mat.to_translation()
            if bone.parent:
                y, z = z, -y
            pos.setAttribute('x', '%6f' % x)
            pos.setAttribute('y', '%6f' % y)
            pos.setAttribute('z', '%6f' % z)

            # the rotation tag (subtag of bone)
            rot = doc.createElement('rotation')  # "rotation", not "rotate"
            b.appendChild(rot)
            # add the rotation
            q = mat.to_quaternion()
            angle = q.angle
            x, y, z = q.axis
            if bone.parent:
                y, z = z, -y
            else:
                angle = angle+3.14159265359/2
            rot.setAttribute('angle', '%6f' % angle)

            # the axis tag (subtag of rotation)
            axis = doc.createElement('axis')
            rot.appendChild(axis)
            axis.setAttribute('x', '%6f' % x)
            axis.setAttribute('y', '%6f' % y)
            axis.setAttribute('z', '%6f' % z)

            # Ogre bones do not have initial scaling

        arm = self.arm
        # remember some things so we can put them back later
        savedFrame = bpy.context.scene.frame_current
        # save the current pose
        for b in self.bones:
            b.save_pose_transform()

        # the animations tag (subtag of skeleton)
        anims = doc.createElement('animations')
        root.appendChild(anims)

        # Look for an "Actions.txt" in the directory of the current file
        animationList, animation_export_groups = self.getActionsTxt()
        
        if animationList is not None:  # assume all is controled by a handmade Actions.txt
            _fps = float(bpy.context.scene.render.fps)

            # Test if we have a second control armature
            if "CONTROL_body" in bpy.data.objects:
                arm2 = bpy.data.objects["CONTROL_body"]
            else:
                arm2 = arm
                
            try:
                arm_previous_action = arm.animation_data.action
                arm2_previous_action = arm2.animation_data.action
            except AttributeError:
                arm_previous_action = None
                arm2_previous_action = None

            # Export all animations
            for animation in animationList:
                # Test if animation exists
                print('ActMap track:', animation)
                if not animation["Name"] in bpy.data.actions:
                    print("ERROR: Action %s not found!" % animation["Name"])
                    continue

                # Get action
                action = bpy.data.actions[animation["Name"]]

                # Add animation to doc
                anim = doc.createElement('animation')
                anims.appendChild(anim)
                tracks = doc.createElement('tracks')
                anim.appendChild(tracks)

                # start with the start frame
                start = animation["Start"]
                if start == -1:  # if no start value is given use 0
                    start = int(max(action.frame_range[0], 1))

                # find the end frame
                end = animation["End"]
                if end == -1:  # if no end value is given use the range
                    end = int(action.frame_range[1])

                # add it to the report
                Report.armature_animations.append(
                    '%s : %s [start frame=%s  end frame=%s]' % (arm.name, animation["Name"], start, end))

                # Select name
                if animation["ExportName"]:
                    anim.setAttribute('name', animation["ExportName"])
                else:
                    anim.setAttribute('name', animation["Name"])
                anim.setAttribute('length', str((end - start) / _fps))

                # Find the export group if there is one
                group = 0
                for gr in animation_export_groups:
                    if gr["Name"] == animation["Group"]:
                        group = gr
                        print(group)
                        break

                # Select only bones which belong to the group
                if group:
                    # Include
                    if len(group["Include"]):
                        stripbones = []
                        for bone in arm.pose.bones:
                            for include in group["Include"]:
                                if re.match(include.replace("*", ".*"), bone.name):
                                    stripbones.append(bone.name)
                                    # Exclude
                    else:
                        #print("exlcudes")
                        stripbones = []
                        for bone in arm.pose.bones:
                            doexclude = 0
                            for exclude in group["Exclude"]:
                                if re.match(exclude.replace("*", ".*"), bone.name):
                                    doexclude = 1
                            #print("bone", bone, doexclude)
                            if doexclude == 0:
                                stripbones.append(bone.name)
                # When no group is there use all bones
                else:
                    stripbones = [bone.name for bone in arm.pose.bones]

                _keyframes = {}
                for bonename in stripbones:
                    if self.get_bone(bonename):  # check if the bone was exported
                        track = doc.createElement('track')
                        track.setAttribute('bone', bonename)
                        tracks.appendChild(track)
                        keyframes = doc.createElement('keyframes')
                        track.appendChild(keyframes)
                        _keyframes[bonename] = keyframes

                # Evaluate Reset animation if there is one
                if "RESET" in bpy.data.actions:
                    arm.animation_data.action = bpy.data.actions["RESET"]
                    arm2.animation_data.action = bpy.data.actions["RESET"]
                # Set current animation
                arm.animation_data.action = action
                arm2.animation_data.action = action
                # Process all frames
                for frame in range(int(start), int(end) + 1, bpy.context.scene.frame_step):
                    # Set the frame
                    bpy.context.scene.frame_set(frame)
                    bpy.context.scene.frame_set(frame)
                    # Update bones
                    for bone in self.roots: bone.update()
                    # Save bone transformations
                    for bonename in stripbones:
                        if self.get_bone(bonename):  # check if the bone was exported
                            bone = self.get_bone(bonename)
                            _loc = bone.pose_location
                            _rot = bone.pose_rotation
                            _scl = bone.pose_scale

                            keyframe = doc.createElement('keyframe')
                            keyframe.setAttribute('time', str((frame - start) / _fps))
                            _keyframes[bonename].appendChild(keyframe)
                            trans = doc.createElement('translate')
                            keyframe.appendChild(trans)
                            x, y, z = _loc
                            if bone.parent:
                                y, z = z, -y
                            trans.setAttribute('x', '%6f' % x)
                            trans.setAttribute('y', '%6f' % y)
                            trans.setAttribute('z', '%6f' % z)

                            rot = doc.createElement('rotate')
                            keyframe.appendChild(rot)
                            q = _rot
                            x, y, z = q.axis
                            angle = q.angle
                            if bone.parent:
                                y, z = z, -y
                            else:
                                y, z = z, -y
                                #angle = -angle# + 3.14159265359 / 2
                            rot.setAttribute('angle', '%6f' % angle)
                            axis = doc.createElement('axis')
                            rot.appendChild(axis)
                            axis.setAttribute('x', '%6f' % x)
                            axis.setAttribute('y', '%6f' % y)
                            axis.setAttribute('z', '%6f' % z)

                            scale = doc.createElement('scale')
                            keyframe.appendChild(scale)
                            x, y, z = _scl
                            scale.setAttribute('x', '%6f' % x)
                            scale.setAttribute('y', '%6f' % y)
                            scale.setAttribute('z', '%6f' % z)
                # Evaluate Reset animation if there is one
                if "RESET" in bpy.data.actions:
                    arm.animation_data.action = bpy.data.actions["RESET"]
                    arm2.animation_data.action = bpy.data.actions["RESET"]
                    # Set the frame
                    bpy.context.scene.frame_set(frame)
                    bpy.context.scene.frame_set(frame)
            
            if arm_previous_action is not None:
                arm.animation_data.action = arm_previous_action
                arm2.animation_data.action = arm2_previous_action

        elif not arm.animation_data or (arm.animation_data and not arm.animation_data.nla_tracks):
                # write a single animation from the blender timeline
                self.write_animation(arm, 'my_animation', bpy.context.scene.frame_start, bpy.context.scene.frame_end, doc,
                                     anims)

        elif arm.animation_data:
            savedUseNla = arm.animation_data.use_nla
            savedAction = arm.animation_data.action
            arm.animation_data.use_nla = False
            if not len(arm.animation_data.nla_tracks):
                Report.warnings.append(
                    'you must assign an NLA strip to armature (%s) that defines the start and end frames' % arm.name)

            actions = {}  # actions by name
            # the only thing NLA is used for is to gather the names of the actions
            # it doesn't matter if the actions are all in the same NLA track or in different tracks
            for nla in arm.animation_data.nla_tracks:  # NLA required, lone actions not supported
                print('NLA track:', nla.name)

                for strip in nla.strips:
                    action = strip.action
                    actions[action.name] = action
                    print('   strip name:', strip.name)
                    print('   action name:', action.name)

            actionNames = sorted(actions.keys())  # output actions in alphabetical order
            for actionName in actionNames:
                action = actions[actionName]
                arm.animation_data.action = action  # set as the current action
                suppressedBones = []
                if config.get('ONLY_KEYFRAMED_BONES'):
                    keyframedBones = {}
                    for group in action.groups:
                        keyframedBones[group.name] = True
                    for b in self.bones:
                        if (not b.name in keyframedBones) and b.shouldOutput:
                            # suppress this bone's output
                            b.shouldOutput = False
                            suppressedBones.append(b.name)
                self.write_animation(arm, actionName, action.frame_range[0], action.frame_range[1], doc, anims)
                # restore suppressed bones
                for boneName in suppressedBones:
                    bone = self.get_bone(boneName)
                    bone.shouldOutput = True
            # restore these to what they originally were
            arm.animation_data.action = savedAction
            arm.animation_data.use_nla = savedUseNla

        # restore
        bpy.context.scene.frame_set(savedFrame)
        # restore the current pose
        for b in self.bones:
            b.restore_pose_transform()

        return doc.toprettyxml()

    def getActionsTxt(self):
        import os
        # Look for an "Actions.txt" in the directory of the current file
        act_filename = self.object.clonkExportActionFile
        if act_filename == "":
            animationList = []
            animation_export_groups = []
            for name, action in bpy.data.actions.items():
                if action.clonkActionDoExport:
                    animationList.append({
                        "Name": name, 
                        "ExportName": action.clonkActionExportName,
                        "Start": action.clonkActionStart,
                        "End": action.clonkActionEnd,
                        "Group": ""
                    })
            return animationList, animation_export_groups
        file_exists = os.path.isfile(act_filename)
        if not file_exists:  # assume all is controlled by a handmade Actions.txt
            return None, None

        animationList = []
        animation_export_groups = []

        # Open Actions.txt file
        actlist = open(act_filename, "r");
        Action_Keys = {"Name": str, "ExportName": str, "Start": int, "End": int, "Group": str}
        Group_Keys = {"Name": str, "Exclude": str, "Include": str}
        mode = 0
        # Read file
        for line in actlist:
            # Strip lines and ignore comments or blank lines
            line = line.strip()
            if len(line) == 0 or line[0] == "#":
                continue
            # Read in line in Action block
            if mode == "Action":
                pair = line.split("=")
                if len(pair) == 2 and pair[0] in Action_Keys:
                    animationList[-1][pair[0]] = Action_Keys[pair[0]](pair[1])
                    continue
                if line[0] != "[":
                    print("ERROR: unreadable line " + line)
                    continue
            # Read in line in Group block
            if mode == "Group":
                pair = line.split("=")
                if len(pair) == 2 and pair[0] in Group_Keys:
                    if pair[0] == "Exclude":
                        animation_export_groups[-1]["Exclude"].append(pair[1])
                    elif pair[0] == "Include":
                        animation_export_groups[-1]["Include"].append(pair[1])
                    else:
                        animation_export_groups[-1][pair[0]] = Group_Keys[pair[0]](pair[1])
                    continue
                if line[0] != "[":
                    print("ERROR: unreadable line " + line)
                    continue

            # Test if we have to start a new block
            if line == "[Action]":
                mode = "Action"
                animationList.append({"Name": "", "ExportName": "", "Start": -1, "End": -1, "Group": ""})

            if line == "[Group]":
                mode = "Group"
                animation_export_groups.append({"Name": "", "Exclude": [], "Include": []})

        # Finished with reading the file
        actlist.close()

        return animationList, animation_export_groups

if 0:    
    import os
    print("Start")
    dot_skeleton(bpy.data.objects["Clonk"], os.path.dirname(bpy.data.filepath)+"/scripts/test.mesh.xml", overwrite=True)
    print("End")