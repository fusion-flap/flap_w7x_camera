# -*- coding: utf-8 -*-
"""
Created on Tue May 14 14:14:14 2019

@author: Csega

This is the flap module for W7-X camera diagnostic
(including EDICAM and Photron HDF5)
"""

import os.path
import flap
import numpy as np
import copy
import h5py
import pylab as plt


def get_camera_config_h5(h5_obj, roi_num):
    """
    This function parses the Settings field of the HDF5 file (if available)
    and counts the ROIPs with data. This latter will determine
    the channel names.
    """
    info = dict()
    # Get the actual data
    # print(list(h5_obj.keys()))
    # print(list(h5_obj['Settings'].keys()))
    # TODO: integrate events!
    # TODO: finish the config read!
    info['Clock'] = dict()
    info['Clock']['Auto int'] = np.array(h5_obj['Settings']['Clock']['Auto int'])[0]
    info['Clock']['Clk pol'] = np.array(h5_obj['Settings']['Clock']['Clk pol'])[0]
    info['Clock']['Enable'] = np.array(h5_obj['Settings']['Clock']['Enable'])[0]
    info['Clock']['PLL div'] = np.array(h5_obj['Settings']['Clock']['PLL div'])
    info['Clock']['PLL mult'] = np.array(h5_obj['Settings']['Clock']['PLL mult'])
    info['Clock']['Quality'] = np.array(h5_obj['Settings']['Clock']['Quality'])
    info['Event'] = dict()
    info['Event']['Event1'] = h5_obj['Settings']['Event']['Event1']['Action1'].keys()
    print(list(h5_obj['Settings']['Event']['Event1'].keys()))
    print(list(h5_obj['Settings']['Event']))
    print(list(h5_obj['Settings']['Event'].keys()))
    print(info['Event']['Event1'])
    info['Exposure Settings'] = h5_obj['Settings']['Exposure Settings']
    info['Image Processing Settings'] = h5_obj['Settings']['Image Processing Settings']
    info['ROIP'] = h5_obj['Settings']['ROIP']
    info['Sensor Control'] = h5_obj['Settings']['Sensor Control']
    info['Sensor Settings'] = h5_obj['Settings']['Sensor Settings']
    info['X Start'] = h5_obj['Settings']['ROIP'][roi_num]['X Start'][0]
    info['X Len'] = h5_obj['Settings']['ROIP'][roi_num]['X Len'][0]
    info['Y Start'] = h5_obj['Settings']['ROIP'][roi_num]['Y Start'][0]
    info['Y Len'] = h5_obj['Settings']['ROIP'][roi_num]['Y Len'][0]

    print("-------------------------")
    print(info)
    return info


def get_camera_config_ascii(path):
    """
    This function parses an ASCII file containing the settings of and
    EDICAM or a Photron camera recording.
    """
    info = dict()
    print("In get_camera_config_ascii.")
    # Get the actual settings
    # TODO: implement this!
    return info


def read_hdf5_arr(h5_data, x, y, frame_vec):
    """
    h5_data is a HDF5 dataset object (opened with a known path)
    indices is an array in the form of (x_start:x_end, y_start:y_end, time_slices)
    x: (startx, endx)
    y: (starty, endy)
    # frame_num: (start_frame, end_frame)
    frame_vec: [frame_num1, frame_num2, frame_num3, ...]
    """
    (startx, endx) = x
    (starty, endy) = y
    frame_vec = np.array(frame_vec)

    # low level frame reading
    data_space = h5_data.get_space()
    # dims = data_space.shape
    arr_full = np.zeros((endx - startx, endy - starty, frame_vec.shape[0]), dtype=h5_data.dtype)
    arr = np.zeros((endx - startx, endy - starty), dtype=h5_data.dtype)
    count = (endx, endy, 1)
    h_i = 0  # helper indexer

    for frame_num in frame_vec:
        start = (startx, starty, frame_num)
        end = count
        data_space.select_hyperslab(start, end)
        result_space = h5py.h5s.create_simple(count)
        h5_data.read(result_space, data_space, arr)
        arr_full[:, :, h_i] = arr
    
    return arr_full


def w7x_camera_get_data(exp_id=None, data_name=None, no_data=False, options=None, coordinates=None):
    """ Data read function for the W7-X EDICAM and Photron cameras (HDF5 format)
    data_name: Usually AEQ21_PHOTRON_ROIPx, ... (string) depending on configuration file
    exp_id: Experiment ID, YYYYMMDD.xxx, e.g. 20181018.016
    Options:
            Datapath: the base path at which the camera files can be found (e.g. /data/W7X)
            Time: the date and time the recording was made: 123436 (12:34:36)
            Camera name: either EDICAM or PHOTRON
            Port: the port number the camera was used, e.g. AEQ20
    """

    default_options = {'Datapath': '',
                       'Time': None,
                       'Max_size': None  # in GB!
                       }
    _options = flap.config.merge_options(default_options, options, data_source='W7X_CAMERA')

    name_split = data_name.split("_")
    port = name_split[0]
    cam_name = name_split[1]
    roi_num = name_split[2]

    datapath = _options['Datapath']
    time = _options['Time']
    max_size = _options['Max_size']

    if port is None:
        raise ValueError("Port name and number should be set for W7X camera! (E.g. AEQ20)")
    elif 'aeq' not in port.lower():
        raise ValueError("Port name should contain AEQ!")

    if cam_name is None:
        raise ValueError("Camera name should be set for W7X camera!")
    elif cam_name.lower() == "edicam":
        cam_str = "edi"
    elif cam_name.lower() == "photron":
        cam_str = "phot"
    else:
        raise ValueError("Camera name should be either EDICAM or PHOTRON, not {}.".format(cam_name))

    if (exp_id is None) or (time is None):
        raise ValueError('Both exp_id and Time should be set for W7X camera for now.')
    else:  # yeah, yeah, just to cover all the cases
        exp_id_split = exp_id.split('.')
        date = exp_id_split[0]
        exp_num = exp_id_split[1]
        filename = "_".join([port.upper(), cam_str, date, exp_num, (time + ".h5")])

        path = os.path.join(datapath, cam_name.upper(), port.upper(), date, filename)
        if flap.VERBOSE:
            print("The constructed path is: {}.".format(path))

        if not os.path.exists(path):
            filename = "_".join([port.upper(), cam_str, date, (time + ".h5")])
            path = os.path.join(datapath, cam_name.upper(), port.upper(), date, filename)
            print("Not found the file, trying an alternative path: {}.".format(path))
            if not os.path.exists(path):
                raise FileNotFoundError

    file_size = os.path.getsize(path)  # in bytes!
    file_size = file_size / 1024**3  # in GB
    
    if file_size > max_size:
        print("The size of {} is too large. (size: {} GB, limit: {} GB.)".format(path, file_size, max_size))
        raise IOError("File size is too large!")

    # Getting the file info
    with h5py.File(path, 'r') as h5_obj:
            try:
                info = get_camera_config_h5(h5_obj, roi_num)
            except Exception as e:
                print("Camera config is not found:")
                print(e)
                try:
                    info = get_camera_config_ascii(path)
                except Exception as e:
                    print("Cannot read the info file!")
                    print(e)
            finally:
                if info is None:
                    info = dict()

    print(info)

    # Read the time vectors
    with h5py.File(path, 'r') as h5_obj:
        try:
            time_vec_etu = np.array(h5_obj['ROIP']['{}'.format(roi_num.upper())]['{}ETU'.format(roi_num.upper())])
            print("ETU time vector found!")
        except Exception as e:
            print("Cannot read ETU! Error message:")
            print(e)
            time_vec_etu = None
        try:
            time_vec_w7x = np.array(h5_obj['ROIP']['{}'.format(roi_num.upper())]['{}W7XTime'.format(roi_num.upper())])
            print("W7-X time vector found!")
        except Exception as e:
            print("Cannot read W7-X time units (ns)! Error message:")
            print(e)
            time_vec_w7x = None
        
        if time_vec_w7x is not None:
            print("Using W7-X time vector [ns] for time vector [s] calculation!")
            time_vec_sec = (time_vec_w7x - time_vec_w7x[0]) / 1.e9
        elif time_vec_etu is not None:
            print("Using ETU time vector [100 ns] for time vector [s] calculation!")
            time_vec_sec = (time_vec_etu - time_vec_etu[0]) / 1.e7
        else:
            print("Cannot find any meaningful time vector!")
            print("Exiting...")
            raise IOError("No time vector found!")

    if no_data:
        data_arr = None
    else:
        # Open the file and check the data path and read the data
        try:
            h5_obj = h5py.h5f.open(path.encode('utf-8'))
            print(roi_num)
            h5_path = '/ROIP/{}/{}Data'.format(roi_num.upper(), roi_num.upper())
            print("Opening {} with path {}.".format(roi_num.upper(), h5_path))
            h5_data = h5py.h5d.open(h5_obj, h5_path.encode('utf-8'))
            print("Data size: {}.".format(h5_data.shape))
        except Exception as e:
            print("Something bad happened:")
            print(e)
        
        # Read the data
        data_space = h5_data.get_space()
        dims = data_space.shape
        if coordinates == None:
            # Indices contain everything!
            x = (0, dims[0])
            y = (0, dims[1])
            frame_vec = np.arange(0, dims[2])
            data_arr = read_hdf5_arr(h5_data, x, y, frame_vec)
        else:
            # Take indices from the coordinates!
            # Only time coordinates are working as of now (2019. June 11.)
            if (type(coordinates) is not list):
             _coordinates = [coordinates]
            else:
                _coordinates = coordinates
            for coord in _coordinates:
                if (type(coord) is not flap.Coordinate):
                    raise TypeError("Coordinate description should be flap.Coordinate.")
                if (coord.unit.name is 'Time'):  # assuming the unit to be Second
                    if (coord.unit.unit is not 'Second'):
                        raise NotImplementedError("Your time coordinate unit is not in Seconds! Cannot use it (yet).")
                    if (coord.mode.equidistant):
                        read_range = [float(coord.c_range[0]),float(coord.c_range[1])]
                        # Since np.where gives back indices, it is the same as the frame_vec
                        frame_vec = np.where((time_vec_sec >= read_range[0]) & (time_vec_sec <= read_range[1]))
                    else:
                        # TODO: implement this, we need it!
                        # TODO: construct the frame_num vector!
                        frame_vec = None
                        raise NotImplementedError("Non-equidistant Time axis is not implemented yet.")
            
            # TODO: make this for the spatial coordinates as well! (Binning etc.)
            x = (0, dims[0])
            y = (0, dims[1])
            data_arr = read_hdf5_arr(h5_data, x, y, frame_vec)
        h5_obj.close()

    # Even if we have no_data=True, we need to know the coordinate ranges!
    data_dim = 1  # What is this???
    read_range = None  # What is this???
    coord = [None] * data_dim * 6
    print(time_vec_sec)
    print(data_arr.shape)
    print(time_vec_sec.shape)
    # TODO: check for equidistant time coordinates!
    coord[0] = copy.deepcopy(flap.Coordinate(name='Time',
                                             unit='Second',
                                             mode=flap.CoordinateMode(equidistant=False),
                                             values=time_vec_sec,
                                             shape=time_vec_sec.shape,
                                             dimension_list=[2])
                             )
    coord[1] = copy.deepcopy(flap.Coordinate(name='ETUTime',
                                             unit='ETU',
                                             mode=flap.CoordinateMode(equidistant=False),
                                             values=time_vec_etu,
                                             shape=time_vec_etu.shape,
                                             dimension_list=[2])
                             )
    coord[2] = copy.deepcopy(flap.Coordinate(name='W7XTime',
                                             unit='Nanosecond',
                                             mode=flap.CoordinateMode(equidistant=False),
                                             values=time_vec_w7x,
                                             shape=time_vec_w7x.shape,
                                             dimension_list=[2])
                             )
    coord[3] = copy.deepcopy(flap.Coordinate(name='Sample',
                                             unit='',
                                             mode=flap.CoordinateMode(equidistant=False),
                                             values=frame_vec,
                                             shape=frame_vec.shape,
                                             dimension_list=[2])
                             )
    coord[4] = copy.deepcopy(flap.Coordinate(name='Image x',
                                             unit='Pixel',
                                             mode=flap.CoordinateMode(equidistant=True),
                                             start=int(info['X Start']),
                                             step=int(1),
                                             shape=[],
                                             dimension_list=[0])
                             )
    coord[5] = copy.deepcopy(flap.Coordinate(name='Image y',
                                             unit='Pixel',
                                             mode=flap.CoordinateMode(equidistant=True),
                                             start=int(info['Y Start']),
                                             step=int(1),
                                             shape=[],
                                             dimension_list=[1])
                             )

    data_title = "W7-X CAMERA data: {}".format(data_name)
    d = flap.DataObject(data_array=data_arr,
                        data_unit=flap.Unit(name='Frame', unit='Digit'),
                        coordinates=coord,
                        exp_id=exp_id,
                        data_title=data_title,
                        info={'Options':_options},
                        data_source="W7X_CAMERA")
    return d


def add_coordinate(data_object, new_coordinates, options=None):
    raise NotImplementedError("Coordinate conversions not implemented yet.")

def register():
    flap.register_data_source('W7X_CAMERA',
                              get_data_func=w7x_camera_get_data)
