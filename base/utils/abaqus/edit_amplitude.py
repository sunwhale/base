# -*- coding: utf-8 -*-
"""

"""
import json

import numpy as np


class Load:
    """
    Load类，定义载荷。
    """

    def __init__(self,
                 runing_time=[],
                 temperature=[],
                 axial_strain=[],
                 shear_strain=[],
                 axial_stress=[],
                 torque=[],
                 first_cycle_shift=0):

        self.runing_time = runing_time
        self.temperature = temperature
        self.axial_strain = axial_strain
        self.axial_stress = axial_stress
        self.shear_strain = shear_strain
        self.torque = torque
        self.total_runing_time = self.runing_time[-1]
        self.length = len(self.runing_time)
        self.first_cycle_shift = first_cycle_shift
        self.segment = 1

    def setLoadFromExperiment(self, ExperimentData, runing_time=None):
        self.runing_time = ExperimentData.runing_time
        self.temperature = ExperimentData.temperature
        self.axial_strain = ExperimentData.axial_strain
        self.axial_stress = ExperimentData.axial_stress
        self.shear_strain = ExperimentData.shear_strain
        self.torque = ExperimentData.torque
        if runing_time == None:
            self.total_runing_time = self.runing_time[-1]
        else:
            self.total_runing_time = runing_time
        self.length = len(self.runing_time)
        self.segment = 2

    def listToArray(self):
        self.runing_time = np.array(self.runing_time)
        self.temperature = np.array(self.temperature)
        self.axial_strain = np.array(self.axial_strain)
        self.axial_stress = np.array(self.axial_stress)
        self.shear_strain = np.array(self.shear_strain)
        self.torque = np.array(self.torque)

    def setLoadBiaxial(self, cycles, runing_time, temperature, axial_strain, shear_strain):
        for n in range(cycles):
            self.runing_time += [n * (runing_time[-1] - runing_time[0]) + time for time in runing_time[:-1]]
        self.temperature += temperature[:-1] * cycles
        self.axial_strain += axial_strain[:-1] * cycles
        self.shear_strain += shear_strain[:-1] * cycles

        self.runing_time.append(cycles * (runing_time[-1] - runing_time[0]))
        self.temperature.append(temperature[-1])
        self.axial_strain.append(axial_strain[-1])
        self.shear_strain.append(shear_strain[-1])
        self.total_runing_time = self.runing_time[-1]

        if axial_strain[0] == 0 and shear_strain[0] == 0:
            self.runing_time.pop(1)
            self.temperature.pop(1)
            self.axial_strain.pop(1)
            self.shear_strain.pop(1)
        if axial_strain[0] != 0:
            self.runing_time[1] = self.first_cycle_shift
        if shear_strain[0] != 0:
            self.runing_time[1] = self.first_cycle_shift
        self.length = len(self.runing_time)
        self.axial_stress = np.zeros(self.length)
        self.torque = np.zeros(self.length)
        self.segment = 1


def create_amplitude(loading_cycles=50, period=5, amp_max=1, amp_min=0):
    load = Load(runing_time=[0],
                temperature=[0],
                axial_strain=[0],
                shear_strain=[0],
                first_cycle_shift=period / 8.0)

    amp_mean = (amp_max + amp_min) / 2.0

    load.setLoadBiaxial(int(loading_cycles),
                        [0, period / 4.0, period / 2.0, period / 4.0 * 3.0, period],
                        [0, 0, 0, 0, 0],
                        [amp_mean, amp_max, amp_mean, amp_min, amp_mean],
                        [0, 0, 0, 0, 0])

    amplitude = [[load.runing_time[i], load.axial_strain[i]]
                 for i in range(len(load.runing_time))]
    return amplitude


def amplitude_to_input(outfile_name='amplitude.inp',
                       amplitude_name='Amp-1',
                       amplitude=[]):
    outfile = open(outfile_name, 'w')

    outfile.writelines('*Amplitude, name=%s\n' % amplitude_name)

    for amp in amplitude:
        line = '%-20.10f,%-20.10f\n' % (amp[0], amp[1])
        outfile.writelines(line)

    outfile.close()


if __name__ == "__main__":
    with open('parameters.json', 'r', encoding='utf-8') as f:
        parameters = json.load(f)
    period = float(parameters['period'])
    amplitude = create_amplitude(loading_cycles=10000,
                                 period=period,
                                 amp_max=1,
                                 amp_min=0.1)
    amplitude_to_input(outfile_name='amplitude.inp',
                       amplitude_name='Amp-1',
                       amplitude=amplitude)
