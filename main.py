import time
import threading
import tkinter as tk
from pynput.mouse import Controller, Button
from pynput.keyboard import Listener, KeyCode, Key

# -----------------------
# Configurações visuais
# -----------------------
BG_COLOR = "#2E2E2E"
OVERLAY_BG = "#1E1E1E"
FG_COLOR = "white"
BUTTON_GREEN = "#4CAF50"
BUTTON_GREEN_HOVER = "#45a049"
BUTTON_RED = "#f44336"
BUTTON_RED_HOVER = "#da190b"
FONT_TITLE = ("Arial", 14, "bold")
FONT_LABEL = ("Arial", 12, "bold")
FONT_BUTTON = ("Arial", 11, "bold")
SLEEP_TIME = 0.01
PADDING = 10
FADE_STEP = 0.05  # velocidade do fade
FADE_DELAY = 20   # milissegundos entre passos

class AutoClicker:
    def __init__(self):
        self.clicking = False
        self.running = True
        self.mouse = Controller()
        self.toggle_key_vk = 84  # tecla padrão 'T'

        # Janela overlay (HUD)
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # remove bordas
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0)  # inicial transparente
        self.root.configure(bg=BG_COLOR)

        self.canvas = tk.Canvas(self.root, bg=OVERLAY_BG, highlightthickness=0)
        self.canvas.pack()

        self.overlay_text = self.canvas.create_text(
            PADDING, PADDING,
            text="AutoClick OFF",
            font=FONT_TITLE,
            fill=FG_COLOR,
            anchor="nw"
        )

        self.update_overlay()
        self.hide_overlay(instant=True)

        # Janela de configuração
        self.setup_config_window()

        # Threads
        threading.Thread(target=self.clicker_loop, daemon=True).start()
        threading.Thread(target=self.follow_mouse_loop, daemon=True).start()

        # Listener teclado
        self.listener = Listener(on_press=self.toggle_event)
        self.listener.start()

        self.root.mainloop()

    # -----------------------
    # Overlay com fade
    # -----------------------
    def fade_in(self):
        alpha = 0
        while alpha < 0.85:
            alpha += FADE_STEP
            if alpha > 0.85: alpha = 0.85
            self.root.attributes("-alpha", alpha)
            self.root.update()
            time.sleep(FADE_DELAY/1000)

    def fade_out(self):
        alpha = self.root.attributes("-alpha")
        while alpha > 0:
            alpha -= FADE_STEP
            if alpha < 0: alpha = 0
            self.root.attributes("-alpha", alpha)
            self.root.update()
            time.sleep(FADE_DELAY/1000)
        self.root.withdraw()

    def show_overlay(self):
        self.update_overlay()
        self.root.deiconify()
        threading.Thread(target=self.fade_in, daemon=True).start()

    def hide_overlay(self, instant=False):
        if instant:
            self.root.withdraw()
        else:
            threading.Thread(target=self.fade_out, daemon=True).start()

    def update_overlay(self):
        status = "ON" if self.clicking else "OFF"
        text = f"AutoClick {status} - Tecla: {self.get_toggle_key_display()}"
        self.canvas.itemconfig(self.overlay_text, text=text)
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox(self.overlay_text)
        width = bbox[2] + PADDING*2
        height = bbox[3] + PADDING*2
        self.canvas.config(width=width, height=height)

    # -----------------------
    # Janela de configuração
    # -----------------------
    def setup_config_window(self):
        self.config_window = tk.Toplevel(self.root)
        self.config_window.title("AutoClick")
        self.config_window.attributes("-topmost", True)
        self.config_window.geometry("260x180")
        self.config_window.configure(bg=BG_COLOR)

        tk.Label(self.config_window, text="Escolha a Tecla", font=FONT_LABEL, bg=BG_COLOR, fg=FG_COLOR).pack(pady=5)

        self.key_label = tk.Label(self.config_window, text=f"Tecla atual: {self.get_toggle_key_display()}",
                                  font=FONT_LABEL, bg=BG_COLOR, fg="#00FF00")
        self.key_label.pack(pady=5)

        select_btn = tk.Button(self.config_window, text="Selecionar Tecla", font=FONT_BUTTON,
                               bg=BUTTON_GREEN, fg="white", relief="raised", bd=3, activebackground=BUTTON_GREEN_HOVER,
                               command=self.get_new_key)
        select_btn.pack(pady=8)
        select_btn.bind("<Enter>", lambda e: select_btn.config(bg=BUTTON_GREEN_HOVER))
        select_btn.bind("<Leave>", lambda e: select_btn.config(bg=BUTTON_GREEN))

        close_btn = tk.Button(self.config_window, text="Fechar", font=FONT_BUTTON,
                              bg=BUTTON_RED, fg="white", relief="raised", bd=3, activebackground=BUTTON_RED_HOVER,
                              command=self.close_program)
        close_btn.pack(pady=8)
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg=BUTTON_RED_HOVER))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg=BUTTON_RED))

        self.config_window.protocol("WM_DELETE_WINDOW", self.close_program)

    # -----------------------
    # Seleção de tecla
    # -----------------------
    def get_new_key(self):
        capture_window = tk.Toplevel(self.config_window)
        capture_window.title("Pressione a tecla")
        capture_window.geometry("220x100")
        capture_window.attributes("-topmost", True)
        capture_window.configure(bg=BG_COLOR)

        tk.Label(capture_window, text="Pressione a nova tecla", font=("Arial", 10), bg=BG_COLOR, fg=FG_COLOR).pack(pady=20)

        def on_key(event):
            self.toggle_key_vk = event.keycode
            self.key_label.config(text=f"Tecla atual: {event.keysym.upper()}")
            self.update_overlay()
            capture_window.destroy()
            return "break"

        capture_window.bind_all("<Key>", on_key)
        capture_window.focus_set()

    # -----------------------
    # Lógica de clique
    # -----------------------
    def clicker_loop(self):
        while self.running:
            if self.clicking:
                self.mouse.click(Button.left, 1)
            time.sleep(SLEEP_TIME)

    def follow_mouse_loop(self):
        while self.running:
            if self.clicking:
                x, y = self.mouse.position
                self.root.geometry(f"+{x + 15}+{y + 15}")
            time.sleep(SLEEP_TIME)

    # -----------------------
    # Toggle do autoclick
    # -----------------------
    def toggle_event(self, key):
        vk = None
        if isinstance(key, KeyCode):
            vk = key.vk
        elif isinstance(key, Key):
            try:
                vk = key.value.vk
            except AttributeError:
                return

        if vk == self.toggle_key_vk:
            self.clicking = not self.clicking
            if self.clicking:
                self.show_overlay()
            else:
                self.hide_overlay()
            self.update_overlay()

    # -----------------------
    # Exibe tecla em maiúscula
    # -----------------------
    def get_toggle_key_display(self):
        try:
            return chr(self.toggle_key_vk).upper()
        except:
            return str(self.toggle_key_vk)

    # -----------------------
    # Fechar programa
    # -----------------------
    def close_program(self):
        self.running = False
        self.listener.stop()
        self.root.destroy()


# -----------------------
# Executar AutoClickert
# -----------------------
if __name__ == "__main__":
    AutoClicker()
