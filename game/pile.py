from typing import List
from game.card import Card
from game.consts import CARD_HEIGHT, CARD_WIDTH, CARD_SPACING
import pyxel
import random


class Pile:  # This class will represent a pile of cards, i.e. the stock
    def __init__(self, x, y, render_all= True, render_slot = True) -> None:
        self.x = x
        self.y = y
        self.render_all = render_all
        self.render_slot = render_slot

        self.cards:List[Card] = []  # This list will store ALL the cards in the stock
        
    def render(self):
        if len(self.cards) == 0:
            return
        
        self.cards[-1].render()
    
    def __len__(self) -> int:
        return len(self.cards)

    @property
    def width(self):
        return CARD_WIDTH
    
    @property
    def height(self):
        return CARD_HEIGHT
    
    @property  # card spacing is very necessary 
    def card_spacing(self):
        return CARD_SPACING

    @property
    def is_empty(self):
        return len(self.cards) == 0

    @property  # this might also determine the look of the cards that are laid out in solitaire
    def top_card(self) -> Card:
        """The top card is the last list element."""
        return self.cards[-1] if len(self.cards) > 0 else None

    def position_cards(self, offset_x = None, offset_y = None, hand_size = 0, now = False):
        pile_cards = []
        hand_cards = []

        if hand_size > 0:
            pile_cards = self.cards[:-hand_size]
            hand_cards = self.cards[-hand_size:]
        else:
            pile_cards = self.cards[:]
            
        for i in range(len(pile_cards)):
            card = pile_cards[i]
            if not card:
                break

            # Set card coordinates
            x = self.x
            y = self.y + (i * self.card_spacing) if self.render_all else self.y
            card.move_to(x, y, now)

        for i in range(len(hand_cards)):
            card = hand_cards[i]
            if not card:
                break

            # Set card coordinates
            x = offset_x 
            y = offset_y + (i * self.card_spacing) if self.render_all else offset_y
            card.move_to(x, y, now)

    def add(self, cards:List[Card]): # this will add cards to the pile
        """Add cards from list to the pile."""
        if isinstance(cards, list):
            self.cards = self.cards + cards
            for card in cards:
                card.pile = self

            self.position_cards()
            
    def draw(self, amount:int = 1) -> List[Card]: # this will draw cards from the pile
        """Return a list of cards drawn from the top of the pile (the last elements of the list)."""
        amount = max(1, min(amount, len(self.cards)))
        
        staying_cards = self.cards[:-amount]
        moving_cards = self.cards[-amount:]

        self.cards = staying_cards

        return moving_cards

    def clear(self):  # this will clear the pile
        self.cards.clear()
        
#    def reverse(self):  # this will reverse the order of the cards in the pile - not necessary
#        """Reverse order of cards list."""
#        self.cards.reverse()

    def shuffle(self):  # this will shuffle the cards in the pile - necessary
        """Shuffle pile."""
        random.shuffle(self.cards)

    def flip(self):  # this will flip the cards in the pile - not necessary but cute
        """Reverse pile and flip all cards."""
        self.reverse()
        for i in range(len(self.cards)):
            self.cards[i].flip()