
import traceback
import logging
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib import style

import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, filedialog

from datetime import datetime, timedelta
from pathlib import Path

from GTM6 import Logger, LogFile, PlotConfig


### 
file_version = "2023.09.28"
logfilename = 'hdf5view_logfile.log'
default_plot_params = 'default_plot_params.json'

#banned_sensors = ['SENSOR4','SENSOR5','SENSOR6','SENSOR7','SENSOR8']

#############################################################################################################################################################
class DeviceSelectorMenu(Toplevel):
    def __init__(self, parent, device_list):
        super().__init__(parent)
        self.title("Device Selector Menu")
        
        self.device_list = device_list

        self.checkbox_vars_y = [tk.IntVar() for _ in range(len(device_list))]
        self.radiobox_vars_x = tk.IntVar()

        # Load previously selected devices or initialize to all selected
        self.load_selected_devices()
        
        self.create_widgets()

    def create_widgets(self):
        x_axis_frame = ttk.Frame(self)
        x_axis_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        y_axis_frame = ttk.Frame(self)
        y_axis_frame.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        x_axis_label = ttk.Label(x_axis_frame, text="X-Achse")
        x_axis_label.grid(row=0, column=0, sticky="w")

        y_axis_label = ttk.Label(y_axis_frame, text="Y-Achse")
        y_axis_label.grid(row=0, column=0, sticky="w")

        #y_axis_var =   # 

        for i, (device_name, var_y) in enumerate(zip(self.device_list, self.checkbox_vars_y)):
            radiobutton_y = ttk.Radiobutton(x_axis_frame, text = device_name, variable=self.radiobox_vars_x, value=i)
            radiobutton_y.grid(row=i + 1, column=0, sticky="w")

            #label_y = ttk.Label(x_axis_frame, text=device_name)
            #label_y.grid(row=i + 1, column=1, sticky="w")

            checkbox = ttk.Checkbutton(y_axis_frame, text = device_name, variable=var_y)
            checkbox.grid(row=i + 1, column=0, sticky="w")

            #label = ttk.Label(y_axis_frame, text=device_name)
            #label.grid(row=i + 1, column=1, sticky="w")

        button_frame = ttk.Frame(self)
        button_frame.grid(row=len(self.device_list) + 1, column=0, columnspan=2, padx=10, pady=10)

        save_button = ttk.Button(button_frame, text="Save and Close", command=self.save_and_close)
        save_button.grid(row=0, column=0, padx=5, pady=5)

        clear_button = ttk.Button(button_frame, text="Clear Y", command=self.clear_y)
        clear_button.grid(row=0, column=1, padx=5, pady=5)

    def load_selected_devices(self):
        indx = len(self.device_list) - 1

        for i, var_y in enumerate(self.checkbox_vars_y):
            if self.device_list[i] in self.master.selected_devices_y:
                var_y.set(1) 
            else:
                var_y.set(0)

            if self.device_list[i] in self.master.selected_devices_x:
                indx = i
            
        self.radiobox_vars_x.set(indx)
            

    def save_and_close(self):
        selected_devices_y = [self.device_list[i] for i, var in enumerate(self.checkbox_vars_y) if var.get() == 1]
        selected_devices_x = [self.device_list[self.radiobox_vars_x.get()]]

        self.master.update_selected_devices(selected_devices_x, selected_devices_y)
        self.destroy()
    
    def clear_y(self):
        for var_y in self.checkbox_vars_y:
            var_y.set(0)

        #self.radiobox_vars_y.set(len(self.device_list) - 1)
############################################################################################################################################################
class MatplotStyleMenu(Toplevel):
    def __init__(self, master, initial_line_style, initial_matplotlib_style):
        super().__init__(master)
        self.title("Matplotlib Style Configuration")

        self.master = master

        # Create widgets for configuring line styles and Matplotlib style
        self.line_style_label = ttk.Label(self, text="Line Style:")
        self.line_style_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.line_style_var = tk.StringVar()
        self.line_style_entry = ttk.Entry(self, textvariable=self.line_style_var)
        self.line_style_entry.grid(row=0, column=1, padx=10, pady=10)

        self.matplotlib_style_label = ttk.Label(self, text="Matplotlib Style:")
        self.matplotlib_style_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.matplotlib_style_var = tk.StringVar()
        self.available_styles = style.available
        self.matplotlib_style_entry = ttk.Combobox(self, textvariable=self.matplotlib_style_var, values=self.available_styles)
        self.matplotlib_style_entry.grid(row=1, column=1, padx=10, pady=10)

        # Create a button to apply the line style and Matplotlib style
        self.apply_button = ttk.Button(self, text="Apply", command=self.apply_styles)
        self.apply_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        # Initialize instance variables to store selected values
        self.selected_line_style = "solid"  # Default line style
        self.selected_matplotlib_style = style.use("default")  # Default Matplotlib style

        # Set the initial line style and Matplotlib style from arguments
        self.selected_line_style = initial_line_style
        self.selected_matplotlib_style = initial_matplotlib_style

        # Set initial values for widgets based on stored values
        self.line_style_var.set(self.selected_line_style)
        self.matplotlib_style_var.set(self.selected_matplotlib_style)

    def apply_styles(self):
        self.selected_line_style = self.line_style_var.get()
        self.selected_matplotlib_style = self.matplotlib_style_var.get()

        # apply to Matplotlib
        plt.rcParams["lines.linestyle"] = self.selected_line_style

        style.use(self.selected_matplotlib_style)

        # Update the styles in the HDF5Viewer class
        self.master.update_matplot_styles(self.selected_line_style, self.selected_matplotlib_style)

        self.destroy()
############################################################################################################################################################
class PlotOptionMenu(Toplevel):
    def __init__(self, master, plotconfig = None):
        super().__init__(master)
        self.master = master
        self.title("Plot Optionen")

        if plotconfig is None:
            self.plotconfig = PlotConfig(default_plot_params)

        else:
            self.plotconfig = plotconfig

            logging.debug(f'open menu {self.plotconfig}')

        self.plot_option_states = {}

        self.create_widgets()

        

    def create_widgets(self):

        label_font = ("Arial", 10, "bold")

        for option_idx, (key, item) in enumerate(self.plotconfig.data.items()):
            group_frame = ttk.Frame(self)
            group_frame.pack(anchor="w")

            item_vars = {}

            label = ttk.Label(group_frame, text = f"{item['name']}:", font=label_font)
            label.grid(row=0, column=0, sticky="w")

            if 'active' in item:
                active_var = tk.BooleanVar()
                active_var.set(item['active'])

                active_checkbox = ttk.Checkbutton(group_frame, variable=active_var, text="Active")
                active_checkbox.grid(row=0, column=1, sticky="w")
                item_vars['active'] = active_var
                

            if 'value' in item:
                value_vars = {}
                for value_idx, (value_key, value_item) in enumerate(item['value'].items()):
                    value_label = ttk.Label(group_frame, text=value_key)
                    value_label.grid(row = (value_idx + 1), column=0, sticky="w")

                    value_var = tk.StringVar()
                    value_var.set(str(value_item))
                    value_vars[value_key] = value_var

                    value_input = ttk.Entry(group_frame, textvariable=value_var)
                    value_input.grid(row = (value_idx + 1), column=1, sticky="w")
                    
                item_vars['value'] = value_vars
                    

            separator = ttk.Separator(self, orient="horizontal")
            separator.pack(fill="x")
            self.plot_option_states[key] = item_vars

        # Create frame for buttons at the bottom
        button_frame = ttk.Frame(self)
        button_frame.pack(side="bottom")

        save_button = ttk.Button(button_frame, text="Save", command=self.save_and_close)
        save_button.pack(side="left")

        close_button = ttk.Button(button_frame, text="Close", command=self.destroy)
        close_button.pack(side="left")

        # Add a third button without functionality
        save_config_button = ttk.Button(button_frame, text="Save Config")
        save_config_button.pack(side="left")

    def save_and_close(self):

        for key, item_vars in self.plot_option_states.items():
            orig_item = self.plotconfig.data[key]

            if 'active' in orig_item:
                active_var = item_vars['active']
                # Check if the checkbox state is different from the JSON data
                if active_var.get() != orig_item.get('active', False):
                    orig_item['active'] = active_var.get()

            if 'value' in orig_item and 'value' in item_vars:
                value_vars = item_vars['value']
                for value_key, value_item in orig_item['value'].items():
                    value_var = value_vars.get(value_key)
                    # Check if the text input state is different from the JSON data
                    if value_var and value_var.get() != str(value_item):
                        orig_item['value'][value_key] = value_var.get()

            self.plotconfig.update_key(key, orig_item)

        self.master.update_plot_options(self.plotconfig)
        self.destroy()

    def clear_all(self):
        for var_y in self.checkbox_vars:
            var_y.set(0)
###########################################################################################################################################################
class DateTimePickerDialog(Toplevel):
    def __init__(self, master, initial_datetime=None):
        super().__init__(master)
        self.title("Pick Date and Time")

        self.master = master
        self.initial_datetime = initial_datetime

        self.date_var = tk.StringVar()
        self.hour_var = tk.StringVar()
        self.minute_var = tk.StringVar()
        self.second_var = tk.StringVar()

        ttk.Label(self, text="Enter Date and Time (YYYY-MM-DD HH:MM:SS):").grid(row=0, column=0, columnspan=4)

        ttk.Label(self, text="Date (YYYY-MM-DD):").grid(row=1, column=0, padx=5)
        ttk.Label(self, text="Hour:").grid(row=1, column=3, padx=0)
        ttk.Label(self, text="Minute:").grid(row=1, column=4, padx=0)
        ttk.Label(self, text="Second:").grid(row=1, column=5, padx=0)

        self.date_entry = ttk.Entry(self, textvariable=self.date_var, width=12)
        self.date_entry.grid(row=2, column=0, padx=5)

        self.hour_entry = ttk.Entry(self, textvariable=self.hour_var, width=5)
        self.hour_entry.grid(row=2, column=3, padx=0)

        self.minute_entry = ttk.Entry(self, textvariable=self.minute_var, width=5)
        self.minute_entry.grid(row=2, column=4, padx=0)

        self.second_entry = ttk.Entry(self, textvariable=self.second_var, width=5)
        self.second_entry.grid(row=2, column=5, padx=0)

        if self.initial_datetime is not None and isinstance(self.initial_datetime, datetime):
            self.date_var.set(self.initial_datetime.strftime("%Y-%m-%d"))
            self.hour_var.set(self.initial_datetime.strftime("%H"))
            self.minute_var.set(self.initial_datetime.strftime("%M"))
            self.second_var.set(self.initial_datetime.strftime("%S"))

        self.ok_button = ttk.Button(self, text="OK", command=self.ok)
        self.ok_button.grid(row=3, column=0, columnspan=4, padx=10, pady=10)

    def ok(self):
        try:
            date = self.date_var.get()
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            second = int(self.second_var.get())

            if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                selected_datetime = f"{date} {hour:02d}:{minute:02d}:{second:02d}"
                selected_datetime = pd.Timestamp(selected_datetime)
                self.master.update_datetime_result(selected_datetime)  # Update the main application
                self.destroy()
        except ValueError:
            pass
###########################################################################################################################################################
class LogFileSelectionDialog(Toplevel):
    def __init__(self, master, files):
        super().__init__(master)
        
        self.directory_files = files
        self.selected_files = []

        dir_files_len = len(self.directory_files)

        if dir_files_len > 0:
            self.title("Select Files")
            # Create checkboxes for each file
            self.checkbox_vars = [tk.BooleanVar(value=False) for _ in self.directory_files]
            self.checkboxes = []

            for i, file in enumerate(files):
                checkbox = ttk.Checkbutton(self, text=file, variable=self.checkbox_vars[i])
                checkbox.grid(row=i, column=0, sticky="w")
                self.checkboxes.append(checkbox)
        else:
            self.title("No Files found")
            nothingness_label = ttk.Label(self, text="There are no hdf5 or h5 databases in this folder")
            nothingness_label.grid(row=0, column=0, padx=0, pady=0)

        # Create buttons
        ttk.Button(self, text="Clear All", command=self.clear_all).grid(row = dir_files_len + 1, column=0, sticky="e")
        ttk.Button(self, text="Select All", command=self.select_all).grid(row = dir_files_len + 1, column=1, sticky="w")
        ttk.Button(self, text="Save and Close", command=self.save_and_close).grid(row = dir_files_len + 1, column=2, sticky="w")

    def clear_all(self):
        for var in self.checkbox_vars:
            var.set(False)

    def select_all(self):
        for var in self.checkbox_vars:
            var.set(True)

    def save_and_close(self):
        self.selected_files = [file for file, var in zip(self.directory_files, self.checkbox_vars) if var.get()]
        self.destroy()
############################################################################################################################################################    
class HDF5Viewer(ttk.Frame):
    """
        Main GUI
    """
    def _printError(self, s):
        logging.error(s)

    def _showErrorMessage(self, s):
        self._printError(f'{s}')
        messagebox.showerror('GTM Error', s)

    def _callback_exception(self, exc, val, tb):
        err_message = "{}".format(traceback.format_exc())

        self._showErrorMessage(f'{err_message}')



    def __init__(self, master=None):
        super().__init__(master)
        master.report_callback_exception = self._callback_exception
        self.master = master
        self.master.title( f'GTM6 logfile viewer for hdf5 files - {file_version}')

        self.logfile_path = None
        self.logdir_path = None

        self.selected_devices_x = []
        self.selected_devices_y = []

        self.logfile = None
        self.logfile_lst = []

        self.duration_time_s = 0
        self.plot_start_date = datetime.now()
        # plot optionen information stored in dict
                   

        self.plotconfig = PlotConfig(default_plot_params) #self.initPlotOptions()  # Default plot options


        # matplotlib style configs
        self.selected_line_style = "solid"  # Default line style
        self.selected_matplotlib_style = style.available[9]  # Default Matplotlib style
        

        self.style = ttk.Style()
        self.style.configure("Bold.TButton", font=("Arial", 10, "bold"))

        self.create_widgets()


    #######################################################################################################

    def create_widgets(self):
        self.file_label = ttk.Label(self, text="Select an HDF5 file:")
        self.file_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.file_entry = ttk.Entry(self, state="disabled", width=40)
        self.file_entry.grid(row=0, column=1, columnspan=2, padx=0, pady=0)
        
        self.browse_button = ttk.Button(self, text="Browse File", command=self.browse_file, style="Bold.TButton")
        self.browse_button.grid(row=0, column=3, padx=10, pady=10)

        self.browse_button = ttk.Button(self, text="Browse Directory", command=self.browse_directory, style="Bold.TButton")
        self.browse_button.grid(row=0, column=4, padx=10, pady=10)
        
        self.select_devices_button = ttk.Button(self, text="Devices", command=self.open_device_selector, style="Bold.TButton")
        self.select_devices_button.grid(row=1, column=0, padx=10, pady=10)

        open_picker_button = ttk.Button(self, text="Plot Start Datetime", command=self.open_datetime_picker)
        open_picker_button.grid(row=1, column=1, padx=10, pady=10)

        self.seconds_label = ttk.Label(self, text="Seconds to Plot:")
        self.seconds_label.grid(row=1, column=2, padx=0, pady=0)

        self.seconds_spinbox = ttk.Spinbox(self, from_=1, to=99999)
        self.seconds_spinbox.grid(row=1, column=3, padx=10, pady=10)
        self.seconds_spinbox.delete(0, "end")
        self.seconds_spinbox.insert(0, 60)  # Set an initial value

        # Add the "Line Style" button
        self.line_style_button = ttk.Button(self, text="Line Style", command=self.open_matplot_styles)
        self.line_style_button.grid(row=1, column=5, padx=10, pady=10)

        self.plot_options_button = ttk.Button(self, text="Plot Optionen", command=self.open_plot_options)
        self.plot_options_button.grid(row=1, column=4, padx=10, pady=10)

        self.plot_button = ttk.Button(self, text="Plot Device", command=self.plot_data)
        self.plot_button.grid(row=2, column=0, padx=10, pady=10)

        self.plot_spectrum_button = ttk.Button(self, text="Plot Spectrum", command=self.plot_spectrum)
        self.plot_spectrum_button.grid(row=2, column=1, padx=10, pady=10)

        self.plot_contactedges_button = ttk.Button(self, text="Plot Edges", command=self.plot_contactedges)
        self.plot_contactedges_button.grid(row=2, column=2, padx=10, pady=10)

        self.data_label = ttk.Label(self, text="Data from database:")
        self.data_label.grid(row=3, column=0, padx=10, pady=10)
        
        self.data_text = tk.Text(self, wrap="none", height=10, width=40)
        self.data_text.grid(row=4, column=0, columnspan=4, padx=10, pady=10)
        self.data_text.delete(1.0, "end")
        self.data_text.insert("end", f"Open a logfile first..")
        self.data_text['state'] = 'disabled'
        self.data_text.tag_configure("bold", font=("Arial", 10, "bold"))

        self.info_label = ttk.Label(self, text="Plot parameters:")
        self.info_label.grid(row=3, column=3, padx=10, pady=10)

        self.info_text = tk.Text(self, wrap="none", height=10, width=40)
        self.info_text.grid(row=4, column=3, columnspan=4, padx=10, pady=10)
        self.info_text.delete(1.0, "end")
        self.info_text.insert("end", f"")
        self.info_text['state'] = 'disabled'
        self.info_text.tag_configure("bold", font=("Arial", 10, "bold"))
        
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(4, weight=1)
    
    # open dialogs ####################################################

    def browse_file(self):
        self.logfile_path = Path(filedialog.askopenfilename(filetypes=[ ("h5 files", "*.h5"), ("HDF5 files", "*.hdf5"), ("NeXus files", "*.nxn")]))

        if self.logfile_path.is_file():
            self.logdir_path = None
            self.logfile_lst = []

            self.file_entry_write(self.logfile_path)
    
            
            # Open the HDF5 file
            logfile = LogFile(self.logfile_path, self.plotconfig)
            self.logfile_lst.append(logfile)

            logfile.loadTimeBoundarys()

            self.master.title( f'GTM6 logfile: {self.logfile_path.name} - {file_version}')
            self.update_textbox(delete = True)
            self.update_textbox(text = f"{self.logfile_path.name}\n", bold=True)
            self.update_textbox(text = f"Start: ", bold=True)
            self.update_textbox(text = f"{logfile.getStartTime()}\n")
            self.update_textbox(text = f"End: ", bold=True)
            self.update_textbox(text = f"{logfile.getEndTime()}\n\n")
            
            self.device_list = logfile.listValidSensorsNames()

            self.update_datetime_result(logfile.getStartTime())
        


    def browse_directory(self):
        self.logdir_path = Path(filedialog.askdirectory(title="Select a directory containing HDF5 files", initialdir=Path.cwd()))

        if self.logdir_path.is_dir():

            self.logfile_path = None
            self.logfile_lst = []

            self.file_entry_write(self.logdir_path)

            self.master.title( f'GTM6 log directory: {self.logdir_path} - {file_version}')

            hdf5_files = [f for f in Path.iterdir(self.logdir_path) if f.suffix in (('.h5', '.hdf5', '.nxn'))]

            dialog = LogFileSelectionDialog(self, hdf5_files)
            self.wait_window(dialog)

            selected_files_paths = dialog.selected_files

            self.update_textbox(delete = True)

            for file_path in selected_files_paths:
                logfile = LogFile(file_path, self.plotconfig)

                logfile.loadTimeBoundarys()
                self.device_list = logfile.listValidSensorsNames()

                self.update_textbox(text = f"{file_path.name}\n", bold=True)
                self.update_textbox(text = f"Start: ", bold=True)
                self.update_textbox(text = f"{logfile.getStartTime()}\n")
                self.update_textbox(text = f"End: ", bold=True)
                self.update_textbox(text = f"{logfile.getEndTime()}\n\n")
                self.logfile_lst.append(logfile)

            self.update_datetime_result(self.logfile_lst[0].getStartTime())

    def file_entry_write(self, label:str):
        self.file_entry.config(state="normal")
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, label)
        self.file_entry.config(state="disabled")


    def open_device_selector(self): 
        if self.logfile_path is None and self.logdir_path is None:
            self._showErrorMessage("No logfile or directory loaded!")
            return     
        dialog = DeviceSelectorMenu(self, self.device_list)
        self.wait_window(dialog)
    
    def open_plot_options(self):
        dialog = PlotOptionMenu(self, self.plotconfig)
        self.wait_window(dialog)

    def open_matplot_styles(self):
        dialog = MatplotStyleMenu(self, self.selected_line_style, self.selected_matplotlib_style)
        self.wait_window(dialog)
    
    def open_datetime_picker(self):

        #for log_file in self.logfile_lst:


        initial_datetime = self.plot_start_date#datetime.now()  # Provide your initial datetime here

        dialog = DateTimePickerDialog(self, initial_datetime=initial_datetime)
        #dialog.update_datetime_result = update_datetime_result  # Add update function to dialog
        self.wait_window(dialog)  # Wait for the dialog to close


    def set_default_infobox(self):
        if self.logfile_path is None and self.logdir_path is None:
            self._showErrorMessage("No logfile or directory loaded!")
            return     
        self.info_text['state'] = 'normal'
        self.info_text.delete(1.0, "end")   
        self.info_text.insert("end", f"Plot start timestamp:\n", "bold")
        self.info_text.insert("end", f"{self.plot_start_date}\n\n")
        self.info_text.insert("end", f"Selected Devices:\n", "bold")
        self.info_text.insert("end", f"X {self.selected_devices_x}\nY {self.selected_devices_y}\n\n")
        self.info_text.insert("end", f"Active Plot Options:\n", "bold")

        if not self.plotconfig is None:
            info_option_string = ""
            
            for name in self.plotconfig.get_active_names():
                info_option_string += f"{name}\n"
                            
            self.info_text.insert("end", info_option_string)

                    
        self.info_text['state'] = 'disabled'

    
    def set_default_testbox(self):
        pass
    # update widgets ###########################################################################################
    
    def update_textbox(self, delete: bool = False, text: str = "", bold: bool = False):
        #if self.logfile.getLogFileFilePath() is None:
            #self._showErrorMessage("No h5 file loaded!")
        #    return     
        self.data_text['state'] = 'normal'

        if delete:
            self.data_text.delete(1.0, "end")
        else:
            if bold:
                self.data_text.insert("end", text, "bold")
            else:

                self.data_text.insert("end", text)
        
        self.data_text['state'] = 'disabled'

    def update_selected_devices(self, selected_devices_x, selected_devices_y):
        self.selected_devices_x = selected_devices_x
        self.selected_devices_y = selected_devices_y
        logging.debug(f"Selected Devices: {self.selected_devices_x} {self.selected_devices_y}")
        self.set_default_infobox()

    def update_plot_options(self, plotconfig):
        self.plotconfig = plotconfig
        #logging.debug(f"Plot Options: {self.plotconfig}")
        self.set_default_infobox()
        for logfile in self.logfile_lst:
            logfile.setPlotConfig(self.plotconfig)

    def update_matplot_styles(self, line_style, matplotlib_style):
        self.selected_line_style = line_style
        self.selected_matplotlib_style = matplotlib_style

    def update_datetime_result(self, selected_datetime):
        self.plot_start_date = selected_datetime
        logging.debug(f"Selected DateTime: {self.plot_start_date}")
        self.set_default_infobox()

    # plot functions #############################################################################################
    
    def plot_data(self):
        if len(self.selected_devices_y) == 0:
            self._showErrorMessage("No devices selected for plotting.")
            return
        
        time_s = int(self.seconds_spinbox.get())

        new_duration = (self.duration_time_s != time_s)
        self.duration_time_s = time_s

        sensor_list = []
        sensor_list.extend(self.selected_devices_x)
        sensor_list.extend(self.selected_devices_y)

        # which databases do we need
        selected_logfiles = []

        # check if logfile starttime are in plot timestamps range
        for logfile in self.logfile_lst:
            delta = (self.plot_start_date + timedelta(seconds = self.duration_time_s))       
            if logfile.getStartTime() <= delta:
                selected_logfiles.append(logfile)

        #logging.debug(f'selected log files {selected_logfiles}')        
        
        for logfile_selected in selected_logfiles:

            logfile_selected.setPlotStartTime(self.plot_start_date)

            logfile_selected.loadSensorData(data_label_list=sensor_list, duration_s=time_s, reload_anyway=new_duration)

            logfile_selected.plotSensors(self.selected_devices_x, self.selected_devices_y)

        self.set_default_infobox()
    
    def plot_spectrum(self):
        
        time_s = int(self.seconds_spinbox.get())

        new_duration = (self.duration_time_s != time_s)
        self.duration_time_s = time_s

        for logfile in self.logfile_lst:

            logfile.setPlotStartTime(self.plot_start_date)

            logfile.loadSensorData(data_label_list=self.selected_devices_y, duration_s=time_s, reload_anyway=new_duration)

            logfile.plotSpectrum(self.selected_devices_y)

    def plot_contactedges(self):
        pass

##########################################################################################################################################################

class GTM6App(tk.Tk):
    def __init__(self, topmost:bool):
        super().__init__()
        logging.debug(f'Script version {file_version} start at {datetime.now()}')
        self.lift()
        self.window = HDF5Viewer(self)
        if topmost:
            self.attributes("-topmost", True)       





logger = Logger(logfilename)

app = GTM6App(topmost = False)

app.mainloop() 