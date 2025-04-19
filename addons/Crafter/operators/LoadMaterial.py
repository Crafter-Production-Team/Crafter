import bpy
import os
import json

from ..config import __addon_name__
from ....common.i18n.i18n import i18n
from bpy.props import *
from ..__init__ import dir_cafter_data, dir_resourcepacks_plans, dir_materials, dir_classification_basis, dir_blend_append, dir_init_main, dir_backgrounds
from .Defs import *

# ==================== 加载材质 ====================

class VIEW3D_OT_CrafterLoadMaterial(bpy.types.Operator):
    bl_label = "Load Material"
    bl_idname = "crafter.load_material"
    bl_description = "Load Material"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True
        return any(obj.type == "MESH" for obj in context.selected_objects)

    def execute(self, context: bpy.types.Context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences

        bpy.ops.crafter.reload_all()
        if len(context.selected_objects) != 0:
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        # 删除startswith(CO-)、startswith(CI-)节点组、startswith(C-)节点组
        for node in bpy.data.node_groups:
            if node.name.startswith("CO-") or node.name.startswith("CI-") or node.name.startswith("C-"):
                bpy.data.node_groups.remove(node)
        # 删除Crafter Materials Settings物体、材质
        try:
            bpy.data.objects.remove(bpy.data.objects["Crafter Materials Settings"])
        except:
            pass
        try:
            bpy.data.materials.remove(bpy.data.materials["Crafter Materials Settings"], do_unlink=True)
        except:
            pass
        # 导入C-节点组
        node_groups_use_fake_user = ["C-PBR_Parser","C-lab_PBR_1.3","C-old_continuum","C-old_BSL","C-SEUS_PBR"]
        with bpy.data.libraries.load(dir_blend_append, link=False) as (data_from, data_to):
            data_to.node_groups = [name for name in data_from.node_groups if name in node_groups_use_fake_user]
        for node_group in node_groups_use_fake_user:
            bpy.data.node_groups[node_group].use_fake_user = True
        # 导入Crafter-Moving_texture节点组
        if not "Crafter-Moving_texture" in bpy.data.node_groups:# 若不存在则导入C-节点组
            with bpy.data.libraries.load(dir_blend_append, link=False) as (data_from, data_to):
                data_to.node_groups = ["Crafter-Moving_texture"]
            bpy.data.node_groups["Crafter-Moving_texture"].use_fake_user = True
        # 导入Crafter Materials Settings物体、材质、startswith(CI-)
        blend_material_dir = os.path.join(dir_materials, addon_prefs.Materials_List[addon_prefs.Materials_List_index].name + ".blend")
        with bpy.data.libraries.load(blend_material_dir, link=False) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if name == "Crafter Materials Settings"]
        if "Crafter Materials Settings"  in bpy.data.collections:
            collection_Crafter_Materials_Settings = bpy.data.collections["Crafter Materials Settings"]
        else:
            collection_Crafter_Materials_Settings = bpy.data.collections.new(name="Crafter Materials Settings")
            bpy.context.scene.collection.children.link(collection_Crafter_Materials_Settings)
        collection_Crafter_Materials_Settings.objects.link(bpy.data.objects["Crafter Materials Settings"])
        bpy.data.objects["Crafter Materials Settings"].hide_viewport = True
        bpy.data.objects["Crafter Materials Settings"].hide_render = True
        # 获取分类依据地址
        classification_folder_name = addon_prefs.Classification_Basis_List[addon_prefs.Classification_Basis_List_index].name
        classification_folder_dir = os.path.join(dir_classification_basis, classification_folder_name)
        # 初始化 COs,classification_list,banlist, ban_keyw
        classification_list = {}
        banlist = []
        ban_keyw = []
        # 获取classification_list
        for filename in os.listdir(classification_folder_dir):
            file_path = os.path.join(classification_folder_dir, filename)
            if filename.endswith(".json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        classification_list = make_json_together(classification_list, data)
                        if "ban" in data:
                            banlist.extend(data["ban"])
                        if "ban_keyw" in data:
                            ban_keyw.extend(data["ban_keyw"])
                except:
                    pass
        # 应用 Parsed_Normal_Strength
        bpy.ops.crafter.set_parsed_normal_strength()

        # 添加选中物体的材质到合集
        for obj in context.selected_objects:
            if obj.type == "MESH":
                add_to_mcmts_collection(object=obj,context=context)
                add_C_time(obj=obj)
        # 遍历材质合集
        for name_material in context.scene.Crafter_mcmts:
            imported_by_crafter = False
            if name_material.name in context.scene.Crafter_crafter_mcmts:
                imported_by_crafter = True
            material = bpy.data.materials[name_material.name]
            node_tree_material = material.node_tree
            if node_tree_material == None:
                continue
            nodes = node_tree_material.nodes
            links = node_tree_material.links
            
            node_tex_base = None
            #处理lod材质
            if material.name.startswith("color#"):
                nodes_wait_remove = []
                material.displacement_method = "BOTH"
                for node in nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        if node.target == "EEVEE":
                            node_output_EEVEE = node
                        if node.target == "ALL":
                            node.target = "EEVEE"
                            node_output_EEVEE = node
                        if node.target == "CYCLES":
                            nodes_wait_remove.append(node)
                    if node.type == "BSDF_PRINCIPLED":
                            nodes_wait_remove.append(node)
                    if node.type == "GROUP":
                        if node.node_tree == None:
                            nodes_wait_remove.append(node)
                        else:
                            if node.node_tree.name.startswith("Crafter-biomeTex"):
                                node_biomeTex = node
                for node in nodes_wait_remove:
                    nodes.remove(node)

                # 添加Cycles输出节点
                node_output_Cycles = nodes.new(type="ShaderNodeOutputMaterial")
                node_output_Cycles.target = "CYCLES"
                node_output_Cycles.location = (node_output_EEVEE.location.x, node_output_EEVEE.location.y - 160)
                
                # 添加startswith(CI-)节点组
                group_CI = nodes.new(type="ShaderNodeGroup")
                group_CI.location = (node_output_EEVEE.location.x - 200, node_output_EEVEE.location.y)
                real_name = fuq_bl_dot_number(name_material.name)
                if len(real_name) > 24:
                    last_mao_index = real_name.rfind(':')
                    real_block_name = real_name[last_mao_index+1:]
                    find_CI_group(group_CI=group_CI, real_block_name=real_block_name,classification_list=classification_list)
                else:
                    group_CI.node_tree = bpy.data.node_groups["CI-"]
                if "Base Color" in group_CI.inputs:
                    group_CI.inputs["Base Color"].default_value = [float(material.name[6:10]),float(material.name[11:15]),float(material.name[16:20]),1]
                # 连接CI节点
                Displacement = link_CI_output(group_CI=group_CI, node_output_EEVEE=node_output_EEVEE, node_output_Cycles=node_output_Cycles,links=links)
                if Displacement:# 查看是否需要开启置换
                    material.displacement_method = "BOTH"
                else:
                    material.displacement_method = "BUMP"
                link_biome_tex(node_biomeTex=node_biomeTex, group_CI=group_CI, links=links)
                add_node_parser(group_CI=group_CI,nodes=nodes,links=links)
                continue
            #获取基础贴图节点

            # 注释部分为旧的通过材质名获得mod_name和type_name的方式，暂作保留

            # real_block_name = material.name
            # real_block_name = fuq_bl_dot_number(real_block_name)
            # mod_name = "minecraft"
            # type_name = "block"
            # 获得real_material_name(如果有mod_name,type_name,获得之,但目前好像没用...)
            # last_hen_index = real_material_name.rfind('-')
            # if not last_hen_index == -1:
            #     mod_and_type = real_material_name[:last_hen_index]
            #     real_material_name = real_material_name[last_hen_index+1:]
            #     last____index = mod_and_type.rfind('_')
            #     mod_name = real_material_name[:last____index]
            #     type_name = real_material_name[last____index+1:last_hen_index]
            #获得node_output 并 删去无内容节点组
            nodes_wait_remove = []
            real_block_name = None
            node_tex_normal = None
            node_tex_PBR = None
            for node in nodes:
                if node.type == "TEX_IMAGE" and node.image != None:
                    name_image = fuq_bl_dot_number(node.image.name)
                    if name_image.endswith("_n.png") or name_image.endswith("_s.png") or name_image.endswith("_a.png"):
                        if imported_by_crafter:
                            if name_image.endswith("_n.png"):
                                node_tex_normal = node
                            if name_image.endswith("_s.png") or name_image.endswith("_a.png"):
                                node_tex_PBR = node
                        else:
                            bpy.data.images.remove(node.image)
                            nodes_wait_remove.append(node)
                    elif node_tex_base != None:
                        nodes_wait_remove.append(node)
                    elif name_image.endswith(".png"):
                        node.interpolation = "Closest"
                        node_tex_base = node
                        block_name = fuq_bl_dot_number(node_tex_base.image.name)
                        real_block_name = block_name[:-4]
                if node.type == "OUTPUT_MATERIAL":
                    if node.target == "EEVEE":
                        node_output_EEVEE = node
                    if node.target == "ALL":
                        node.target = "EEVEE"
                        node_output_EEVEE = node
                    if node.target == "CYCLES":
                        nodes_wait_remove.append(node)
                if node.type == "GROUP":
                    if node.node_tree == None:
                        nodes_wait_remove.append(node)
                    else:
                        if node.node_tree.name.startswith("Crafter-biomeTex"):
                            node_biomeTex = node
            if real_block_name == None:
                continue
            # 如果在banlist里直接跳过
            ban = False
            for ban_key in ban_keyw:
                if real_block_name in ban_key:
                    ban = True
                    break
            if ban or real_block_name in banlist:
                continue
            for node in nodes_wait_remove:
                nodes.remove(node)
            # 添加Cycles输出节点
            node_output_Cycles = nodes.new(type="ShaderNodeOutputMaterial")
            node_output_Cycles.target = "CYCLES"
            node_output_Cycles.location = (node_output_EEVEE.location.x, node_output_EEVEE.location.y - 160)
            # 删去原有着色器
            try:
                from_node = node_output_EEVEE.inputs[0].links[0].from_node
                if from_node.type == "BSDF_PRINCIPLED" and material.name not in donot:
                    nodes.remove(from_node)
            except:
                pass
            # 添加startswith(CI-)节点组
            group_CI = nodes.new(type="ShaderNodeGroup")
            group_CI.location = (node_output_EEVEE.location.x - 200, node_output_EEVEE.location.y)
            find_CI_group(group_CI=group_CI, real_block_name=real_block_name,classification_list=classification_list)
            # 连接CI节点
            Displacement = link_CI_output(group_CI=group_CI, node_output_EEVEE=node_output_EEVEE, node_output_Cycles=node_output_Cycles,links=links)
            if Displacement:# 查看是否需要开启置换
                # 设置材质置换方式为仅置换
                material.displacement_method = "BOTH"
            else:
                material.displacement_method = "BUMP"
            link_biome_tex(node_biomeTex=node_biomeTex, group_CI=group_CI, links=links)
            node_C_PBR_Parser = add_node_parser(group_CI=group_CI,nodes=nodes,links=links)
            if not imported_by_crafter:
                node_tex_normal, node_tex_PBR = load_normal_and_PBR(node_tex_base=node_tex_base, nodes=nodes, links=links,)
            link_base_normal_and_PBR(node_tex_base=node_tex_base, group_CI=group_CI, links=links, node_C_PBR_Parser=node_C_PBR_Parser,node_tex_normal=node_tex_normal, node_tex_PBR=node_tex_PBR)
        bpy.ops.crafter.set_pbr_parser
        # 添加选中物体的材质到合集
        for obj in context.selected_objects:
            if obj.type == "MESH":
                add_to_crafter_mcmts_collection(object=obj,context=context)

        return {'FINISHED'}

    def invoke(self, context, event):
        addon_prefs = context.preferences.addons[__addon_name__].preferences

        bpy.ops.crafter.reload_all()
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        layout = self.layout

        row_PBR_Parser = layout.row()
        row_PBR_Parser.prop(addon_prefs, "PBR_Parser")

        row_Parsed_Normal_Strength = layout.row()
        row_Parsed_Normal_Strength.prop(addon_prefs, "Parsed_Normal_Strength")

        layout.label(text="Materials")
        row_Materials_List = layout.row()
        row_Materials_List.template_list("VIEW3D_UL_CrafterMaterials", "", addon_prefs, "Materials_List", addon_prefs, "Materials_List_index", rows=1)
        col_Materials_List_ops = row_Materials_List.column()
        col_Materials_List_ops.operator("crafter.open_materials",icon="FILE_FOLDER",text="")
        col_Materials_List_ops.operator("crafter.reload_all",icon="FILE_REFRESH",text="")

        layout.label(text="Classification Basis")
        row_Classification_Basis = layout.row()
        row_Classification_Basis.template_list("VIEW3D_UL_CrafterClassificationBasis", "", addon_prefs, "Classification_Basis_List", addon_prefs, "Classification_Basis_List_index", rows=1)
        row_Classification_Basis_ops = row_Classification_Basis.column()
        row_Classification_Basis_ops.operator("crafter.open_classification_basis",icon="FILE_FOLDER",text="")
        row_Classification_Basis_ops.operator("crafter.reload_all",icon="FILE_REFRESH",text="")

# ==================== 设置PBR解析器 ====================

class VIEW3D_OT_CrafterSetPBRParser(bpy.types.Operator):
    bl_label = "Set PBR Parser"
    bl_idname = "crafter.set_pbr_parser"
    bl_description = " "
    
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

    def execute(self, context: bpy.types.Context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences

        node_C_PBR_Parser = bpy.data.node_groups["C-PBR_Parser"]
        nodes = node_C_PBR_Parser.nodes
        links = node_C_PBR_Parser.links
        for node in nodes:
            if node.type == "GROUP_OUTPUT":
                node_output = node
            elif node.type == "GROUP_INPUT":
                node_input = node
            elif node.type == "GROUP":
                node_Parser = node
        node_Parser.node_tree = bpy.data.node_groups["C-" + addon_prefs.PBR_Parser]
        for input in node_Parser.inputs:
            links.new(input, node_output.outputs[input.name])
        for input in node_Parser.inputs:
            links.new(input, node_input.outputs[input.name])
        PBR_value = [0.291769,0.039546,0,1]
        if addon_prefs.PBR_Parser == "old_continuum":
            PBR_value = [0.291769,0,0,1]
        elif addon_prefs.PBR_Parser == "old_BSL":
            PBR_value = [0.5,0,0,1]
        elif addon_prefs.PBR_Parser == "SEUS_PBR":
            PBR_value = [0.5,0,0,1]
        for name_material in context.scene.Crafter_mcmts:
            material = bpy.data.materials[name_material.name]
            node_tree_material = material.node_tree
            for node in node_tree_material.nodes:
                if node.type == "GROUP":
                    if node.node_tree.name != None:
                        if node.node_tree.name == "C-PBR_Parser":
                            node.inputs["PBR"].default_value = PBR_value
        return {'FINISHED'}

# ==================== 打开材质列表文件夹 ====================

class VIEW3D_OT_CrafterOpenMaterials(bpy.types.Operator):
    bl_label = "Open Materials"
    bl_idname = "crafter.open_materials"
    bl_description = " "
    
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

    def execute(self, context: bpy.types.Context):
        folder_path = dir_materials
        open_folder(folder_path)

        return {'FINISHED'}

# ==================== 打开分类依据文件夹 ====================

class VIEW3D_OT_CrafterOpenClassificationBasis(bpy.types.Operator):
    bl_label = "Open Classification Basis"
    bl_idname = "crafter.open_classification_basis"
    bl_description = " "
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

    def execute(self, context: bpy.types.Context):
        folder_path = dir_classification_basis
        open_folder(folder_path)

        return {'FINISHED'}

# ==================== 应用解析法向强度 ====================

class VIEW3D_OT_CrafterSetParsedNormalStrength(bpy.types.Operator):
    bl_label = "Set Parsed Normal Strength"
    bl_idname = "crafter.set_parsed_normal_strength"
    bl_description = " "
    
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True
    
    def execute(self, context: bpy.types.Context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences

        if "C-Parsed_Normal_Strength" in bpy.data.node_groups:
            node_group_C_Parsed_Normal_Strength = bpy.data.node_groups["C-Parsed_Normal_Strength"]
            for node in node_group_C_Parsed_Normal_Strength.nodes:
                if node.type == "GROUP_OUTPUT":
                    node_output = node
                    break
            node_output.inputs[0].default_value = addon_prefs.Parsed_Normal_Strength

        return {'FINISHED'}



# ==================== 刷新 ====================

class VIEW3D_OT_CrafterReloadMaterials(bpy.types.Operator):#刷新材质列表
    bl_label = "Reload Materials"
    bl_idname = "crafter.reload_materials"
    bl_description = " "
    
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

    def execute(self, context: bpy.types.Context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences

        addon_prefs.Materials_List.clear()
        for folder in os.listdir(dir_materials):
            base, extension = os.path.splitext(folder)
            if extension == ".blend":
                material_name = addon_prefs.Materials_List.add()
                material_name.name = base
        return {'FINISHED'}

class VIEW3D_OT_CrafterReloadClassificationBasis(bpy.types.Operator):#刷新分类依据菜单
    bl_label = "Reload Classification Basis"
    bl_idname = "crafter.reload_classification_basis"
    bl_description = " "
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

    def execute(self, context: bpy.types.Context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences

        addon_prefs.Classification_Basis_List.clear()
        for folder in os.listdir(dir_classification_basis):
            if os.path.isdir(os.path.join(dir_classification_basis, folder)):
                plan_name = addon_prefs.Classification_Basis_List.add()
                plan_name.name = folder

        return {'FINISHED'}

# ==================== UIList ====================

class VIEW3D_UL_CrafterMaterials(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {"DEFAULT","COMPACT"}:
            layout.label(text=item.name)

class VIEW3D_UL_CrafterClassificationBasis(bpy.types.UIList):
     def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {"DEFAULT","COMPACT"}:
            layout.label(text=item.name)
