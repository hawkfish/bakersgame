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

def onSolved( improvements = 100 ):
    untried = improvements

    def callback(*args, **kwargs):
        b = kwargs['board']
        if not b.solved(): return True

        nonlocal untried
        untried = untried - 1
        if untried < 1:
            print()
            return False

        elif 0 == ( untried % (improvements/10) ):
            sys.stdout.write('.')
            sys.stdout.flush()

        return True

    return callback

def generateSolvableBoard( improvements = 1 ):
    attempt = 0
    while True:
        deck = [*range(0,52)]
        random.shuffle(deck)
        b = board.Board(deck)
        solution = b.solve( onSolved( improvements ) )
        attempt = attempt + 1
        if b.solved():
            plural = "s" if attempt != 1 else ""
            print( f"Found a {len(solution)} move game after {attempt} attempt{plural}" )
            return (deck, solution, )

def playSolution( deck, solution, name = 'Generated' ):
    b = board.Board( deck )

    print( f"Solving {name} deal" )

    if not solution:
        print( "*" * 23 )
        print( b )
        print( "Unsolvable!" )
        return True

    for turn in solution:
        if not turn: continue

        print( "*" * 23 )
        print( b )
        sys.stdout.write( '> ' )
        sys.stdout.flush()
        cmd = sys.stdin.readline().strip()
        if cmd == 'q': return False
        elif cmd == 'n': break

        formatted = []
        for move in turn:
            formatted.append( formatMove( b, move ) )
            b.moveCard( move, False )
        print( ", ".join( formatted ) )

    print( f"Finished {name}!")

    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Plays Baker's Game at the console")
    parser.add_argument( 'files', metavar='file', type=str, nargs='*', help="Deck files to read and play.")
    parser.add_argument( '-i', '--improve', dest='improvements', type=int, default=1, help="The number of improvements to try when solving")
    parser.add_argument( '-v', '--validate', dest='validate', action="store_true", help="Validate each move")
    args = parser.parse_args()

    if args.files:
        for filename in args.files:
            try:
                deck = board.parseDeck( open( filename, "r" ).read() )
            except AssertionError as msg:
                print( f"Unable to parse file {filename}:", str( msg ) )
                raise

            b = board.Board(deck)
            solution = b.solve( onSolved( args.improvements ), args.validate )
            playSolution( deck, solution, filename )
    else:
        playing = True
        while( playing ):
            deck, solution = generateSolvableBoard( args.improvements )
            playing = playSolution(deck, solution)
