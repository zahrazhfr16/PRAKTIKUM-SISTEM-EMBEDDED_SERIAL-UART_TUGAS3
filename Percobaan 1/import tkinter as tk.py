import tkinter as tk
import serial
import threading

ser = serial.Serial('COM5',115200,timeout=1)

def send(cmd):
    ser.write((cmd+"\n").encode())

def update_btn(b1,b2):
    lbl1.config(text="BTN1: "+("TEKAN" if b1=="1" else "LEPAS"))
    lbl2.config(text="BTN2: "+("TEKAN" if b2=="1" else "LEPAS"))

def read_serial():
    while True:
        try:
            line=ser.readline().decode().strip()

            if line.startswith("BTN1"):
                parts=line.split(",")
                b1=parts[0].split(":")[1]
                b2=parts[1].split(":")[1]

                root.after(0,update_btn,b1,b2)
        except:
            pass

root=tk.Tk()
root.title("ESP32 Control Panel")

tk.Button(root,text="LED1 ON",width=10,
command=lambda:send("LED1:1")).pack()

tk.Button(root,text="LED1 OFF",width=10,
command=lambda:send("LED1:0")).pack()

tk.Button(root,text="LED2 ON",width=10,
command=lambda:send("LED2:1")).pack()

tk.Button(root,text="LED2 OFF",width=10,
command=lambda:send("LED2:0")).pack()

lbl1=tk.Label(root,text="BTN1: -",font=("Arial",12))
lbl1.pack(pady=5)

lbl2=tk.Label(root,text="BTN2: -",font=("Arial",12))
lbl2.pack(pady=5)

threading.Thread(target=read_serial,daemon=True).start()

root.mainloop()