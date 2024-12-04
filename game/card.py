from game.enums import Suit
from game.consts import CARD_HEIGHT, CARD_WIDTH, CARD_DISTANCE_SPLIT
import pyxel


class Card:
    def __init__(self, suit, rank, is_face_up=False) -> None:
        self.suit = suit
        self.rank = rank
        self.is_face_up = is_face_up
        self.pile = None

        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        self.update_uv()

    @property  # Makes the width an attribute of the class
    def width(self):
        return CARD_WIDTH

    @property  # Makes the height an attribute of the class
    def height(self):
        return CARD_HEIGHT

    @property  # Makes the center an attribute of the class
    def center(self):
        return (self.x + (CARD_WIDTH // 2), self.y + (CARD_HEIGHT // 2))
    
    @property  # Makes the suit an attribute of the class
    def suit(self):
        return self._suit

    @suit.setter  # Sets the suit of the card
    def suit(self, value):
        self._suit = value

    @property  # to be used to calculate the points within deck0 or deck1
    def points(self):
        """Returns the Briscola point value of the card based on its rank."""
        point_values = {
            0: 11,  # Ace
            2: 10,  # Three
            7: 2,  # Jack
            8: 3,  # Queen
            9: 4,  # King
        }
        return point_values.get(self.rank, 0)  # Default to 0 for ranks not in the dictionary

    def update(self):  # Updates the card's position
        if self.x != self.target_x:
            dx = (self.target_x - self.x) // CARD_DISTANCE_SPLIT  # Smooths the movement
            self.x = self.x + dx if dx != 0 else self.target_x

        if self.y != self.target_y:
            dy = (self.target_y - self.y) // CARD_DISTANCE_SPLIT  # Smooths the movement
            self.y = self.y + dy if dy != 0 else self.target_y

    def render(self):  # Renders the card
        pyxel.blt(self.x, self.y, 0, self.u, self.v, CARD_WIDTH, CARD_HEIGHT, 14)

    def set_face_up(self):  # Sets the card face up
        self.is_face_up = True
        self.update_uv()

    def set_face_down(self):  # Sets the card face down
        self.is_face_up = False
        self.update_uv()

    def flip(self):  # Flips the card
        self.is_face_up = not self.is_face_up
        self.update_uv()

    def update_uv(self):  # Updates the card's UV coordinates (used for rendering)
        self.u = (self.rank * CARD_WIDTH) if self.is_face_up else 0
        self.v = ((self.suit * CARD_HEIGHT) + CARD_HEIGHT) if self.is_face_up else 0

    def move_to(self, x, y, instant = False):  #  Moves the card to the specified position
        self.target_x = x
        self.target_y = y
        if instant:
            self.x = x
            self.y = y

    def is_moving(self) -> bool:
        return self.x != self.target_x and self.y != self.target_y