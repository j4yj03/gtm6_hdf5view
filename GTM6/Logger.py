import logging
from pathlib import Path


class Logger(logging.Logger):
    def __init__(self, logfilename: str, level:int=logging.DEBUG):
        super().__init__('HDF5ViewerLogger', level=level)
        self.loglevel = level
        self.logfilepath = Path.cwd().joinpath(logfilename)
        self.new = False
        
        if not self.logfilepath.is_file():
            fp = open(self.logfilepath, 'x')
            fp.close()
            self.new = True
            
            #print(f'{logfilename} created..')

        logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        self.setup_logging()

    def setup_logging(self):
        # Create a formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        logging.basicConfig(
            level=self.loglevel, 
            filename=self.logfilepath, 
            filemode='a', 
            format=formatter._fmt
        )
        if self.new:
            logging.info(f'Hello HDF5Viewer logfile!')

#logger=logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
#logging.getLogger('matplotlib.font_manager').disabled = True

