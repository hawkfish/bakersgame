#!/usr/bin/python3

import argparse
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

def onSolved( solutions = 100 ):
    untried = solutions

    def callback(*args, **kwargs):
        nonlocal untried
        untried = untried - 1
        if untried < 1:
            print()
            return False

        elif 0 == ( untried % (solutions/10) ):
            sys.stdout.write('.')
            sys.stdout.flush()

        return True

    return callback

def generateSolvableBoard( solutions = 1 ):
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

def playSolution(deck, solution):
    b = board.Board( deck )
    if not solution:
        print( b )
        print("Unsolvable!")
        return

    for turn in solution:
        if not turn: continue

        print( b )
        sys.stdout.write( '> ' )
        sys.stdout.flush()
        sys.stdin.readline()

        formatted = []
        for move in turn:
            formatted.append( formatMove( b, move ) )
            b.moveCard( move, False )
        print( ", ".join( formatted ) )

    print( "Finished!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Plays Baker's Game at the console")
    parser.add_argument('files', metavar='file', type=str, nargs='*', help="Deck files to read and play.")
    parser.add_argument('--solutions, -s', dest='solutions', nargs=1, type=int, default=[1], help="The number of solutions to try when solving")
    args = parser.parse_args()

    if args.files:
        for filename in args.files:
            deck = board.parseDeck( file( filename, "rb" ).read() )
            b = board.Board(deck)
            solution = b.solve( onSolved( args.solutions[0] ) )
            playSolution( deck, solution )

    else:
        deck, solution = generateSolvableBoard( args.solutions[0] )
        playSolution(deck, solution)
