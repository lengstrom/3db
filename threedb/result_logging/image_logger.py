"""
threedb.result_logging.image_logger
====================================

Subclass of :mod:`threedb.result_logging.base_logger.BaseLogger`.
"""

import importlib
from os import makedirs, path
from typing import Any, Dict, Type

import cv2
import numpy as np
from threedb.rendering.base_renderer import BaseRenderer
from threedb.result_logging.base_logger import BaseLogger
from threedb.utils import CyclicBuffer

class ImageLogger(BaseLogger):
    """
    This logger saves all the images generated by 3DB during a given experiment.

    The renderer should expose a static property ``KEYS`` (e.g.
    :prop:`threedb.rendering.render_blender.Blender.KEY`) that contains the
    dictionary keys that correspond to renderered images. For each key, images
    of that type are saved to an ``images/<KEY>`` subdirectory of the given
    logging directory.

    For more information on this, see [TODO].
    """

    def __init__(self,
                 save_dir: str,
                 result_buffer: CyclicBuffer,
                 config: Dict[str, Any]) -> None:
        """Initializes an ImageLogger

        Parameters
        ----------
        save_dir : str
            Parent directory in which the images will be saved (in an
            ``images/`` subdirectory)
        result_buffer : CyclicBuffer
            The buffer that is being written to by the policy controller
            containing all the results
        config : Dict[str, Any]
            Config that the experiment was run with (see `here 
            <quickstart.html#writing-a-configuration-file>`_ for information
            on config file format)
        """
        super().__init__(save_dir, result_buffer, config)
        engine = importlib.import_module(config['render_args']['engine'])
        rendering_module: Type[BaseRenderer] = getattr(engine, 'Renderer')
        self.save_keys = rendering_module.KEYS
        self.result_buffer = result_buffer
        self.regid = self.result_buffer.register()

        self.folder = path.join(save_dir, 'images/')
        if not path.exists(self.folder):
            makedirs(self.folder)
        print(f'==> [Logging images to {self.folder} with regid {self.regid}]')

    def log(self, item: Dict[str, Any]) -> None:
        """Implementation of ``log()`` for ImageLogger

        Parameters
        ----------
        item : Dict[str, Any]
            Writes the images (as dictated by the
            :property:``threedb.rendering.base_renderer.BaseRenderer.KEYS``
            field in the renderer) to the appropriate subdirectory.
        """
        rix = item['result_ix']
        buf_data = self.result_buffer[rix]
        for channel_name in self.save_keys:
            if not channel_name in buf_data.keys():
                continue

            image = buf_data[channel_name]
            if channel_name == 'segmentation':
                img_name = item['id'] + '_' + channel_name + '.npy'
                img_path = path.join(self.folder, img_name)
                np.save(img_path, image.numpy()[0])
            else:
                img_name = item['id'] + '_' + channel_name + '.png'
                img_path = path.join(self.folder, img_name)
                img_arr = image.permute(1, 2, 0).numpy() * 255.0
                img_to_write = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
                cv2.imwrite(img_path, img_to_write)
        self.result_buffer.free(rix, self.regid)
    
    def end(self) -> None:
        pass

Logger = ImageLogger
