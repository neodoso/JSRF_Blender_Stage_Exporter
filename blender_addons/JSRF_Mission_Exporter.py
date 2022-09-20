

bl_info = {
    "name": "JSRF Mission Exporter",
    "author": "neodos",
    "version": (1, 0, 1),
    "blender": (3, 2, 0),
    "category": "Export",
    "location": "Scene properties",
    "description": "JSRF Mission Exporter."
}

import bpy, os, shutil, importlib, sys, subprocess, math
from mathutils import Vector
from collections import defaultdict


from bpy.types import (
        Operator,
        Menu,
        Panel,
        AddonPreferences,
        )
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty,
        )

    
    
class JSRF_Mission_Exporter_Panel(bpy.types.Panel):

    bl_label = "JSRF Mission Exporter"
    bl_idname = "SCENE_PT_JSRF_Mission_Exporter"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator("scene.export_mission")
        row = layout.row()
        
        row = layout.row()
        row.prop(context.scene, 'export_dir')
        
        row = layout.row()
        row.prop(context.scene, 'media_dir')
        
        row = layout.row()
        row.prop(context.scene, 'compiler_path')
  


class Export_Mission(bpy.types.Operator):

    bl_idname = "scene.export_mission"
    bl_label = "Export Mission"
    bl_options = {'REGISTER'}


    def draw(self, context):
        layout = self.layout


    def execute(self, context):

        global export_dir
        global media_dir
        global compiler_path
        export_dir = os.path.realpath(bpy.path.abspath(bpy.context.scene.export_dir)) + "\\"
        media_dir = os.path.realpath(bpy.path.abspath(bpy.context.scene.media_dir)) + "\\"
        compiler_path = os.path.realpath(bpy.path.abspath(bpy.context.scene.compiler_path))

        global scene
        global ctx
        #context = bpy.context
        scene = context.scene
        ctx = bpy.context

        export_mission()

        return {'FINISHED'}

def register():
    bpy.utils.register_class(Export_Mission)
    
    
    bpy.types.Scene.export_dir = bpy.props.StringProperty \
      (
          name = "Stage Export Path",
          default = "",
          description = "Define the folder where the mission data will be exported to.",
          subtype = 'DIR_PATH'
      )
      
    bpy.types.Scene.media_dir = bpy.props.StringProperty \
      (
          name = "Media Directory",
          default = "",
          description = "Define the path to the game's Media folder.",
          subtype = 'DIR_PATH'
      )
      
    bpy.types.Scene.compiler_path = bpy.props.StringProperty \
      (
          name = "Mission Compiler tool filepath",
          default = "*.exe",
          description = "Define the path to the JSRF Mission Compiler executable.",
          subtype = 'FILE_PATH'
      )
      
      
    bpy.utils.register_class(JSRF_Mission_Exporter_Panel)


def unregister():
    del bpy.types.Scene.export_dir
    del bpy.types.Scene.media_dir
    del bpy.types.Scene.compiler_path
    bpy.utils.unregister_class(JSRF_Mission_Mission_Panel)
    bpy.utils.unregister_class(Export_Mission)
    
 
#if __name__ == "__main__":
#    register()

##########################################################################################################################################################
## Export items (spray cans) #############################################################################################################################
##########################################################################################################################################################

def export_items(coll):
    
    lines = [];
    
    for childObj in coll.objects:
            if childObj.type == "MESH":
                ppos = childObj.location
                pos_str = str(round(ppos.x * -1, 4)) + " " + str(round(ppos.z, 4)) + " " + str(round(ppos.y * -1, 4)) + " "
                
                if "spray_can_blue" in childObj.name:
                    lines.append(pos_str + "1")
                        
                elif "spray_can_health" in childObj.name:
                    lines.append(pos_str + "2")
                    
                elif "spray_can" in childObj.name:
                    lines.append(pos_str + "0")
                
            # write text file
            with open(export_dir + "Mission\\" + "Items.txt", "w") as f:
                for line in lines:
                    f.write(line + '\n')
                
##########################################################################################################################################################
## Export checkpoints  ###################################################################################################################################
##########################################################################################################################################################

def get_point_coords(pco):
    return str(round(pco.x * -1, 4)) + " " + str(round(pco.z, 4)) + " " + str(round(pco.y *-1, 4))


def export_Checkpoints(coll, filepath, isGlobal):
    lines = [];
    count = 0;
    orderA = [2, 3 ,1 ,0, 4]
    orderB = [3, 1 ,0 ,2, 4]

    for childObj in coll.objects:
        
        if childObj.type == "MESH":
            
            if(len(childObj.data.vertices) != 5):
                continue
            
            index = orderA;
            if(count == 2 and isGlobal == True):
                index = orderB
            
            pco = childObj.matrix_world @ childObj.data.vertices[index[0]].co
            lines.append(get_point_coords(pco))
                
            pco = childObj.matrix_world @ childObj.data.vertices[index[1]].co
            lines.append(get_point_coords(pco))

            pco = childObj.matrix_world @ childObj.data.vertices[index[2]].co
            lines.append(get_point_coords(pco))

            pco = childObj.matrix_world @ childObj.data.vertices[index[3]].co
            lines.append(get_point_coords(pco))

            #pcoA = obj.matrix_world @ obj.data.vertices[2].co
            pco = childObj.matrix_world @ childObj.data.vertices[index[4]].co
            lines.append(str(round(pco.x * -1, 4)) + " " + str(round(pco.z, 4)) + " " + str(round(pco.y *-1, 4)))
            count+=1
            
    # write text file
    with open(filepath, "w") as f:
        for line in lines:
            f.write(line + '\n')
##########################################################################################################################################################
## Player spawns  ########################################################################################################################################
##########################################################################################################################################################

def export_PlayerSpawnPos(obj, filepath):
    
    if(obj == None):
        return;
    
    # player spawn point export 
    lines = [];
    
    ppos = obj.location
    pos_str = "position:" + str(round(ppos.x * -1, 4)) + " " + str(round(ppos.z, 4)) + " " + str(round(ppos.y * -1, 4))
    lines.append(pos_str)
    
    # export orientation
    rotation = obj.matrix_local.to_euler()
    rot = -rotation.z * 32768 / math.pi + 32768
    rot = int(rot) % 65536
    lines.append("orientation:" + str(rot))
    
        # write text file
    with open(filepath, "w") as f:
        for line in lines:
            f.write(line + '\n')

##########################################################################################################################################################
## Export death warp planes and spawns  ##################################################################################################################
##########################################################################################################################################################

def export_DeathWarps(coll, filepath):
    lines = [];
    
    if(coll == None):
        return

    for childObj in coll.objects:
        str_split = childObj.name.split("_") 
        # if name has 3 string split by _ char
        if(len(str_split) == 3):
            found_spawn = False
            # if name contains dw_plane_
            if("dw_plane_" in childObj.name):
            
                # search dw_spawn
                for childObj_spawn in coll.objects:
                        # if name contains dw_plane_X (X being the number as dw_plane_X)
                        if("dw_spawn_" + str_split[2]  in childObj_spawn.name):
                            
                            # export spawn position
                            found_spawn = True
                            ppos = childObj_spawn.location
                            pos_str = "spawn:" + str(round(ppos.x * -1, 4)) + " " + str(round(ppos.z, 4)) + " " + str(round(ppos.y * -1, 4))
                            lines.append(pos_str)
                            
                            # export orientation
                            rotation = childObj_spawn.matrix_local.to_euler()
                            rot = -rotation.z * 32768 / math.pi + 32768
                            rot = int(rot) % 65536
                            lines.append("orientation:" + str(rot))       
                            break
            
            # if found the dw_spawn object
            if(found_spawn):
                #export plane
                if(len(childObj.data.vertices) == 4):
                    
                    pco = childObj.matrix_world @ childObj.data.vertices[2].co
                    lines.append("plane_a:" + get_point_coords(pco))
                        
                    pco = childObj.matrix_world @ childObj.data.vertices[0].co
                    lines.append("plane_b:" + get_point_coords(pco))

                    pco = childObj.matrix_world @ childObj.data.vertices[1].co
                    lines.append("plane_c:" + get_point_coords(pco))

                    pco = childObj.matrix_world @ childObj.data.vertices[3].co
                    lines.append("plane_d:" + get_point_coords(pco))
            
            
    # write text file
    with open(filepath, "w") as f:
        for line in lines:
            f.write(line + '\n')

##########################################################################################################################################################
## Run mission compiler   ################################################################################################################################
##########################################################################################################################################################
    
def compile():
    
    args = [compiler_path, media_dir, export_dir]
    print(args)
    subprocess.call(args)   

##########################################################################################################################################################
## Export mission data    ################################################################################################################################
##########################################################################################################################################################

def export_mission():

    context = bpy.context
    #bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    
    coll_Stage = None
    coll_Mission = None
    coll_Items = None
    coll_Checkpoints = None
    coll_CheckpointsGlobal = None
    coll_DeathWarps = None
    obj_PlayerSpawnPosition = None

    # browse scene collections
    # check if JSRF Stage collections exist
    if len(bpy.data.collections) > 0:
        
        # delete export dir and it's contents
        shutil.rmtree(export_dir + "Mission\\", ignore_errors=True)
        os.mkdir(export_dir + "Mission\\")

        for coll in bpy.data.collections:
                # if collection is named Stage
                if coll.name == "Stage":
                    coll_Stage = coll
                            
                    #for all child in coll
                    for collChild in coll.children:
                                         
                       if collChild.name == "Mission":
                            coll_Mission = collChild
                            
                            for ob in coll_Mission.objects:
                                if ob.name == "PlayerSpawnPosition":
                                    obj_PlayerSpawnPosition = ob
                            
                            for MissionChild in coll_Mission.children:
                                          
                                if MissionChild.name == "Items":
                                    coll_Items = MissionChild

                                if MissionChild.name == "Checkpoints":
                                    coll_Checkpoints = MissionChild
                                    
                                if MissionChild.name == "CheckpointsGlobal":
                                    coll_CheckpointsGlobal = MissionChild
                                    
                                if MissionChild.name == "DeathWarps":
                                    coll_DeathWarps = MissionChild
                                    
                                
                            
        if coll_Stage       == None : print("Error: could not find 'Stage' collection in outliner layers.");                  return                     
        if coll_Mission     == None : print("Error: could not find 'Mission' collection in outliner layers.");                return
        if coll_Items       == None : print("Error: could not find 'Items' collection in outliner layers.");                  return
        #if coll_Checkpoints == None : print("Error: could not find 'Checkpoints' collection in outliner layers.");            return
        #if coll_CheckpointsGlobal== None : print("Error: could not find 'Checkpointsglobal' collection in outliner layers."); return
    
    
    export_DeathWarps(coll_DeathWarps, export_dir + "Mission\\DeathWarps.txt")
    # export items and mission spawn position
    export_items(coll_Items)
    export_PlayerSpawnPos(obj_PlayerSpawnPosition, export_dir + "Mission\\PlayerSpawn.txt")
    
    # export checkint points   
    if(coll_Checkpoints != None and coll_CheckpointsGlobal != None):
        export_Checkpoints(coll_Checkpoints, export_dir + "Mission\\Checkpoints.txt", False)
        export_Checkpoints(coll_CheckpointsGlobal, export_dir + "Mission\\CheckpointsGlobal.txt", True)    
        
    
    compile() 

    


