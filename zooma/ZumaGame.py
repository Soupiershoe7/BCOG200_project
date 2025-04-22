"""This file was created with the help of github copilot, 
and is intended as a basic starting point for structuring the game.
"""
class ZoomaGame:
    """
    Represents the Zooma game which for intellectual property reasons is definitely not a clone of Zuma.
    """

    def __init__(self):
        """
        Initializes the Zooma game.

        :param board: The game board.
        :param player: The player.
        """
        self.score = 0
        self.board = self.create_board()
        self.player = self.create_player()
        self.shooter = self.create_shooter()
        self.balls = self.create_balls()

    def play(self):
        """
        Starts the game loop.
        """
        while not self.is_game_over():
            self.display_board()
            move = self.get_player_move()
            self.make_move(move)
            self.update_score()

    def is_game_over(self):
        """
        Checks if the game is over.

        :return: True if the game is over, False otherwise.
        """
        return False