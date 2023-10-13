
import h5py
import logging

from pathlib import Path
import numpy as np
from scipy.signal import spectrogram

import pandas as pd

import seaborn as sns

import matplotlib

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import matplotlib.style as mplstyle

import plotly.express as px

from datetime import datetime, timedelta


from . import CutEdges, PlotConfig


from ._helper import LR_fit, LR_predict


mplstyle.use('fast')

matplotlib.use('TkAgg')

class InvalidGTM6LogFileException(Exception):
    pass

# ################################################################################################################################
class LogFile(h5py.File):


    def __init__(self, h5filepath: Path, plotconfig: PlotConfig=None):
        
        self.h5filepath = h5filepath
        
        super().__init__(self.h5filepath, 'r')

        try:
            self.sensorGroup = self['GTM6']['LOG']

            self.sensorValidListIdx = [] 
            self.sensorList = list(self.sensorGroup.keys()) 

            # every sensor vector should have the same length, with lenght of time-vector being the expected lenght 
            self.n_sensorTime_data = self['GTM6']['LOG']['TIME'].shape[0]

            for sensor in self.sensorGroup:
                self.sensorValidListIdx.append((self.sensorGroup[sensor].shape[0] == self.n_sensorTime_data))
        
        
        except KeyError as ke:
            raise InvalidGTM6LogFileException(f'{self.h5filepath} not a valid GTM6 log file')
        
        try:
            self.cutGroup = self['GTM6']['CUTS']

        except KeyError as ke:
            logging.debug(f'gtm6 log {self.h5filepath} has no cuts information')


        self.plotconfig = plotconfig

        self.Fs = self.plotconfig.get_values_by_name('sample frequency')['Fs']

        # load time information
        self.data_start_time = None
        self.data_plot_start_time = None
        self.data_end_time = None
        self.dataFrameTSIndex = None
        self.dataFrame = pd.DataFrame()
        #self.loadTimeData()


    def getSensorGroup(self):
        """
            return sensor group database
        """
        return self.sensorGroup
    
    def getStartTime(self) -> np.datetime64:
        if self.data_start_time is None:
            return
        else:
            return self.data_start_time
          
    def getEndTime(self) -> np.datetime64:
        if self.data_end_time is None:
            return
        else:
            return self.data_end_time
 
    def getSensorDataFrame(self) -> pd.DataFrame:
        return self.dataFrame
    
    def getLogFileFilePath(self) -> Path:
        return self.h5filepath

    def listValidSensorsIdx(self):
        return [i for i, x in enumerate(self.sensorList) if self.sensorValidListIdx[i] == 1]
    
    
    def listValidSensorsNames(self):
        # return only valid sensor names
        return [x for i, x in enumerate(self.sensorList) if self.sensorValidListIdx[i] == 1]
    
    def setPlotConfig(self, plotconfig: PlotConfig):
        self.plotconfig = plotconfig
    
    def setPlotStartTime(self, starttimestamp: np.datetime64):
        self.data_plot_start_time  = starttimestamp
    
    
    def loadTimeBoundarys(self):
        """loads min and max datime time from database"""
        self.data_start_time =  pd.to_datetime(self.sensorGroup['TIME'][0], unit='us')
        self.data_end_time = pd.to_datetime(self.sensorGroup['TIME'][-1], unit='us')

    
    def loadTimeData(self):
        """loads TIME vector from database"""
        times = pd.to_datetime(self.sensorGroup['TIME'][:], unit='us') 

        self.data_start_time = times[0]
        self.data_end_time = times[-1]

        self.dataFrameTSIndex = times

    
        
    def sensorIsInData(self, sensor_label: str) -> bool:
        return sensor_label in self.dataFrame.columns
    
    def timeIsMonotonicIncreasing(self) -> bool:
        return self.dataFrame.index.is_monotonic_increasing
    
    def loadCutsData(self):
        if not self.cutGroup is None:
            pass

    
    def loadSensorData(self, data_label_list: list, duration_s: int = 120, reload_anyway: bool = False):
        """
        """
        if len(data_label_list) < 1:
            return
        


        delta = timedelta(seconds = duration_s)
        tresh_l = int((self.data_plot_start_time).timestamp() * 1e6)
        tresh_h = int((self.data_plot_start_time + delta).timestamp() * 1e6)

        data = {}

        mask = np.logical_and(self.sensorGroup['TIME'][:] > tresh_l ,self.sensorGroup['TIME'][:] < tresh_h)

        if reload_anyway:
            self.dataFrame = pd.DataFrame()

        if self.dataFrameTSIndex is None or reload_anyway:
            self.dataFrameTSIndex = pd.to_datetime(self.sensorGroup['TIME'][:][mask], unit='us')

        for label in data_label_list:
            if reload_anyway or (not self.sensorIsInData(label)):
                if label != 'TIME':
                    # apply mask
                    data[label] = self.sensorGroup[label][mask]
            
        if data:
            tmp_dataFrame = pd.DataFrame(data=data, index=self.dataFrameTSIndex).sort_index()
            #tmp_dataFrame.set_index(self.dataFrameTSIndex, inplace=True) 
            #tmp_dataFrame.sort_index(inplace=True)      
            self.dataFrame = pd.concat([self.dataFrame, tmp_dataFrame], axis = 1)

        if reload_anyway:
            # have to do this last
            self.dataFrame.set_index(self.dataFrameTSIndex, inplace=True)
            self.dataFrame.sort_index(inplace=True)

        # estimated_value = value_1 + (timestamp - timestamp_1) * ((value_2 - value_1) / (timestamp_2 - timestamp_1))
        #self.dataFrame.interpolate(method='time', inplace=True) #fillna(method='ffill', inplace=True)
        self.dataFrame.ffill(inplace=True)


    def plotSensors(self, data_x_label_list: list, data_y_label_list: list):
        """
        """

        active_plot_options = self.plotconfig.get_active_names()

        if len(data_x_label_list) > 1:
            return
        
        n_plots = len(data_y_label_list)
        # data_x_label_list is a list so we can maybe add multiple X axis support later
        data_x_label = data_x_label_list[0]
        # try loading missing data
        
        logging.debug(active_plot_options)
        
        # begin plotting
        fig, ax1 = plt.subplots()
        fig.set_size_inches(8 + (n_plots * 2), 8)

        axis_list = [ax1.twinx() for _ in range(n_plots - 1)]
        axis_list.insert(0, ax1)

        filtered_device = self.dataFrame.copy()

        offset = 0

        ax1.set_title(f"""{self.h5filepath.name}
                        {data_x_label_list} vs {data_y_label_list}
                        {self.dataFrame.index.min()} -> {self.dataFrame.index.max()}""")

        for axn, data_y_label, color in zip(axis_list, data_y_label_list, list(mcolors.TABLEAU_COLORS)):

            ######################################
            if data_y_label == 'GRAVER_Z' and 'plot smoothed gradient' in active_plot_options:

                ms = int(self.plotconfig.get_values_by_name('plot smoothed gradient')['lookahead ms'])

                delta = pd.Timedelta(milliseconds=ms)

                shift_periods = int(self.plotconfig.get_values_by_name('plot smoothed gradient')['shift'])

                #logging.debug(f'{self.timeIsMonotonicIncreasing()}, {delta} {shift_periods}')

                offset = np.mean(np.nan_to_num(filtered_device[data_y_label].to_numpy()))

                filtered_device[data_y_label] = (filtered_device[data_y_label].rolling(window = delta).mean()).shift( -shift_periods)

                filtered_device[f'{data_y_label}_GRAD'] = np.gradient((filtered_device[data_y_label] - offset) * 500) 
                filtered_device[f'{data_y_label}_GRAD_AVG'] = filtered_device[f'{data_y_label}_GRAD'].rolling(window = delta).mean().shift( -shift_periods)

            ######################################
            if data_x_label == 'TIME':
                axn.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y %H:%M:%S.%f'))
                fig.autofmt_xdate()

                idx = np.arange(len(self.dataFrame.index))

                x_plot = self.dataFrame.index
            elif data_x_label == 'INDEX':
                x_plot = idx 

            else:
                x_plot = self.dataFrame[data_x_label]

            axn.plot(x_plot, self.dataFrame[data_y_label], color=color, label=data_y_label)

            if data_y_label == 'GRAVER_Z' and 'plot smoothed gradient' in active_plot_options:
                pass
                #axn.plot(x_plot, filtered_device[data_y_label], color='r', label='')
                #axn.plot(x_plot, filtered_device[f'{data_y_label}_GRAD'] + offset, color='grey', label='')
                axn.plot(x_plot, filtered_device[f'{data_y_label}_GRAD_AVG'] + offset, color='black', label='GRAVER_Z smoothed gradient')
            axn.set_xlabel(data_x_label)
            axn.set_ylabel(data_y_label, color=color)
            axn.tick_params(axis='y', labelcolor=color)

            axn.legend()
        plt.show()


    def plotSpectrum(self, data_y_label_list: list):
        # Calculate the spectrogram
        

        for data_y_label in data_y_label_list:
            frequencies, times, Sxx = spectrogram(self.dataFrame[data_y_label], fs=self.Fs, noverlap=32, nperseg=48, nfft = 512)  # fs is the sample rate

            # Create a 2D heatmap (spectrogram plot)
            fig, ax = plt.subplots()
            fig.set_size_inches(12, 8)

            

            
            ax.pcolormesh(self.dataFrame.iloc[times].index, frequencies, 10 * np.log10(Sxx))  # Use log scale for better visualization
            #plt.colorbar(label='Power/Frequency (dB/Hz)', ax=ax)
            ax.set_xlabel('TIME')
            ax.set_ylabel('Frequency (Hz)')
            ax.set_title(f'{self.h5filepath.name}\nSpectrogram of Sensor Data {data_y_label}')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y %H:%M:%S.%f'))
            fig.autofmt_xdate()
            
            plt.show()
            pass


    def closeLogfile(self):
        """
            delete object and close file
        """
        del self


    def readSensor(self, sensorwhich: str):
        """
            function to read on sensor vector against time
        """
        pass


    def readSensorPair(self, sensorwhich_x: str, sensorwhich_y: str):
        """
            function to read a pait of sensor vectors against time
        """
        pass


    def calculateTimeSlice(self, time, seconds_advance):
        """
            function to calculate aprox slices for a given time interval with starting time
        """
        
        
        pass