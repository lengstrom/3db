"""Defines the MaterialControl Blender Control"""

from os import path
from glob import glob

from threedb.controls.base_control import BaseControl


class MaterialControl(BaseControl):
    """Control that swap material of an object with another one

    Discrete Dimensions
    -------------------
    replacement_material
        The name of the material that will be replacing the original one

    Note
    ----
    The possible values for `replacement_material` can be any file
    (without `.blend`) found in ROOT_FOLDER/blender_control_material.

    Each of these file should have a single material in it otherwise it
    is ambiguous which material should be applied to the object
    """
    kind = 'pre'

    continuous_dims = {}

    discrete_dims = {
        "replacement_material": None
    }

    def __init__(self, root_folder):
        super().__init__(root_folder)
        self.files_in_folder = list(sorted(glob(path.join(
            root_folder,
            'blender_control_material',
            '*.blend'))))

        self.root_folder = root_folder
        self.files_in_folder.append('keep_original')
        self.files_in_folder = [x.replace(root_folder, '') for x in self.files_in_folder]
        self.discrete_dims["replacement_material"] = self.files_in_folder


    def apply(self, context, replacement_material: str):
        """Replace the material of the target object with the material
        corresponding to `replacement_material`

        Parameters
        ----------
        context
            The blender scene context
        replaced_materials
            The name of the material to apply
        """
        import bpy

        state = {
            'added_materials': [],
            'replaced_materials': []
        }

        context['material_control_state'] = state

        if replacement_material == "keep_original":
            return

        fname = path.join(self.root_folder, replacement_material)
        current_materials = set(x.name for x in bpy.data.materials)

        with bpy.data.libraries.load(fname) as (data_from, data_to):
            for material in data_from.materials:
                if material not in current_materials:
                    state['added_materials'].append(material)
                    data_to.materials.append(material)

        if len(state['added_materials']) != 1:
            raise Exception(f"File {fname} contains more than one material")

        replacing_with = state['added_materials'][0]

        for slot in context['object'].material_slots:
            try:
                state['replaced_materials'].append(slot.material.name)
            except:
                state['replaced_materials'].append(None)

            slot.material = bpy.data.materials[replacing_with]



    def unapply(self, context):
        import bpy

        state = context['material_control_state']

        for slot, material_name in zip(context['object'].material_slots,
                                       state['replaced_materials']):

            if material_name is None:
                slot.material = None
            else:
                slot.material = bpy.data.materials[material_name]

        for material_name in state['added_materials']:
            bpy.data.materials.remove(bpy.data.materials[material_name])


BlenderControl = MaterialControl
