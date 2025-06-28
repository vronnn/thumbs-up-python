from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
from game_state import ThumbsUpGame
from socket import *
import socket

game = ThumbsUpGame()

class GameServer(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
    def do_GET(self):
        if self.path == '/join':
            player_id = self.headers.get('Player-ID')
            if game.add_player(player_id):
                response = {
                    'status': 'OK',
                    'message': 'Joined game',
                    'player_id': player_id,
                    'game_started': game.game_started
                }
            else:
                response = {
                    'status': 'ERROR',
                    'message': 'Game full or already joined'
                }
                
        elif self.path == '/game_state':
            player_id = self.headers.get('Player-ID')
            response = {
                'status': 'OK',
                'players': game.players,
                'current_turn': game.current_turn,
                'current_bet': game.current_bet,
                'is_my_turn': player_id == game.current_turn,
                'winner': game.winner,
                'waiting_for_players': game.waiting_for_players  # Track who hasn't submitted thumbs
            }
            
        self._set_response()
        self.wfile.write(json.dumps(response).encode('utf-8'))
        
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))
        player_id = self.headers.get('Player-ID')
        
        if self.path == '/submit_bet':
            if game.submit_bet(player_id, post_data['bet'], post_data['own_thumbs']):
                response = {'status': 'OK'}
            else:
                response = {'status': 'ERROR', 'message': 'Not your turn'}
                
        elif self.path == '/submit_thumbs':
            success = game.submit_thumbs(player_id, post_data['thumbs'])
            if success:
                response = {'status': 'OK'}
                
                # If all players submitted, evaluate the round
                if game.all_thumbs_submitted():
                    round_result = game.evaluate_round()
                    if round_result:
                        response['game_over'] = True
                        response['winner'] = game.winner
                    else:
                        response['next_turn'] = game.current_turn
            else:
                response = {'status': 'ERROR', 'message': 'Cannot submit thumbs'}
                
        self._set_response()
        self.wfile.write(json.dumps(response).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=GameServer, port=55556):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    # Add this line before serve_forever()
    httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()