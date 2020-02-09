#----------------------------------------------------------
# File panel_props.py
#----------------------------------------------------------
import bpy
import mathutils
import math
import json
import os
from pathlib import Path
from report import Report
import importlib

def Trans_Identity():
    return mathutils.Matrix()
    
def Trans_Translate(x, y, z):
    return mathutils.Matrix.Translation((x, y, z))
    
def Trans_Rotate(angle, x, y, z):
    return mathutils.Matrix.Rotation(angle*math.pi/180, 4, (x, y, z))
    
def Trans_Scale(x, y=None, z=None):
    if y is None:
        y = x
    if z is None:
        z = x
    return mathutils.Matrix.Scale(x, 4, (1, 0, 0))*mathutils.Matrix.Scale(y, 4, (0, 1, 0))*mathutils.Matrix.Scale(z, 4, (0, 0, 1))

def Trans_Mul(a, b):
    return a*b

def applyTransformation(ob, trans):
    if trans is None:
        trans = Trans_Identity()
    else:
        trans = eval(trans)
        trans = trans*mathutils.Matrix(((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
    print("trans", ob)
    print(trans)
    ob.location = trans.to_translation()
    ob.rotation_quaternion = trans.to_quaternion()
    ob.rotation_mode = "QUATERNION"
    ob.scale = trans.to_scale()
    print(ob.location)
    print(ob.rotation_quaternion)
 
# Define an RNA prop for every object
bpy.types.Object.clonkExportActionFile = bpy.props.StringProperty(
    name="Action.txt",
    default="",
    subtype='FILE_PATH')

bpy.types.Object.clonkExportName = bpy.props.StringProperty(
    name="Export Mesh Name",
    description="The name to be used when exporting the object, e.g. Graphics.mesh",
    default="Graphics")
    
bpy.types.Object.clonkExportSkeletonName = bpy.props.StringProperty(
    name="Export Skeleton Name",
    description="The name to be used when exporting the object, e.g. Clonk.skeleton",
    default="Clonk")

bpy.types.Action.clonkActionDoExport = bpy.props.BoolProperty(
    name="Export",
    description="Whether to export this action.",
    default=True)
bpy.types.Action.clonkActionExportName = bpy.props.StringProperty(
    name="Export Name",
    description="When set export under a different name.",
    default="")
bpy.types.Action.clonkActionStart = bpy.props.IntProperty(
    name="Start",
    min=-1,
    description="Define the frame number where to start the action. When -1 select automatically.",
    default=-1)
bpy.types.Action.clonkActionEnd = bpy.props.IntProperty(
    name="End",
    min=-1,
    description="Define the frame number where to end the action. When -1 select automatically.",
    default=-1)
    
bpy.types.Action.clonkAttachMesh = bpy.props.StringProperty(
    name="Attach Mesh",
    description="The name of an object which should be attached to the Clonk during this action.",
    default="")
bpy.types.Action.clonkAttachBone = bpy.props.StringProperty(
    name="Parent Bone",
    description="Which bone of the Clonk to use.",
    default="")
bpy.types.Action.clonkAttachBone2 = bpy.props.StringProperty(
    name="Child Bone",
    description="Which bone of the tool to use.",
    default="")
bpy.types.Action.clonkAttachTransformation = bpy.props.StringProperty(
    name="Transformation",
    description="Optinal a transformation to apply when attaching the mesh.",
    default="")
bpy.types.Action.clonkAttachAction = bpy.props.StringProperty(
    name="Action",
    description="Optinal an action to select in the child mesh.",
    default="")
 
#   Button
class OBJECT_OT_Button(bpy.types.Operator):
    bl_idname = "clonk.export_mesh"
    bl_label = "Export Mesh"
 
    def execute(self, context):
        ob = context.object
        if ob.type == "ARMATURE":
            if len(ob.children):
               ob = ob.children[0]
               
        import mesh
        importlib.reload(mesh)
        target_folder = Path(bpy.data.filepath).parent / "export"
        materials = mesh.dot_mesh(ob, target_folder, overwrite=True)
        
        import material
        importlib.reload(material)
        material.writeMaterials(target_folder / "Scene.material", materials)
        Report.show()
        return{'FINISHED'}
    
class OBJECT_OT_Button2(bpy.types.Operator):
    bl_idname = "clonk.export_skeleton_all"
    bl_label = "Export Skeleton"
 
    def execute(self, context):
        ob = context.object
        if ob.type == "ARMATURE":
            if len(ob.children):
               ob = ob.children[0]
               
        import skeleton
        from report import Report
        import importlib
        importlib.reload(skeleton)
        skeleton.dot_skeleton(ob, os.path.dirname(bpy.data.filepath)+"/export", overwrite=True)
        Report.show()
        return{'FINISHED'}
 
#    Property panel
class ActionPanel(bpy.types.Panel):
    bl_label = "Action Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        ob = bpy.context.object
        if not ob:
            return

        try:
            action = ob.animation_data.action
        except AttributeError:
            action = None
        if action is not None:
            return True
 
    def draw(self, context):
        ob = bpy.context.object
        if not ob:
            return
        layout = self.layout

        try:
            action = ob.animation_data.action
        except AttributeError:
            action = None
        if action is not None:
            self.layout.label(text="Name: "+ob.animation_data.action.name)
            layout.prop(ob.animation_data.action, 'clonkActionDoExport')
            layout.prop(ob.animation_data.action, 'clonkActionExportName')
            layout.prop(ob.animation_data.action, 'clonkActionStart')
            layout.prop(ob.animation_data.action, 'clonkActionEnd')
            
class ClonkActionPanel(bpy.types.Panel):
    bl_label = "Action Attach Display"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        ob = bpy.context.object
        if not ob:
            return

        try:
            action = ob.animation_data.action
        except AttributeError:
            action = None
        if action is not None:
            return True
 
    def draw(self, context):
        ob = bpy.context.object
        if not ob:
            return
        layout = self.layout

        try:
            action = ob.animation_data.action
        except AttributeError:
            action = None
        if action is not None:
            layout.prop(ob.animation_data.action, 'clonkAttachMesh')
            layout.prop(ob.animation_data.action, 'clonkAttachBone')
            layout.prop(ob.animation_data.action, 'clonkAttachBone2')
            layout.prop(ob.animation_data.action, 'clonkAttachTransformation')
            layout.prop(ob.animation_data.action, 'clonkAttachAction')
            
class ExportPanel(bpy.types.Panel):
    bl_label = "Clonk Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        if context.object is None:
            return
        if context.object.type == "MESH":
            return True
        if context.object.type == "ARMATURE":
           if len(context.object.children):
               obj = context.object.children[0]
               if obj.type == "MESH":
                   return True
 
    def draw(self, context):
        ob = bpy.context.object
        if not ob:
            return
        layout = self.layout
        if ob.type == "ARMATURE":
            if len(ob.children):
               ob = ob.children[0]
        if ob.type == 'MESH':
            layout.prop(ob, 'clonkExportActionFile')
            layout.prop(ob, 'clonkExportName')
            layout.prop(ob, 'clonkExportSkeletonName')
            layout.operator("clonk.export_mesh")
            layout.operator("clonk.export_skeleton_all")
                

def getBoneFromObject(object_name, bone_name):
    # get the object given by object_name
    attachMesh = bpy.data.objects.get(object_name)
    
    # get the armature of this object
    if attachMesh:
        attachArmature = attachMesh.parent
    else:
        attachArmature = None
        
    # get the bone given by bone_name
    if attachArmature:
        attachBone = attachArmature.pose.bones.get(bone_name)
    else:
        attachBone = None
    return attachMesh, attachArmature, attachBone
    
# Registration
bpy.utils.register_class(OBJECT_OT_Button)
bpy.utils.register_class(OBJECT_OT_Button2)
bpy.utils.register_class(ActionPanel)
bpy.utils.register_class(ClonkActionPanel)
bpy.utils.register_class(ExportPanel)

# initalize the attachHash if it is not present yet
scene = bpy.context.scene
try:
    scene["attachHash"]
except KeyError:
    scene["attachHash"] = None

# get the Armatures
try:
    clonkArmature = bpy.data.objects["Armature"]
    clonkArmatureHelper = bpy.data.objects["CONTROL_body"]
except KeyError:
    clonkArmature = None
    clonkArmatureHelper = None

def my_handler(scene):
    # get the currently selected object
    ob = bpy.context.object

    # test if the Armature and the CONTROL_body have the same action
    try:
        equal = (clonkArmature.animation_data.action == clonkArmatureHelper.animation_data.action)
    except AttributeError:
        equal = False
    
    # if they are not equal, make them equal!
    if not equal:
        # if the user has selected the Armature object, copy from this
        if ob == clonkArmature:
            print("Copy animation from Armature to helper")
            clonkArmatureHelper.animation_data.action = clonkArmature.animation_data.action
        # if not, copy the other way around
        else:
            print("Copy animation form Helper to Armature")
            clonkArmature.animation_data.action = clonkArmatureHelper.animation_data.action
    
    # try to get the current action of the Clonk's Armature
    try:
        # get the action
        action = clonkArmature.animation_data.action
        # and create a hash from the metadata
        hash = json.dumps([action.name, action.clonkAttachMesh, action.clonkAttachBone, action.clonkAttachBone2, action.clonkAttachTransformation, action.clonkAttachAction])
    except AttributeError:
        # if not set both to None
        action = None
        hash = None
    
    # if the hash has changed, we have to update the attached mesh
    if scene["attachHash"] != hash:
        
        # if there is an old mesh, we have to remove it
        if scene["attachHash"]:
            # get the metadata
            action_name, object_name, source_bone, target_bone, transformation, attach_action = json.loads(scene["attachHash"])
            # get the associated objects
            attachMesh, attachArmature, attachBone = getBoneFromObject(object_name, target_bone)
            
            # if the bone has been found
            if attachBone is not None:
                # get the constraint list
                constraintList = attachBone.constraints
                # and remove the constraint
                if len(constraintList):
                    constraintList.remove(constraintList[-1])
            # if the mesh has been found
            if attachMesh:
                # hide it in the layer 10
                #attachMesh.layers[10] = False
                attachMesh.hide_set(True)
                # and reset the transformation
                applyTransformation(attachMesh, None)
            
            # clear the hash
            scene["attachHash"] = None
            
        # get the new metadata
        action_name, object_name, source_bone, target_bone, transformation, attach_action = json.loads(hash)
        
        # set the hash
        scene["attachHash"] = hash
        
        # if an object name is given
        if object_name:
            # try to get the object
            attachMesh, attachArmature, attachBone = getBoneFromObject(object_name, target_bone)
        
            # print error messages if something has not been found
            if attachMesh is None:
                print("ERROR: mesh %s not found" % object_name)
            elif attachArmature is None:
                print("ERROR: no armature found for mesh %s" % object_name)
            elif attachBone is None:
                print("ERROR: bone %s not found in armature %s(%s)" % (target_bone, attachArmature.name, object_name))
                
            # if all has been found, proceed
            if attachMesh and attachArmature and attachBone:
                print(attachMesh, attachMesh.hide_viewport)
                # show the mesh in layer 10
                #attachMesh.layers[10] = True
                attachMesh.hide_set(False)
                
                # if an action is given, 
                if attach_action:
                    # try to get it
                    attach_action = bpy.data.actions.get(attach_action)
                # and apply it
                if attach_action:
                    attachArmature.animation_data.action = attach_action
                # or reset the action
                else:
                    try:
                        attachArmature.animation_data.action = None
                    except AttributeError:
                        pass

                # if a transformation is given            
                if action.clonkAttachTransformation:
                    # try to apply it
                    try:
                        applyTransformation(attachMesh, action.clonkAttachTransformation)
                    except Exception as err:
                        # if not, print an error message
                        print("ERROR: transform is not valid:", action.clonkAttachTransformation)
                        print(err)
                        # and reset the transformation
                        applyTransformation(attachMesh, None)
                else:
                    # the default is also a reseted transformation
                    applyTransformation(attachMesh, None)
                
                # get the constraint list of the bone
                constraintList = attachBone.constraints
                
                # and add a copy transfroms constraint with the target bone from the Clonk's Armature
                constraint = constraintList.new(type='COPY_TRANSFORMS')
                constraint.target = clonkArmature
                constraint.subtarget = action.clonkAttachBone

if scene["attachHash"] is not None:
    scene["attachHash"] = scene["attachHash"]+" "
if len(bpy.app.handlers.frame_change_pre):
    bpy.app.handlers.frame_change_pre.remove(bpy.app.handlers.frame_change_pre[-1])
bpy.app.handlers.frame_change_pre.append(my_handler)

#bpy.COPY_TRANSFORMS

# = bpy.data.objects["ArmatureShovel"].pose.bones["main"].constraints.new(type='COPY_TRANSFORMS')

def getBonesForControl(control):
    if control.endswith(".R"):
        bones = getBonesForControl2(control.replace(".R", ".L"))
        bones = [bone.replace(".L", ".R") for bone in bones]
    else:
        bones = getBonesForControl2(control)
    return bones

def getBonesForControl2(control):
    # a foot will take the whole leg
    if control == "mainfoot.L":
        return ["skeleton_leg_upper.L", "skeleton_leg_lower.L", "skeleton_foot_ball.L", "skeleton_foot_tip.L"]
    # a hand takes thw whole arm
    if control == "hand.L":
        return ["skeleton_arm_upper.L", "skeleton_arm_lower.L", "skeleton_arm_hand.L"]
    # the head
    if control == "head":
        return ["skeleton_head"]
    # the eyes
    if control == "eyes_target":
        return ["eye.L", "eye.R"]
    
    # the thumb
    if control == "thumb.L":
        return ["skeleton_hand_digit1.L", "skeleton_hand_digit2.L", "skeleton_hand_digit3.L"]
    # index finger
    if control == "index.L":
        return ["skeleton_hand_index1.L", "skeleton_hand_index2.L", "skeleton_hand_index3.L"]
    # middle finger
    if control == "middle.L":
        return ["skeleton_hand_middle1.L", "skeleton_hand_middle2.L", "skeleton_hand_middle3.L"]
    # ring finger
    if control == "ring.L":
        return ["skeleton_hand_ring1.L", "skeleton_hand_ring2.L", "skeleton_hand_ring3.L"]
    # little finger
    if control == "little.L":
        return ["skeleton_hand_small1.L", "skeleton_hand_small2.L", "skeleton_hand_small3.L"]
    
    if control == "body":
        return ["RootB"]
    if control == "body2":
        return ["skeleton_body"]
