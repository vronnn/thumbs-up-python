import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import requests
import time
import os

SERVER_URL = 'http://localhost:55556'

class ThumbsUpClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Thumbs Up Game 🎮")
        self.root.geometry("400x550")
        self.root.resizable(False, False)

        # Load background image
        bg_path = "thumb.png"
        if os.path.exists(bg_path):
            self.bg_image = Image.open(bg_path).resize((400, 550))
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label = tk.Label(self.root, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Main white frame
        self.frame = tk.Frame(root, bg="white", bd=0, highlightthickness=2, highlightbackground="#4FC3F7")
        self.frame.place(relx=0.5, rely=0.5, anchor="center", width=340, height=460)

        self.player_id = ""
        self.headers = {}
        self.current_phase = None

        self.setup_login_screen()

    def setup_login_screen(self):
        self.clear_frame()

        if os.path.exists("like.png"):
            thumb_icon = Image.open("like.png").resize((60, 60))
            self.thumb_photo = ImageTk.PhotoImage(thumb_icon)
            tk.Label(self.frame, image=self.thumb_photo, bg="white").pack(pady=(10, 0))

        tk.Label(self.frame, text="👍 THUMBS UP GAME", font=("Arial", 16, "bold"), bg="white", fg="#2196F3").pack(pady=10)
        tk.Label(self.frame, text="Enter your Player ID", font=("Arial", 12), bg="white").pack(pady=10)

        self.entry_player_id = tk.Entry(self.frame, font=("Arial", 12), fg="black", relief="solid", bd=1)
        self.entry_player_id.pack(pady=5)

        tk.Button(self.frame, text="Join Game", command=self.join_game,
                  bg="#4CAF50", fg="white", font=("Arial", 11), width=20, relief="flat").pack(pady=15)

        self.footer = tk.Label(self.frame, text="Created by Team 15", font=("Arial", 8), bg="white", fg="gray")
        self.footer.pack(side="bottom", pady=5)

    def join_game(self):
        self.player_id = self.entry_player_id.get()
        self.headers = {'Player-ID': self.player_id}
        try:
            response = requests.get(f'{SERVER_URL}/join', headers=self.headers).json()
            if response['status'] == 'OK':
                self.setup_game_screen()
                threading.Thread(target=self.update_game_state, daemon=True).start()
            else:
                messagebox.showerror("Error", response['message'])
        except Exception:
            messagebox.showerror("Connection Error", "Failed to connect to server.")

    def setup_game_screen(self):
        self.clear_frame()

        if os.path.exists("thumb_icon.png"):
            thumb_icon = Image.open("thumb_icon.png").resize((60, 60))
            self.thumb_photo = ImageTk.PhotoImage(thumb_icon)
            tk.Label(self.frame, image=self.thumb_photo, bg="white").pack(pady=(10, 0))

        tk.Label(self.frame, text="👍 THUMBS UP GAME", font=("Arial", 16, "bold"), bg="white", fg="#2196F3").pack(pady=10)

        self.label_status = tk.Label(self.frame, text="Game started...", font=("Arial", 12, "bold"), bg="white")
        self.label_status.pack(pady=8)

        self.label_turn = tk.Label(self.frame, text="", font=("Arial", 12), bg="white")
        self.label_turn.pack(pady=5)

        self.label_players = tk.Label(self.frame, text="", font=("Arial", 12), bg="white")
        self.label_players.pack(pady=5)

        self.entry_bet = tk.Entry(self.frame, font=("Arial", 12), fg="gray", relief="solid", bd=1)
        self.entry_thumbs = tk.Entry(self.frame, font=("Arial", 12), fg="gray", relief="solid", bd=1)
        self.button_submit = tk.Button(self.frame, text="Submit", bg="#FFB74D", fg="white", font=("Arial", 11),
                                       width=15, relief="flat")

        self.set_placeholder(self.entry_bet, "Enter your bet")
        self.set_placeholder(self.entry_thumbs, "Thumbs (0-2)")

        self.footer = tk.Label(self.frame, text="Created by Team 15", font=("Arial", 8), bg="white", fg="gray")
        self.footer.pack(side="bottom", pady=5)

    def update_game_state(self):
        while True:
            try:
                state = requests.get(f'{SERVER_URL}/game_state', headers=self.headers).json()
                self.render_game_state(state)
                time.sleep(1)
            except:
                break

    def render_game_state(self, state):
        if state.get('winner'):
            winner = state['winner']
            self.show_game_over_screen(winner)
            return

        self.label_players.config(text=f"Players: {state['players']}")
        self.label_turn.config(text=f"Current turn: {state['current_turn']}")

        if state['is_my_turn']:
            new_phase = "bet"
        elif state['current_bet'] and self.player_id in state['waiting_for_players']:
            new_phase = "thumb"
        else:
            new_phase = "waiting"

        if self.current_phase != new_phase:
            self.current_phase = new_phase
            if new_phase == "bet":
                self.label_status.config(text="🎯 It's your turn to bet!")
                self.show_bet_input()
            elif new_phase == "thumb":
                self.label_status.config(text=f"🖐 Player {state['current_turn']} bet {state['current_bet']['bet']}")
                self.show_thumb_input()
            else:
                self.label_status.config(text="⏳ Waiting for others...")
                self.hide_inputs()

    def show_bet_input(self):
        self.hide_inputs()
        self.entry_bet.pack(pady=5)
        self.entry_thumbs.pack(pady=5)
        self.set_placeholder(self.entry_bet, "Enter your bet")
        self.set_placeholder(self.entry_thumbs, "Thumbs (0-2)")
        self.button_submit.config(command=self.submit_bet)
        self.button_submit.pack(pady=10)

    def show_thumb_input(self):
        self.hide_inputs()
        self.entry_thumbs.pack(pady=5)
        self.set_placeholder(self.entry_thumbs, "Thumbs (0-2)")
        self.button_submit.config(command=self.submit_thumbs)
        self.button_submit.pack(pady=10)

    def submit_bet(self):
        bet_text = self.entry_bet.get()
        thumb_text = self.entry_thumbs.get()
        if bet_text in ["", "Enter your bet"] or thumb_text in ["", "Thumbs (0-2)"]:
            messagebox.showerror("Invalid Input", "Please enter valid numbers.")
            return
        try:
            bet = int(bet_text)
            own_thumbs = int(thumb_text)
            response = requests.post(f'{SERVER_URL}/submit_bet', headers=self.headers,
                                     json={'bet': bet, 'own_thumbs': own_thumbs}).json()
            if response['status'] != 'OK':
                messagebox.showerror("Error", response['message'])
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter numbers between 0 and 2.")

    def submit_thumbs(self):
        thumb_text = self.entry_thumbs.get()
        if thumb_text in ["", "Thumbs (0-2)"]:
            messagebox.showerror("Invalid Input", "Please enter your thumbs.")
            return
        try:
            thumbs = int(thumb_text)
            response = requests.post(f'{SERVER_URL}/submit_thumbs', headers=self.headers,
                                     json={'thumbs': thumbs}).json()
            if response['status'] != 'OK':
                messagebox.showerror("Error", response['message'])
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a number between 0 and 2.")

    def set_placeholder(self, entry, placeholder):
        entry.delete(0, tk.END)
        entry.insert(0, placeholder)
        entry.config(fg='gray')

        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg='black')

        def on_focus_out(event):
            if entry.get() == "":
                entry.insert(0, placeholder)
                entry.config(fg='gray')

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def hide_inputs(self):
        self.entry_bet.pack_forget()
        self.entry_thumbs.pack_forget()
        self.button_submit.pack_forget()

    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    def show_game_over_screen(self, winner):
        self.clear_frame()

        is_winner = (winner == self.player_id)
        result_text = "🎉 You Win!" if is_winner else "😢 You Lose!"
        result_color = "#A5D6A7" if is_winner else "#EF9A9A"
        image_path = "winner.png" if is_winner else "loser.png"

        self.frame.config(bg=result_color)

        if os.path.exists(image_path):
            img = Image.open(image_path).resize((100, 100))
            self.end_photo = ImageTk.PhotoImage(img)
            tk.Label(self.frame, image=self.end_photo, bg=result_color).pack(pady=(30, 10))

        tk.Label(self.frame, text=result_text, font=("Arial", 18, "bold"), bg=result_color).pack(pady=(0, 5))
        tk.Label(self.frame, text=f"Winner: {winner}", font=("Arial", 12), bg=result_color).pack(pady=(0, 15))

        tk.Button(self.frame, text="🔁 Play Again", command=self.setup_login_screen,
                  bg="#4FC3F7", fg="white", font=("Arial", 11), width=20).pack(pady=5)
        tk.Button(self.frame, text="❌ Exit", command=self.root.quit,
                  bg="#E57373", fg="white", font=("Arial", 11), width=20).pack(pady=5)


if __name__ == '__main__':
    root = tk.Tk()
    app = ThumbsUpClientGUI(root)
    root.mainloop()

