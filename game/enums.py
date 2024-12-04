from enum import IntEnum, auto

# Suits follow italian playing card conventions, never been done before from our google searches
class Suit(IntEnum):  # IntEnum is a subclass of Enum that automatically assigns values to the members
    Cups = 0
    Coins = 1
    Swords = 2
    Clubs = 3
    Win = 4  # This is a special suit that represents the win condition, not used
