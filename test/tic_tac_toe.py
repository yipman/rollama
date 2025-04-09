class TicTacToe:
    def __init__(self):
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        
    def print_board(self):
        print('\n')
        for i, row in enumerate(self.board):
            print(f' {row[0]} | {row[1]} | {row[2]} ')
            if i < 2:
                print('-----------')
        print('\n')
    
    def make_move(self, row, col):
        if not (0 <= row <= 2 and 0 <= col <= 2):
            return False, "Invalid position! Row and column must be between 0 and 2"
        
        if self.board[row][col] != ' ':
            return False, "That position is already taken!"
            
        self.board[row][col] = self.current_player
        return True, "Move successful"
    
    def check_winner(self):
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != ' ':
                return row[0]
        
        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != ' ':
                return self.board[0][col]
        
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != ' ':
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != ' ':
            return self.board[0][2]
        
        # Check for tie
        if all(self.board[i][j] != ' ' for i in range(3) for j in range(3)):
            return 'Tie'
            
        return None
    
    def switch_player(self):
        self.current_player = 'O' if self.current_player == 'X' else 'X'

def main():
    game = TicTacToe()
    
    print("Welcome to Tic Tac Toe!")
    print("Enter moves using row and column numbers (0-2)")
    print("Example: '1 2' for middle row, right column")
    
    while True:
        game.print_board()
        print(f"Player {game.current_player}'s turn")
        
        try:
            row, col = map(int, input("Enter row and column (0-2): ").split())
            success, message = game.make_move(row, col)
            
            if not success:
                print(message)
                continue
                
            winner = game.check_winner()
            if winner:
                game.print_board()
                if winner == 'Tie':
                    print("It's a tie!")
                else:
                    print(f"Player {winner} wins!")
                break
                
            game.switch_player()
            
        except ValueError:
            print("Invalid input! Please enter two numbers separated by space")
        except KeyboardInterrupt:
            print("\nGame ended by user")
            break

if __name__ == "__main__":
    main()