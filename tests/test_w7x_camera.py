import unittest
import datetime
import numpy as np
import flap
import flap.modules.w7x_camera as w7x_camera


def test_register():
    flap.register_data_source('W7X_CAMERA',
                              get_data_func=w7x_camera.w7x_camera_get_data)
    return 'W7X_WEBAPI' in flap.list_data_sources()


def test_get_data():
    w7x_camera.w7x_camera_get_data(exp_id="20181018.032", data_name="AEQ20_EDICAM_ROIP1", options={'Datapath': '/data/W7-X/', 'Time': '154804', 'Max_size':4})
