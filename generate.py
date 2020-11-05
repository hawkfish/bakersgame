#!/usr/bin/python3

import random

import board

def generateSolvableBoard():
    tries = 0
    while True:
        deck = [*range(0,52)]
        random.shuffle(deck)
        b = board.Board(deck)
        solution = b.solve()
        tries = tries + 1
        if b.solved():
            print( f"Found a {len(solution)} move game after {tries} attempts:" )
            return deck

if __name__ == '__main__':
    print( board.Board( generateSolvableBoard() ) )

