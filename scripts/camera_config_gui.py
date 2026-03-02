import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os

# Helper to run shell command and get output
def run_cmd(args):
    try:
        # Replace first argument with GX_SCRIPT absolute path if it matches the script name
        if args and os.path.basename(args[0]) == os.path.basename(GX_SCRIPT):
            args = [GX_SCRIPT] + args[1:]
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=GX_SCRIPT_DIR)
        return result.stdout.strip()
    except Exception as e:
        return str(e)

# Camera bus number (should be set by user)
I2C_BUS = '4'
GX_SCRIPT = '/home/rms/source/raspberrypi_v4l2/gx_i2c_tools/gx_mipi_i2c.sh'
GX_SCRIPT_DIR = os.path.dirname(GX_SCRIPT)

class CameraConfigGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('GX MIPI Camera Configurator')
        self.geometry('900x700')
        self.lift()
        self.focus_force()
        self.attributes('-topmost', True)
        # Initialize all initial_* variables here
        self.initial_imgacq = None
        self.initial_workmode = None
        self.initial_trgsrc = None
        self.initial_trgnum = None
        self.initial_trginterval = None
        self.initial_i2caddr = None
        self.initial_nondisc = None
        self.initial_slave = None
        self.initial_imgprop = {}
        self.initial_imgproc = {}
        self.initial_imgproc_dual = {}
        self.initial_ioctrl = {}
        self.create_widgets()
        self.after(1000, lambda: self.attributes('-topmost', False))

    def create_widgets(self):
        # Main layout: notebook (with scrollable tabs) + fixed button frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)

        def make_scrollable_tab(parent):
            canvas = tk.Canvas(parent)
            vscroll = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
            canvas.configure(yscrollcommand=vscroll.set)
            scroll_frame = ttk.Frame(canvas)
            scroll_frame_id = canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
            def on_configure(event):
                canvas.configure(scrollregion=canvas.bbox('all'))
            scroll_frame.bind('<Configure>', on_configure)
            canvas.bind('<Configure>', lambda e: canvas.itemconfig(scroll_frame_id, width=e.width))
            canvas.pack(side='left', fill='both', expand=True)
            vscroll.pack(side='right', fill='y')
            return scroll_frame

        # 7.2 Basic Parameters (read-only)
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text='Basic Parameters')
        basic_frame = make_scrollable_tab(basic_tab)
        self.add_basic_params(basic_frame)

        # 7.3 Image Acquisition
        acq_tab = ttk.Frame(notebook)
        notebook.add(acq_tab, text='Image Acquisition')
        acq_frame = make_scrollable_tab(acq_tab)
        self.add_acq_params(acq_frame)

        # 7.4 Image Properties
        imgprop_tab = ttk.Frame(notebook)
        notebook.add(imgprop_tab, text='Image Properties')
        imgprop_frame = make_scrollable_tab(imgprop_tab)
        self.add_imgprop_params(imgprop_frame)

        # 7.5 Image Processing
        imgproc_tab = ttk.Frame(notebook)
        notebook.add(imgproc_tab, text='Image Processing')
        imgproc_frame = make_scrollable_tab(imgproc_tab)
        self.add_imgproc_params(imgproc_frame)

        # 7.6 IO Control
        ioctrl_tab = ttk.Frame(notebook)
        notebook.add(ioctrl_tab, text='7.6 IO Control')
        ioctrl_frame = make_scrollable_tab(ioctrl_tab)
        self.add_ioctrl_params(ioctrl_frame)

        # Fixed button frame at the bottom
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side='bottom', fill='x', pady=10)
        ttk.Button(btn_frame, text='Factory Param', command=self.factory_param).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Param Save', command=self.param_save).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Reboot', command=self.reboot).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Apply', command=self.apply_params).pack(side='right', padx=5)

    def add_basic_params(self, frame):
        params = [
            ('manufacturer', 'Manufacturer'),
            ('model', 'Model'),
            ('sensorname', 'Sensor Name'),
            ('version', 'Version'),
            ('serialno', 'Serial No'),
            ('timestamp', 'Timestamp'),
            ('fmtcap', 'Format Capabilities'),
            ('readmodecap', 'Read Mode Capabilities'),
            ('workmodecap', 'Work Mode Capabilities'),
            ('lanecap', 'Lane Capabilities'),
            ('temp', 'Temperature'),
            ('videomodecap', 'Video Mode Capabilities'),
            ('videomodenum', 'Video Mode Number'),
        ]
        self.basic_labels = {}
        for i, (cmd, label) in enumerate(params):
            ttk.Label(frame, text=label+':').grid(row=i, column=0, sticky='e', padx=5, pady=2)
            val = run_cmd([GX_SCRIPT, '-r', cmd, '-b', I2C_BUS])
            lbl = ttk.Label(frame, text=val)
            lbl.grid(row=i, column=1, sticky='w', padx=5, pady=2)
            self.basic_labels[cmd] = lbl

    def add_acq_params(self, frame):
        # Make Image Acquisition section read-only
        params = [
            ('imgacq', 'Image Acquisition'),
            ('workmode', 'Work Mode'),
            ('trgsrc', 'Trigger Source'),
            ('trgnum', 'Trigger Number'),
            ('trginterval', 'Trigger Interval (us)'),
            ('i2caddr', 'I2C Address'),
            ('nondiscontinuousmode', 'MIPI Clock Mode'),
            ('slavemode', 'Slave Mode'),
        ]
        self.acq_labels = {}
        for i, (cmd, label) in enumerate(params):
            ttk.Label(frame, text=label+':').grid(row=i, column=0, sticky='e', padx=5, pady=2)
            val = run_cmd([GX_SCRIPT, '-r', cmd, '-b', I2C_BUS])
            lbl = ttk.Label(frame, text=val)
            lbl.grid(row=i, column=1, sticky='w', padx=5, pady=2)
            self.acq_labels[cmd] = lbl

    def bind_slider_label(self, var, lbl):
        def update_label(*args):
            lbl.config(text=str(var.get()))
        var.trace_add('write', update_label)

    def add_imgprop_params(self, frame):
        # Define options and ranges for known parameters
        pixelformat_options = ['Mono8', 'Mono10', 'UYVY', 'RGB888', 'YUYV']
        imgdir_options = ['Normal', 'Flip', 'Mirror', 'Flip+Mirror']
        videomode_options = ['ROI', 'VideoMode']
        readmode_options = ['Normal', 'Binning', 'Subsampling']
        lanenum_options = [1, 2, 3, 4]
        fps_range = (1, 120)
        mipidatarate_range = (100, 1500)
        params = [
            ('pixelformat', 'Pixel Format', 'radio', pixelformat_options),
            ('maxwh', 'Max Width/Height', 'label', None),
            ('minwh', 'Min Width/Height', 'label', None),
            ('maxfps', 'Max FPS', 'label', None),
            ('minfps', 'Min FPS', 'label', None),
            ('curwh', 'Current Width/Height', 'label', None),
            ('imgdir', 'Image Direction', 'radio', imgdir_options),
            ('videomode', 'Video Mode', 'radio', videomode_options),
            ('readmode', 'Read Mode', 'radio', readmode_options),
            ('lanenum', 'Lane Number', 'radio', lanenum_options),
            ('mipidatarate', 'MIPI Data Rate', 'slider', mipidatarate_range),
            ('fps', 'FPS', 'slider', fps_range),
        ]
        self.imgprop_labels = {}
        self.imgprop_vars = {}
        self.imgprop_slider_labels = {}
        for i, (cmd, label, widget, options) in enumerate(params):
            ttk.Label(frame, text=label+':').grid(row=i, column=0, sticky='e', padx=5, pady=2)
            val = run_cmd([GX_SCRIPT, '-r', cmd, '-b', I2C_BUS])
            if widget == 'label':
                lbl = ttk.Label(frame, text=val)
                lbl.grid(row=i, column=1, sticky='w', padx=5, pady=2)
                self.imgprop_labels[cmd] = lbl
            elif widget == 'radio':
                var = tk.StringVar(value=val)
                self.imgprop_vars[cmd] = var
                self.initial_imgprop[cmd] = var.get()
                for j, opt in enumerate(options):
                    ttk.Radiobutton(frame, text=str(opt), variable=var, value=str(opt)).grid(row=i, column=1+j, sticky='w')
            elif widget == 'slider':
                var = tk.IntVar(value=int(val) if val.isdigit() else options[0])
                self.imgprop_vars[cmd] = var
                self.initial_imgprop[cmd] = var.get()
                slider = ttk.Scale(frame, from_=options[0], to=options[1], variable=var, orient='horizontal')
                slider.grid(row=i, column=1, columnspan=2, sticky='we')
                value_label = ttk.Label(frame, text=str(var.get()))
                value_label.grid(row=i, column=3, sticky='w', padx=5)
                self.imgprop_slider_labels[cmd] = value_label
                self.bind_slider_label(var, value_label)

    def add_imgproc_params(self, frame):
        # Define options/ranges for known parameters
        expmode_options = ['Auto', 'Manual']
        aestrategy_options = ['Speed', 'Accuracy']
        wbmode_options = ['Auto', 'Manual']
        antiflicker_options = ['Off', '50Hz', '60Hz']
        slowshutter_options = [0, 1]
        slowshutter_range = (0, 100)  # Example range, update as needed
        param_ranges = {
            'aetarget': (0, 255),
            'metime': (1, 1000000),
            'aemaxtime': (1, 1000000),
            'exptime': (1, 1000000),
            'mgain': (0, 255),
            'aemaxgain': (0, 255),
            'awbcolortempmin': (2000, 8000),
            'awbcolortempmax': (2000, 8000),
            'mwbbgain': (0, 255),
            'mwbrgain': (0, 255),
            'colortemp': (2000, 8000),
            'aemintime': (1, 1000000),
            'gamma_index': (0, 10),
            'wdrparam': (0, 255),
            'sharppen': (0, 255),
            'denoise2d': (0, 255),
            'denoise3d': (0, 255),
            'saturation': (0, 255),
            'contrast': (0, 255),
            'hue': (0, 255),
            'ldc': (0, 255),
            'dehaze': (0, 255),
            'drc': (0, 255),
        }
        params = [
            ('expmode', 'Exposure Mode', 'radio', expmode_options),
            ('aetarget', 'AE Target', 'slider', param_ranges['aetarget']),
            ('aestrategy', 'AE Strategy', 'radio', aestrategy_options),
            ('metime', 'Manual Exposure Time', 'slider', param_ranges['metime']),
            ('aemaxtime', 'AE Max Time', 'slider', param_ranges['aemaxtime']),
            ('exptime', 'Exposure Time', 'slider', param_ranges['exptime']),
            ('curgain', 'Current Gain', 'label', None),
            ('mgain', 'Manual Gain', 'slider', param_ranges['mgain']),
            ('aemaxgain', 'AE Max Gain', 'slider', param_ranges['aemaxgain']),
            ('wbmode', 'White Balance Mode', 'radio', wbmode_options),
            ('awbcolortempmin', 'AWB Color Temp Min', 'slider', param_ranges['awbcolortempmin']),
            ('awbcolortempmax', 'AWB Color Temp Max', 'slider', param_ranges['awbcolortempmax']),
            ('mwbbgain', 'Manual WB B Gain', 'slider', param_ranges['mwbbgain']),
            ('mwbrgain', 'Manual WB R Gain', 'slider', param_ranges['mwbrgain']),
            ('colortemp', 'Color Temp', 'slider', param_ranges['colortemp']),
            ('currgain', 'Current R Gain', 'label', None),
            ('curbgain', 'Current B Gain', 'label', None),
            ('aemintime', 'AE Min Time', 'slider', param_ranges['aemintime']),
            ('gamma_index', 'Gamma Index', 'slider', param_ranges['gamma_index']),
            ('antiflicker', 'Anti-Flicker', 'radio', antiflicker_options),
            ('wdrparam', 'WDR Param', 'slider', param_ranges['wdrparam']),
            ('sharppen', 'Sharpen', 'slider', param_ranges['sharppen']),
            ('denoise2d', 'Denoise 2D', 'slider', param_ranges['denoise2d']),
            ('denoise3d', 'Denoise 3D', 'slider', param_ranges['denoise3d']),
            ('saturation', 'Saturation', 'slider', param_ranges['saturation']),
            ('contrast', 'Contrast', 'slider', param_ranges['contrast']),
            ('hue', 'Hue', 'slider', param_ranges['hue']),
            ('slowshutter', 'Slow Shutter', 'dual', (slowshutter_options, slowshutter_range)),
            ('ldc', 'LDC', 'slider', param_ranges['ldc']),
            ('dehaze', 'Dehaze', 'slider', param_ranges['dehaze']),
            ('drc', 'DRC', 'slider', param_ranges['drc']),
        ]
        self.imgproc_labels = {}
        self.imgproc_vars = {}
        self.imgproc_slider_labels = {}
        self.imgproc_dual_vars = {}
        for i, (cmd, label, widget, options) in enumerate(params):
            ttk.Label(frame, text=label+':').grid(row=i, column=0, sticky='e', padx=5, pady=2)
            val = run_cmd([GX_SCRIPT, '-r', cmd, '-b', I2C_BUS])
            if widget == 'label':
                lbl = ttk.Label(frame, text=val)
                lbl.grid(row=i, column=1, sticky='w', padx=5, pady=2)
                self.imgproc_labels[cmd] = lbl
            elif widget == 'radio':
                var = tk.StringVar(value=val)
                self.imgproc_vars[cmd] = var
                self.initial_imgproc[cmd] = var.get()
                for j, opt in enumerate(options):
                    ttk.Radiobutton(frame, text=str(opt), variable=var, value=str(opt)).grid(row=i, column=1+j, sticky='w')
            elif widget == 'slider':
                var = tk.IntVar(value=int(val) if val.isdigit() else options[0])
                self.imgproc_vars[cmd] = var
                self.initial_imgproc[cmd] = var.get()
                slider = ttk.Scale(frame, from_=options[0], to=options[1], variable=var, orient='horizontal')
                slider.grid(row=i, column=1, columnspan=2, sticky='we')
                value_label = ttk.Label(frame, text=str(var.get()))
                value_label.grid(row=i, column=3, sticky='w', padx=5)
                self.imgproc_slider_labels[cmd] = value_label
                self.bind_slider_label(var, value_label)
            elif widget == 'dual':
                # Dual control: radio + slider
                radio_var = tk.IntVar(value=options[0][0])
                slider_var = tk.IntVar(value=options[1][0])
                self.imgproc_dual_vars[cmd] = (radio_var, slider_var)
                self.initial_imgproc_dual[cmd] = (radio_var.get(), slider_var.get())
                for j, opt in enumerate(options[0]):
                    ttk.Radiobutton(frame, text=str(opt), variable=radio_var, value=opt).grid(row=i, column=1+j, sticky='w')
                slider = ttk.Scale(frame, from_=options[1][0], to=options[1][1], variable=slider_var, orient='horizontal')
                slider.grid(row=i, column=3, columnspan=2, sticky='we')
                value_label = ttk.Label(frame, text=str(slider_var.get()))
                value_label.grid(row=i, column=5, sticky='w', padx=5)
                self.bind_slider_label(slider_var, value_label)

    def add_ioctrl_params(self, frame):
        param_ranges = {
            'trgdelay': (0, 10000),
            'trgedge': (0, 1),
            'trgexp_delay': (0, 10000),
            'outio1_rvs': (0, 1),
        }
        params = [
            ('trgdelay', 'Trigger Delay', 'slider', param_ranges['trgdelay']),
            ('trgedge', 'Trigger Edge', 'radio', ['Rising', 'Falling']),
            ('trgexp_delay', 'Trigger Exposure Delay', 'slider', param_ranges['trgexp_delay']),
            ('outio1_rvs', 'Out IO1 Reverse', 'radio', ['Off', 'On']),
        ]
        self.ioctrl_vars = {}
        self.ioctrl_slider_labels = {}
        for i, (cmd, label, widget, options) in enumerate(params):
            ttk.Label(frame, text=label+':').grid(row=i, column=0, sticky='e', padx=5, pady=2)
            val = run_cmd([GX_SCRIPT, '-r', cmd, '-b', I2C_BUS])
            if widget == 'radio':
                var = tk.StringVar(value=val)
                self.ioctrl_vars[cmd] = var
                self.initial_ioctrl[cmd] = var.get()
                for j, opt in enumerate(options):
                    ttk.Radiobutton(frame, text=str(opt), variable=var, value=str(opt)).grid(row=i, column=1+j, sticky='w')
            elif widget == 'slider':
                var = tk.IntVar(value=int(val) if val.isdigit() else options[0])
                self.ioctrl_vars[cmd] = var
                self.initial_ioctrl[cmd] = var.get()
                slider = ttk.Scale(frame, from_=options[0], to=options[1], variable=var, orient='horizontal')
                slider.grid(row=i, column=1, columnspan=2, sticky='we')
                value_label = ttk.Label(frame, text=str(var.get()))
                value_label.grid(row=i, column=3, sticky='w', padx=5)
                self.ioctrl_slider_labels[cmd] = value_label
                self.bind_slider_label(var, value_label)

    def factory_param(self):
        out = run_cmd([GX_SCRIPT, '-w', 'factoryparam', '-b', I2C_BUS])
        messagebox.showinfo('Factory Param', out)

    def param_save(self):
        out = run_cmd([GX_SCRIPT, '-w', 'paramsave', '-b', I2C_BUS])
        messagebox.showinfo('Param Save', out)

    def reboot(self):
        out = run_cmd([GX_SCRIPT, '-w', 'reboot', '-b', I2C_BUS])
        messagebox.showinfo('Reboot', out)

    def apply_params(self):
        cmds = []
        changes = []
        # Image Acquisition
        # (No parameters to apply, section is read-only)
        # Image Properties
        for cmd in self.imgprop_vars:
            if self.imgprop_vars[cmd].get() != self.initial_imgprop[cmd]:
                cmds.append([GX_SCRIPT, '-w', cmd, self.imgprop_vars[cmd].get(), '-b', I2C_BUS])
                changes.append((cmd, str(self.imgprop_vars[cmd].get())))
        # Image Processing
        for cmd in self.imgproc_vars:
            if self.imgproc_vars[cmd].get() != self.initial_imgproc[cmd]:
                cmds.append([GX_SCRIPT, '-w', cmd, self.imgproc_vars[cmd].get(), '-b', I2C_BUS])
                changes.append((cmd, str(self.imgproc_vars[cmd].get())))
        for cmd in self.imgproc_dual_vars:
            radio_var, slider_var = self.imgproc_dual_vars[cmd]
            initial_radio, initial_slider = self.initial_imgproc_dual[cmd]
            if radio_var.get() != initial_radio or slider_var.get() != initial_slider:
                cmds.append([GX_SCRIPT, '-w', cmd, str(radio_var.get()), str(slider_var.get()), '-b', I2C_BUS])
                changes.append((cmd, f"{radio_var.get()}, {slider_var.get()}"))
        # IO Control
        for cmd in self.ioctrl_vars:
            if self.ioctrl_vars[cmd].get() != self.initial_ioctrl[cmd]:
                cmds.append([GX_SCRIPT, '-w', cmd, self.ioctrl_vars[cmd].get(), '-b', I2C_BUS])
                changes.append((cmd, str(self.ioctrl_vars[cmd].get())))
        # Print changes to console
        if changes:
            print("Parameters to be applied:")
            for param, value in changes:
                print(f"  {param}: {value}")
        results = []
        for cmd in cmds:
            results.append(run_cmd(cmd))
        if results:
            messagebox.showinfo('Apply Params', '\n'.join(results))
        else:
            messagebox.showinfo('Apply Params', 'No parameters changed.')

if __name__ == '__main__':
    app = CameraConfigGUI()
    app.mainloop()

