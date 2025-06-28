import pygame
import requests
import json
import sys
import time

# Server config
SERVER_URL = 'http://localhost:55556'

# Pygame setup
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Thumbs Up Game")
font = pygame.font.SysFont('Arial', 24)
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_BLUE = (173, 216, 230)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

class InputBox:
    def __init__(self, x, y, w, h, text='', active=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = LIGHT_BLUE if active else GRAY
        self.text = text
        self.txt_surface = font.render(text, True, BLACK)
        self.active = active
        self.numeric_only = True
        self.enabled = True  # Add enabled state

    def handle_event(self, event):
        if not self.enabled:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Only activate if the box is enabled and clicked
            if self.rect.collidepoint(event.pos):
                self.active = True
                self.color = LIGHT_BLUE
                return False
            
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if self.numeric_only and event.unicode.isdigit():
                    self.text += event.unicode
                elif not self.numeric_only:
                    self.text += event.unicode
                    
            self.txt_surface = font.render(self.text, True, BLACK)
        return False

    def set_enabled(self, enabled):
        """Enable or disable the input box"""
        self.enabled = enabled
        if not enabled:
            self.active = False
            self.color = GRAY
        else:
            self.color = LIGHT_BLUE if self.active else GRAY

    def update(self):
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        # Draw differently based on enabled state
        color = self.color if self.enabled else GRAY
        pygame.draw.rect(screen, color, self.rect, 2)
        
        # Text color based on enabled state
        text_color = BLACK if self.enabled else (128, 128, 128)
        text_surface = font.render(self.text, True, text_color)
        screen.blit(text_surface, (self.rect.x+5, self.rect.y+5))

class ThumbsUpClientGUI:
    def __init__(self, player_id):
        self.player_id = player_id
        self.headers = {'Player-ID': player_id}
        
        # Initialize game connection
        try:
            self.join_game()
            self.connection_error = False
        except requests.exceptions.ConnectionError:
            self.connection_error = True
            self.message = "Failed to connect to server"
        
        # Input boxes
        self.bet_box = InputBox(300, 200, 200, 32, '', False)
        self.thumbs_box = InputBox(300, 300, 200, 32, '', False)
        self.submit_btn = pygame.Rect(300, 400, 200, 50)
        
        # Game state
        self.game_state = {}
        self.message = "Connecting to game..."
        self.running = True
        
        # Submission tracking
        self.has_submitted_bet = False
        self.has_submitted_thumbs = False
        self.my_bet = None
        self.my_thumbs = None
        self.last_current_bet = None  # Track when bet changes to reset submission state
        
    def join_game(self):
        response = requests.get(f'{SERVER_URL}/join', headers=self.headers)
        return response.json()
        
    def get_game_state(self):
        try:
            response = requests.get(f'{SERVER_URL}/game_state', headers=self.headers)
            return response.json()
        except requests.exceptions.ConnectionError:
            return {'status': 'ERROR', 'message': 'Connection failed'}
        
    def submit_bet(self, bet, own_thumbs):
        try:
            data = {'bet': bet, 'own_thumbs': own_thumbs}
            response = requests.post(
                f'{SERVER_URL}/submit_bet',
                headers=self.headers,
                json=data,
                timeout=3
            )
            return response.json()
        except requests.exceptions.RequestException:
            return {'status': 'ERROR', 'message': 'Submission failed'}
        
    def submit_thumbs(self, thumbs):
        try:
            data = {'thumbs': thumbs}
            response = requests.post(
                f'{SERVER_URL}/submit_thumbs',
                headers=self.headers,
                json=data,
                timeout=3
            )
            return response.json()
        except requests.exceptions.RequestException:
            return {'status': 'ERROR', 'message': 'Submission failed'}
        
    def handle_events(self):
        submit_clicked = False
        bet_return = False
        thumbs_return = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # Handle input boxes
            if self.bet_box.handle_event(event):
                bet_return = True
            if self.thumbs_box.handle_event(event):
                thumbs_return = True
                
            # Handle mouse clicks for deactivating boxes
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if submit button was clicked
                if self.submit_btn.collidepoint(event.pos):
                    submit_clicked = True
                else:
                    # Deactivate boxes if clicking outside them
                    if not self.bet_box.rect.collidepoint(event.pos):
                        if self.bet_box.enabled:
                            self.bet_box.active = False
                            self.bet_box.color = LIGHT_BLUE if self.bet_box.enabled else GRAY
                    if not self.thumbs_box.rect.collidepoint(event.pos):
                        if self.thumbs_box.enabled:
                            self.thumbs_box.active = False
                            self.thumbs_box.color = LIGHT_BLUE if self.thumbs_box.enabled else GRAY
                    
        return submit_clicked or bet_return or thumbs_return
        
    def update(self):
        if self.connection_error:
            time.sleep(1)  # Try to reconnect
            try:
                self.join_game()
                self.connection_error = False
                self.message = "Reconnected to game!"
            except:
                return
                
        # Get latest game state
        self.game_state = self.get_game_state()
        
        if self.game_state.get('status') == 'ERROR':
            self.message = "Connection error. Retrying..."
            time.sleep(1)
            return
            
        if self.game_state.get('winner'):
            self.message = f"Game over! Winner is {self.game_state['winner']}"
            return
        
        # Check if we need to reset submission state (new round started)
        current_bet = self.game_state.get('current_bet')
        if self.last_current_bet != current_bet:
            if current_bet is None:  # Round ended, reset for next round
                self.has_submitted_bet = False
                self.has_submitted_thumbs = False
                self.my_bet = None
                self.my_thumbs = None
            elif self.last_current_bet is None and current_bet is not None:
                # New bet started, reset thumbs submission but keep bet if I made it
                if current_bet.get('player') != self.player_id:
                    self.has_submitted_thumbs = False
                    self.my_thumbs = None
            self.last_current_bet = current_bet
            
        # Update input box visibility and enabled state
        self.update_input_visibility()
        
        # Handle submission if needed
        if self.handle_events():
            if self.game_state.get('is_my_turn', False) and not self.has_submitted_bet:
                self.handle_bet_submission()
            elif (self.game_state.get('current_bet') and 
                  self.player_id in self.game_state.get('waiting_for_players', []) and 
                  not self.has_submitted_thumbs):
                self.handle_thumbs_submission()
        
        # Update input boxes
        self.bet_box.update()
        self.thumbs_box.update()
        
    def handle_bet_submission(self):
        try:
            bet = int(self.bet_box.text) if self.bet_box.text else 0
            thumbs = int(self.thumbs_box.text) if self.thumbs_box.text else 0
            
            if not self.bet_box.text or not self.thumbs_box.text:
                self.message = "Please fill in both bet and thumbs!"
                return
                
            if 0 <= thumbs <= 2:
                result = self.submit_bet(bet, thumbs)
                if result.get('status') == 'OK':
                    self.message = "Bet submitted! Waiting for other players..."
                    # Store the submitted values and mark as submitted
                    self.my_bet = bet
                    self.my_thumbs = thumbs
                    self.has_submitted_bet = True
                    # Clear input boxes
                    self.bet_box.text = ''
                    self.thumbs_box.text = ''
                    self.bet_box.txt_surface = font.render('', True, BLACK)
                    self.thumbs_box.txt_surface = font.render('', True, BLACK)
                else:
                    self.message = result.get('message', 'Submission failed')
            else:
                self.message = "Thumbs must be 0-2!"
        except ValueError:
            self.message = "Please enter valid numbers!"
            
    def handle_thumbs_submission(self):
        try:
            if not self.thumbs_box.text:
                self.message = "Please enter number of thumbs!"
                return
                
            thumbs = int(self.thumbs_box.text)
            if 0 <= thumbs <= 2:
                result = self.submit_thumbs(thumbs)
                if result.get('status') == 'OK':
                    self.message = "Thumbs submitted! Waiting for round evaluation..."
                    # Store the submitted thumbs and mark as submitted
                    self.my_thumbs = thumbs
                    self.has_submitted_thumbs = True
                    # Clear input box
                    self.thumbs_box.text = ''
                    self.thumbs_box.txt_surface = font.render('', True, BLACK)
                else:
                    self.message = result.get('message', 'Submission failed')
            else:
                self.message = "Thumbs must be 0-2!"
        except ValueError:
            self.message = "Please enter a valid number!"
            
    def update_input_visibility(self):
        is_my_turn = self.game_state.get('is_my_turn', False)
        current_bet = self.game_state.get('current_bet')
        waiting_for_me = self.player_id in self.game_state.get('waiting_for_players', [])
        
        # Enable bet box only when it's my turn AND I haven't submitted yet
        self.bet_box.set_enabled(is_my_turn and not self.has_submitted_bet)
        
        # Enable thumbs box when:
        # 1. It's my turn and I haven't submitted bet yet, OR
        # 2. I need to respond to a bet and haven't submitted thumbs yet
        thumbs_enabled = ((is_my_turn and not self.has_submitted_bet) or 
                         (current_bet and waiting_for_me and not self.has_submitted_thumbs))
        self.thumbs_box.set_enabled(thumbs_enabled)
        
    def draw(self):
        screen.fill(WHITE)
        
        # Title
        title = font.render(f"Player: {self.player_id}", True, BLACK)
        screen.blit(title, (20, 20))
        
        # Game state
        if 'players' in self.game_state:
            state_text = font.render("Game State:", True, BLACK)
            screen.blit(state_text, (20, 60))
            
            y_offset = 90
            for player, thumbs in self.game_state['players'].items():
                player_text = font.render(f"{player}: {thumbs} thumbs", True, 
                                        GREEN if player == self.player_id else BLACK)
                screen.blit(player_text, (20, y_offset))
                y_offset += 30
                
            turn_text = font.render(
                f"Current turn: {self.game_state.get('current_turn', '')}",
                True, BLACK
            )
            screen.blit(turn_text, (20, y_offset + 20))
        
        # Message display
        msg_text = font.render(self.message, True, RED)
        screen.blit(msg_text, (20, HEIGHT - 50))
        
        # Input fields - show different interfaces based on game state and submission status
        if self.game_state.get('is_my_turn', False):
            if self.has_submitted_bet:
                self.draw_submitted_bet_display()
            else:
                self.draw_bet_interface()
        elif self.game_state.get('current_bet') and self.player_id in self.game_state.get('waiting_for_players', []):
            if self.has_submitted_thumbs:
                self.draw_submitted_thumbs_display()
            else:
                self.draw_thumbs_interface()
        elif self.game_state.get('current_bet') and self.has_submitted_thumbs:
            self.draw_submitted_thumbs_display()
        else:
            self.draw_waiting_message()
        
        pygame.display.flip()
        
    def draw_bet_interface(self):
        bet_label = font.render("Your bet for total thumbs:", True, BLACK)
        screen.blit(bet_label, (20, 200))
        self.bet_box.draw(screen)
        
        thumbs_label = font.render("Your thumbs to raise (0-2):", True, BLACK)
        screen.blit(thumbs_label, (20, 300))
        self.thumbs_box.draw(screen)
        
        pygame.draw.rect(screen, GREEN, self.submit_btn)
        submit_text = font.render("Submit", True, BLACK)
        screen.blit(submit_text, (self.submit_btn.x + 70, self.submit_btn.y + 15))
        
    def draw_thumbs_interface(self):
        bet = self.game_state.get('current_bet', {}).get('bet', 0)
        bet_label = font.render(f"Player {self.game_state['current_turn']} bet: {bet}", True, BLACK)
        screen.blit(bet_label, (20, 200))
        
        thumbs_label = font.render("Your thumbs to raise (0-2):", True, BLACK)
        screen.blit(thumbs_label, (20, 300))
        self.thumbs_box.draw(screen)
        
        pygame.draw.rect(screen, GREEN, self.submit_btn)
        submit_text = font.render("Submit", True, BLACK)
        screen.blit(submit_text, (self.submit_btn.x + 70, self.submit_btn.y + 15))
        
    def draw_waiting_message(self):
        wait_text = font.render("Waiting for other players...", True, BLACK)
        screen.blit(wait_text, (300, 250))
        
    def draw_submitted_bet_display(self):
        """Display the submitted bet and thumbs (read-only)"""
        bet_label = font.render(f"Your bet: {self.my_bet} total thumbs", True, GREEN)
        screen.blit(bet_label, (50, 200))
        
        thumbs_label = font.render(f"Your thumbs: {self.my_thumbs}", True, GREEN)
        screen.blit(thumbs_label, (50, 250))
        
        status_text = font.render("✓ Bet submitted - waiting for other players", True, GREEN)
        screen.blit(status_text, (50, 300))
        
    def draw_submitted_thumbs_display(self):
        """Display the submitted thumbs for responding to a bet (read-only)"""
        current_bet = self.game_state.get('current_bet', {})
        bet_label = font.render(f"Player {current_bet.get('player', '')} bet: {current_bet.get('bet', 0)}", True, BLACK)
        screen.blit(bet_label, (50, 200))
        
        thumbs_label = font.render(f"Your thumbs: {self.my_thumbs}", True, GREEN)
        screen.blit(thumbs_label, (50, 250))
        
        status_text = font.render("✓ Thumbs submitted - waiting for round evaluation", True, GREEN)
        screen.blit(status_text, (50, 300))
        
    def run(self):
        while self.running:
            self.update()
            self.draw()
            clock.tick(30)
            
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python client_gui.py <player_id>")
        sys.exit(1)
        
    client = ThumbsUpClientGUI(sys.argv[1])
    client.run()