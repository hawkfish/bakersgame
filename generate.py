#!/usr/bin/python3

import random
import sys

import board

def formatIndex( b, idx ):
    if b.isFoundationIndex( idx ):
        ace = board.makeCard( b.foundationOfIndex( idx ), 0 )
        return f"{board.formatCard( ace )[1]}"

    elif b.isCellIndex( idx ):
        return "Cell"

    else:
        return f"{ idx + 1 }"

def formatMove( b, move ):
    start, finish = move
    card = b.cardOfIndex( start )

    return f"{board.formatCard(card)}: {formatIndex( b, start)} => {formatIndex( b, finish )}"

def onSolved( solutions = 1000 ):
    untried = solutions

    def callback(*args, **kwargs):
        nonlocal untried
        untried = untried - 1
        if untried < 1:
            print()
            return False

        elif 0 == ( untried % 100):
            sys.stdout.write('.')
            sys.stdout.flush()

        return True

    return callback

def generateSolvableBoard( solutions = 1000 ):
    attempt = 0
    while True:
        deck = [*range(0,52)]
        random.shuffle(deck)
        b = board.Board(deck)
        solution = b.solve( onSolved( solutions ) )
        attempt = attempt + 1
        if b.solved():
            plural = "s" if attempt != 1 else ""
            print( f"Found a {len(solution)} move game after {attempt} attempt{plural}" )
            return (deck, solution, )

if __name__ == '__main__':
    deck, solution = generateSolvableBoard()
    b = board.Board( deck )
    for turn in solution:
        print( b )
        sys.stdout.write( '> ' )
        sys.stdout.flush()
        sys.stdin.readline()

        formatted = []
        for move in turn:
            formatted.append( formatMove( b, move ) )
            b.moveCard( move, False )
        print( ", ".join( formatted ) )

