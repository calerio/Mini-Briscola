from time import perf_counter, time_ns
import random
import pyxel

from game.card import Card
from game.pile import Pile
from game.move import Move
from game.consts import CARD_HEIGHT, CARD_WIDTH

# Buttons used in the game
Buttons = {
    'end_round': pyxel.KEY_R,
    'new': pyxel.KEY_N, 
    'briscola_rules': pyxel.KEY_B,
    'game_rules': pyxel.KEY_G,
    'select': pyxel.MOUSE_BUTTON_LEFT,
    'cancel': pyxel.MOUSE_BUTTON_RIGHT,
    'pl0_cards_face_switch': pyxel.KEY_1,
    'pl1_cards_face_switch': pyxel.KEY_2
}


class App:
    def __init__(self) -> None:
        width = 160
        height = 144

        pyxel.init(width, height, title="Mini-Briscola", fps= 60)
        pyxel.load("assets/assets_italian.pyxres")  

        pyxel.mouse(True)

        self.config = {
            "drag_and_drop": True
        }

        self.rng_seed = None
        self.offset_x = 0
        self.offset_y = 0
        self.game_status = "new"
        self.last_click_time = 0

        self.next_move = Move()
        self.perform_next_move = True

        self.show_game_rules = False
        self.show_briscola_rules = False


        self.end_round = False # Bool to know whether the button to end the current round was pressed
        self.first_mover = 0 # Bool that stores who the first mover of the turn is
        self.win_turn = 5 # Default value when no one has won the turn yet
        self.mover_advantage = 5 # Default value when no one has has moved yet
        self.pause = False # Check to see if we're in the pausing status
        self.briscola_suit = 0 # Variable to store the Briscola suit

        self.cards = [Card(i // 10, i % 10) for i in range(40)]
        # Ace, 2, 3, 4, 5, 6, 7, Jack, Queen, King = 10

        self.piles = {  # Layout of the game
            "pl0_1": Pile(52, 100),
            "pl0_2": Pile(72, 100),
            "pl0_3": Pile(92, 100),
            
            "pl1_1": Pile(52, 10),
            "pl1_2": Pile(72, 10),
            "pl1_3": Pile(92, 10),
            
            "foundation0": Pile(72, 70, render_all= False),
            "foundation1": Pile(72, 40, render_all= False),
            
            "deck0": Pile(120, 100, render_all= False),
            "deck1": Pile(24, 10, render_all= False),
            
            "stock": Pile(20, 60, render_all= False, render_slot= False),
            "briscola": Pile(40, 60)
        }

        for key in self.piles.keys(): self.piles[key].id = key

        self.new_game()  
        pyxel.run(self.update, self.render)  


    def get_cursor_pos(self):  # Cursor position 
        return (pyxel.mouse_x, pyxel.mouse_y)
    

    def get_offset_cursor(self):  # Cursor position with the offset 
        return (pyxel.mouse_x - self.offset_x, pyxel.mouse_y - self.offset_y)


    def set_cursor_offset(self, x, y):  
        self.offset_x = x
        self.offset_y = y


    # The method that creates the game state (resets the game state and starts a new one) 
    def new_game(self, seed = None):  
        
        # Sets all cards face down, clears assigned pile
        for card in self.cards:
            card.set_face_down()
            card.pile = None

        # Clear all piles
        for pile in self.piles.values(): pile.clear()

        # Resets state
        self.rng_seed = time_ns() if seed == None else seed
            
        random.seed(self.rng_seed)
        self.game_status = "new"
        self.reset_move()  # Move state reset to default

        self.move_count = 0
        self.first_turn = True

        # Assigns cards to stock pile and shuffle
        stock = self.piles["stock"]
        stock.add(self.cards)
        stock.shuffle()
        stock.position_cards(now = True)



    # Returns pile at the indicated (x, y) coordinates
    def get_pile_at(self, x, y) -> Pile:  
        for pile in self.piles.values():
            if x > pile.x and y > pile.y and x < pile.x + pile.width and y < pile.y + pile.height:
                return pile        
        return None
    
    
    # Returns the card at the indicated (x,y) coordinates
    def get_card_at(self, x, y) -> Card:  
        pile = self.get_pile_at(x, y)

        if pile and len(pile) > 0:
            if pile.render_all:
                for i in range( len(pile.cards)-1 , -1, -1):
                    card = pile.cards[i]
                    if x > card.x and y > card.y and x < card.x + card.width and y < card.y + card.height: return card
            else: return pile.top_card
        return None
    
    
    # Returns the amount of cards to move (will always be one)
    def get_card_amount(self, card:Card):  
        return 1


    # Returns a list of cards currently moving (will always be one)
    def get_cards_moving(self):  
        cards = [c for c in self.cards if c.is_moving() == True]
        return cards


    # Configures the next move 
    def config_move( 
        self,
        source:Pile = None,
        target:Pile = None,
        amount:int = None,
        flip_source_top:bool = None,
        flip_source_pile:bool = None,
        flip_target_top:bool = None,
        flip_target_pile:bool = None
    ):
        if source != None: self.next_move.source = source
        if target != None: self.next_move.target = target
        if amount != None: self.next_move.amount = amount
        if flip_source_top != None: self.next_move.flip_source_top = flip_source_top
        if flip_source_pile != None: self.next_move.flip_source_pile = flip_source_pile
        if flip_target_top != None: self.next_move.flip_target_top = flip_target_top
        if flip_target_pile != None: self.next_move.flip_target_pile = flip_target_pile


    # Validate moves performed by dragging cards
    def validate_move(self, source: Pile, target: Pile, amount: int) -> bool: 

        # Amount is non-positive, invalid
        if amount <= 0: return False

        # Source is the same as Target, invalid 
        if source == target: return False

        # Source is empty, invalid
        if source.is_empty: return False

        # Moves from pl0_1, pl0_2, pl0_3 to foundation0 (only if foundation0 is empty and the cards are face up)
        if source.id in ['pl0_1', 'pl0_2', 'pl0_3'] and target.id == 'foundation0':
            # Look if at least one card is face up
            face_up_conditions = [
                self.piles['pl0_1'].top_card.is_face_up if not self.piles['pl0_1'].is_empty else False,
                self.piles['pl0_2'].top_card.is_face_up if not self.piles['pl0_2'].is_empty else False,
                self.piles['pl0_3'].top_card.is_face_up if not self.piles['pl0_3'].is_empty else False,
            ]
            
            if any(face_up_conditions):  # if at least one is face up (for the last rounds of the game)
                if target.is_empty: return True


        # Moves from pl1_1, pl1_2, pl1_3 to foundation1 (only if foundation1 is empty and the cards are face up)
        if source.id in ['pl1_1', 'pl1_2', 'pl1_3'] and target.id == 'foundation1':
            face_up_conditions = [
                self.piles['pl1_1'].top_card.is_face_up if not self.piles['pl1_1'].is_empty else False,
                self.piles['pl1_2'].top_card.is_face_up if not self.piles['pl1_2'].is_empty else False,
                self.piles['pl1_3'].top_card.is_face_up if not self.piles['pl1_3'].is_empty else False,
            ]
            
            if any(face_up_conditions):  
                if target.is_empty: return True



        # Moves from stock to pl0_1, pl0_2, pl0_3, pl1_1, pl1_2, pl1_3 (only if there is an empty slot)
        if source.id == 'stock' and target.id in ['pl0_1', 'pl0_2', 'pl0_3', 'pl1_1', 'pl1_2', 'pl1_3']:
            if target.is_empty: return True

        if source.id == 'briscola' and target.id in ['pl0_1', 'pl0_2', 'pl0_3', 'pl1_1', 'pl1_2', 'pl1_3']:
            if target.is_empty: return True

        return False          
    
    
    # Determines the *overall* winner of the game (not the round winner)
    def overall_winner(self):  
        sum_player1 = sum(card.points for card in self.piles['deck1'].cards)
        if sum_player1 > 60: return 1
        elif sum_player1 == 60: return 5 # Default value if the overall game resulted in a tie
        else: return 0
         
            
    # Performs the movement of cards between piles 
    def perform_move(
        self,
        source:Pile,
        target:Pile,
        amount = None,
        flip_source_top = False,
        flip_source_pile = False,
        flip_target_top = False,
        flip_target_pile = False
    ):
        
        # If no amount is defined, move whole source
        if amount == None: amount = len(source)
        elif amount == 0: return
        
        # Move cards from source to target
        target.add(source.draw(amount))
        
        # Play sound
        pyxel.play(0, 0)

        if not source.is_empty:
            # Flip source's top card and source pile if requested
            if flip_source_top: source.top_card.flip()
            if flip_source_pile: source.flip()

        # Flip target's top card and target pile if requested
        if flip_target_top: target.top_card.flip()
        if flip_target_pile: target.flip()


    # Resets the move state back to defaults
    def reset_move(self): 
        self.next_move.source = None
        self.next_move.target = None
        self.next_move.amount = 0
        self.next_move.flip_source_pile = False
        self.next_move.flip_source_top = False
        self.next_move.flip_target_pile = False
        self.next_move.flip_target_top = False


    # Performs a quick move by double clicking (fun to have) 
    def try_quick_move(self, pile, card: Card):  
        if not card or not card.is_face_up: return False

        # Determine the target foundation based on the source pile
        if pile.id in ['pl0_1', 'pl0_2', 'pl0_3']: target_pile = self.piles['foundation0']
        elif pile.id in ['pl1_1', 'pl1_2', 'pl1_3']: target_pile = self.piles['foundation1']
        else: return False

        # Check if the target foundation is empty and is yes it performs the quick move
        if target_pile.is_empty:
            amount = self.get_card_amount(card)
            if amount > 0:
                self.config_move(pile, target_pile, amount)
                return True
            
        return False   


    # Handles the click event 
    def on_click(self, x, y, quick_move = False): 
        pile = self.get_pile_at(x, y)
        card = self.get_card_at(x, y)

        # No pile clicked
        if pile == None: return

        # Move type
        if quick_move: self.try_quick_move(pile, card)

        elif self.next_move.source == None:
            if card is None: return
            self.set_cursor_offset(x - card.x, y - card.y)
            amount = self.get_card_amount(card) if 'tableau' in pile.id else 1
            self.config_move(source= pile, amount= amount)

        elif self.next_move.target == None: self.config_move(target= pile)
        

    # Handles the input from keyboard and mouse/trackpad
    def handle_input(self):  
        # New game
        if pyxel.btnp(Buttons['new']): self.new_game()

        # Ends the current round and starts a new one
        elif pyxel.btnp(Buttons['end_round']): self.end_round = True

        # Shows game rules and briscola rules
        elif pyxel.btnp(Buttons['game_rules']):
            self.show_game_rules = not self.show_game_rules
            if self.show_game_rules: self.show_briscola_rules = False  # If the game rules are shown, the briscola rules are hidden

        elif pyxel.btnp(Buttons['briscola_rules']):
            self.show_briscola_rules = not self.show_briscola_rules
            if self.show_briscola_rules: self.show_game_rules = False  # If the briscola rules are shown, the game rules are hidden


    # Used to create text with a shadow
    def drop_text(self, x, y, s, fg=pyxel.COLOR_WHITE, bg=pyxel.COLOR_BLACK):  
        pyxel.text(x, y+1, s, bg)
        pyxel.text(x, y, s, fg)
     
        
    # First method of game logic extracts the data from each pile at the beginning of the round 
    def extract_pile_data(self):  


        # Extracts foundation top cards and suits data
        foundation0_top_card = self.piles['foundation0'].top_card
        foundation1_top_card = self.piles['foundation1'].top_card

        foundation0_suit = foundation0_top_card.suit if foundation0_top_card else None
        foundation1_suit = foundation1_top_card.suit if foundation1_top_card else None

        # Verifies if the cards played are briscola
        foundation0_is_briscola = foundation0_suit == self.briscola_suit if foundation0_top_card else False
        foundation1_is_briscola = foundation1_suit == self.briscola_suit if foundation1_top_card else False

        return {
            'briscola_suit': self.briscola_suit,
            'foundation0_top_card': foundation0_top_card,
            'foundation1_top_card': foundation1_top_card,
            'foundation0_is_briscola': foundation0_is_briscola,
            'foundation1_is_briscola': foundation1_is_briscola,
            'foundation0_suit': foundation0_suit,
            'foundation1_suit': foundation1_suit,
        }


    # Second method of game logic determines the winner of every turn
    def determine_winning_turn(self, pile_data):  
        self.win_turn = 5 #default value

        f0_card = pile_data['foundation0_top_card']
        f1_card = pile_data['foundation1_top_card']
        f0_is_briscola = pile_data['foundation0_is_briscola']
        f1_is_briscola = pile_data['foundation1_is_briscola']
        f0_suit = pile_data['foundation0_suit']
        f1_suit = pile_data['foundation1_suit']

        # Case 1: One of the played cards is briscola and one is not
        if f0_is_briscola and not f1_is_briscola: self.win_turn = 0
        elif f1_is_briscola and not f0_is_briscola: self.win_turn = 1
            
        # Case 2: Both of the played cards are briscola     
        elif f1_is_briscola and f0_is_briscola:
            if f0_card and f1_card:
                if f0_card.points == 0 and f1_card.points == 0:
                    self.win_turn = 1 if f1_card.rank > f0_card.rank else 0
                elif f0_card.points > f1_card.points: self.win_turn = 0
                elif f1_card.points > f0_card.points: self.win_turn = 1
        
        # Case 3: None is briscola
        elif not f1_is_briscola and not f0_is_briscola:
            # Case 3.1: Cards have the same suit
            if f1_suit == f0_suit and f0_card and f1_card: 
                # Case 3.1.1: None of the cards have points, winner is decided based on rank
                if f0_card.points == 0 and f1_card.points == 0: 
                    if f1_card.rank > f0_card.rank: self.win_turn = 1 
                    else: self.win_turn = 0
                # Case 3.1.2: At least one of the cards has points, the card with more points wins   
                elif f0_card.points > f1_card.points: self.win_turn = 0
                elif f1_card.points > f0_card.points: self.win_turn = 1
    
            #Case 3.2 Cards have different suits
            elif f1_suit!= f0_suit and f0_card and f1_card:
                self.win_turn = 1 if self.mover_advantage == 1 else 0


    # Updates the game state continuously, effectively running the game 
    def update(self):  
        self.handle_input()

        # NEW GAME IS SET UP
        if self.game_status == "new": 

            # List of piles to deal cards to
            target_piles = ['pl0_1', 'pl0_2', 'pl0_3', 'pl1_1', 'pl1_2', 'pl1_3']
            
            # Get the piles from self.piles
            f_piles = [self.piles[pile_id] for pile_id in target_piles]

            moving = self.get_cards_moving()

            if len(moving) == 0:
                for pile in f_piles:
                    self.perform_move(self.piles["stock"], pile, 1)
                    pile.top_card.set_face_down()

            # Add a card from stock to the briscola pile and set it face up
            self.perform_move(self.piles["stock"], self.piles["briscola"], 1)
            self.piles["briscola"].top_card.set_face_up()

            # Extracts briscola card and suit data
            briscola_card = self.piles['briscola'].top_card
            self.briscola_suit = briscola_card.suit if briscola_card else None
                
            self.game_status = "play"


        # PLAYERS CHOOSE WHICH CARDS TO PLAY
        elif self.game_status == "play":
            moving = self.get_cards_moving()

            self.end_round = False

            # Sets player 0's cards face down if the player has finished their turn
            if not self.piles['foundation0'].is_empty:
                target_piles = ['pl0_1', 'pl0_2', 'pl0_3']
                f_piles = [self.piles[pile_id] for pile_id in target_piles]
                for pile in f_piles:
                    if pile.is_empty == False: pile.top_card.set_face_down()

            # Sets player 1's cards face down if the player has finished their turn
            if not self.piles['foundation1'].is_empty:
                target_piles = ['pl1_1', 'pl1_2', 'pl1_3']
                f_piles = [self.piles[pile_id] for pile_id in target_piles]
                for pile in f_piles:
                    if pile.is_empty == False: pile.top_card.set_face_down()

            # If '1' is pressed on the keyboard, the faces of player 0's cards are shown
            if pyxel.btnp(Buttons['pl0_cards_face_switch']) and (self.first_mover == 0 or not self.piles['foundation1'].is_empty):
                target_piles = ['pl0_1', 'pl0_2', 'pl0_3']
                f_piles = [self.piles[pile_id] for pile_id in target_piles]
                for pile in f_piles:
                    if pile.is_empty == False: pile.top_card.set_face_up()
            
            # If '2' is pressed on the keyboard, the faces of player 1's cards are shown
            if pyxel.btnp(Buttons['pl1_cards_face_switch']) and (self.first_mover == 1 or not self.piles['foundation0'].is_empty):
                target_piles = ['pl1_1', 'pl1_2', 'pl1_3']
                f_piles = [self.piles[pile_id] for pile_id in target_piles]
                for pile in f_piles:
                    if pile.is_empty == False: pile.top_card.set_face_up()

            # Defines who has the mover advantage
            if self.piles['foundation0'].is_empty and not self.piles['foundation1'].is_empty:
                self.mover_advantage = 1
            else: self.mover_advantage = 0

            # Left Mouse draws and places
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                click_time = perf_counter()
                self.on_click(*self.get_cursor_pos(), pyxel.btn(pyxel.KEY_SHIFT) or click_time - self.last_click_time < 0.5)
                self.last_click_time = click_time

            if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT): map(lambda p: p.position_cards(), self.piles.values())

            # Release movement 
            if self.config["drag_and_drop"]:
                if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT) and self.next_move.source != None:
                    
                    source_card = self.next_move.source.cards[-self.next_move.amount]
                    self.next_move.target = self.get_pile_at(*source_card.center)

                    if self.next_move.source == None: self.next_move.target = self.get_pile_at(*self.get_cursor_pos())

                    if self.next_move.source != None:
                        if self.next_move.target != None:
                            if self.next_move.source == self.next_move.target: self.reset_move()
                        else: self.reset_move()

            # Process move if any
            if self.next_move.source != None and self.next_move.target != None:                
                
                m = self.next_move

                # Perform move if valid
                is_valid = self.validate_move(m.source, m.target, m.amount)
                if is_valid: self.perform_move(m.source, m.target, m.amount, m.flip_source_top, m.flip_source_pile, m.flip_target_top, m.flip_target_pile)

                self.reset_move()

            # Cards in hand
            if self.next_move.source and self.next_move.amount > 0: 
                self.next_move.source.position_cards(*self.get_offset_cursor(), self.next_move.amount, now = True)
            if not self.piles["foundation0"].is_empty and not self.piles["foundation1"].is_empty: 
                self.game_status = "foudations_ready"
       
        # WINNER IS DECIDED (GAME LOGIC)
        elif self.game_status == "foudations_ready":
            
            pile_data = self.extract_pile_data()
            self.determine_winning_turn(pile_data)
            self.game_status = 'pause'
        
        # GAME IS PAUSED 
        elif self.game_status == 'pause':
            if self.pause == False:
                self.game_status = 'new_hand'

        # CARDS GET REDISTRIBUTED TO THE WINNER AND PLAYERS GET NEW HAND
        elif self.game_status == "new_hand":

            # Redistributes the cards to the winner
            target_deck = self.piles['deck1'] if self.win_turn == 1 else self.piles['deck0']
            self.first_mover = self.win_turn
        
            while not self.piles['foundation0'].is_empty:
                card = self.piles['foundation0'].draw(1)  
                target_deck.add(card) 

            while not self.piles['foundation1'].is_empty:
                card = self.piles['foundation1'].draw(1)  
                target_deck.add(card)
                    
            if target_deck.top_card: target_deck.top_card.set_face_down()

            # Refills the specified piles from the source pile
            def refill_pile(piles, source_pile, pile_names):
                for pile_name in pile_names:
                    if piles[pile_name].is_empty:
                        card = source_pile.draw(1)
                        piles[pile_name].add(card)
                        if piles[pile_name].top_card: piles[pile_name].top_card.set_face_down()

            # List of pile names to be checked
            pl0_piles = ["pl0_1", "pl0_2", "pl0_3"]
            pl1_piles = ["pl1_1", "pl1_2", "pl1_3"]

            # Refilling logic
            if len(self.piles['stock'].cards) > 1: refill_pile(self.piles, self.piles['stock'], pl0_piles + pl1_piles)

            elif len(self.piles['stock'].cards) == 1 and not self.piles['briscola'].is_empty:
                if not self.piles['stock'].is_empty:
                    if self.win_turn == 0:
                        refill_pile(self.piles, self.piles['stock'], pl0_piles)
                        refill_pile(self.piles, self.piles['briscola'], pl1_piles)
                    else:
                        refill_pile(self.piles, self.piles['stock'], pl1_piles)
                        refill_pile(self.piles, self.piles['briscola'], pl0_piles)

            # Defining the loop such that rounds repeat       
            if all(self.piles[pile].is_empty for pile in self.piles if pile.startswith("pl")): self.game_status = "win"
            
            else: self.game_status = "play"
        
        # SETTING GAME STATUS TO WIN 
        elif self.game_status == "win": pass                            
      
        for card in self.cards: card.update() # Update cards and same with piles
        for pile in self.piles.values(): pile.position_cards()

    # Executes the rendering of the game (draws game elements)
    def render(self):
        stock = self.piles["stock"]

        pyxel.cls(12)  # Background color

        # Render stock pile's unique slot
        if len(stock) == 0: pyxel.blt(stock.x, stock.y, 0, 32, 0, CARD_WIDTH, CARD_HEIGHT, 14)

        # Render pile slots
        for pile in self.piles.values():
            if pile.render_slot: pyxel.blt(pile.x, pile.y, 0, 16, 0, CARD_WIDTH, CARD_HEIGHT, 14)

        # Render piles and cards
        for pile in self.piles.values():
            if pile != self.next_move.source: pile.render()

        # Render currently selected pile
        if self.next_move.source != None: self.next_move.source.render()

        # Render moving cards on top of the rest
        moving = self.get_cards_moving()

        for card in moving: card.render()

        # Renders who won the game
        if self.game_status == "win":  
            screen_width = pyxel.width
            screen_height = pyxel.height

            # If it's not a tie 
            if self.overall_winner() != 5:
                text1 = f"Player {self.overall_winner()+1} won!"
                pl0_points = sum(card.points for card in self.piles['deck0'].cards)
                pl1_points = sum(card.points for card in self.piles['deck1'].cards)
                text2 = f"Player 1 points: {pl0_points}"
                text3 = f"Player 2 points: {pl1_points}"
            else:
                text1 = "It's a tie!"
                pl0_points = sum(card.points for card in self.piles['deck0'].cards)
                pl1_points = sum(card.points for card in self.piles['deck1'].cards)
                text2 = f"Player 1 points: {pl0_points}"
                text3 = f"Player 2 points: {pl1_points}"

            # Text specificities
            max_text_width = max(len(text2), len(text3)) * 4  
            text1_width = len(text1) * 4 
            line_height = 6  
            num_lines = 3  
            padding = 5  
            rect_width = max(max_text_width, text1_width) + 2 * padding
            rect_height = num_lines * line_height + (num_lines - 1) * padding + 2 * padding

            rect_x = (screen_width - rect_width) // 2
            rect_y = (screen_height - rect_height) // 2

            pyxel.rect(rect_x, rect_y, rect_width, rect_height, pyxel.COLOR_NAVY)

            text1_x = rect_x + (rect_width - text1_width) // 2  
            text_y = rect_y + padding  

            self.drop_text(text1_x, text_y, text1, 7)  
            self.drop_text(rect_x + padding, text_y + line_height + padding, text2, 7)  
            self.drop_text(rect_x + padding, text_y + 2 * (line_height + padding), text3, 7)

        # Render text that says which player won the turn
        if self.win_turn != 5 and self.game_status == 'pause':
            self.pause = True
            screen_width = pyxel.width
            screen_height = pyxel.height

            text1 = f"Player {self.win_turn+1} won the turn!"

            text1_width = len(text1) * 4
            line_height = 6
            num_lines = 1
            padding = 5
            rect_width = text1_width + 2 * padding
            rect_height = num_lines * line_height + (num_lines) * padding + padding

            rect_x = (screen_width - rect_width) // 2
            rect_y = 121

            pyxel.rect(rect_x, rect_y, rect_width, rect_height, pyxel.COLOR_NAVY)

            text1_x = rect_x + (rect_width - text1_width) // 2
            text_y = 121 + padding

            self.drop_text(text1_x, text_y, text1, 7)
            
            # Turns downwards the faces of all of the player's cards so while the text is shown players can't turn their cards' faces upwards
            target_piles = ['pl0_1', 'pl0_2', 'pl0_3', 'pl1_1', 'pl1_2', 'pl1_3']
            f_piles = [self.piles[pile_id] for pile_id in target_piles]
            for pile in f_piles:
                if pile.is_empty == False: pile.top_card.set_face_down()

            if self.end_round == True: self.pause = False
 
        else:
            if not self.next_move.source:
                pile = self.get_pile_at(*self.get_cursor_pos())
                card = self.get_card_at(*self.get_cursor_pos())

            else: self.next_move.source.render()

        # Display game rules and briscola rules
        s = "  [G] Game Rules    [B] Briscola Rules"
        self.drop_text(2, pyxel.height - 7, s, 7)

        if self.show_game_rules: 
            pyxel.rect(2, 4, 156, 136, pyxel.COLOR_NAVY)

            s = """Game Rules:

-1: Flips Player 1's cards
    making them play first
-2: Flips Player 2's cards
    making them play first
-R  Ends the current round/trick
-N  Starts a new game

Either double click on a card to
'quick-play' it or drag and drop
it to the desired location.
"""
            self.drop_text(8, 8, s)
        
        if self.show_briscola_rules: 
            pyxel.rect(2, 4, 156, 136, pyxel.COLOR_NAVY)

            s = """Briscola Rules:

-Goal: Score more than 60 points
by collecting high-value cards.
-Card Values:
Ace: 11; 3: 10; King: 4; Queen: 3;
Jack: 2
-Gameplay:
*Each player gets 3 cards
*The top deck card determines the 
 Briscola suit
*Players play one card per turn
*Highest Briscola card wins the trick
*If no Briscola cards, highest 
 leading suit card wins.
*Trick winner takes cards and leads
 the next trick.
"""
            self.drop_text(8, 8, s)

def main():  # Starts the game
    App()

if __name__ == '__main__':  # Runs the game
    main()
