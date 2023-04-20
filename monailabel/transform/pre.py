# Copyright (c) MONAI Consortium
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import Optional

from monai.config import KeysCollection
from monai.data import ImageReader, MetaTensor
from monai.transforms import LoadImaged, MapTransform
from monai.utils import PostFix

logger = logging.getLogger(__name__)


class LoadImageTensord(MapTransform):
    def __init__(self, keys: KeysCollection, allow_missing_keys: bool = False, load_image_d=None) -> None:
        """
        MapTransform that loads images from file paths or numpy arrays into MetaTensors.

        Args:
            keys: keys of the data dictionary to be transformed.
            allow_missing_keys: whether to allow missing keys in the data dictionary.
            load_image_d: a default function to load images if all the keys are not present.
        """
        super().__init__(keys, allow_missing_keys)
        self.load_image_d = load_image_d

    def __call__(self, data):
        """
        Transforms the input data dictionary by loading images into MetaTensors.

        Args:
            data: a dictionary of input data.

        Returns:
            A dictionary of transformed data with the same keys as the input data.
        """
        d = dict(data)

        use_default = True
        for key in self.keys:
            if isinstance(d[key], str):
                # Load image from file path
                image_np = np.asarray(Image.open(d[key]))
            else:
                # Convert numpy array to MetaTensor
                meta_dict_key = f"{key}_{PostFix.meta()}"
                meta_dict = d.setdefault(meta_dict_key, {})
                meta_dict["spatial_shape"] = d[key].shape[:-1]
                meta_dict["original_channel_dim"] = -1
                meta_dict["original_affine"] = None
                image_np = d[key]
                d[key] = MetaTensor(image_np, meta=meta_dict)
                use_default = False

        if use_default:
            # Load default image if all keys are not present
            d = self.load_image_d(d)

        return d


class LoadImageExd(LoadImaged):
    def __call__(self, data, reader: Optional[ImageReader] = None):
        """
        Transforms the input data dictionary by loading images from file paths or numpy arrays into MetaTensors.

        Args:
            data: a dictionary of input data.
            reader: an optional ImageReader to read images from file paths.

        Returns:
            A dictionary of transformed data with the same keys as the input data.
        """
        d = dict(data)

        direct_image = False
        for i, key in enumerate(self.keys):
            if isinstance(d[key], np.ndarray):
                # Convert numpy array to MetaTensor
                direct_image = True
                meta_dict_key = f"{key}_{self.meta_key_postfix[i]}"
                meta_dict = d.setdefault(meta_dict_key, {})
                meta_dict["spatial_shape"] = d[key].shape[:-1]
                meta_dict["original_channel_dim"] = -1
                meta_dict["original_affine"] = None
                image_np = d[key]
                d[key] = MetaTensor(image_np, meta=meta_dict)

        if not direct_image:
            # Load images from file paths using the parent class method
            d = super().__call__(d, reader)

        return d



class NormalizeLabeld(MapTransform):
    def __init__(self, keys: KeysCollection, allow_missing_keys: bool = False, value=1) -> None:
        """
        MapTransform that normalizes label images by setting all non-zero values to a specified value.

        Args:
            keys: keys of the data dictionary to be transformed.
            allow_missing_keys: whether to allow missing keys in the data dictionary.
            value: the value to set non-zero pixels to.
        """
        super().__init__(keys, allow_missing_keys)
        self.value = value

    def __call__(self, data):
        """
        Transforms the input data dictionary by normalizing the label images.

        Args:
            data: a dictionary of input data.

        Returns:
            A dictionary of transformed data with the same keys as the input data.
        """
        d = dict(data)
        for key in self.keys:
            label = d[key]
            label[label > 0] = self.value
            d[key] = label
        return d

