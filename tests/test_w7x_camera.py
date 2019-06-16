import unittest
import datetime
import numpy as np
import time

import flap
import flap_w7x_camera
import flap_w7x_abes

flap_w7x_camera.register()
flap_w7x_abes.register()

#def test_register():
#    flap.register_data_source('W7X_CAMERA',
#                              get_data_func=w7x_camera.w7x_camera_get_data)
#    return 'W7X_WEBAPI' in flap.list_data_sources()


def test_get_data():
    
    try:
        flap.get_data('CAMERA_APSD')
        apsd_available =  True
    except:
        apsd_available = False
    
    if (not apsd_available):    
        try:
    #       flap.get_data('W7X_CAMERA',exp_id="20181018.032", name="AEQ20_EDICAM_ROIP1", coordinates={'Time':[3,4]}, object_name="EDI_ROIP1")
           flap.get_data('W7X_CAMERA',
                         exp_id="20181018.012", 
                         name="AEQ21_PHOTRON_ROIP1",  
                         coordinates={'Time':[6.05,6.25]},
                         no_data=False, 
                         object_name="CAMERA")        
        except Exception  as e:
            raise e
        flap.list_data_objects()
        
    #    flap.plot("CAMERA",plot_type='anim-image',axes=['Image y','Image x','Time'],options={'Wait':0.01,'Clear':True}) 
        print("Slicing start")
        flap.slice_data('CAMERA',
                        slicing={'Image x':flap.Intervals(0,4,step=5),'Image y':flap.Intervals(0,4,step=5)},
                        summing={'Interval(Image x) sample index':'Mean','Interval(Image y) sample index':'Mean'},
                        output_name='CAMERA_sliced')
        print("Slicing stop") 
    #    flap.plot("CAMERA_sliced",
    #              plot_type='anim-image',
    #              axes=['Start Image y in int(Image y)','Start Image x in int(Image x)','Time'],
    #              options={'Wait':0.01,'Clear':True, 'Z range':[0,3000]})
        print("*** APSD start")
        start = time.time()
        flap.apsd("CAMERA_sliced",coordinate='Time',options={'Res':200,'Range':[0,1e4]},output_name='CAMERA_APSD')
        stop = time.time()
        print('**** APSD STOP')
        print("**** Calculation time: {:5.2f} second".format(stop-start))
        plt.close('all')
#    flap.plot('CAMERA_APSD',
#              slicing={'Start Image y in int(Image y)':50},
#              plot_type='image',
#              axes=['Frequency','Start Image x in int(Image x)'],
#              options={'Z range':[0,5],'Aspect':'auto'})
#    plt.figure()
    return
    flap.plot('CAMERA_APSD',
              plot_type='anim-image',
              axes=['Frequency','Start Image x in int(Image x)','Start Image y in int(Image y)'],
              options={'Z range':[0,5],'Aspect':'auto','Wait':0.1})
    
    flap.list_data_objects()


test_get_data()
