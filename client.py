import requests
import json
import time

SERVER_URL = 'http://localhost:55556'

class ThumbsUpClient:
    def __init__(self, player_id):
        self.player_id = player_id
        self.headers = {'Player-ID': player_id}
        self.join_game()
        
    def join_game(self):
        response = requests.get(f'{SERVER_URL}/join', headers=self.headers)
        return response.json()
        
    def get_game_state(self):
        response = requests.get(f'{SERVER_URL}/game_state', headers=self.headers)
        return response.json()
        
    def submit_bet(self, bet, own_thumbs):
        data = {'bet': bet, 'own_thumbs': own_thumbs}
        response = requests.post(
            f'{SERVER_URL}/submit_bet',
            headers=self.headers,
            json=data
        )
        return response.json()
        
    def submit_thumbs(self, thumbs):
        data = {'thumbs': thumbs}
        response = requests.post(
            f'{SERVER_URL}/submit_thumbs',
            headers=self.headers,
            json=data
        )
        return response.json()
        
    def play_turn(self):
        while True:
            state = self.get_game_state()
            
            if state.get('winner'):
                print(f"Game over! Winner is {state['winner']}")
                return
                
            if state['is_my_turn']:
                print("\nIt's your turn!")
                print(f"Current game state: {state['players']}")
                bet = int(input("Enter your bet for total thumbs: "))
                own_thumbs = int(input("Enter how many thumbs you're raising (0-2): "))
                self.submit_bet(bet, own_thumbs)
                print("Waiting for other players to submit their thumbs...")
                
                # Wait until round is evaluated
                while True:
                    state = self.get_game_state()
                    if not state['current_bet'] or state.get('winner'):
                        break
                    time.sleep(1)
            else:
                if state['current_bet'] and self.player_id in state['waiting_for_players']:
                    print(f"\nPlayer {state['current_turn']} has bet {state['current_bet']['bet']}")
                    thumbs = int(input("Enter how many thumbs you're raising (0-2): "))
                    self.submit_thumbs(thumbs)
                    print("Waiting for round evaluation...")
                    
                    # Wait until round is evaluated
                    while True:
                        state = self.get_game_state()
                        if not state['current_bet'] or state.get('winner'):
                            break
                        time.sleep(1)
                else:
                    print("Waiting for current player to make a bet...")
                    time.sleep(1)

if __name__ == '__main__':
    player_id = input("Enter your player ID: ")
    client = ThumbsUpClient(player_id)
    client.play_turn()