# filepath: system_info_app.py
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import os
import socket
import platform
import subprocess
import psutil
import time
from PIL import Image, ImageTk
import winreg

class SystemInfo:
    """Utility class for fetching system information."""

    @staticmethod
    def get_ip():
        """Retrieve the system's IP address."""
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    @staticmethod
    def get_internal_disks():
        """Fetch information about internal disk partitions."""
        partitions = psutil.disk_partitions()
        internal_disks = []
        for partition in partitions:
            if "rw" in partition.opts and not partition.device.startswith("\\"):
                usage = psutil.disk_usage(partition.mountpoint)
                internal_disks.append({
                    "Device": partition.device,
                    "Mountpoint": partition.mountpoint,
                    "Total": usage.total,
                    "Used": usage.used,
                    "Free": usage.free
                })
        return internal_disks

    @staticmethod
    def get_network_adapters_info():
        """Get details about network adapters, including IPv4 and IPv6 addresses."""
        adapters = psutil.net_if_addrs()
        adapter_info = {}
        for adapter, addresses in adapters.items():
            adapter_info[adapter] = {
                'IPv4': [addr.address for addr in addresses if addr.family == socket.AF_INET],
                'IPv6': [addr.address for addr in addresses if addr.family == socket.AF_INET6]
            }
        return adapter_info

    @staticmethod
    def get_system_uptime():
        """Calculate system uptime in seconds since last boot."""
        boot_time = psutil.boot_time()
        return int(time.time() - boot_time)

    @staticmethod
    def get_hardware_info():
        """Retrieve hardware details, including CPU, RAM, manufacturer, and model."""
        cpu_count = psutil.cpu_count(logical=True)
        ram = psutil.virtual_memory()
        ram_total = f"{ram.total / (1024**3):.2f} GB"
        try:
            processor_info = subprocess.check_output("wmic cpu get name", shell=True).decode().strip().splitlines()
            cpu_info = processor_info[1].strip() if len(processor_info) > 1 else "Unknown"
        except Exception:
            try:
                reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                cpu_info = winreg.QueryValueEx(reg_key, "ProcessorNameString")[0]
                winreg.CloseKey(reg_key)
            except Exception:
                cpu_info = "Unknown"
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS")
            manufacturer = winreg.QueryValueEx(reg_key, "SystemManufacturer")[0]
            model = winreg.QueryValueEx(reg_key, "SystemProductName")[0]
            winreg.CloseKey(reg_key)
        except Exception:
            manufacturer = "Unknown"
            model = "Unknown"
        return cpu_count, ram_total, cpu_info, manufacturer, model


class SystemInfoApp:
    """Main application class for the System Information Tool."""

    def __init__(self, root):
        self.root = root
        self.root.title("Information System")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        self.create_widgets()

    def create_widgets(self):
        """Set up the main interface elements."""
        frame = tk.Frame(self.root, bg="white", bd=2, relief="groove")
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.setup_logo(frame)
        self.setup_system_info_tree(frame)
        self.setup_disk_info_tree(frame)
        self.setup_buttons(frame)

        # Ensure grid adjusts to resize
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=1)

    def setup_logo(self, frame):
        """Add a logo and title at the top of the interface."""
        try:
            logo_image = Image.open('logo.png').resize((100, 50))
            logo_photo = ImageTk.PhotoImage(logo_image)
            label_logo = tk.Label(frame, image=logo_photo, bg="white")
            label_logo.image = logo_photo
            label_logo.grid(row=0, column=0, padx=(0, 10), pady=10)
        except Exception as e:
            print(f"Error loading logo: {e}")
        label_title = tk.Label(frame, text="INFORMATION SYSTEM", font=("Arial", 24, "bold"), bg="white")
        label_title.grid(row=0, column=1, pady=10, sticky='w')

    def setup_system_info_tree(self, frame):
        """Set up the table displaying system information."""
        columns = ('Information', 'Value')
        self.tree_system = ttk.Treeview(frame, columns=columns, show='headings', height=10)
        self.tree_system.heading('Information', text='Information')
        self.tree_system.heading('Value', text='Value')
        self.tree_system.column('Information', width=200, anchor='w')
        self.tree_system.column('Value', width=400, anchor='w')
        self.tree_system.grid(row=1, column=0, columnspan=2, pady=10, sticky="nsew")
        self.populate_system_info()

    def populate_system_info(self):
        """Populate the system information table with data."""
        hostname = socket.gethostname()
        username = os.getlogin()
        ip_address = SystemInfo.get_ip()
        os_version = platform.platform()
        win32_ver = platform.win32_ver()
        win32_edition = platform.win32_edition()
        cpu_count, ram_total, cpu_info, manufacturer, model = SystemInfo.get_hardware_info()
        uptime_seconds = SystemInfo.get_system_uptime()

        infos = [
            ('Hostname', hostname),
            ('Username', username),
            ('IP Address', ip_address),
            ('Windows Version', os_version),
            ('Windows Details', win32_ver),
            ('Windows Edition', win32_edition),
            ('CPU Cores', cpu_count),
            ('Processor', cpu_info),
            ('Computer Brand', f"{manufacturer} {model}"),
            ('RAM', ram_total),
            ('Uptime', f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"),
        ]
        for info in infos:
            self.tree_system.insert('', tk.END, values=info)

    def setup_disk_info_tree(self, frame):
        """Set up the table displaying disk information."""
        columns = ('Disk', 'Mounted On', 'Total', 'Used', 'Free')
        self.tree_disk = ttk.Treeview(frame, columns=columns, show='headings', height=5)
        for col in columns:
            self.tree_disk.heading(col, text=col)
            self.tree_disk.column(col, anchor='center')
        self.tree_disk.grid(row=2, column=0, columnspan=2, pady=10, sticky="nsew")
        self.populate_disk_info()

    def populate_disk_info(self):
        """Populate the disk information table with data."""
        disks = SystemInfo.get_internal_disks()
        for disk in disks:
            total = f"{disk['Total'] / (1024**3):.2f} GB"
            used = f"{disk['Used'] / (1024**3):.2f} GB"
            free = f"{disk['Free'] / (1024**3):.2f} GB"
            self.tree_disk.insert('', tk.END, values=(disk['Device'], disk['Mountpoint'], total, used, free))

    def setup_buttons(self, frame):
        """Add action buttons at the bottom."""
        buttons = [
            ("Copy Information", self.copy_information),
            ("Open Event Viewer", self.open_logs),
            ("System Settings", self.open_system_settings),
            ("Open Task Manager", self.open_task_manager)
        ]
        for idx, (text, command) in enumerate(buttons):
            button = tk.Button(frame, text=text, command=command, bg="#2196F3", fg="white", width=20, height=2)
            button.grid(row=3 + idx // 2, column=idx % 2, padx=5, pady=5, sticky='ew')

    def copy_information(self):
        """Copy system information to clipboard."""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append("Information copied")
            self.root.update()
            messagebox.showinfo("Copied", "Information copied to clipboard.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_logs(self):
        """Open Windows Event Viewer."""
        try:
            os.startfile("eventvwr.msc")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_system_settings(self):
        """Open Windows system settings."""
        try:
            subprocess.run("start ms-settings:about", shell=True)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_task_manager(self):
        """Open Windows Task Manager."""
        try:
            subprocess.Popen("taskmgr")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = SystemInfoApp(root)
    root.mainloop()
