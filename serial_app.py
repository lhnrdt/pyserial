import tkinter as tk
from tkinter import ttk
import serial
import threading
from datetime import datetime

# Function to handle receiving data in a separate thread


def receive_data(ser, text_widget: tk.Text, output_format):
    while True:
        if ser.in_waiting:
            incoming_data = ser.read(ser.in_waiting)
            if output_format.get() == "Binary":
                incoming_data_str = " ".join(f"{byte:08b}" for byte in incoming_data)
            else:  # ASCII
                incoming_data_str = incoming_data.decode('ascii', errors='replace')
            # display with timestamp
            string = f"[{datetime.now().strftime('%H:%M:%S')}]: {incoming_data_str}\n"
            text_widget.insert(tk.END, string)
            text_widget.see(tk.END)  # Auto-scroll

# Function to send data


def send_data(ser, data_entry, receive_text, output_format):
    if not data_entry.get():
        receive_text.insert(tk.END, "No data to send.\n")
        return

    # Get the binary string from the entry and split by spaces
    binary_strings = data_entry.get().split()
    # Convert each binary string to a byte
    bytes_to_send = bytearray()
    for binary_string in binary_strings:
        try:
            byte = int(binary_string, 2)  # Convert binary string to integer
            bytes_to_send.append(byte)
        except ValueError:
            receive_text.insert(tk.END, f"Invalid binary value: {binary_string}\n")
            # convert to binary and send

    # Send the bytes over the serial connection
    ser.write(bytes_to_send)

    # Clear entry after sending and log the sent data
    data_entry.delete(0, tk.END)
    formatted_data_str = " ".join(binary_strings)
    receive_text.insert(tk.END, f"Sent: {formatted_data_str} \n")

# Main GUI application


class SerialApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Serial Communication")
        self.geometry("500x400")

        # Output format option
        self.output_format = tk.StringVar(value="Binary")

        # Serial connection
        self.serial_connection = None

        # Configuration
        self.port = tk.StringVar(value="/dev/ttyUSB0")
        self.baud_rate = tk.IntVar(value=57600)

        # UI Setup
        ttk.Label(self, text="Port:").grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        port_entry = ttk.Entry(self, textvariable=self.port)
        port_entry.grid(column=1, row=0, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(self, text="Baud Rate:").grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)
        baud_rate_entry = ttk.Entry(self, textvariable=self.baud_rate)
        baud_rate_entry.grid(column=1, row=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(self, text="Output Format:").grid(column=0, row=2, padx=5, pady=5, sticky=tk.W)
        output_format_combo = ttk.Combobox(self, textvariable=self.output_format, values=["Binary", "ASCII"])
        output_format_combo.grid(column=1, row=2, padx=5, pady=5, sticky=tk.EW)
        output_format_combo.current(0)

        self.connect_button = ttk.Button(self, text="Connect", command=self.connect)
        self.connect_button.grid(column=2, row=0, rowspan=3, padx=5, pady=5, sticky=tk.EW)

        self.connection_status_label = ttk.Label(self, text="Status: Disconnected")
        self.connection_status_label.grid(column=0, row=3, columnspan=3, padx=5, pady=5, sticky=tk.W)

        ttk.Label(self, text="Send Data:").grid(column=0, row=4, padx=5, pady=5, sticky=tk.W)
        self.data_entry = ttk.Entry(self)
        self.data_entry.grid(column=1, row=4, padx=5, pady=5, sticky=tk.EW)

        send_button = ttk.Button(self, text="Send", command=self.send)
        send_button.grid(column=2, row=4, padx=5, pady=5, sticky=tk.EW)

        self.receive_text = tk.Text(self, height=10)
        self.receive_text.grid(column=0, row=5, columnspan=3, padx=5, pady=5, sticky=tk.EW)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(5, weight=1)

    def connect(self):
        if self.serial_connection:
            self.disconnect()  # Call disconnect method
        else:
            port = self.port.get()
            baud_rate = self.baud_rate.get()
            try:
                self.serial_connection = serial.Serial(port, baud_rate)
                if self.serial_connection:
                    threading.Thread(target=receive_data, args=(self.serial_connection, self.receive_text, self.output_format), daemon=True).start()
                    self.receive_text.insert(tk.END, f"Connected to {port} at {baud_rate} baud.\n")
                    self.update_connection_status(True)
            except serial.SerialException as e:
                self.receive_text.insert(tk.END, f"Connection Error: {e}\n")

    def disconnect(self):
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
            self.receive_text.insert(tk.END, "Disconnected.\n")
            self.update_connection_status(False)

    def send(self):
        if self.serial_connection:
            # Now passing receive_text widget to send_data for error logging
            send_data(self.serial_connection, self.data_entry, self.receive_text, self.output_format)
        else:
            self.receive_text.insert(tk.END, "Not connected.\n")

    def update_connection_status(self, connected):
        if connected:
            self.connect_button.config(text="Disconnect")
            self.connection_status_label.config(text="Status: Connected")
        else:
            self.connect_button.config(text="Connect")
            self.connection_status_label.config(text="Status: Disconnected")


if __name__ == "__main__":
    app = SerialApp()
    app.mainloop()
