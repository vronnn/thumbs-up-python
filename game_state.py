class ThumbsUpGame:
    def __init__(self):
        self.players = {}  # {player_id: remaining_thumbs}
        self.current_turn = None
        self.current_bet = None
        self.game_started = False
        self.winner = None
        self.submissions = []  # Track thumb submissions
        self.waiting_for_players = []  # Track who hasn't submitted thumbs
        
    def add_player(self, player_id):
        if len(self.players) < 3 and player_id not in self.players:
            self.players[player_id] = 2  # Start with 5 thumbs
            if len(self.players) >= 2 and not self.game_started:
                self.start_game()
            return True
        return False
    
    def start_game(self):
        self.game_started = True
        self.current_turn = list(self.players.keys())[0]  # First player starts
        
    def submit_bet(self, player_id, bet, own_thumbs):
        if player_id != self.current_turn:
            return False
            
        self.current_bet = {
            'player': player_id,
            'bet': bet,
            'own_thumbs': own_thumbs
        }
        self.submissions = [{'player': player_id, 'thumbs': own_thumbs}]  # Reset submissions
        self.waiting_for_players = [p for p in self.players if p != player_id]  # Others must submit
        return True
    
    def submit_thumbs(self, player_id, thumbs):
        if player_id not in self.waiting_for_players:
            return False  # Already submitted or not their turn
            
        self.submissions.append({'player': player_id, 'thumbs': thumbs})
        self.waiting_for_players.remove(player_id)
        return True
    
    def all_thumbs_submitted(self):
        return len(self.waiting_for_players) == 0
    
    def evaluate_round(self):
        if not self.current_bet or not self.all_thumbs_submitted():
            return False
            
        total_thumbs = sum(sub['thumbs'] for sub in self.submissions)
        
        if total_thumbs == self.current_bet['bet']:
            # Correct bet - remove one thumb
            betting_player = self.current_bet['player']
            self.players[betting_player] -= 1
            
            # Check for winner
            if self.players[betting_player] <= 0:
                self.winner = betting_player
                return True
                
        # Move to next player
        player_list = list(self.players.keys())
        current_index = player_list.index(self.current_turn)
        next_index = (current_index + 1) % len(player_list)
        self.current_turn = player_list[next_index]
        self.current_bet = None
        self.submissions = []
        return False