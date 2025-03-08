import bpy
import os
import shutil

from .config import __addon_name__
from .i18n.dictionary import dictionary
from ...common.class_loader import auto_load
from ...common.class_loader.auto_load import add_properties, remove_properties
from ...common.i18n.dictionary import common_dictionary
from ...common.i18n.i18n import load_dictionary
from bpy.props import StringProperty, IntProperty, BoolProperty, IntVectorProperty, EnumProperty, CollectionProperty, FloatProperty
from .properties import ResourcePlan, ResourcePlansInfo, Material


# Add-on info
bl_info = {
    "name": "Crafter",
    "author": "Crafter Production Team [ 白给 若有来生 少年忠城 WangXinRui ]",
    "blender": (4, 2, 0),
    "version": (0, 0, 4),
    "description": "目标是成为从Minecraft到Blender全流程的Blender插件",
    "warning": "",
    "doc_url": "https://github.com/Crafter-Production-Team/Crafter?tab=readme-ov-file#crafter",
    "tracker_url": "https://github.com/Crafter-Production-Team/Crafter/issues",
    "support": "COMMUNITY",
    "category": "3D View"
}

_addon_properties = {
    bpy.types.Scene: {
        # "Crafter_rain":FloatProperty(name="Rain",
        #                            description="rain",
        #                            subtype="FACTOR",
        #                            min=0,
        #                            max=1,
        #                            default=0),
    },
    bpy.types.Object:{
        "Crafter_import_by": BoolProperty(name="import by Crafter",
                                          default=False),
        "Crafter_name": StringProperty(name="Crafter name",
                                       default="")
    }
}


# You may declare properties like following, framework will automatically add and remove them.
# Do not define your own property group class in the __init__.py file. Define it in a separate file and import it here.
# 注意不要在__init__.py文件中自定义PropertyGroup类。请在单独的文件中定义它们并在此处导入。
# _addon_properties = {
#     bpy.types.Scene: {
#         "property_name": bpy.props.StringProperty(name="property_name"),
#     },
# }

#==========初始化cafter_data地址==========
dir_extension = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dir_extensions = os.path.dirname(dir_extension)
dir_init_main = os.path.dirname(os.path.abspath(__file__))
dir_defaults = os.path.join(dir_init_main, "defaults")
dir_defaults_materials = os.path.join(dir_defaults, "materials")
dir_defaults_classification_basis = os.path.join(dir_defaults, "classification basis")
dir_blend_append = os.path.join(dir_defaults,"append.blend")

dir_cafter_data = os.path.join(dir_extensions, "cafter_data")
dir_resourcepacks_plans = os.path.join(dir_cafter_data, "resourcepacks")
dir_original = os.path.join(dir_resourcepacks_plans, "original")
dir_materials = os.path.join(dir_cafter_data, "materials")
dir_classification_basis = os.path.join(dir_cafter_data, "classification basis")
dir_classification_basis_default = os.path.join(dir_classification_basis, "default")

#==========注册==========
def register():
    # Register classes
    auto_load.init()
    auto_load.register()
    add_properties(_addon_properties)

    # Internationalization
    load_dictionary(dictionary)
    bpy.app.translations.register(__addon_name__, common_dictionary)

    #==========初始化cafter_data文件夹==========
    os.makedirs(dir_cafter_data, exist_ok=True)
    os.makedirs(dir_resourcepacks_plans, exist_ok=True)
    os.makedirs(dir_original, exist_ok=True)
    os.makedirs(dir_materials, exist_ok=True)
    os.makedirs(dir_classification_basis, exist_ok=True)
    os.makedirs(dir_classification_basis_default, exist_ok=True)
    #==========初始化默认方案==========
    for filename in os.listdir(dir_defaults_materials):
        src_file = os.path.join(dir_defaults_materials, filename)
        dest_file = os.path.join(dir_materials, filename)
        shutil.copy(src_file, dest_file)
    for filename in os.listdir(dir_defaults_classification_basis):
        src_file = os.path.join(dir_defaults_classification_basis, filename)
        dest_file = os.path.join(dir_classification_basis_default, filename)
        shutil.copy(src_file, dest_file)

    print("{} addon is installed.".format(__addon_name__))

#==========注销==========
def unregister():
    # #==========注销crafter_resource_icons==========
    # from .operators.AddonOperators import crafter_resources_icons
    # bpy.utils.previews.remove(crafter_resources_icons)
    # Internationalization
    bpy.app.translations.unregister(__addon_name__)
    # unRegister classes
    auto_load.unregister()
    remove_properties(_addon_properties)
    print("{} addon is uninstalled.".format(__addon_name__))
