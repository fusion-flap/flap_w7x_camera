import unittest
import datetime
import numpy as np
import flap
import flap_w7x_camera

flap_w7x_camera.register()

#def test_register():
#    flap.register_data_source('W7X_CAMERA',
#                              get_data_func=w7x_camera.w7x_camera_get_data)
#    return 'W7X_WEBAPI' in flap.list_data_sources()


def test_get_data():
    try:
        flap.get_data('W7X_CAMERA',exp_id="20181018.032", name="AEQ20_EDICAM_ROIP1", options={'Time': '154804'}, object_name="EDI_ROIP1")
    except Exception as e:
        raise e
    flap.list_data_objects()
    flap.slice_data('EDI_ROIP1',slicing={'Time':0}, output_name='EDI_sliced')

test_get_data()
