import subprocess
import sys
import json
import random
import socket
import threading

def install(package):
    subprocess.check_call([sys.executable, "pip", "install", package])

def check_and_install(module_name):
    try:
        __import__(module_name)
        print(f"{module_name} est déjà installé.")
    except ImportError:
        print(f"{module_name} n'est pas installé, installation en cours...")
        install(module_name)
        print(f"{module_name} a été installé avec succès.")

modules_to_install = ['pygame','stockfish']

for module in modules_to_install:
    check_and_install(module)

import pygame
from stockfish import Stockfish
import os

# Initialisation de Pygame
pygame.init()

# Obtenir les informations sur l'écran de l'utilisateur
info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h

# Définir les marges
MARGIN = 50

# Calculer la taille de l'échiquier en fonction de la taille de l'écran et des marges
chessboard_size = min(screen_width - 2 * MARGIN, screen_height - 2 * MARGIN)
SQ_SIZE = chessboard_size // 8

# Définir les dimensions de l'écran
WIDTH, HEIGHT = chessboard_size + 2 * MARGIN, chessboard_size + 2 * MARGIN

# Définir les couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
KHAKI = (195, 176, 145)
RED = (255, 0, 0)

# Classe de base pour les pièces
class Piece:
    def __init__(self, color):
        self.color = color
        self.has_moved = False

    def get_valid_moves(self, board, r, c):
        raise NotImplementedError

# Sous-classe pour le Pion
class Pawn(Piece):
    def get_valid_moves(self, board, r, c):
        moves = []
        direction = -1 if self.color == 'w' else 1
        start_row = 6 if self.color == 'w' else 1
        if board[r + direction][c] is None:  # Move forward
            moves.append((r + direction, c))
            if r == start_row and board[r + 2 * direction][c] is None:
                moves.append((r + 2 * direction, c))
        if c - 1 >= 0 and board[r + direction][c - 1] is not None and board[r + direction][c - 1].color != self.color:  # Capture left
            moves.append((r + direction, c - 1))
        if c + 1 < 8 and board[r + direction][c + 1] is not None and board[r + direction][c + 1].color != self.color:  # Capture right
            moves.append((r + direction, c + 1))
        return moves

# Sous-classe pour la Tour
class Rook(Piece):
    def get_valid_moves(self, board, r, c):
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for d in directions:
            for i in range(1, 8):
                end_row, end_col = r + d[0] * i, c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if board[end_row][end_col] is None:
                        moves.append((end_row, end_col))
                    elif board[end_row][end_col].color != self.color:
                        moves.append((end_row, end_col))
                        break
                    else:
                        break
                else:
                    break
        return moves

# Sous-classe pour le Cavalier
class N(Piece):
    def get_valid_moves(self, board, r, c):
        moves = []
        knight_moves = [(-2, -1), (-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1)]
        for m in knight_moves:
            end_row, end_col = r + m[0], c + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                if board[end_row][end_col] is None or board[end_row][end_col].color != self.color:
                    moves.append((end_row, end_col))
        return moves

# Sous-classe pour le Fou
class Bishop(Piece):
    def get_valid_moves(self, board, r, c):
        moves = []
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for d in directions:
            for i in range(1, 8):
                end_row, end_col = r + d[0] * i, c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if board[end_row][end_col] is None:
                        moves.append((end_row, end_col))
                    elif board[end_row][end_col].color != self.color:
                        moves.append((end_row, end_col))
                        break
                    else:
                        break
                else:
                    break
        return moves

# Sous-classe pour la Reine
class Queen(Piece):
    def get_valid_moves(self, board, r, c):
        return Rook(self.color).get_valid_moves(board, r, c) + Bishop(self.color).get_valid_moves(board, r, c)

# Sous-classe pour le Roi
class King(Piece):
    def get_valid_moves(self, board, r, c):
        moves = []
        king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for m in king_moves:
            end_row, end_col = r + m[0], c + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                if board[end_row][end_col] is None or board[end_row][end_col].color != self.color:
                    moves.append((end_row, end_col))
        # Ajouter les mouvements de roque
        if not self.has_moved:
            if isinstance(board[r][0], Rook) and not board[r][0].has_moved:
                if board[r][1] is None and board[r][2] is None and board[r][3] is None:
                    moves.append((r, 2))
            if isinstance(board[r][7], Rook) and not board[r][7].has_moved:
                if board[r][5] is None and board[r][6] is None:
                    moves.append((r, 6))
        return moves
piece_mapping = {
    'P': Pawn,
    'R': Rook,
    'N': N,
    'B': Bishop,
    'Q': Queen,
    'K': King
}
# Charger les images des pièces
def load_images():
    pieces = ['bP', 'bR', 'bN', 'bB', 'bQ', 'bK', 'wP', 'wR', 'wN', 'wB', 'wQ', 'wK']
    images = {}
    for piece in pieces:
        images[piece] = pygame.transform.scale(pygame.image.load(f"images/{piece}.png"), (SQ_SIZE, SQ_SIZE))
    return images

# Dessiner l'échiquier
def draw_board(screen):
    colors = [pygame.Color(255, 255, 255), pygame.Color(118, 150, 86)]
    
    # Remplir la zone autour de l'échiquier avec de la couleur kaki
    screen.fill(KHAKI)
    
    # Dessiner les cases de l'échiquier
    for r in range(8):
        for c in range(8):
            color = colors[(r + c) % 2]
            pygame.draw.rect(screen, color, pygame.Rect(MARGIN + c * SQ_SIZE, MARGIN + r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

# Dessiner les pièces sur l'échiquier
def draw_pieces(screen, board, images):
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is not None:
                piece_str = piece.color + piece.__class__.__name__[0]
                screen.blit(images[piece_str], pygame.Rect(MARGIN + c * SQ_SIZE, MARGIN + r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

# Dessiner les mouvements valides
def draw_valid_moves(screen, valid_moves, board):
    for move in valid_moves:
        r, c = move
        if board[r][c] is not None:  # Vérifier si le mouvement mène à une capture
            pygame.draw.rect(screen, RED, pygame.Rect(MARGIN + c * SQ_SIZE, MARGIN + r * SQ_SIZE, SQ_SIZE, SQ_SIZE), 3)
        else:
            pygame.draw.rect(screen, GREEN, pygame.Rect(MARGIN + c * SQ_SIZE, MARGIN + r * SQ_SIZE, SQ_SIZE, SQ_SIZE), 3)

# Position initiale des pièces
def initial_board():
    return [
        [Rook('b'), N('b'), Bishop('b'), Queen('b'), King('b'), Bishop('b'), N('b'), Rook('b')],
        [Pawn('b'), Pawn('b'), Pawn('b'), Pawn('b'), Pawn('b'), Pawn('b'), Pawn('b'), Pawn('b')],
        [None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None],
        [Pawn('w'), Pawn('w'), Pawn('w'), Pawn('w'), Pawn('w'), Pawn('w'), Pawn('w'), Pawn('w')],
        [Rook('w'), N('w'), Bishop('w'), Queen('w'), King('w'), Bishop('w'), N('w'), Rook('w')]
    ]

def is_in_check(board, color):
    king_pos = None
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is not None and piece.color == color and isinstance(piece, King):
                king_pos = (r, c)
                break
        if king_pos:
            break
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is not None and piece.color != color:
                if king_pos in piece.get_valid_moves(board, r, c):
                    return True
    return False


# Vérifier si un joueur est en échec et mat
def is_checkmate(board, color):
    if not is_in_check(board, color):
        return False
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is not None and piece.color == color:
                valid_moves = piece.get_valid_moves(board, r, c)
                for move in valid_moves:
                    board_copy = [row[:] for row in board]
                    board_copy[r][c], board_copy[move[0]][move[1]] = None, piece
                    if not is_in_check(board_copy, color):
                        return False
    return True

def is_pat(board):
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is not None:
                valid_moves = piece.get_valid_moves(board, r, c)
                if len(valid_moves) != 0:
                    return False


    return True

def does_move_put_king_in_check(board, start_pos, end_pos, color):
    r1, c1 = start_pos
    r2, c2 = end_pos
    board_copy = [row[:] for row in board]
    board_copy[r2][c2] = board_copy[r1][c1]
    board_copy[r1][c1] = None
    return is_in_check(board_copy, color)

def is_game_in_progress(board):
    initial = initial_board()
    return board != initial

def save_game(board, current_turn, ai_mode):
    state = {
        'board': [[(piece.color + piece.__class__.__name__[0]) if piece else None for piece in row] for row in board],
        'current_turn': current_turn,
        'ai_mode': ai_mode
    }
    with open('.chess_save.json', 'w') as f:
        json.dump(state, f)


def load_game():
    piece_mapping = {'P': Pawn, 'R': Rook, 'N': N, 'B': Bishop, 'Q': Queen, 'K': King}
    try:
        with open('.chess_save.json', 'r') as f:
            state = json.load(f)
        board_data = state['board']
        board = [[None if cell is None else piece_mapping[cell[1]](cell[0]) for cell in row] for row in board_data]
        current_turn = state['current_turn']
        ai_mode = state.get('ai_mode', 'random')  # Default to 'random' if not found
        game_in_progress = is_game_in_progress(board)
        return board, current_turn, ai_mode, game_in_progress
    except FileNotFoundError:
        return initial_board(), 'w', 'random', False


# Fonction pour afficher la fenêtre de promotion des pions
def promote_pawn(screen, color):
    promotion_pieces = [Queen, Rook, Bishop, N]
    piece_names = ['Q', 'R', 'B', 'N']
    selected_piece = None

    while selected_piece is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                for i, piece in enumerate(promotion_pieces):
                    if 100 * i <= x <= 100 * (i + 1) and HEIGHT // 2 - 50 <= y <= HEIGHT // 2 + 50:
                        selected_piece = piece(color)
                        break

        for i, name in enumerate(piece_names):
            rect = pygame.Rect(100 * i, HEIGHT // 2 - 50, 100, 100)
            pygame.draw.rect(screen, WHITE, rect)
            piece_image = pygame.transform.scale(pygame.image.load(f'images/{color}{name}.png'), (100, 100))
            screen.blit(piece_image, rect)

        pygame.display.flip()

    return selected_piece

#Fonction IA déplacement des pièces aléatoires
def random_ai_move(board, color):
    valid_moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is not None and piece.color == color:
                moves = piece.get_valid_moves(board, r, c)
                valid_moves.extend([(r, c, move[0], move[1]) for move in moves if not does_move_put_king_in_check(board, (r, c), move, color)])
    
    if valid_moves:
        move = random.choice(valid_moves)
        start_pos, end_pos = (move[0], move[1]), (move[2], move[3])
        piece = board[start_pos[0]][start_pos[1]]
        board[start_pos[0]][start_pos[1]] = None
        board[end_pos[0]][end_pos[1]] = piece
        piece.has_moved = True

#Fonction IA déplacement des pièces selon leurs valeurs
def ai_move(board, color):
    # Fonction pour évaluer un mouvement
    def evaluate_move(board, start_pos, end_pos, color):
        # Effectuer le mouvement
        r1, c1 = start_pos
        r2, c2 = end_pos
        piece = board[r1][c1]
        target_piece = board[r2][c2]
        board[r1][c1] = None
        board[r2][c2] = piece
        
        # Évaluer le mouvement
        score = 0
        if is_in_check(board, color):
            score -= 1000  # Très mauvais mouvement si cela met le roi en échec
        else:
            if target_piece is not None:
                score += piece_value(target_piece)  # Bonus pour capturer une pièce
            if isinstance(piece, Pawn) and (r2 == 0 or r2 == 7):
                score += 10  # Bonus pour la promotion d'un pion
            score += piece_value(piece)  # Bonus pour le déplacement de la pièce
        
        # Annuler le mouvement
        board[r1][c1] = piece
        board[r2][c2] = target_piece
        
        return score
    
    # Générer tous les mouvements légaux
    valid_moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is not None and piece.color == color:
                moves = piece.get_valid_moves(board, r, c)
                valid_moves.extend([(r, c, move[0], move[1]) for move in moves if not does_move_put_king_in_check(board, (r, c), move, color)])
    
    # Choisir le meilleur mouvement
    best_move = None
    best_score = -10000
    for move in valid_moves:
        start_pos, end_pos = (move[0], move[1]), (move[2], move[3])
        score = evaluate_move(board, start_pos, end_pos, color)
        if score > best_score:
            best_score = score
            best_move = move
    
    # Effectuer le meilleur mouvement
    if best_move:
        start_pos, end_pos = (best_move[0], best_move[1]), (best_move[2], best_move[3])
        piece = board[start_pos[0]][start_pos[1]]
        board[start_pos[0]][start_pos[1]] = None
        board[end_pos[0]][end_pos[1]] = piece
        piece.has_moved = True

#Fonction pour donner la valeur des pièces
def piece_value(piece):

    if isinstance(piece, King):
        return 100
    elif isinstance(piece, Queen):
        return 9
    elif isinstance(piece, Rook):
        return 5
    elif isinstance(piece, Bishop) or isinstance(piece, N):
        return 3
    elif isinstance(piece, Pawn):
        return 1
    return 0

#Fonction IA déplacement des pièces sofistiquées
def stockfish_ai_move(board, color):
    stockfish = Stockfish(path="stockfish-windows\stockfish-windows-x86-64-vnni512.exe")
    
    if os.name == 'posix':
        stockfish = Stockfish(path="stockfish-linux/stockfish-ubuntu-x86-64")
    elif os.name == 'nt':
        stockfish = Stockfish(path="stockfish-windows/stockfish-windows-x86-64-vnni512.exe")
    elif os.name == 'Darwin':
        stockfish = Stockfish(path="stockfish-mac/stockfish-mac-x86-64")
    
    # Convertir le plateau de Pygame à un plateau FEN
    board_fen = convert_to_fen(board, color)
    stockfish.set_fen_position(board_fen)
    
    best_move = stockfish.get_best_move()
    move = stockfish.get_best_move()

    start_square = (8 - int(move[1]), ord(move[0]) - ord('a'))
    end_square = (8 - int(move[3]), ord(move[2]) - ord('a'))

    piece = board[start_square[0]][start_square[1]]
    board[start_square[0]][start_square[1]] = None
    board[end_square[0]][end_square[1]] = piece
    piece.has_moved = True

def convert_to_fen(board, color):
    fen = ""
    for r in range(8):
        empty = 0
        for c in range(8):
            piece = board[r][c]
            if piece is None:
                empty += 1
            else:
                if empty > 0:
                    fen += str(empty)
                    empty = 0
                fen += piece_to_fen_char(piece)
        if empty > 0:
            fen += str(empty)
        if r != 7:
            fen += "/"
    fen += " w " if color == 'w' else " b "
    fen += "KQkq - 0 1"  # Compléter la chaîne FEN correctement
    return fen

def piece_to_fen_char(piece):
    if isinstance(piece, King):
        return 'K' if piece.color == 'w' else 'k'
    elif isinstance(piece, Queen):
        return 'Q' if piece.color == 'w' else 'q'
    elif isinstance(piece, Rook):
        return 'R' if piece.color == 'w' else 'r'
    elif isinstance(piece, Bishop):
        return 'B' if piece.color == 'w' else 'b'
    elif isinstance(piece, N):
        return 'N' if piece.color == 'w' else 'n'
    elif isinstance(piece, Pawn):
        return 'P' if piece.color == 'w' else 'p'
    return ''

def display_1_player_screen(screen, game_in_progress):
    font = pygame.font.SysFont('Arial', 48)
    text_random_ai = font.render('Random AI', True, BLACK)
    text_smart_ai = font.render('Smart AI', True, BLACK)
    text_stockfish_ai = font.render('Stockfish AI', True, BLACK)
    
    if game_in_progress:
        text_continue = font.render('Continue Game', True, BLACK)
    
    while True:
        screen.fill(WHITE)
        screen.blit(text_random_ai, (WIDTH // 2 - text_random_ai.get_width() // 2, HEIGHT // 2 - 200))
        screen.blit(text_smart_ai, (WIDTH // 2 - text_smart_ai.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(text_stockfish_ai, (WIDTH // 2 - text_stockfish_ai.get_width() // 2, HEIGHT // 2))
        
        if game_in_progress:
            screen.blit(text_continue, (WIDTH // 2 - text_continue.get_width() // 2, HEIGHT // 2 + 100))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if (WIDTH // 2 - text_random_ai.get_width() // 2 <= x <= WIDTH // 2 + text_random_ai.get_width() // 2 and
                        HEIGHT // 2 - 200 <= y <= HEIGHT // 2 - 200 + text_random_ai.get_height()):
                    return 'new_game', 'random'
                elif (WIDTH // 2 - text_smart_ai.get_width() // 2 <= x <= WIDTH // 2 + text_smart_ai.get_width() // 2 and
                        HEIGHT // 2 - 100 <= y <= HEIGHT // 2 - 100 + text_smart_ai.get_height()):
                    return 'new_game', 'smart'
                elif (WIDTH // 2 - text_stockfish_ai.get_width() // 2 <= x <= WIDTH // 2 + text_stockfish_ai.get_width() // 2 and
                        HEIGHT // 2 <= y <= HEIGHT // 2 + text_stockfish_ai.get_height()):
                    return 'new_game', 'stockfish'
                elif game_in_progress and (WIDTH // 2 - text_continue.get_width() // 2 <= x <= WIDTH // 2 + text_continue.get_width() // 2 and
                        HEIGHT // 2 + 100 <= y <= HEIGHT // 2 + 100 + text_continue.get_height()):
                    return 'continue', None
        
        pygame.display.flip()


# Fonction pour afficher l'écran d'accueil
def display_start_screen(screen):
    font = pygame.font.SysFont('Arial', 48)
    text_1_player = font.render('1 Player', True, BLACK)
    text_2_players_local = font.render('2 Players - Same Device', True, BLACK)
    text_2_players_remote = font.render('2 Players - Remote', True, BLACK)

    # Calculer les positions des textes
    text_1_player_rect = text_1_player.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
    text_2_players_local_rect = text_2_players_local.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    text_2_players_remote_rect = text_2_players_remote.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))

    while True:
        screen.fill(WHITE)
        screen.blit(text_1_player, text_1_player_rect.topleft)
        screen.blit(text_2_players_local, text_2_players_local_rect.topleft)
        screen.blit(text_2_players_remote, text_2_players_remote_rect.topleft)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if text_1_player_rect.collidepoint(x, y):
                    return '1_player'
                elif text_2_players_local_rect.collidepoint(x, y):
                    return '2_players_local'
                elif text_2_players_remote_rect.collidepoint(x, y):
                    return '2_players_remote'

        pygame.display.flip()


def display_endgame_screen(screen, message):
    font = pygame.font.SysFont('Arial', 48)
    text = font.render(message, True, pygame.Color('Red'))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

    button_font = pygame.font.SysFont('Arial', 36)
    button_quit = button_font.render('Quit', True, BLACK)
    button_restart = button_font.render('Restart', True, BLACK)
    button_quit_rect = button_quit.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
    button_restart_rect = button_restart.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150))

    while True:
        screen.fill(WHITE)
        screen.blit(text, text_rect)
        pygame.draw.rect(screen, WHITE, button_quit_rect.inflate(20, 20))
        pygame.draw.rect(screen, WHITE, button_restart_rect.inflate(20, 20))
        screen.blit(button_quit, button_quit_rect)
        screen.blit(button_restart, button_restart_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if button_quit_rect.collidepoint(x, y):
                    pygame.quit()
                    sys.exit()
                elif button_restart_rect.collidepoint(x, y):
                    return 'restart'

        pygame.display.flip()

def receive_data(client_socket, board, current_turn, screen, images):
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if data:
                # Charger l'état de l'échiquier reçu
                state = json.loads(data)
                board[:] = [[None if cell is None else piece_mapping[cell[1]](cell[0]) for cell in row] for row in state['board']]
                current_turn = state['current_turn']
                draw_board(screen)
                draw_pieces(screen, board, images)
                pygame.display.flip()
        except:
            print("Connexion au serveur perdue.")
            client_socket.close()
            break

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    screen.fill(pygame.Color("white"))
    images = load_images()

    action = display_start_screen(screen)

    if action == '1_player':
        board, current_turn, ai_mode, game_in_progress = load_game()
        action, ai_mode = display_1_player_screen(screen, game_in_progress)
    elif action == '2_players_local':
        board = initial_board()  # Initialiser le plateau pour 2 joueurs sur le même appareil
        current_turn = 'w'  # Le joueur blanc commence
        ai_mode = None
        game_in_progress = True
    elif action == '2_players_remote':
        board = initial_board()  # Initialiser le plateau pour 2 joueurs en distant
        current_turn = 'w'
        ai_mode = None
        game_in_progress = True

        # Configurer la connexion réseau
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('82.66.7.199', 65432))  # Adresse et port du serveur

        # Démarrer un thread pour recevoir les données
        threading.Thread(target=receive_data, args=(client_socket, board, current_turn, screen, images), daemon=True).start()

    selected_piece = None
    valid_moves = []

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                location = pygame.mouse.get_pos()
                col = (location[0] - MARGIN) // SQ_SIZE
                row = (location[1] - MARGIN) // SQ_SIZE

                if action == '2_players_remote':
                    # Envoyer les données au serveur après chaque coup
                    if selected_piece and (row, col) in valid_moves:
                        state = {
                            'board': [[(piece.color + piece.__class__.__name__[0]) if piece else None for piece in row] for row in board],
                            'current_turn': 'b' if current_turn == 'w' else 'w'
                        }
                        client_socket.send(json.dumps(state).encode('utf-8'))
                if selected_piece:
                    if (row, col) in valid_moves:
                        if not does_move_put_king_in_check(board, selected_piece, (row, col), current_turn):
                            piece = board[selected_piece[0]][selected_piece[1]]
                            board[selected_piece[0]][selected_piece[1]] = None
                            if isinstance(piece, King) and abs(col - selected_piece[1]) == 2:
                                if col == 2:  # Roque côté dame
                                    board[row][0], board[row][3] = None, board[row][0]
                                else:  # Roque côté roi
                                    board[row][7], board[row][5] = None, board[row][7]
                            board[row][col] = piece
                            piece.has_moved = True
                            if isinstance(piece, Pawn) and (row == 0 or row == 7):
                                board[row][col] = promote_pawn(screen, piece.color)  # Promotion de pion
                            selected_piece = None
                            valid_moves = []
                            draw_board(screen)
                            draw_pieces(screen, board, images)
                            pygame.display.flip()

                            # Envoyer l'état de l'échiquier au serveur
                            state = {
                                'board': [[(piece.color + piece.__class__.__name__[0]) if piece else None for piece in row] for row in board],
                                'current_turn': 'b' if current_turn == 'w' else 'w'
                            }
                            if action == '2_players_remote':
                                client_socket.send(json.dumps(state).encode('utf-8'))
                            if is_checkmate(board, 'b' if current_turn == 'w' else 'w'):
                                result = display_endgame_screen(screen, f"Checkmate! {'White' if current_turn == 'w' else 'Black'} wins!")
                                if result == 'restart':
                                    board = initial_board()
                                    current_turn = 'w'
                                    game_in_progress = False
                                    action, ai_mode = display_1_player_screen(screen, game_in_progress)
                                    continue
                            

                            if is_pat(board):
                                result = display_endgame_screen(screen, f"Pat! it's a tie !")
                                if result == 'restart':
                                    board = initial_board()
                                    current_turn = 'w'
                                    game_in_progress = False
                                    action, ai_mode = display_1_player_screen(screen, game_in_progress)
                                    continue

                                else:
                                    running = False
                            else:
                                current_turn = 'b' if current_turn == 'w' else 'w'
                        else:
                            selected_piece = None
                            valid_moves = []
                    else:
                        selected_piece = None
                        valid_moves = []
                piece = board[row][col]
                if piece is not None and piece.color == current_turn:
                    selected_piece = (row, col)
                    valid_moves = piece.get_valid_moves(board, row, col)
                    # Filtrer les mouvements qui mettent le roi en échec
                    valid_moves = [move for move in valid_moves if not does_move_put_king_in_check(board, (row, col), move, current_turn)]

        draw_board(screen)
        draw_valid_moves(screen, valid_moves, board)
        draw_pieces(screen, board, images)
        pygame.display.flip()
        clock.tick(60)

        if current_turn == 'b' and ai_mode:
            if ai_mode == 'random':
                random_ai_move(board, 'b')
            elif ai_mode == 'smart':
                ai_move(board, 'b')
            elif ai_mode == 'stockfish':
                stockfish_ai_move(board, 'b')
            if is_checkmate(board, 'w'):
                result = display_endgame_screen(screen, "Checkmate! Black wins!")
                if result == 'restart':
                    board = initial_board()
                    current_turn = 'w'
                    game_in_progress = False
                    action, ai_mode = display_1_player_screen(screen, game_in_progress)
                    continue
                else:
                    running = False
            current_turn = 'w'

    save_game(board, current_turn, ai_mode)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
