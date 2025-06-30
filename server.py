import sys
import os.path
import uuid
import json
import socket
import threading
from glob import glob
from datetime import datetime
from game_state import ThumbsUpGame

class GameHttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {}
        self.types['.json'] = 'application/json'
        self.types['.txt'] = 'text/plain'
        self.types['.html'] = 'text/html'
        self.game = ThumbsUpGame()
        
    def response(self, kode=404, message='Not Found', messagebody=bytes(), headers={}):
        tanggal = datetime.now().strftime('%c')
        resp = []
        resp.append("HTTP/1.0 {} {}\r\n".format(kode, message))
        resp.append("Date: {}\r\n".format(tanggal))
        resp.append("Connection: close\r\n")
        resp.append("Server: gameserver/1.0\r\n")
        resp.append("Content-Length: {}\r\n".format(len(messagebody)))
        for kk in headers:
            resp.append("{}:{}\r\n".format(kk, headers[kk]))
        resp.append("\r\n")

        response_headers = ''
        for i in resp:
            response_headers = "{}{}".format(response_headers, i)
        
        # Convert messagebody to bytes if it's not already
        if (type(messagebody) is not bytes):
            messagebody = messagebody.encode()

        response = response_headers.encode() + messagebody
        return response

    def proses(self, data):
        requests = data.split("\r\n")
        baris = requests[0]
        
        # Parse headers
        all_headers = {}
        for header_line in requests[1:]:
            if header_line == '':
                break
            if ':' in header_line:
                key, value = header_line.split(':', 1)
                all_headers[key.strip()] = value.strip()
        
        # Find request body for POST requests
        request_body = ''
        try:
            empty_line_index = requests.index('')
            if empty_line_index < len(requests) - 1:
                request_body = '\r\n'.join(requests[empty_line_index + 1:])
        except ValueError:
            pass

        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            if (method == 'GET'):
                object_address = j[1].strip()
                return self.http_get(object_address, all_headers)
            if (method == 'POST'):
                object_address = j[1].strip()
                return self.http_post(object_address, all_headers, request_body)
            else:
                return self.response(400, 'Bad Request', '', {})
        except IndexError:
            return self.response(400, 'Bad Request', '', {})

    def http_get(self, object_address, headers):
        player_id = headers.get('Player-ID', '')
        
        if object_address == '/join':
            if self.game.add_player(player_id):
                response_data = {
                    'status': 'OK',
                    'message': 'Joined game',
                    'player_id': player_id,
                    'game_started': self.game.game_started
                }
            else:
                response_data = {
                    'status': 'ERROR',
                    'message': 'Game full or already joined'
                }
                
        elif object_address == '/game_state':
            response_data = {
                'status': 'OK',
                'players': self.game.players,
                'current_turn': self.game.current_turn,
                'current_bet': self.game.current_bet,
                'is_my_turn': player_id == self.game.current_turn,
                'winner': self.game.winner,
                'waiting_for_players': self.game.waiting_for_players
            }
        else:
            # Default 404 response
            return self.response(404, 'Not Found', '', {})
        
        # Convert response to JSON and return
        json_response = json.dumps(response_data)
        response_headers = {'Content-type': 'application/json'}
        return self.response(200, 'OK', json_response, response_headers)

    def http_post(self, object_address, headers, request_body):
        player_id = headers.get('Player-ID', '')
        
        try:
            post_data = json.loads(request_body) if request_body else {}
        except json.JSONDecodeError:
            return self.response(400, 'Bad Request', 'Invalid JSON', {})
        
        if object_address == '/submit_bet':
            if self.game.submit_bet(player_id, post_data.get('bet'), post_data.get('own_thumbs')):
                response_data = {'status': 'OK'}
            else:
                response_data = {'status': 'ERROR', 'message': 'Not your turn'}
                
        elif object_address == '/submit_thumbs':
            success = self.game.submit_thumbs(player_id, post_data.get('thumbs'))
            if success:
                response_data = {'status': 'OK'}
                
                # If all players submitted, evaluate the round
                if self.game.all_thumbs_submitted():
                    round_result = self.game.evaluate_round()
                    if round_result:
                        response_data['game_over'] = True
                        response_data['winner'] = self.game.winner
                    else:
                        response_data['next_turn'] = self.game.current_turn
            else:
                response_data = {'status': 'ERROR', 'message': 'Cannot submit thumbs'}
        else:
            return self.response(404, 'Not Found', '', {})
        
        # Convert response to JSON and return
        json_response = json.dumps(response_data)
        response_headers = {'Content-type': 'application/json'}
        return self.response(200, 'OK', json_response, response_headers)

    def run_server(self, host='localhost', port=55556):
        """Run the server to accept client connections"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((host, port))
            server_socket.listen(5)
            print(f'Game server started on {host}:{port}')
            print('Waiting for connections...')
            
            while True:
                client_socket, client_address = server_socket.accept()
                print(f'Connection from {client_address}')
                
                # Handle each client in a separate thread
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print('\nShutting down server...')
        finally:
            server_socket.close()
    
    def handle_client(self, client_socket, client_address):
        """Handle individual client connections"""
        try:
            while True:
                # Receive data from client
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                print(f'Received from {client_address}: {data[:100]}...')
                
                # Process the HTTP request
                response = self.proses(data)
                
                # Send response back to client
                client_socket.send(response)
                
                # Close connection after response (HTTP/1.0 behavior)
                break
                
        except Exception as e:
            print(f'Error handling client {client_address}: {e}')
        finally:
            client_socket.close()
            print(f'Connection with {client_address} closed')

if __name__ == "__main__":
    gameserver = GameHttpServer()
    
    # Run the server
    gameserver.run_server(host='0.0.0.0', port=55556)