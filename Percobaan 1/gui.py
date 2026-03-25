import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time


class ESP32GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 UART Controller")
        self.root.resizable(False, False)

        self.serial_conn = None
        self.running = False
        self.led1_state = False
        self.led2_state = False

        self._build_ui()
        self._refresh_ports()

    def _build_ui(self):
        self.root.configure(bg="#1e1e2e")
        pad = dict(padx=10, pady=6)

        conn_frame = tk.LabelFrame(
            self.root, text=" Koneksi Serial ",
            bg="#1e1e2e", fg="#cdd6f4",
            font=("Segoe UI", 10, "bold"),
            relief="groove", bd=2
        )
        conn_frame.grid(row=0, column=0, columnspan=2, sticky="ew",
                        padx=14, pady=(14, 4))

        tk.Label(conn_frame, text="Port:", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Segoe UI", 9)).grid(row=0, column=0, **pad)

        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(
            conn_frame, textvariable=self.port_var,
            width=14, state="readonly"
        )
        self.port_combo.grid(row=0, column=1, **pad)

        tk.Label(conn_frame, text="Baud:", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Segoe UI", 9)).grid(row=0, column=2, **pad)

        self.baud_var = tk.StringVar(value="115200")
        baud_combo = ttk.Combobox(
            conn_frame,
            textvariable=self.baud_var,
            values=["9600", "19200", "38400", "57600", "115200"],
            width=8,
            state="readonly"
        )
        baud_combo.grid(row=0, column=3, **pad)

        self.btn_refresh = tk.Button(
            conn_frame, text="↻", width=3,
            command=self._refresh_ports,
            bg="#313244", fg="#cdd6f4", relief="flat",
            font=("Segoe UI", 11), cursor="hand2"
        )
        self.btn_refresh.grid(row=0, column=4, padx=(0, 4), pady=6)

        self.btn_connect = tk.Button(
            conn_frame, text="Hubungkan",
            command=self._toggle_connect,
            bg="#a6e3a1", fg="#1e1e2e", relief="flat",
            font=("Segoe UI", 9, "bold"), width=12, cursor="hand2"
        )
        self.btn_connect.grid(row=0, column=5, **pad)

        wiring_frame = tk.Frame(conn_frame, bg="#313244")
        wiring_frame.grid(row=1, column=0, columnspan=6, sticky="ew",
                          padx=8, pady=(0, 8))

        tk.Label(
            wiring_frame,
            text="Wiring ESP32:",
            bg="#313244", fg="#fab387",
            font=("Segoe UI", 8, "bold")
        ).grid(row=0, column=0, padx=(8, 16), pady=4)

        wiring_text = "LED1=GPIO23   LED2=GPIO22   BTN1=GPIO18   BTN2=GPIO5"
        tk.Label(
            wiring_frame,
            text=wiring_text,
            bg="#313244", fg="#cdd6f4",
            font=("Consolas", 8, "bold")
        ).grid(row=0, column=1, padx=4, pady=4)

        led_frame = tk.LabelFrame(
            self.root, text=" Kontrol LED ",
            bg="#1e1e2e", fg="#cdd6f4",
            font=("Segoe UI", 10, "bold"),
            relief="groove", bd=2
        )
        led_frame.grid(row=1, column=0, sticky="nsew", padx=(14, 6), pady=4)

        tk.Label(led_frame, text="LED 1 (Pin 23)",
                 bg="#1e1e2e", fg="#cdd6f4",
                 font=("Segoe UI", 9)).grid(row=0, column=0, columnspan=2, pady=(8, 2))

        self.led1_indicator = tk.Canvas(led_frame, width=28, height=28,
                                        bg="#1e1e2e", highlightthickness=0)
        self.led1_circle = self.led1_indicator.create_oval(
            4, 4, 24, 24, fill="#45475a", outline="#6c7086"
        )
        self.led1_indicator.grid(row=1, column=0, columnspan=2, pady=2)

        self.btn_led1_on = tk.Button(
            led_frame, text="ON", width=6,
            command=lambda: self._set_led(1, True),
            bg="#a6e3a1", fg="#1e1e2e", relief="flat",
            font=("Segoe UI", 9, "bold"), cursor="hand2", state="disabled"
        )
        self.btn_led1_on.grid(row=2, column=0, padx=6, pady=8)

        self.btn_led1_off = tk.Button(
            led_frame, text="OFF", width=6,
            command=lambda: self._set_led(1, False),
            bg="#f38ba8", fg="#1e1e2e", relief="flat",
            font=("Segoe UI", 9, "bold"), cursor="hand2", state="disabled"
        )
        self.btn_led1_off.grid(row=2, column=1, padx=6, pady=8)

        tk.Label(led_frame, text="LED 2 (Pin 22)",
                 bg="#1e1e2e", fg="#cdd6f4",
                 font=("Segoe UI", 9)).grid(row=3, column=0, columnspan=2, pady=(8, 2))

        self.led2_indicator = tk.Canvas(led_frame, width=28, height=28,
                                        bg="#1e1e2e", highlightthickness=0)
        self.led2_circle = self.led2_indicator.create_oval(
            4, 4, 24, 24, fill="#45475a", outline="#6c7086"
        )
        self.led2_indicator.grid(row=4, column=0, columnspan=2, pady=2)

        self.btn_led2_on = tk.Button(
            led_frame, text="ON", width=6,
            command=lambda: self._set_led(2, True),
            bg="#a6e3a1", fg="#1e1e2e", relief="flat",
            font=("Segoe UI", 9, "bold"), cursor="hand2", state="disabled"
        )
        self.btn_led2_on.grid(row=5, column=0, padx=6, pady=8)

        self.btn_led2_off = tk.Button(
            led_frame, text="OFF", width=6,
            command=lambda: self._set_led(2, False),
            bg="#f38ba8", fg="#1e1e2e", relief="flat",
            font=("Segoe UI", 9, "bold"), cursor="hand2", state="disabled"
        )
        self.btn_led2_off.grid(row=5, column=1, padx=6, pady=8)

        btn_frame = tk.LabelFrame(
            self.root, text=" Status Tombol ",
            bg="#1e1e2e", fg="#cdd6f4",
            font=("Segoe UI", 10, "bold"),
            relief="groove", bd=2
        )
        btn_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 14), pady=4)

        for label_text, row, attr in [
            ("BTN 1 (Pin 18)", 0, "btn1"),
            ("BTN 2 (Pin 5)", 3, "btn2"),
        ]:
            tk.Label(btn_frame, text=label_text,
                     bg="#1e1e2e", fg="#cdd6f4",
                     font=("Segoe UI", 9)).grid(row=row, column=0,
                                                 padx=18, pady=(8, 2))

            canvas = tk.Canvas(btn_frame, width=28, height=28,
                               bg="#1e1e2e", highlightthickness=0)
            circle = canvas.create_oval(
                4, 4, 24, 24, fill="#45475a", outline="#6c7086"
            )
            canvas.grid(row=row + 1, column=0, padx=18, pady=2)

            lbl = tk.Label(btn_frame, text="RELEASED",
                           bg="#1e1e2e", fg="#6c7086",
                           font=("Segoe UI", 8, "bold"))
            lbl.grid(row=row + 2, column=0, pady=(0, 6))

            setattr(self, f"{attr}_canvas", canvas)
            setattr(self, f"{attr}_circle", circle)
            setattr(self, f"{attr}_label", lbl)

        log_frame = tk.LabelFrame(
            self.root, text=" Log Serial ",
            bg="#1e1e2e", fg="#cdd6f4",
            font=("Segoe UI", 10, "bold"),
            relief="groove", bd=2
        )
        log_frame.grid(row=2, column=0, columnspan=2, sticky="ew",
                       padx=14, pady=(4, 14))

        self.log_text = tk.Text(
            log_frame, height=8, width=62,
            bg="#181825", fg="#cdd6f4",
            font=("Consolas", 9), relief="flat",
            state="disabled", wrap="word",
            insertbackground="#cdd6f4"
        )
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.grid(row=0, column=0, padx=(8, 0), pady=8)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 4), pady=8)

        btn_clear = tk.Button(
            log_frame, text="Bersihkan Log",
            command=self._clear_log,
            bg="#313244", fg="#cdd6f4", relief="flat",
            font=("Segoe UI", 8), cursor="hand2"
        )
        btn_clear.grid(row=1, column=0, columnspan=2, pady=(0, 6))

        self.status_var = tk.StringVar(value="Tidak terhubung")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            bg="#313244", fg="#a6e3a1",
            font=("Segoe UI", 8), anchor="w", padx=10
        )
        status_bar.grid(row=3, column=0, columnspan=2, sticky="ew")

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports:
            self.port_combo.current(0)

    def _toggle_connect(self):
        if self.serial_conn and self.serial_conn.is_open:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self.port_var.get()
        baud = int(self.baud_var.get())

        if not port:
            messagebox.showwarning("Port kosong", "Pilih port COM terlebih dahulu.")
            return

        try:
            self.serial_conn = serial.Serial(port, baud, timeout=1)
            self.running = True
            self._set_connected_state(True)
            self._log(f"[INFO] Terhubung ke {port} @ {baud} baud\n")

            thread = threading.Thread(target=self._read_loop, daemon=True)
            thread.start()

            time.sleep(0.3)
            self._send("PING")

        except serial.SerialException as e:
            messagebox.showerror("Gagal terhubung", str(e))

    def _disconnect(self):
        self.running = False
        time.sleep(0.3)

        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None

        self._set_connected_state(False)
        self._log("[INFO] Terputus\n")

    def _set_connected_state(self, connected: bool):
        color = "#f38ba8" if connected else "#a6e3a1"
        text = "Putuskan" if connected else "Hubungkan"
        self.btn_connect.configure(bg=color, text=text)

        state = "normal" if connected else "disabled"
        for btn in (self.btn_led1_on, self.btn_led1_off,
                    self.btn_led2_on, self.btn_led2_off):
            btn.configure(state=state)

        port = self.port_var.get()
        self.status_var.set(
            f"Terhubung: {port} @ {self.baud_var.get()} baud"
            if connected else "Tidak terhubung"
        )

    def _read_loop(self):
        while self.running and self.serial_conn and self.serial_conn.is_open:
            try:
                line = self.serial_conn.readline().decode("utf-8", errors="replace").strip()
                if line:
                    self._log(f"[RX] {line}\n")
                    self._parse_status(line)
            except serial.SerialException:
                break

        self.running = False

    def _send(self, command: str):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write((command + "\n").encode("utf-8"))
                self._log(f"[TX] {command}\n")
            except serial.SerialException as e:
                self._log(f"[ERR] {e}\n")

    def _set_led(self, led_num: int, state: bool):
        cmd = f"LED{led_num}:{'1' if state else '0'}"
        self._send(cmd)

        if led_num == 1:
            self.led1_state = state
            self._update_led_indicator(self.led1_indicator, self.led1_circle, state)
        else:
            self.led2_state = state
            self._update_led_indicator(self.led2_indicator, self.led2_circle, state)

    def _update_led_indicator(self, canvas, circle, state: bool):
        color = "#f9e2af" if state else "#45475a"
        outline = "#fab387" if state else "#6c7086"
        canvas.itemconfig(circle, fill=color, outline=outline)

    def _parse_status(self, line: str):
        if "BTN1:" not in line or "BTN2:" not in line:
            return

        try:
            parts = dict(p.split(":") for p in line.split(","))
            b1 = int(parts["BTN1"])
            b2 = int(parts["BTN2"])

            self.root.after(
                0, self._update_btn_indicator,
                self.btn1_canvas, self.btn1_circle, self.btn1_label, b1
            )
            self.root.after(
                0, self._update_btn_indicator,
                self.btn2_canvas, self.btn2_circle, self.btn2_label, b2
            )
        except (ValueError, KeyError):
            pass

    def _update_btn_indicator(self, canvas, circle, label, pressed: int):
        if pressed:
            canvas.itemconfig(circle, fill="#89b4fa", outline="#74c7ec")
            label.configure(text="DITEKAN", fg="#89b4fa")
        else:
            canvas.itemconfig(circle, fill="#45475a", outline="#6c7086")
            label.configure(text="RELEASED", fg="#6c7086")

    def _log(self, msg: str):
        def _append():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", msg)
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.root.after(0, _append)

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def on_close(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ESP32GUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()