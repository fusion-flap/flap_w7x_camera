# -*- coding: utf-8 -*-
"""
Created on Tue May 14 14:14:14 2019

@author: Csega

This is the flap module for W7-X camera diagnostic
(including EDICAM and Photron HDF5)
"""

import os.path
import fnmatch
import numpy as np
import copy
import h5py
import pylab as plt
import scipy.io as io

import flap



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
    if (type(frame_vec) is not np.ndarray):
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
        h_i = h_i + 1
    
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

    default_options = {'Datapath': 'data',
                       'Timing path': 'data',
                       'Time': None,
                       'Max_size': 4  # in GB!
                       }
    _options = flap.config.merge_options(default_options, options, data_source='W7X_CAMERA')

    name_split = data_name.split("_")
    port = name_split[0]
    cam_name = name_split[1].upper()
    roi_num = name_split[2]

    datapath = _options['Datapath']
    time = _options['Time']
    max_size = _options['Max_size']
    timing_path = _options['Timing path']

    if (coordinates is None):
        _coordinates = []
    else:
        if (type(coordinates) is not list):
            _coordinates = [coordinates]
        else:
            _coordinates = coordinates

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

    if (exp_id is None):
        raise ValueError('Both exp_id should be set for W7X camera.')
    exp_id_split = exp_id.split('.')
    date = exp_id_split[0]
    exp_num = exp_id_split[1]
    dp = os.path.join(datapath, cam_name.upper(), port.upper(), date)
    dp_timing = os.path.join(timing_path,date)
    flist = os.listdir(dp)
    for i in range(len(flist)):
        flist[i] = flist[i].upper()

    if (time is None):
        filename_mask = "_".join([port.upper(), cam_str, date, exp_num, ("*.h5")])
    else:
        filename_mask = "_".join([port.upper(), cam_str, date, exp_num, (time + ".h5")])
    filename_mask = filename_mask.upper()
    fnames = fnmatch.filter(flist, filename_mask)
    if (len(fnames) > 1):
        if (time is not None):
            raise ValueError("Multiple files found, 'Time' option should be set?")
        else:
            raise ValueError("Multiple files found:{:s}.".format(os.path.join(dp,filename_mask))) 
    elif (len(fnames) == 0):
        if (time is not None):
            filename_mask = "_".join([port.upper(), cam_str, date, (time + ".h5")])
            filename_mask = filename_mask.upper()
            fnames = fnmatch.filter(flist, filename_mask)
            if (len(fnames) == 0):
                raise ValueError("Cannot find any file for this measurement.")
            else:
                time = fnames[0].split('_')[3]
                time = time.split('.')[0]
        else:
            raise ValueError("Cannot find file without time parameter. Filename mask:"+filename_mask+" dp:"+dp)
    else:
        time = fnames[0].split('_')[4]
        time = time.split('.')[0]
        
    path = os.path.join(dp,fnames[0]) 

    if (cam_name == 'EDICAM'):
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
                #print("ETU time vector found!")
            except Exception as e:
                print("Cannot read ETU! Error message:")
                print(e)
                time_vec_etu = None
            try:
                time_vec_w7x = np.array(h5_obj['ROIP']['{}'.format(roi_num.upper())]['{}W7XTime'.format(roi_num.upper())])
                #print("W7-X time vector found!")
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
    
        # Open the file and check the data path and read the data
        try:
            h5_obj = h5py.h5f.open(path.encode('utf-8'))
            # print(roi_num)
            h5_path = '/ROIP/{}/{}Data'.format(roi_num.upper(), roi_num.upper())
            # print("Opening {} with path {}.".format(roi_num.upper(), h5_path))
            h5_data = h5py.h5d.open(h5_obj, h5_path.encode('utf-8'))
            # print("Data size: {}.".format(h5_data.shape))
        except Exception as e:
            print("Something bad happened:")
            print(e)
        
        # Read the data
        data_space = h5_data.get_space()
        dims = data_space.shape
        if coordinates == None:
            # Indices contain everything!
            frame_vec = np.arange(0, dims[2])
        else:
            # Take indices from the coordinates!
            # Only time coordinates are working as of now (2019. June 11.)
            for coord in _coordinates:
                if (type(coord) is not flap.Coordinate):
                    raise TypeError("Coordinate description should be flap.Coordinate.")
                if (coord.unit.name is 'Time'):  # assuming the unit to be Second
    #                if (coord.unit.unit is not 'Second'):
    #                    raise NotImplementedError("Your time coordinate unit is not in Seconds! Cannot use it (yet).")
                    if (coord.c_range is None):
                        raise NotImplementedError("At present only simple tie range selection is supported.")
                    read_range = [float(coord.c_range[0]),float(coord.c_range[1])]
                    # Since np.where gives back indices, it is the same as the frame_vec
                    n_frames = len(time_vec_sec)
                    frame_vec = np.where((time_vec_sec >= read_range[0]) & (time_vec_sec <= read_range[1]))[0]
                    time_vec_sec = time_vec_sec[frame_vec]
                    time_vec_etu = time_vec_etu[frame_vec]
                    time_vec_w7x = time_vec_w7x[frame_vec]
                else:
                    raise NotImplementedError("Coordinate selection for image coordinates is not supported yet.")
            
            dt = time_vec_sec[1:] - time_vec_sec[0:-1]
            if (np.nonzero((np.abs(dt[0] - dt) / dt[0]) > 0.001)[0].size == 0):
                time_equidistant = True
                time_step = dt[0]
                time_start = time_vec_sec[0]
            else:
                time_equidistant = False
        # TODO: make this for the spatial coordinates as well! (Binning etc.)
        x = (0, dims[0])
        y = (0, dims[1])
        # We will set data_shape in flap.DataObject to show what the shape would be if data was read
        if (no_data):
            data_arr = None
            data_shape = (dims[0],dims[1],len(frame_vec))
        else:
            file_size = os.path.getsize(path)  # in bytes!
            file_size = file_size / 1024**3  # in GB
            fraction = len(frame_vec) / n_frames            
            if file_size * fraction > max_size:
                print("The expected read size from {} is too large. (size: {} GB, limit: {} GB.)".format(path, file_size * fraction, max_size))
                raise IOError("File size is too large!")          
            data_arr = read_hdf5_arr(h5_data, x, y, frame_vec)
            data_shape = data_arr.shape
        h5_obj.close()
    elif (cam_name == 'PHOTRON'):
        time_fn = os.path.join(dp_timing,"_".join([port, cam_str, date, time, 'integ', ('v1' + ".sav")])) 
        time_fn = time_fn.replace('\\','/',)
        try:
            idldat = io.readsav(time_fn,python_dict=True,verbose=False)
        except IOError as e:
            raise IOError("Error reading file {:s}.".format(time_fn))
        time_vec_sec = idldat['resa'][0][4]
        time_vec_etu = None
        time_vec_w7x = None
        frame_per_trig = idldat['resa'][0][15]['frame_per_trig'][0]
        rec_rate = idldat['resa'][0][15]['rec_rate'][0]
        trig_times = []
        for i in range(0,len(time_vec_sec),frame_per_trig):
            trig_times.append(time_vec_sec[i])
        trig_times = np.array(trig_times)
        meas_end_times = trig_times + 1. / rec_rate * (frame_per_trig - 1)
                # Open the file and check the data path and read the data
        try:
            h5_obj = h5py.h5f.open(path.encode('utf-8'))
            # print(roi_num)
            h5_path = '/ROIP/{}/{}Data'.format(roi_num.upper(), roi_num.upper())
            # print("Opening {} with path {}.".format(roi_num.upper(), h5_path))
            h5_data = h5py.h5d.open(h5_obj, h5_path.encode('utf-8'))
            # print("Data size: {}.".format(h5_data.shape))
        except Exception as e:
            print("Something bad happened:")
            print(e)        
        data_space = h5_data.get_space()
        dims = data_space.shape
        if (dims[2] != len(time_vec_sec)):
            RuntimeError("Frame number in HDF5 file and time file are different.")
        n_frames = dims[2]
        for coord in _coordinates:
            if (type(coord) is not flap.Coordinate):
                raise TypeError("Coordinate description should be flap.Coordinate.")
            if (coord.unit.name is 'Time'):  # assuming the unit to be Second
        #                if (coord.unit.unit is not 'Second'):
        #                    raise NotImplementedError("Your time coordinate unit is not in Seconds! Cannot use it (yet).")
                if (coord.c_range is None):
                    raise NotImplementedError("At present only simple tie range selection is supported.")
                read_range = [float(coord.c_range[0]),float(coord.c_range[1])]
                # Since np.where gives back indices, it is the same as the frame_vec
                frame_vec = np.nonzero(np.logical_and((time_vec_sec >= read_range[0]),(time_vec_sec < read_range[1])))[0]
                if (len(frame_vec) == 0):
                    raise ValueError("No data in time range.")
                start_block = int(frame_vec[0] // frame_per_trig)
                end_block = int(frame_vec[-1] // frame_per_trig)
                if (end_block == start_block):
                    time_equidistant  = True
                    time_step = 1./rec_rate
                    time_start = time_vec_sec[frame_vec[0]]
                else:
                    time_equidistant = False
            else:
                raise NotImplementedError("Coordinate selection for image coordinates is not supported yet.")
        try:
            frame_vec
        except NameError:
            frame_vec = np.arange(len(time_vec_sec),dtype=np.int32)
            if (len(trig_times) != 1):
                time_equidistant = False
            else:
                time_equidistant = True
                   
        x = (0, dims[0])
        y = (0, dims[1])
        info = {}
        with h5py.File(path, 'r') as h5_obj_config:
            try:
                info['X Start'] = h5_obj_config['Settings']['X pos'][0]
                info['Y Start'] = h5_obj_config['Settings']['Y pos'][0]
            except Exception as e:
                raise IOError("Could not find ROI x and y position in HDF5 file.")
  
        # We will set data_shape in flap.DataObject to show what the shape would be if data was read
        if (no_data):
            data_arr = None
            data_shape = (dims[0],dims[1],len(frame_vec))
        else:
            file_size = os.path.getsize(path)  # in bytes!
            file_size = file_size / 1024**3  # in GB
            fraction = len(frame_vec) / n_frames            
            if file_size * fraction > max_size:
                print("The expected read size from {} is too large. (size: {} GB, limit: {} GB.)".format(path, file_size * fraction, max_size))
                raise IOError("File size is too large!")          
            data_arr = read_hdf5_arr(h5_data, x, y, frame_vec)
            data_arr = np.flip(data_arr,axis=0)
            data_shape = data_arr.shape
        h5_obj.close()
    else:
        raise ValueError("Invalid camera name.")
    coord = []
    # TODO: check for equidistant time coordinates!
    if (time_equidistant):
        coord.append(copy.deepcopy(flap.Coordinate(name='Time',
                                                   unit='Second',
                                                   mode=flap.CoordinateMode(equidistant=True),
                                                   start = time_start, 
                                                   step = time_step,
                                                   shape=[],
                                                   dimension_list=[2]
                                                   )
                                    )          
                    )
    else:
        coord.append(copy.deepcopy(flap.Coordinate(name='Time',
                                                   unit='Second',
                                                   mode=flap.CoordinateMode(equidistant=False),
                                                   values = time_vec_sec, 
                                                   shape=time_vec_sec.shape,
                                                   dimension_list=[2]
                                                   )
                                    )          
                    )
        
        
    if (time_vec_etu is not None):
        coord.append(copy.deepcopy(flap.Coordinate(name='ETUTime',
                                                   unit='ETU',
                                                   mode=flap.CoordinateMode(equidistant=False),
                                                   values=time_vec_etu,
                                                   shape=time_vec_etu.shape,
                                                   dimension_list=[2]
                                                   )
                                   )
                    )
    
    if (time_vec_w7x is not None):
        coord.append(copy.deepcopy(flap.Coordinate(name='W7XTime',
                                                   unit='Nanosecond',
                                                   mode=flap.CoordinateMode(equidistant=False),
                                                   values=time_vec_w7x,
                                                   shape=time_vec_w7x.shape,
                                                   dimension_list=[2]
                                                   )
                                    )
                    )
    coord.append(copy.deepcopy(flap.Coordinate(name='Sample',
                                               unit='',
                                               mode=flap.CoordinateMode(equidistant=False),
                                               values=frame_vec,
                                               shape=frame_vec.shape,
                                               dimension_list=[2]
                                               )
                              )
                )
    coord.append(copy.deepcopy(flap.Coordinate(name='Image x',
                                               unit='Pixel',
                                               mode=flap.CoordinateMode(equidistant=True),
                                               start=int(info['X Start']),
                                               step=int(1),
                                               shape=[],
                                               dimension_list=[0]
                                               )
                              )
                )
    coord.append(copy.deepcopy(flap.Coordinate(name='Image y',
                                               unit='Pixel',
                                               mode=flap.CoordinateMode(equidistant=True),
                                               start=int(info['Y Start']),
                                               step=int(1),
                                               shape=[],
                                               dimension_list=[1]
                                               )
                              )
                 )

    data_title = "W7-X CAMERA data: {}".format(data_name)
    d = flap.DataObject(data_array=data_arr,
                        data_shape=data_shape,
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
