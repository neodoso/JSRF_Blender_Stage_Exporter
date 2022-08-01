

bl_info = {
    "name": "JSRF Stage Exporter",
    "author": "neodos",
    "version": (1, 0, 1),
    "blender": (3, 2, 0),
    "category": "Export",
    "location": "Scene properties",
    "description": "JSRF stage exporter."
}

import bpy, os, shutil, importlib, sys, subprocess
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

    
    
class JSRF_Stage_Exporter_Panel(bpy.types.Panel):

    bl_label = "JSRF Stage Exporter"
    bl_idname = "SCENE_PT_JSRF_Stage_Exporter"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator("scene.export")
        row = layout.row()
        
        #row.operator("render.export_btn")
               
        row = layout.row()
        row.prop(context.scene, 'stage_id') 
        row = layout.row()
        row.prop(context.scene, 'export_path')
        row = layout.row()
        row.prop(context.scene, 'media_dir')
        row = layout.row()
        row.prop(context.scene, 'modtool_path')
  


class Export_Stage(bpy.types.Operator):

    bl_idname = "scene.export"
    bl_label = "Export Stage"
    bl_options = {'REGISTER'}


    def draw(self, context):
        layout = self.layout


    def execute(self, context):
        global stage_num 
        global export_dir
        global media_dir
        global modtool_path
        stage_num = bpy.context.scene.stage_id
        export_dir = os.path.realpath(bpy.path.abspath(bpy.context.scene.export_path)) + "\\"
        media_dir = os.path.realpath(bpy.path.abspath(bpy.context.scene.media_dir)) + "\\"
        modtool_path = os.path.realpath(bpy.path.abspath(bpy.context.scene.modtool_path))

        global scene
        global ctx
        #context = bpy.context
        scene = context.scene
        ctx = bpy.context

        export_jsrf_stage()

        return {'FINISHED'}

def register():
    bpy.utils.register_class(Export_Stage)
    
    bpy.types.Scene.stage_id = bpy.props.StringProperty \
      (
          name = "Stage ID",
          default = "stg00",
          description = "Define the name of the Stage file it will compile as.",
     
      )
    
    bpy.types.Scene.export_path = bpy.props.StringProperty \
      (
          name = "Stage Export Path",
          default = "",
          description = "Define the folder where the Stage data will be exported to.",
          subtype = 'DIR_PATH'
      )
      
    bpy.types.Scene.media_dir = bpy.props.StringProperty \
      (
          name = "Media Directory",
          default = "",
          description = "Define the game's Media folder path.",
          subtype = 'DIR_PATH'
      )
      
    bpy.types.Scene.modtool_path = bpy.props.StringProperty \
      (
          name = "ModTool filepath",
          default = "*.exe",
          description = "Define the path to the JSRF ModTool executable.",
          subtype = 'FILE_PATH'
      )
      
    bpy.utils.register_class(JSRF_Stage_Exporter_Panel)


def unregister():
    del bpy.types.Scene.export_path
    del bpy.types.Scene.stage_id
    del bpy.types.Scene.media_dir
    del bpy.types.Scene.modtool_path
    bpy.utils.unregister_class(JSRF_Stage_Exporter_Panel)
    bpy.utils.unregister_class(Export_Stage)
    
 
#if __name__ == "__main__":
#    register()

##########################################################################################################################################################
## Functions to export meshes and curves(grind paths) ####################################################################################################
##########################################################################################################################################################

# export Stage meshes based on the Visul and Collision collections
def export_meshes(coll, coll_name):
    # make collision models visible(otherwise the obj exporter outputs empty obj files)
    #if coll.name == coll_name:
        #bpy.data.collections[coll.name_full].hide_viewport = False
        
    for model_group in coll.children:
        # if collection is instance of Collection type
        if isinstance(model_group, bpy.types.Collection): 
            
            for childObj in model_group.objects:
                
                if childObj.type == "MESH":
                    # add mesh to selection
                    childObj.select_set(True)
                    
                    export_path =  export_dir + "\\" + get_name_prefix(coll_name) + "\\" + get_name_prefix(model_group.name) + "\\";
                    os.makedirs(export_path, exist_ok=True)
                     # Export models in one OBJ
                    bpy.ops.export_scene.obj(
                                                filepath = export_path + get_name_prefix(model_group.name) + ".obj", 
                                                check_existing=False, use_selection=True,
                                                use_mesh_modifiers=True, use_edges=True, 
                                                use_smooth_groups=False, use_normals=True, 
                                                use_uvs=True, use_materials=True, use_triangles=True, 
                                                use_blen_objects=False, 
                                                keep_vertex_order=True,
                                                group_by_object=True
                                             )
            #  group_by_object=True, group_by_material = True
            
            bpy.ops.object.select_all(action='DESELECT')
            
    # turn off Collision models visibility       
    #if group.name == "Collision":
        #bpy.data.collections[group.name_full].hide_viewport = True
        
# export curves (grind paths)
def export_curves(group):
        lines = []; flagA = 0; flagB = 0;
        # for each child in group
        for idp, coll in enumerate(group.children):
            
            # if it's a collection instance
            if isinstance(coll, bpy.types.Collection):
                
                # for each child object in coll.
                for idc, childObject in enumerate(coll.objects):
                    
                    flagA = 0
                    flagB = 0
                    
                    if("_F0" in childObject.name):
                        flagA = 2
                        flagB = 1
                        
                    if("_F1" in childObject.name):
                        flagA = 6
                        flagB = 1
                    
                    # grind path header as follows: [model_container_index + ":" + curve_item_number + ":" + flagA + " " +  flagB]
                    # add to lines list
                    lines.append("[" + str(idp) + ":" + str(idc)  + ":" + str(flagA) + " " + str(flagB) + "]")
                    
                    # if object is a curve
                    if childObject.type == "CURVE":
                        
                        for spline in childObject.data.splines:
                            oMatrix = childObject.matrix_world
                            for point in spline.points:
                                 # get world position of spline point (relative to curve object matrix)
                                 pco = Vector(point.co[0:3])
                                 pco = (oMatrix @ pco)
                                 # add (point and normal) to lines
                                 lines.append(str(round(pco.x * -1, 4)) + " " + str(round(pco.z, 4)) + " " + str(round(pco.y * -1, 4)) + " 0 1 0")
                                
                    lines.append("end")
        
            # create GrindPaths directory if it doesn't exist
            # os.makedirs(export_dir + "GrindPaths" + "\\", exist_ok=True)

            # write text file
            with open(export_dir + "\\grind_paths.txt", "w") as f:
                for line in lines:
                    f.write(line + '\n')

                    
##########################################################################################################################################################
## functions to pre-process a copy of the meshes of collections (Visual/Collision) #######################################################################
##########################################################################################################################################################

def copy_objects(from_col, to_col, linked, dupe_lut):
    for o in from_col.objects:
        dupe = o.copy()
        if not linked and o.data:
            dupe.data = dupe.data.copy()
        to_col.objects.link(dupe)
        dupe_lut[o] = dupe
        
def copy(parent, collection, linked=False):
    
    dupe_lut = defaultdict(lambda : None)
    def _copy(parent, collection, linked=False):
        cc = bpy.data.collections.new(collection.name)
        copy_objects(collection, cc, linked, dupe_lut)

        for c in collection.children:
            _copy(cc, c, linked)

        parent.children.link(cc)
    
    _copy(parent, collection, linked)

    for o, dupe in tuple(dupe_lut.items()):
        parent = dupe_lut[o.parent]
        if parent:
            dupe.parent = parent



# joins meshes (inside a collection) into one, 
def join_meshes_inCollection(parentCollection):
    meshes_orphaned = []
    meshes = []
    
    for childObject in parentCollection.objects:
        if childObject.type == 'MESH':
            
            bpy.context.view_layer.objects.active = childObject
            # apply edge split
            bpy.ops.object.modifier_add(type='EDGE_SPLIT')
            bpy.context.view_layer.objects.active.modifiers["EdgeSplit"].use_edge_angle = False
            bpy.ops.object.modifier_apply(modifier="EdgeSplit")
            
            meshes.append(childObject)
            meshes_orphaned.append(childObject.data)
            #bpy.data.objects.remove(childObject, do_unlink=True)
            
    ctx = bpy.context.copy()
    # one of the objects to join
    ctx['active_object'] = meshes[0]
    ctx['selected_editable_objects'] = meshes
    
    joined_mesh = bpy.ops.object.join(ctx)
    
    # delete orphaned meshes
    for mesh in meshes_orphaned[1:]: # skip first item
            # Delete the meshes
            bpy.data.meshes.remove(mesh)    

    
# splits mesh into separate meshes per material    
def split_mesh_by_material():
    
    bpy.ops.object.mode_set(mode='OBJECT')

    if bpy.context.active_object.type == 'MESH':
        # Edit Mode
        bpy.ops.object.mode_set(mode='EDIT')
        # Seperate by material
        bpy.ops.mesh.separate(type='MATERIAL')
        # Object Mode
        bpy.ops.object.mode_set(mode='OBJECT')



# duplicates collection(coll_name) recursively
def duplicate_collection(coll):
    #coll = bpy.data.collections.get(coll_name)
    assert(coll is not scene.collection)

    coll_copt = copy(scene.collection, coll)
    return bpy.data.collections.get(coll.name + '.001')



# processes meshes inside collection (merge all, separate mesh by material) 
def process_Collection(Coll):
    
    bpy.ops.object.select_all(action='DESELECT')
    
    # loop through collection's items and join meshes into one
    for meshColl in Coll.children:
        # if collection is instance of Collection type
        if isinstance(meshColl, bpy.types.Collection):
            join_meshes_inCollection(meshColl)
            
    # loop through collection children and  split meshes by material
    for meshColl in Coll.children:
  
         # if collection is instance of Collection type
        if isinstance(meshColl, bpy.types.Collection): 
            
            for ob in meshColl.objects:
                # whatever objects you want to join
                if ob.type == 'MESH':
                    
                    # select mesh
                    bpy.data.objects[ob.name].select_set(True)
                    
                    # flip on X axis
                    bpy.ops.transform.mirror(constraint_axis=(True, False, False), orient_type='GLOBAL')
                    ob.location.x = ob.location.x *-1
                    
                    bpy.context.view_layer.objects.active = bpy.data.objects[ob.name]
                    merge_duplicate_materials_inMesh()
                    
                    # separate into multiple, one for each material
                    split_mesh_by_material()
                    
                    bpy.ops.object.select_all(action="DESELECT")
                    break
                    



# removes the collection duplicates if they exists in the outliner layers
def remove_JSRF_Stage_CollCopy(CollCopy):
  
    # if collection 'Visual.001' exists, remove it and nested objects
    try:
        #CollCopy = bpy.data.collections.get(CollName)
        
        # for VisCopy children
        for CollchildObj in CollCopy.children:
            
            # collects orphaned meshes from deleted objects
            meshes_orphaned = set()
            
            # if collection is instance of Collection type
            if isinstance(CollchildObj, bpy.types.Collection): 

                # remove child objects from obj collection
                for childObject in CollchildObj.objects:
                    meshes_orphaned.add(childObject.data)
                    bpy.data.objects.remove(childObject, do_unlink=True)          
                
                # Look at meshes that are orphan after objects removal
                for mesh in [m for m in meshes_orphaned if m.users == 0]:
                    # Delete the meshes
                    bpy.data.meshes.remove(mesh)
                    
                # remove parent collection
                bpy.data.collections.remove(CollchildObj)
                    
            else: # else delete object is not a collection, remove object
                bpy.data.objects.remove(CollchildObj, do_unlink=True)
                

                
        # remove VisCopy collection
        bpy.data.collections.remove(CollCopy)

    except Exception:
        pass
    #except Exception #as e: #print(e)



def get_name_prefix(input_string):
    if(input_string.count(".") == 1):
        return input_string.split('.', 1)[0]
    else:
        return input_string
    

##########################################################################################################################################################
## Merge duplicate materials in mesh object   ############################################################################################################
##########################################################################################################################################################

# returns texture filepath that is set as Base Color in the provided material
def get_mat_tex_filepath(material):
    
    nodes = material.node_tree.nodes
    principled = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    base_color = principled.inputs['Base Color'] #Or principled.inputs[0]

    link = base_color.links[0]
    link_node = link.from_node
    
    return link_node.image.filepath

# removes duplicate materials within a mesh, 
# merges them into a single material if they use the same texture file as Base Color
def merge_duplicate_materials_inMesh():

    mats_list = [x.material.name for x in bpy.context.active_object.material_slots]
    discarded_slots = []

    #mat_slots_count = len(bpy.context.object.material_slots.items())
    mat_slots_count = len(bpy.context.active_object.material_slots.items())
    matA_index = 0
    matB_index = 0
    
    while matA_index < mat_slots_count:
        
        matA = bpy.context.active_object.material_slots[matA_index]
        matA_index += 1
        
        # reset matB_index if we reach the end of the list
        if(matB_index == mat_slots_count):
            matB_index = 0


        while matB_index < mat_slots_count:
            
            matB = bpy.context.active_object.material_slots[matB_index]
            matB_index += 1
            
            # skip if it's the same material
            if matA.material.name == matB.material.name:
                continue

            # if matA and matB texture filepath are equal
            if get_mat_tex_filepath(matA.material) == get_mat_tex_filepath(matB.material):
                  #print(matA.material.name + " " + str(mat_list.index(matA.material.name)) + " and " + matB.material.name + " " + str(mat_list.index(matB.material.name))  + " share the tame texture")
                  
                  # store material indices, for the original material and the duplicate material
                  source_mat_index = mats_list.index(matA.material.name)
                  duplicate_mat_index = mats_list.index(matB.material.name)
                  
                  # get faces which have the duplicate material assigned
                  faces_with_duplicate_mat = [x for x in bpy.context.active_object.data.polygons if x.material_index == duplicate_mat_index]
                    
                  # set faces material to source material index
                  for f in faces_with_duplicate_mat:
                    f.material_index = source_mat_index
 
                  discarded_mat_name = matB.name
                  for obj in bpy.context.selected_editable_objects:
                      # if matB.name is found in bpy.context.active_object.material_slots[]
                      if matB.name in [x.name for x in obj.material_slots]:
                          # set active material index to the index of "matB.name" index 
                          #bpy.context.active_object.active_material_index = [x.material.name for x in bpy.context.active_object.material_slots].index(matB.name)
                          obj.active_material_index = [x.material.name for x in obj.material_slots].index(matB.name)
                          # remove material slot
                          bpy.ops.object.material_slot_remove({'object': obj})                  
    
                  
                  mat_slots_count = len(bpy.context.active_object.material_slots.items())
                  matA_index = 0
                  matB_index = 0
                  
                  mats_list = [x.material.name for x in bpy.context.active_object.material_slots]
                  
                   
                  #break
      
    #for s in discarded_slots:
        
        # get material_slot by name
        #if s in [x.name for x in bpy.context.object.material_slots]:
            # set active material index to the index of "s" index 
            #bpy.context.object.active_material_index = [x.material.name for x in bpy.context.object.material_slots].index(s)
            # remove material slot
            #bpy.ops.object.material_slot_remove()
    
##########################################################################################################################################################
## Run stage compiler   ##################################################################################################################################
##########################################################################################################################################################
    
def compile():
    
    args = [modtool_path, "stage_compile", export_dir, media_dir, stage_num]
    print(args)
    subprocess.call(args)

##########################################################################################################################################################
## Process & Export Stage data   ########################################################################################################################
##########################################################################################################################################################

def export_jsrf_stage():

    context = bpy.context
    #bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    
    coll_Stage = None
    coll_Visual = None
    coll_Collision = None
    collGrindPaths = None

    # browse scene collections
    # check if JSRF Stage collections exist
    if len(bpy.data.collections) > 0:
        
        # delete export dir and it's contents
        shutil.rmtree(export_dir, ignore_errors=True)

        for coll in bpy.data.collections:
                # if collection is named Stage
                if coll.name == "Stage":
                    coll_Stage = coll
                            
                    #for all child in coll
                    for collChild in coll.children:
                                
                       if collChild.name == "Visual":
                           coll_Visual = collChild
                           
                       if collChild.name == "Collision":
                            coll_Collision = collChild
                            
                       if collChild.name == "GrindPaths":
                            collGrindPaths = collChild
                            
                             
        if coll_Stage     == None : print("Error: could not find 'Stage' collection in outliner layers");      return
        if coll_Visual    == None : print("Error: could not find 'Visual' collection in outliner layers");     return
        if coll_Collision == None : print("Error: could not find 'Collision' collection in outliner layers");  return
        if collGrindPaths == None : print("Error: could not find 'GrindPaths' collection in outliner layers"); return    
                 

    # removes duplicate collections(and nested items) used for pre-processing meshes for export 
    remove_JSRF_Stage_CollCopy('Visual.001')
    remove_JSRF_Stage_CollCopy('Collision.001')


    # duplicate Visual/Collision collection
    # process collection (join and split meshes by material)
    # export meshes
    VisDupeColl = duplicate_collection(coll_Visual)
    process_Collection(VisDupeColl)
    export_meshes(VisDupeColl, "Visual")
    remove_JSRF_Stage_CollCopy(VisDupeColl) # 'Visual.001'

    #bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")


    CollisionDupeColl = duplicate_collection(coll_Collision)
    process_Collection(CollisionDupeColl)
    export_meshes(CollisionDupeColl, "Collision")
    remove_JSRF_Stage_CollCopy(CollisionDupeColl) #'Collision.001'


    export_curves(collGrindPaths)

    compile()