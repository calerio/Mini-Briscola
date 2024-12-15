# Mini-Briscola

## Overview

**Briscola** is a Python implementation of the classic Italian card game, brought to life with a retro-style graphical interface using the [Pyxel](https://github.com/kitao/pyxel) game engine. This project combines the logic of Briscola with pixel art to create a fun, engaging experience for two players on the same computer. Players take turns to play cards, score points, and compete to achieve the highest total.

## Features

- 🎮 **Two-player gameplay**: Play Briscola with a friend on the same computer.
- 🎨 **Graphical interface**: A pixel-art-inspired retro game environment using Pyxel.
- 🔄 **Randomized gameplay**: Cards are shuffled for a unique experience every time.
- ⏳ **Turn-based mechanics**: Ensures a smooth flow between players.
- ✨ **Retro vibe**: Designed with a nostalgic aesthetic.

## Getting Started

### Prerequisites

Ensure you have Python installed on your system. To run the game, you also need the following library:

- **Pyxel**: Install it via pip:
  ```bash
  pip install pyxel
  ```

### Running the Game

1. Open your terminal.
2. Navigate to the directory containing the game files:
   ```bash
   cd <path/to/game-directory>
   ```
3. Launch the game by running:
   ```bash
   python briscola.py
   ```

Enjoy the game!

## Modules Used

This game uses the following Python libraries:

- **Pyxel**: For rendering graphics and managing game mechanics.
- **enum**: For managing card suits and ranks (part of Python's standard library).
- **random**: For shuffling the deck and creating randomized gameplay (also part of Python's standard library).

## How to Play

1. The game alternates between two players, with each taking turns to play a card.
2. The player who wins the trick collects the played cards and scores points based on their values.
3. The game continues until all cards are played.
4. The player with the highest total score wins.

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

## Acknowledgements

Portions of this project were adapted from [mini-solitaire](https://github.com/SteelWool32/mini-solitaire) by SteelWool32, which is licensed under the MIT License.  
