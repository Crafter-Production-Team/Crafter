import bpy
import os
import time
import subprocess
import threading
from ..config import __addon_name__
from ..__init__ import resourcepacks_dir, materials_dir

#==========导入世界操作==========
class VIEW3D_OT_CrafterImportWorld(bpy.types.Operator):
    bl_label = "Import World"
    bl_idname = "crafter.import_world"
    bl_description = "Import world"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

    def execute(self, context: bpy.types.Context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        worldconfig = {
            "worldPath": addon_prefs.World_Path,
            "biomeMappingFile": "config\\mappings\\biomes_mapping.json",
            "solid": addon_prefs.solid,
            "minX": min(addon_prefs.XYZ_1[0], addon_prefs.XYZ_2[0]),
            "maxX": max(addon_prefs.XYZ_1[0], addon_prefs.XYZ_2[0]),
            "minY": min(addon_prefs.XYZ_1[1], addon_prefs.XYZ_2[1]),
            "maxY": max(addon_prefs.XYZ_1[1], addon_prefs.XYZ_2[1]),
            "minZ": min(addon_prefs.XYZ_1[2], addon_prefs.XYZ_2[2]),
            "maxZ": max(addon_prefs.XYZ_1[2], addon_prefs.XYZ_2[2]),
            "status": 0,
        }

        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        importer_dir = os.path.join(parent_dir, "importer")
        config_dir = os.path.join(importer_dir, "config")
        os.makedirs(config_dir, exist_ok=True)

        config_file_path = os.path.join(config_dir, "config.json")

        with open(config_file_path, 'w', encoding='gbk') as config_file:
            for key, value in worldconfig.items():
                config_file.write(f"{key} = {value}\n")

        self.report({'INFO'}, f"World config saved to {config_file_path}")

        importer_exe = os.path.join(importer_dir, "WorldImporter.exe")
        
        if os.path.exists(importer_exe):
            try:
                # 在新的进程中运行WorldImporter.exe
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                DETACHED_PROCESS = 0x00000008
                subprocess.Popen(
                    [importer_exe],
                    cwd=importer_dir,
                    creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS
                )
                self.report({'INFO'}, f"WorldImporter.exe started in a new process")

                # 使用线程监控状态
                threading.Thread(target=self.monitor_status, args=(config_file_path,), daemon=True).start()

            except Exception as e:
                self.report({'ERROR'}, f"Error: {e}")
        else:
            self.report({'ERROR'}, f"WorldImporter.exe not found at {importer_exe}")

        return {'FINISHED'}

    def monitor_status(self, config_file_path):
        while True:
            time.sleep(0.2)  # 每秒检查一次
            try:
                with open(config_file_path, 'r', encoding='gbk') as config_file:
                    content = config_file.read()
                    if "status = 3" in content:
                        content = content.replace("status = 3", "status = 0")
                        with open(config_file_path, 'w', encoding='gbk') as config_file:
                            config_file.write(content)
                        bpy.app.timers.register(self.import_output)
                        break
            except Exception as e:
                print(f"Error reading config file: {e}")
                continue

    def import_output(self):
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        importer_dir = os.path.join(parent_dir, "importer")
        output_obj = os.path.join(importer_dir, "output.obj")
        if os.path.exists(output_obj):
            bpy.ops.wm.obj_import(filepath=output_obj)
            self.report({'INFO'}, f"Imported {output_obj}")
        else:
            self.report({'WARNING'}, f"output.obj not found at {output_obj}")

class VIEW3D_OT_CrafterImportSurfaceWorld(bpy.types.Operator):
    bl_label = "Import Surface World"
    bl_idname = "crafter.import_surface_world"
    bl_description = "Import the surface world"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

    def execute(self, context: bpy.types.Context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        addon_prefs.solid = 0
        bpy.ops.crafter.improt_world()
        return {'FINISHED'}

class VIEW3D_OT_CrafterImportSolidArea(bpy.types.Operator):
    bl_label = "Import Solid Area"
    bl_idname = "crafter.import_solid_area"
    bl_description = "Import the solid area"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return False#完善后开启

    def execute(self, context: bpy.types.Context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        #这里应该还要删除物体在坐标内的顶点，但时间紧任务重，稍后再写
        addon_prefs.solid = 1
        bpy.ops.crafter.improt_world()
        return {'FINISHED'}

#==========导入纹理操作==========
class VIEW3D_OT_CrafterReloadResourcesPlans(bpy.types.Operator):
    bl_label = "Reload Resources Plans"
    bl_idname = "crafter.reload_resources_plans"
    bl_description = "Reload resources plans"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

    def execute(self, context: bpy.types.Context):
        context.scene.Resources_Plans_List.clear()
        for folder in os.listdir(resourcepacks_dir):
            if os.path.isdir(os.path.join(resourcepacks_dir, folder)):
                plan_name = context.scene.Resources_Plans_List.add()
                plan_name.name = folder
        return {'FINISHED'}

class VIEW3D_OT_CrafterSetTextureInterpolation(bpy.types.Operator):
    bl_label = "Set Texture Interpolation"    
    bl_idname = "crafter.set_texture_interpolation"
    bl_description = "Set Texture Interpolation"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.selected_objects and bpy.context.active_object.type == "MESH":
            return True

    def execute(self, context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        if context.active_object.type == "MESH":
            for mat in bpy.context.active_object.data.materials:
                if mat.node_tree:
                    for node in mat.node_tree.nodes:
                        if node.bl_idname == "ShaderNodeTexImage":
                            node.interpolation = addon_prefs.Texture_Interpolation
        return {'FINISHED'}