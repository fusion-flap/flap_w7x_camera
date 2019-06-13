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
        flap.get_data('W7X_CAMERA',exp_id="20181018.032", name="AEQ20_EDICAM_ROIP2", options={'Time': '154804'}, object_name="cam")
    except Exception  as e:
        raise e

test_get_data()
flap.plot('cam',slicing={'Time':2},plot_type='image')