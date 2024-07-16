# imports
import numpy as np
from controllers.base.baseState import *
from .fsm_config import *

# define state
class ReleaseObject(BaseState):
    def __init__(self):
        self.name = "ReleaseObject"
        self.enabled = 0

    def enter(self, GP):
        print(self.name)
        self.enabled = 1
        # get initial time
        self.start_time = GP.time()

    def exit(self, GP):
        self.enabled = 0

    def execute(self, GP):

        # stay in this state
        next_state = self.name

        # get current time
        cur_time = GP.time()

        # hold at desired grasp positions
        GP.gr_data.set_q_des(GP.gr_data.all_idxs,   fsm_params.q_des_default)
        GP.gr_data.set_qd_des(GP.gr_data.all_idxs,  np.zeros((9,)))
        GP.gr_data.set_tau_ff(GP.gr_data.all_idxs,  np.zeros((9,)))
        GP.gr_data.set_kp(GP.gr_data.all_idxs,      fsm_params.kp_default)
        GP.gr_data.set_kd(GP.gr_data.all_idxs,      fsm_params.kd_default)

        # set wrist cartesian position
        GP.gr_data.kinematics['base_des']['p'] = fsm_params.base_pos_hold
        GP.gr_data.kinematics['base_des']['R'] = fsm_params.base_R_hold

        # state transition to reset
        if (cur_time-self.start_time) > fsm_params.times['release']:
            next_state = "Reset"

        # check for manual state transition to reset
        if GP.char_in=='R' or GP.char_in=='r':
            next_state = "Reset"

        return next_state