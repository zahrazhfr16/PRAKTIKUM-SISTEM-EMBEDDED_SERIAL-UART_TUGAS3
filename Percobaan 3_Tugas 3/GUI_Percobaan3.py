import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime

# ─────────────────────────────────────────────
#  Konstanta warna (Catppuccin Mocha)
# ─────────────────────────────────────────────
CLR_BG         = "#1e1e2e"
CLR_PANEL      = "#2a2a3e"
CLR_BORDER     = "#44475a"
CLR_TEXT       = "#cdd6f4"
CLR_SUBTEXT    = "#6c7086"
CLR_GREEN      = "#a6e3a1"
CLR_RED        = "#f38ba8"
CLR_YELLOW     = "#f9e2af"
CLR_BLUE       = "#89b4fa"
CLR_MAUVE      = "#cba6f7"
CLR_BTN_SEND   = "#313244"
CLR_BTN_HOVER  = "#45475a"

LED_ON_COLOR   = "#f9e2af"   # kuning menyala
LED_OFF_COLOR  = "#45475a"   # abu-abu mati
SW_PRESS_COLOR = "#a6e3a1"   # hijau – PRESSED
SW_REL_COLOR   = "#45475a"   # abu-abu – Released


class UartGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("STM32F103 – LED Control & Switch Monitor  |  USART Half-Duplex")
        self.configure(bg=CLR_BG)
        self.geometry("900x620")
        self.minsize(800, 520)

        self._serial: serial.Serial | None = None
        self._rx_thread: threading.Thread | None = None
        self._running = False

        # State LED (4) & Switch (2)
        self._led_state = [False] * 4
        self._sw_state  = [False] * 2

        self._tx_count  = 0
        self._rx_count  = 0

        self._build_ui()
        self._refresh_ports()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─────────────────────────────────────────
    #  Bangun antarmuka
    # ─────────────────────────────────────────
    def _build_ui(self):
        # ── Baris atas: koneksi ──────────────────────────────
        top = tk.Frame(self, bg=CLR_BG, pady=6, padx=10)
        top.pack(fill=tk.X)

        tk.Label(top, text="Port:", bg=CLR_BG, fg=CLR_TEXT,
                 font=("Segoe UI", 10)).pack(side=tk.LEFT)

        self._port_cb = ttk.Combobox(top, width=14, state="readonly",
                                     font=("Segoe UI", 10))
        self._port_cb.pack(side=tk.LEFT, padx=(4, 12))

        tk.Label(top, text="Baud:", bg=CLR_BG, fg=CLR_TEXT,
                 font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self._baud_cb = ttk.Combobox(top, width=9, state="readonly",
                                     values=["9600", "19200", "38400",
                                             "57600", "115200", "230400"],
                                     font=("Segoe UI", 10))
        self._baud_cb.set("115200")
        self._baud_cb.pack(side=tk.LEFT, padx=(4, 12))

        tk.Button(top, text="⟳ Refresh",
                  command=self._refresh_ports,
                  bg=CLR_BTN_SEND, fg=CLR_TEXT,
                  activebackground=CLR_BTN_HOVER,
                  relief=tk.FLAT, padx=8,
                  font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 6))

        self._btn_connect = tk.Button(top, text="Connect",
                                      command=self._toggle_connect,
                                      bg="#2e7d32", fg="white",
                                      activebackground="#388e3c",
                                      relief=tk.FLAT, padx=12,
                                      font=("Segoe UI", 10, "bold"))
        self._btn_connect.pack(side=tk.LEFT)

        self._status_lbl = tk.Label(top, text="● Terputus",
                                    bg=CLR_BG, fg=CLR_RED,
                                    font=("Segoe UI", 10))
        self._status_lbl.pack(side=tk.LEFT, padx=12)

        # ── Tengah: terminal + panel kanan ──────────────────
        mid = tk.Frame(self, bg=CLR_BG)
        mid.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))

        # Terminal log (kiri)
        log_frame = tk.Frame(mid, bg=CLR_PANEL, bd=1,
                             relief=tk.SOLID, highlightthickness=1,
                             highlightbackground=CLR_BORDER)
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="Terminal Log", bg=CLR_PANEL,
                 fg=CLR_SUBTEXT, font=("Segoe UI", 9)).pack(anchor=tk.W,
                                                             padx=6, pady=(4, 0))

        self._log = scrolledtext.ScrolledText(
            log_frame, bg="#11111b", fg=CLR_TEXT,
            insertbackground=CLR_TEXT, relief=tk.FLAT,
            font=("Consolas", 10), wrap=tk.WORD,
            state=tk.DISABLED)
        self._log.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._log.tag_config("rx",   foreground=CLR_GREEN)
        self._log.tag_config("tx",   foreground=CLR_BLUE)
        self._log.tag_config("info", foreground=CLR_YELLOW)
        self._log.tag_config("err",  foreground=CLR_RED)
        self._log.tag_config("sw",   foreground=CLR_MAUVE)

        # Panel kanan
        right = tk.Frame(mid, bg=CLR_BG, width=230)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        right.pack_propagate(False)

        # ── Kontrol LED (4 buah) ─────────────────────────────
        tk.Label(right, text="Kontrol LED",
                 bg=CLR_BG, fg=CLR_SUBTEXT,
                 font=("Segoe UI", 9, "bold")).pack(pady=(4, 4))

        led_names = [
            "LED 1  (PA0)", "LED 2  (PA1)",
            "LED 3  (PA2)", "LED 4  (PA3)",
        ]
        self._led_canvas = []
        for idx, name in enumerate(led_names):
            frm = tk.Frame(right, bg=CLR_PANEL, bd=0,
                           highlightthickness=1,
                           highlightbackground=CLR_BORDER)
            frm.pack(fill=tk.X, pady=2)

            c = tk.Canvas(frm, width=18, height=18,
                          bg=CLR_PANEL, bd=0, highlightthickness=0)
            c.pack(side=tk.LEFT, padx=5, pady=3)
            oval = c.create_oval(1, 1, 17, 17, fill=LED_OFF_COLOR, outline="")
            self._led_canvas.append((c, oval))

            tk.Label(frm, text=name, bg=CLR_PANEL, fg=CLR_TEXT,
                     font=("Segoe UI", 9), width=11,
                     anchor=tk.W).pack(side=tk.LEFT)

            i = idx
            tk.Button(frm, text="ON",
                      command=lambda i=i: self._send_cmd(f"LED{i+1}_ON"),
                      bg="#1b5e20", fg="white",
                      activebackground="#2e7d32",
                      relief=tk.FLAT, padx=5, pady=1,
                      font=("Segoe UI", 8, "bold")).pack(
                          side=tk.LEFT, padx=(0, 2), pady=3)

            tk.Button(frm, text="OFF",
                      command=lambda i=i: self._send_cmd(f"LED{i+1}_OFF"),
                      bg="#b71c1c", fg="white",
                      activebackground="#c62828",
                      relief=tk.FLAT, padx=5, pady=1,
                      font=("Segoe UI", 8, "bold")).pack(
                          side=tk.LEFT, padx=(0, 4), pady=3)

        # Separator
        tk.Frame(right, bg=CLR_BORDER, height=1).pack(fill=tk.X, pady=6)

        # ── Monitor Switch (2 buah) ──────────────────────────
        sw_header = tk.Frame(right, bg=CLR_BG)
        sw_header.pack(fill=tk.X, pady=(0, 4))
        tk.Label(sw_header, text="Monitor Switch",
                 bg=CLR_BG, fg=CLR_SUBTEXT,
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        tk.Button(sw_header, text="Poll SW?",
                  command=lambda: self._send_cmd("SW?"),
                  bg="#1565c0", fg="white",
                  activebackground="#1976d2",
                  relief=tk.FLAT, padx=6, pady=1,
                  font=("Segoe UI", 8, "bold")).pack(side=tk.RIGHT, padx=(0, 4))

        self._sw_canvas = []
        self._sw_labels = []
        for idx, name in enumerate(["SW 1  (PB0)", "SW 2  (PB1)"]):
            frm = tk.Frame(right, bg=CLR_PANEL, bd=0,
                           highlightthickness=1,
                           highlightbackground=CLR_BORDER)
            frm.pack(fill=tk.X, pady=2)

            c = tk.Canvas(frm, width=18, height=18,
                          bg=CLR_PANEL, bd=0, highlightthickness=0)
            c.pack(side=tk.LEFT, padx=5, pady=3)
            oval = c.create_oval(1, 1, 17, 17, fill=SW_REL_COLOR, outline="")
            self._sw_canvas.append((c, oval))

            tk.Label(frm, text=name, bg=CLR_PANEL, fg=CLR_TEXT,
                     font=("Segoe UI", 9), anchor=tk.W,
                     width=11).pack(side=tk.LEFT)

            lbl = tk.Label(frm, text="Released",
                           bg=CLR_PANEL, fg=CLR_SUBTEXT,
                           font=("Segoe UI", 8))
            lbl.pack(side=tk.LEFT, padx=(0, 4))
            self._sw_labels.append(lbl)

        # Separator
        tk.Frame(right, bg=CLR_BORDER, height=1).pack(fill=tk.X, pady=6)

        # ── Statistik ────────────────────────────────────────
        tk.Label(right, text="Statistik",
                 bg=CLR_BG, fg=CLR_SUBTEXT,
                 font=("Segoe UI", 9, "bold")).pack()

        self._stat_tx = tk.StringVar(value="TX: 0 byte")
        self._stat_rx = tk.StringVar(value="RX: 0 byte")
        for sv in (self._stat_tx, self._stat_rx):
            tk.Label(right, textvariable=sv, bg=CLR_BG, fg=CLR_TEXT,
                     font=("Consolas", 9)).pack(anchor=tk.W, padx=4)

        # ── Bawah: kirim manual ──────────────────────────────
        bot = tk.Frame(self, bg=CLR_PANEL, bd=1,
                       relief=tk.SOLID, highlightthickness=1,
                       highlightbackground=CLR_BORDER)
        bot.pack(fill=tk.X, padx=10, pady=(0, 8))

        tk.Label(bot, text="Kirim:", bg=CLR_PANEL,
                 fg=CLR_SUBTEXT, font=("Segoe UI", 10)).pack(
                     side=tk.LEFT, padx=8, pady=6)

        self._entry = tk.Entry(bot, bg="#11111b", fg=CLR_TEXT,
                               insertbackground=CLR_TEXT,
                               relief=tk.FLAT, font=("Consolas", 11))
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=6)
        self._entry.bind("<Return>", lambda e: self._send_manual())

        self._nl_var = tk.BooleanVar(value=True)
        tk.Checkbutton(bot, text="\\n", variable=self._nl_var,
                       bg=CLR_PANEL, fg=CLR_TEXT, selectcolor=CLR_BTN_SEND,
                       activebackground=CLR_PANEL,
                       font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=6)

        self._btn_send = tk.Button(bot, text="Kirim ▶",
                                   command=self._send_manual,
                                   bg="#1565c0", fg="white",
                                   activebackground="#1976d2",
                                   relief=tk.FLAT, padx=12, pady=4,
                                   font=("Segoe UI", 10, "bold"),
                                   state=tk.DISABLED)
        self._btn_send.pack(side=tk.LEFT, padx=6, pady=4)

        tk.Button(bot, text="Bersihkan",
                  command=self._clear_log,
                  bg=CLR_BTN_SEND, fg=CLR_SUBTEXT,
                  activebackground=CLR_BTN_HOVER,
                  relief=tk.FLAT, padx=8, pady=4,
                  font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8), pady=4)

    # ─────────────────────────────────────────
    #  Refresh daftar port COM
    # ─────────────────────────────────────────
    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self._port_cb["values"] = ports
        if ports:
            self._port_cb.current(0)

    # ─────────────────────────────────────────
    #  Connect / Disconnect
    # ─────────────────────────────────────────
    def _toggle_connect(self):
        if self._serial and self._serial.is_open:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self._port_cb.get()
        baud = int(self._baud_cb.get())
        if not port:
            self._log_msg("[!] Pilih port COM terlebih dahulu.\n", "err")
            return
        try:
            self._serial = serial.Serial(port, baud, timeout=0.1)
            self._running = True
            self._rx_thread = threading.Thread(
                target=self._rx_loop, daemon=True)
            self._rx_thread.start()

            self._btn_connect.config(text="Disconnect",
                                     bg="#c62828", activebackground="#d32f2f")
            self._status_lbl.config(
                text=f"● Terhubung  {port} @ {baud}", fg=CLR_GREEN)
            self._btn_send.config(state=tk.NORMAL)
            self._log_msg(
                f"[INFO] Terhubung ke {port} @ {baud} baud\n", "info")
        except serial.SerialException as exc:
            self._log_msg(f"[ERR] Gagal buka port: {exc}\n", "err")

    def _disconnect(self):
        self._running = False
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._btn_connect.config(text="Connect",
                                 bg="#2e7d32", activebackground="#388e3c")
        self._status_lbl.config(text="● Terputus", fg=CLR_RED)
        self._btn_send.config(state=tk.DISABLED)
        self._log_msg("[INFO] Koneksi diputus.\n", "info")
        for i in range(4):
            self._set_led(i, False)
        self._set_sw(0, False)
        self._set_sw(1, False)

    # ─────────────────────────────────────────
    #  Thread penerima RX
    # ─────────────────────────────────────────
    def _rx_loop(self):
        buf = ""
        while self._running:
            try:
                raw = self._serial.read(64)
                if raw:
                    buf += raw.decode("utf-8", errors="replace")
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        line = line.strip()
                        if line:
                            self._rx_count += len(line)
                            self._schedule(self._handle_rx_line, line)
            except serial.SerialException:
                break
            time.sleep(0.02)

    def _handle_rx_line(self, line: str):
        ts = datetime.now().strftime("%H:%M:%S")

        # LED feedback (4 LED)
        led_map = {
            "LED1:ON": (0, True),  "LED1:OFF": (0, False),
            "LED2:ON": (1, True),  "LED2:OFF": (1, False),
            "LED3:ON": (2, True),  "LED3:OFF": (2, False),
            "LED4:ON": (3, True),  "LED4:OFF": (3, False),
        }
        sw_map = {
            "SW1:PRESSED":  (0, True),  "SW1:RELEASED": (0, False),
            "SW2:PRESSED":  (1, True),  "SW2:RELEASED": (1, False),
        }

        if line in led_map:
            idx, state = led_map[line]
            self._set_led(idx, state)
            self._log_msg(f"[{ts}] ← {line}\n", "rx")
        elif line in sw_map:
            idx, state = sw_map[line]
            self._set_sw(idx, state)
            self._log_msg(f"[{ts}] ← {line}\n", "sw")
        else:
            self._log_msg(f"[{ts}] ← {line}\n", "info")

        self._update_stats()

    # ─────────────────────────────────────────
    #  Kirim perintah LED
    # ─────────────────────────────────────────
    def _send_cmd(self, cmd: str):
        if not (self._serial and self._serial.is_open):
            self._log_msg("[!] Belum terhubung.\n", "err")
            return
        try:
            data = (cmd + "\n").encode("utf-8")
            self._serial.write(data)
            self._tx_count += len(data)
            ts = datetime.now().strftime("%H:%M:%S")
            self._log_msg(f"[{ts}] → {cmd}\n", "tx")
            self._update_stats()
        except serial.SerialException as exc:
            self._log_msg(f"[ERR] Gagal kirim: {exc}\n", "err")

    def _send_manual(self):
        text = self._entry.get()
        if not text:
            return
        self._send_cmd(text)
        self._entry.delete(0, tk.END)

    # ─────────────────────────────────────────
    #  Helpers UI
    # ─────────────────────────────────────────
    def _log_msg(self, msg: str, tag: str = ""):
        self._log.config(state=tk.NORMAL)
        self._log.insert(tk.END, msg, tag)
        self._log.see(tk.END)
        self._log.config(state=tk.DISABLED)

    def _clear_log(self):
        self._log.config(state=tk.NORMAL)
        self._log.delete("1.0", tk.END)
        self._log.config(state=tk.DISABLED)

    def _set_led(self, index: int, on: bool):
        c, oval = self._led_canvas[index]
        c.itemconfig(oval, fill=LED_ON_COLOR if on else LED_OFF_COLOR)
        self._led_state[index] = on

    def _set_sw(self, index: int, pressed: bool):
        c, oval = self._sw_canvas[index]
        c.itemconfig(oval, fill=SW_PRESS_COLOR if pressed else SW_REL_COLOR)
        self._sw_labels[index].config(
            text="PRESSED" if pressed else "Released",
            fg=CLR_GREEN if pressed else CLR_SUBTEXT)
        self._sw_state[index] = pressed

    def _update_stats(self):
        self._stat_tx.set(f"TX: {self._tx_count} byte")
        self._stat_rx.set(f"RX: {self._rx_count} byte")

    def _schedule(self, fn, *args):
        """Jadwalkan pemanggilan fungsi UI dari thread RX."""
        self.after(0, fn, *args)

    # ─────────────────────────────────────────
    #  Tutup jendela
    # ─────────────────────────────────────────
    def _on_close(self):
        self._disconnect()
        self.destroy()


if __name__ == "__main__":
    app = UartGui()
    app.mainloop()
