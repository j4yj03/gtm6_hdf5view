import pandas as pd
import numpy as np

from multiprocessing import Process



from ._helper import butter_bandpass_filter

from .PlotConfig import PlotConfig



class _CutEdgesWorker(Process):

    def __init__(self, parent, id):
        super(self).__init__()
        self.id = id
        self.parent = parent
    
    # run method of spawned process
    def run(self):
        pass


class CutEdges():
    """
        objects of this class hold information about landing and lifting position of graver in substrat
    """

    

    def __init__(self, graver_z_data: pd.Series, options: dict) -> None:
        
        self.graver_z = graver_z_data
        self.options = options

        workerid = np.random.randint(0xFFFF)

        self.worker = _CutEdgesWorker(self, workerid)

        self.workerTask_list = [
            self.find_gradient, # 0
            self.find_edges     # 1
        ]


        pass

    def find_gradient(self):
        pass

    def find_edges(self):
        pass

    def setWorkerTask(self, taskid: int):
        if taskid <= len(self.workerTask_list) and taskid >= 0:
            self.worker.run = self.workerTask_list[taskid]
            self.workerTask = taskid
    