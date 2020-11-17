#!/usr/bin/python3

noCard = -1

king = 12
ace = 0

suitChars = ['C', 'D', 'H', 'S', ]
pipsChars = ['-', 'A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', ]

def makeCard(suit, pips):
    return suit * 13 + pips

def suit(card):
    return card // 13

def pips(card):
    return card % 13

def formatPips(suit, pips):
    return pipsChars[pips + 1] + suitChars[suit]

def formatCard(card):
    return formatPips( suit(card), pips(card) ) if card != noCard else '--'

def parseCard(cardStr):
    if cardStr == '--': return noCard

    try:
        pips = pipsChars.index(cardStr[0]) - 1
        suit = suitChars.index(cardStr[1])
        return makeCard(suit, pips)

    except:
        print( cardStr[0], cardStr[1] )
        raise

def parseDeck(deckStr):
    deck = [parseCard(cardStr) for cardStr in deckStr.split()]
    cards = set()
    for d, card in enumerate(deck):
        assert card not in cards, f"Duplicate card {formatCard(card)} at position {d+1}"
        cards.add( card )
    return deck

def isStacked( cascade ):
    return len(cascade) > 1 and cascade[-1] == cascade[-2] - 1

def isKingStack( cascade ):
    if not cascade: return False

    prev = cascade[0]
    if pips( prev ) != king: return False

    for row, card in enumerate( cascade ):
        if not row: continue
        if prev != card + 1: return False
        prev = card

    return True

class Board:
    def __init__(self, deck):
        #   How many suits were we given?
        self._nsuits = suit(len(deck))

        #   Aces contains the highest pip number for that ace
        self._foundations = self._nsuits * [ noCard ]

        #   Cells contains cards
        self._cells = self._nsuits * [ noCard ]
        self._firstFree = 0

        #   Columns contains the main board layout
        self._tableau = [ [] for c in range(self._nsuits * 2) ]
        for d in range(0, len(deck)):
            self._tableau[d % len(self._tableau)].append(deck[d])

        #   We use a hash of the sorted cascades as a memento
        #   to avoid looping. Resorting is expensive, so we
        #   try to avoid it by setting a flag when the sort
        #   order becomes invalid. Since cards are unique,
        #   the sort order only changes when the first card
        #   in a cascade changes. We need to rehash whenever
        #   cards move, so that is a separate flag.
        self._memento = None
        self._resort = True
        self._rehash = True
        self._sorted = [cascade for cascade in self._tableau]

    def __str__(self):
        result = []

        #   Aces stacks across the top
        result.append('Aces:')
        row = []
        for suit, pips in enumerate(self._foundations):
            row.append( formatPips( suit, pips ) )
        row.reverse()
        result.append(' '.join(row))
        result.append('')

        #   Columns in the middle
        result.append('Table:')
        rows = max([len(cascade) for cascade in self._tableau])
        for r in range(rows):
            row = []
            for cascade in self._tableau:
                row.append(formatCard(cascade[r] if r < len(cascade) else noCard))
            result.append(' '.join(row))
        result.append('')

        #    Cells at the bottom
        result.append('Cells:')
        row = [formatCard(card) for card in self._cells]
        result.append(' '.join(row))
        result.append('')

        return '\n'.join(result)

    def isFoundationIndex(self, idx):
        return idx < 0

    def indexOfFoundation(self, cardSuit):
        return -cardSuit - 1

    def foundationOfIndex(self, idx):
        return -idx - 1

    def isCellIndex(self, idx):
        return idx >= len(self._tableau)

    def indexOfCell(self, cell):
        return cell + len(self._tableau)

    def cellOfIndex(self, idx):
        return idx - len(self._tableau)

    def cardOfIndex(self, idx):
        if self.isCellIndex( idx ) :
            return self._cells[self.cellOfIndex( idx )]

        elif self.isFoundationIndex( idx ):
            cardSuit = foundationOfIndex( idx )
            return makeCard( cardSuit, self._foundations[ cardSuit ] )

        else:
            return self._tableau[idx][-1]

    def checkCards(self):
        cards = set()

        for cardSuit, topPips in enumerate(self._foundations):
            for cardPips in range(topPips + 1):
                cards.add(makeCard(cardSuit, cardPips))

        for cell, card in enumerate(self._cells):
            assert card not in cards, f"Duplicate card {formatCard(card)} in cell {cell}"
            if card != noCard: cards.add(card)

        for column, cascade in enumerate(self._tableau):
            for row, card in enumerate(cascade):
                assert card not in cards, f"Duplicate card {formatCard(card)} in cascade {column}, row {row}"

                cards.add(card)

        if len(cards) != self._nsuits * 13:
            for card in range(0, self._nsuits * 13):
                assert card in cards, f"Missing card {formatCard(card)}"

    def moveCard(self, move, validate = False):
        """Move a card at the start location to the finish
        location. Negative locations are the aces;
        locations past the number of cascades are the
        holding cells.

        moveCard works in both directions so it can
        be used to backtrack."""
        start, finish = move

        card = noCard

        #   From a foundation
        if self.isFoundationIndex(start):
            foundation = self.foundationOfIndex(start)
            if validate:
                assert foundation < len(self._foundations), f"Move from invalid foundation {foundation}"
                assert self._foundations[foundation] != noCard, f"Move from empty foundation {foundation}"
            cardPips = self._foundations[foundation]
            self._foundations[foundation] = cardPips - 1
            card = makeCard(foundation, cardPips)

        #   From a cell
        elif self.isCellIndex(start):
            cell = self.cellOfIndex(start)
            if validate:
                assert cell < len(self._cells), f"Move from invalid cell {cell}"
                assert self._cells[cell] != noCard, f"Move from empty cell {cell}"
            card = self._cells[cell]
            self._cells[cell] = noCard

            #   Check whether this is now the first free cell
            if self._firstFree > cell:
                self._firstFree = cell

        #   From a cascade
        else:
            cascade = self._tableau[start]
            if validate:
                assert cascade, f"Move from empty cascade {start}"
            card = cascade.pop()
            if not cascade: self._resort = True


        #   To a foundation
        if self.isFoundationIndex(finish):
            foundation = self.foundationOfIndex(finish)
            cardPips = pips(card)
            if validate:
                assert foundation < len(self._foundations), f"Move to invalid foundation {foundation}"
                assert foundation == suit(card), f"Move of {formatCard(card)} to the wrong foundation {foundation}"
                assert self._foundations[foundation] == cardPips - 1, f"Move of {formatCard(card)} to foundation {foundation} not onto previous card {formatCard(makeCard(foundation, self._foundations[foundation]))}"
            self._foundations[foundation] = cardPips

        #   To a cell
        elif self.isCellIndex(finish):
            #   Insert into cell
            cell = self.cellOfIndex(finish)
            if validate:
                assert cell < len(self._cells), f"Move to invalid cell {cell}"
                assert self._cells[cell] == noCard, f"Move to occupied cell {formatCard(self._cells[cell])}"
            self._cells[cell] = card

            #   Update the first free cell
            if cell == self._firstFree:
                self._firstFree += 1
                while self._firstFree < len(self._cells):
                    if self._cells[self._firstFree] == noCard:
                        break
                    self._firstFree += 1

        #   To a cascade
        else:
            cascade = self._tableau[finish]
            if validate and cascade:
                assert cascade[-1] == card + 1, f"Move of {formatCard(card)} to cascade {finish} not onto subsequent card {formatCard(cascade[-1])}"
            if not cascade: self._resort = True
            cascade.append(card)

        #   Need to rehash after moving
        self._rehash = True

        if validate:
            self.checkCards()

        return move

    def backtrack(self, moves, validate = False):
        """Undoes a sequence of moves by executing them in reverse order."""
        while moves:
            finish, start = moves.pop()
            self.moveCard((start, finish,), validate)

    def moveToFoundations( self, validate = False ):
        """Move all cards that can cover aces.
        Return a list of the moves.
        This list should be treated as a single unit."""
        moves = []

        moved = len(moves) - 1
        while moved != len(moves):
            moved = len(moves)

            for cell, card in enumerate(self._cells):
                if card == noCard: continue

                cardSuit = suit(card)
                cardPips = pips(card)

                #   Can we remove it?
                if self._foundations[cardSuit] == cardPips - 1:
                    start = self.indexOfCell(cell)
                    finish = self.indexOfFoundation(cardSuit)
                    moves.append( self.moveCard( (start, finish, ), validate ) )

            for start, cascade in enumerate(self._tableau):
                while cascade:
                    card = cascade[-1]
                    cardSuit = suit(card)
                    cardPips = pips(card)
                    #   Can we remove it?
                    if self._foundations[cardSuit] != cardPips - 1: break

                    finish = self.indexOfFoundation(cardSuit)
                    moves.append( self.moveCard( (start, finish, ), validate ) )

        return moves

    def enumerateFinishCascades(self, start, card):
        """Enumerate all the finish cascades for a card."""
        moves = []

        fromCell = self.isCellIndex( start )
        for finish, cascade in enumerate(self._tableau):
            if start == finish: continue

            if cascade:
                under = cascade[-1]
                #   We can't stack a king on an ace because
                #   exposed aces are always removed first
                if under == card + 1:
                    moves.append((start, finish,))

            #   Don't move between empty cascades - NOP
            elif fromCell or len(self._tableau[start]) > 1:
                moves.append((start, finish,))

        return moves

    def enumerateMoves(self):
        """Enumerate all the legal moves that can be made."""

        #   3. Move from cascades to the first open cell
        stacked_to_cell = []        #   Stacked card to free cell
        isolate_to_cell = []        #   Isolate card to free cell
        openCells = 0
        if self._firstFree < len(self._cells):
            for card in self._cells: openCells += ( card == noCard )

            finish = self.indexOfCell(self._firstFree)
            for start, cascade in enumerate(self._tableau):
                if not cascade:
                    continue

                elif isStacked( cascade ):
                    #   If the stack is anchored on a king, don't move anything
                    if openCells >= len( cascade ) or not isKingStack( cascade ):
                        stacked_to_cell.append( (start, finish,) )

                else:
                    isolate_to_cell.append( (start, finish,) )

        #   2. Move from cells to cascades
        cell_to_cascade = []        #   Cell card to any cascade
        for start, card in enumerate(self._cells):
            if card != noCard:
                cell_to_cascade.extend(self.enumerateFinishCascades(self.indexOfCell(start), card))

        #   1. Move from cascades to cascades
        stacked_to_open = []        #   Stacked card to open cascade
        isolate_to_cascade = []     #   Isolate card to any cascade
        for start, cascade in enumerate(self._tableau):
            if cascade:
                finishes = self.enumerateFinishCascades(start, cascade[-1])
                if isStacked( cascade ):
                    if openCells >= len( cascade ) or not isKingStack( cascade ):
                        stacked_to_open.extend( finishes )
                else:
                    isolate_to_cascade.extend( finishes )

        #   Build the list in reverse order
        #   because we will pop choices from the back.

        moves = []
        moves.extend( stacked_to_cell )
        moves.extend( isolate_to_cell )
        moves.extend( cell_to_cascade )
        moves.extend( stacked_to_open )
        moves.extend( isolate_to_cascade )

        return moves

    def memento(self):
        """Lazily compute the cached memento."""

        #   If the cascades are out of order, then re-sort them
        if self._resort:
            self._sorted.sort()
            self._resort = False
            self._rehash = True

        #   If cards moved, re-hash the sorted cascades
        if self._rehash:
            self._memento = hash( tuple(tuple(cascade) for cascade in self._sorted) )
            self._rehash = False

        return self._memento

    def solved(self):
        return sum(self._foundations) == self._nsuits * 12

    def solve(self, callback = None, validate = False ):
        """Finds the first solution of the board using a depth first search.
        If a callback is provided, it will be given the board, solution and visited hash set
        and should return True to keep searching for shorter solutions, False to terminate."""
        solution = []

        #   Search state
        visited = set()
        stack = []
        history = []

        #   Move the aces
        moves = self.moveToFoundations()
        history.append(moves)
        if self.solved(): solution = history

        #   Remember the starting position
        visited.add(self.memento())

        #   Add the first level, if any
        level = self.enumerateMoves()
        if level: stack.append(level)
        while stack:
            #   We always remove from the backs of lists
            #   to avoid copying
            if stack[-1]:
                moves = stack[-1]
                move = moves.pop()
                try:
                    self.moveCard( move, validate )
                except:
                    print( move )
                    print( self )
                    raise

                moves = [move,]
                moves.extend(self.moveToFoundations())
                history.append(moves)

                tooLong = ( solution and len(solution) <= len(history) )

                #   Are we done?
                terminated = callback and not callback(board=self, solution=solution, visited=visited)
                if terminated or self.solved():
                    #   Keep the shortest
                    if not tooLong:
                        solution = history.copy()
                        if terminated or not callback: break

                    #   Nowhere else to go
                    self.backtrack(history.pop())
                    continue

                #   Check whether we have been here before
                memento = self.memento()
                if memento in visited or tooLong:
                    #   Abort this level if we have been here before
                    self.backtrack( history.pop(), validate )

                else:
                    #   Remember this position
                    visited.add(memento)
                    #   Go down one level, if we can
                    level = self.enumerateMoves()
                    if level:
                        stack.append(level)
                    else:
                        self.backtrack( history.pop(), validate )

            else:
                #   Go up one level
                stack.pop()
                #   Back out the move
                self.backtrack(history.pop())

        #   Empty stack => empty history
        return solution

if __name__ == '__main__':
    b = Board(range(0,52))
    print(b)
    print(b.solve())
