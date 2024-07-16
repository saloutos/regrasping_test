# imports
import brl_gripper as bg
import mujoco as mj
import numpy as np
import atexit
import tty
import termios
import sys
import os
import time
import csv
from datetime import datetime as dt

# initialization
print("Starting init.")
init_settings = termios.tcgetattr(sys.stdin)

# add object to model here
xml_path = os.path.join(bg.assets.ASSETS_DIR, 'scene')
xml_string = """
<mujoco model="scene">
    <include file=\"""" + xml_path + ".xml\"" + """/>
    <!-- CUBE -->
    <worldbody>
        <body name="object" pos="0.23 0 0.05">
            <joint type="free" name="object" group="3" stiffness="0" damping="0" frictionloss="0" armature="0"/>
            <inertial pos="0 0 0" mass="0.2" diaginertia="0.00012 0.00012 0.00012"/>
            <geom name="object" type="box" group="3" size="0.03 0.03 0.03" rgba="0.7 0.2 0.1 0.6" contype="1" conaffinity="1" condim="4" priority="2" friction="1 0.02 0.0001" solimp="0.95 0.99 0.001 0.5 2"  solref="0.002 1"/>
        </body>
    </worldbody>
    <option impratio="10" timestep="0.0005" integrator="implicitfast" cone="elliptic" solver="Newton" noslip_iterations="0">
        <flag contact="enable" override="disable" multiccd="disable"/>
    </option>
</mujoco>
"""

# mj_model = mj.MjModel.from_xml_path(os.path.join(bg.assets.ASSETS_DIR, 'scene_with_object.xml'))
mj_model = mj.MjModel.from_xml_string(xml_string)

# platform
log_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'logs/')
GP = bg.GripperPlatform(mj_model, viewer_enable=True, hardware_enable=bg.HardwareEnable.NO_HW, log_path=None)

# controller
from controllers.regrasp.RegraspFSM import RegraspFSM
controller = RegraspFSM()

# shutdown
atexit.register(GP.shutdown)
print("Finished init.")

# start experiment
try:
    tty.setcbreak(sys.stdin.fileno())
    GP.initialize() # TODO: make sure that this waits for gripper to be initialized
    controller.begin(GP)
    GP.apply_control()
    GP.sync_viewer()
    print("Starting main loop.")
    real_start_time = time.time()
    while GP.mode==bg.PlatformMode.HW_NO_VIS or GP.mj_viewer.is_running(): # TODO: better way to do this?
        if not GP.paused:
            # step in time to update data from hardware or sim
            GP.step()
            # run controller and update commands
            GP.dt_comp = 0.0 # for real-time simulation
            if GP.run_control:
                control_start_time = GP.time()
                GP.run_control = False
                GP.sync_data()
                controller.update(GP)
                GP.apply_control()
                GP.log_data()
                GP.dt_comp += GP.time() - control_start_time
            # sync viewer
            if GP.run_viewer_sync:
                viewer_sync_start_time = GP.time()
                GP.run_viewer_sync = False
                GP.sync_viewer()
                GP.dt_comp += GP.time() - viewer_sync_start_time

# end experiment
finally:
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, init_settings)