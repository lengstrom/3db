import subprocess
import shutil
from pathlib import Path
import copy
import functools
from ruamel.yaml import YAML

ryaml = YAML()

zsh = functools.partial(subprocess.call, shell=True, executable='/usr/bin/zsh')

base_yaml = {
    'base_config': 'base.yaml',
    'controls': [
        {
            'module': 'threedb.controls.blender.camera',
            'view_point_x': 0.,
            'view_point_y': 0.,
            'view_point_z': 0.,
            'zoom_factor': 1,
            'aperture': 5.,
            'focal_length': 100.
        }
    ],
    'logging': {
        'logger_modules': [
            "threedb.result_logging.image_logger"
        ]
    }
}

denoiser = {
    'module': 'threedb.controls.blender.denoiser'
}

obj_loc_in_frame = {
    'module': 'threedb.controls.blender.obj_loc_in_frame',
    'x_shift': (-1., 1.0),
    'y_shift': (-1, 1.0)
}

chungus = None

control_to_yaml = {
    'obj_loc_in_frame': obj_loc_in_frame,
    'denoiser': chungus,
    'no_denoiser': chungus,
    'background': {
        'module': 'threedb.controls.blender.background',
        'H':(0., 1.),
        'S':(0., 1.),
        'V':(0., 1.)
    },
    'camera': {
        'module': 'threedb.controls.blender.camera',
        'view_point_x': (-1., 1.),
        'view_point_y': (-1., 1.),
        'view_point_z': (0., 1.),
        'zoom_factor': (0.5, 2.),
        'aperture': (1., 32.),
        'focal_length': (10, 400)
    },
    'imagenet_c': {
        'module': 'threedb.controls.blender.imagenet_c',
        'corruption_name': ['impulse_noise'],
        'severity': [1, 2, 3, 4, 5]
    },
    'material': {
        'module': 'threedb.controls.blender.material',
        'replacement_material': [
            'skin-crocodile.blend',
            'skin-elephant.blend',
            'skin-leopard.blend',
            'skin-tiger.blend',
            'keep_original'
        ]
    },
    'occlusion': {
        'module': 'threedb.controls.blender.occlusion',
        'occlusion_ratio': (0.3, 0.6),
        'zoom': (.1, .4),
        'scale': (.04, .07),
        'direction': [0, 1, 2, 3, 4, 5, 6, 7],
        'occluder': [
            '000b76f2b03e44e8ab44e1a1614be0f4.blend',
            '000ff3a4edcb41d8a511850d49e171af.blend',
            '001f16707683405cb2340cd7194b7eba.blend',
            '00327d46729043cb9b06bd0ca6ffb344.blend',
            '003725c9dd7d47ada2b2a2ced2f23953.blend'
        ]
    },
    'orientation': {
        'module': 'threedb.controls.blender.orientation',
        'rotation_X': (-3.14, 3.14),
        'rotation_Y': (-3.14, 3.14),
        'rotation_Z': (-3.14, 3.14)
    },
    'pin_to_ground': {
        'module': 'threedb.controls.blender.pin_to_ground',
        'z_ground': (0.0, 0.03)
    },
    'position': {
        'module': 'threedb.controls.blender.position',
        'offset_x': (-0.02, .02),
        'offset_y': (-0.02, .02),
        'offset_z': (-0.02, .02)
    },
    'scale': {
        'module': 'threedb.controls.blender.scale',
        'factor': (0.25, 1.)
    }
}

def listify(obj):
    if obj is None:
        return obj

    for k, v in obj.items():
        if type(v) is tuple:
            obj[k] = list(v)

    return obj

for k, v in control_to_yaml.items():
    control_to_yaml[k] = listify(v)

SHOULD_REMOVE_DENOISER = ['no_denoiser']
SHOULD_REMOVE_DENOISER = ['no_denoiser']
SHOULD_REMOVE_CAMERA = ['camera']
# ONLY MISSING MATERIAL
# docs/_static/logs/position/images
# `position`
# `pin_to_ground`
# `occlusion`

def make_unit_test_yaml(name, add_denoiser=None, remove_camera=None):
    if add_denoiser is None:
        add_denoiser = not (name in SHOULD_REMOVE_DENOISER)
    
    if remove_camera is None:
        remove_camera = (name in SHOULD_REMOVE_CAMERA)

    control = control_to_yaml[name]
    base = copy.deepcopy(base_yaml)

    if remove_camera:
        base['controls'].pop()

    if add_denoiser:
        base['controls'].append(denoiser)

    if control is not None:
        base['controls'].append(control)

    return base

import yaml
client = open('sandbox_client.sbatch', 'r').readlines()
def client_maker(name):
    new_lines = []
    for l in client:
        if '#' in l:
            l = l.replace('log.log', f'{name}_log.log')
            l = l.replace('aiilyas/slurm/logs', 'engstrom/slurm_logs')
            l = l.replace('job-name=sandbox', f'job-name={name}')

        new_lines.append(l)

    sbatch_fp = f'/tmp/synthetic_sbox_{name}'
    with open(sbatch_fp, 'w+') as f:
        f.write(''.join(new_lines))

    return sbatch_fp

def make_unit_test_sbatch(name, add_denoiser=None, remove_camera=None):
    unit_test = make_unit_test_yaml(name, add_denoiser=add_denoiser,
                                    remove_camera=None)
    config_file = f'examples/unit_tests/{name}.yaml'
    with open(config_file, 'w+') as f:
        yaml.dump(unit_test, f, default_flow_style=None)

    out_path = Path(f'docs/_static/logs/{name}')
    if out_path.exists():
        shutil.rmtree(out_path)
    out_path.mkdir()

    client_path = client_maker(name)

    preamble = 'BLENDER_DATA=~/store/3db_unit_tests'
    preamble = f'{preamble} OUTPUT_FOLDER={out_path} YAML_CONFIG={config_file}' 
    cmd = f'{preamble} sbatch {client_path}'
    zsh(cmd)
    print(cmd)

for k in control_to_yaml.keys():
    make_unit_test_sbatch(k)