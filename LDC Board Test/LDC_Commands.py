#!/usr/bin/env python3
# LDC_Commands.py

import os
import matplotlib.pyplot as plt
import numpy as np
import time
from tkinter import Tk
from tkinter.filedialog import askdirectory
from datetime import datetime


class LDC:
    """
    Sets up the commands to control the Leakage Detection Circuit board alongside an instrument with SCPI communication
    """

    def __init__(self):
        """
        Instantiates the class, all necessary variables and modules
        """
        import pydrs
        from SCPI_Commands import SCPI

        self.drs = pydrs.SerialDRS()
        port_num = int(input("Insert the number of the COM port: "))
        com_port = 'COM' + str(port_num)
        comunic_instrumentip = input("Insert instrument ip: ")
        self.drs.connect(com_port)  # PyDRS Communication with IIB
        instrument = 'TCPIP::' + str(comunic_instrumentip) + '::inst0::INSTR'
        self.scpi = SCPI(instrument)
        self.frequency = 10
        self.period = 1 / self.frequency
        self.mean = 0
        self.maximum = 0
        self.minimum = 0
        self.ppc = 0
        self.mean_error = 0
        self.std_dev = 0
        self.test_time = 0
        self.samples = []
        self.time_samples = []
        self.error = []
        print("LDC functions enabled!")

    def read_ground_leakage(self, duration):
        """
        Reads the ground leakage current detected with the LDC board

        :param duration: Duration of the measurement in seconds
        :type duration: int

        :return: The measured values for the leakage current
        :rtype: str
        """
        self.samples.clear()
        self.time_samples.clear()
        self.error.clear()
        print("Waiting for acquisition...\n")
        for x in range(int(self.frequency * duration)):
            current_value = self.scpi.instrument.query_ascii_values(':MEASure:CURRent:DC? (%s)' % '@1')
            self.samples.append((self.drs.read_bsmp_variable(53, 'float'))*1000)
            self.time_samples.append(round(x * self.period, 2))
            self.error.append((current_value[0]*1000) - self.samples[x])
            time.sleep(self.period)
            np_samples = np.array(self.samples)
            np_error = np.array(self.error)
        self.test_time = datetime.today()
        self.mean = np_samples.mean()
        self.maximum = np_samples.max()
        self.minimum = np_samples.min()
        self.ppc = (np_samples.max() - np_samples.min())
        self.mean_error = abs(np_error.mean())
        self.std_dev = np_samples.std()
        return print("Mean: {0:.3f} mA\n"
                     "Maximum: {1:.3f} mA\n"
                     "Minimum: {2:.3f} mA\n"
                     "Peak to peak: {3:.3f} mA\n"
                     "Mean Error: {4:.3f} mA\n"
                     "Standard Deviation: {5:.3f} mA\n".format(self.mean, self.maximum, self.minimum,
                                                               self.ppc, self.mean_error, self.std_dev))

    def save_csv_file(self, file_name='Leakage Current'):
        """
        Saves the data of a ground leakage measure in a csv format file
        :argument file_name: Gives a custom name to the file. Default gives 'Leakage Current'

        :return: A string confirming the execution
        :rtype: str
        """
        name = file_name+'.csv'
        data = [['Leakage Current'], ['Time']]
        column0 = data[0]
        column1 = data[1]
        for row in range(len(self.samples)):
            column0.append(self.samples[row])
            column1.append(self.time_samples[row])
        np.savetxt(name, [p for p in zip(column0, column1)], delimiter=',', fmt='%s')
        return "CSV file named '{}' saved successfully!".format(name)

    def plot_graph(self, graph_name='Leakage Current'):
        """
        Plots the graphic of the ground leakage measure

        :return: Return the matplotlib window with the measure plot
        """
        fig, ax = plt.subplots(1, 1, figsize=(10, 5))
        ax.locator_params(axis='y', tight=True, nbins=15)
        ax.locator_params(axis='x', tight=True, nbins=30)
        ax.plot(self.time_samples, self.samples)
        plt.xlabel('Time [s]')
        plt.ylabel('Leakage Current [mA]')
        plt.grid()
        plt.title(graph_name)
        return plt.show()

    def save_graph(self, graph_name='Leakage Current'):
        """
        Saves a jpg file of the ground leakage graphic

        :return: Returns a string confirming the jpg file saving
        :rtype: str
        """
        name = graph_name+'.jpg'
        fig, ax = plt.subplots(1, 1, figsize=(10, 5))
        ax.locator_params(axis='y', tight=True, nbins=15)
        ax.locator_params(axis='x', tight=True, nbins=30)
        ax.plot(self.time_samples, self.samples)
        plt.xlabel('Time [s]')
        plt.ylabel('Leakage Current [mA]')
        plt.grid()
        plt.title(graph_name)
        plt.savefig(name)
        plt.close()
        return "Graph file named '{}' saved successfully!".format(name)

    def degauss(self):
        self.scpi.disable_output()
        self.drs.reset_interlocks()
        time.sleep(0.3)
        self.drs.reset_interlocks()
        time.sleep(0.15)
        return "Applied degaussing process!"


if __name__ == '__main__':
    cwd = os.getcwd()
    ldc = LDC()
    read_current = float(input("Insert the desired current, in Amperes: "))
    read_duration = int(input("Insert the duration of the ground leakage measure, in seconds: "))
    apply_degauss = int(input("Apply the degaussing process? 1(yes)/0(No):"))
    if apply_degauss == 1:
        ldc.degauss()
    elif apply_degauss == 0:
        pass
    ldc.scpi.set_current(read_current)
    current = ldc.scpi.measure_current()
    time.sleep(0.15)
    ldc.read_ground_leakage(read_duration)
    ldc.scpi.disable_output()
    ldc.plot_graph()
    answer = int(input("Save plot and csv file? 1(yes)/0(No): "))
    if answer == 1:
        Tk().withdraw()
        path = askdirectory(title='Select Folder')
        folder_name = str(input("Insert the folder name: "))
        os.makedirs(os.path.join(path, folder_name))
        os.chdir(os.path.join(path, folder_name))
        ldc.plot_graph(graph_name='Leakage Current Measurement, Iref = {0:.1f}mA'.format(current*1000))
        ldc.save_csv_file(file_name='Leakage_Current_Measurement-Iref_{0:.1f}mA'.format(current*1000))
        print("Files saved in the folder {}!".format(folder_name))
        os.chdir(cwd)
        exit()
    elif answer == 0:
        exit()
