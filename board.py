#!/usr/bin/python3

import copy

noCard = -1

suitChars = ['C', 'D', 'H', 'S', ]
pipsChars = ['-', 'A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', ]

def makeCard(suit, pips):
    return suit * 13 + pips

def suit(card):
    return card // 13

def pips(card):
    return card % 13

def formatCard(card):
    return pipsChars[pips(card) + 1] + suitChars[suit(card)]

def parseCard(cardStr):
    pips = pipsChars.index(cardStr[0]) - 1
    suit = suitChars.index(cardStr[1])
    return makeCard(suit, pips)

def parseDeck(deckStr):
    deck = [parseCard(cardStr) for cardStr in deckStr.split()]
    cards = set()
    for d, card in enumerate(deck):
        assert card not in cards, f"Duplicate card {formatCard(card)} at position {d+1}"
    return deck

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
        for suit in range(len(self._foundations)):
            row.append(pipsChars[self._foundations[suit] + 1] + suitChars[suit] )
        row.reverse()
        result.append(' '.join(row))
        result.append('')

        #   Columns in the middle
        result.append('Table:')
        r = 0
        while(1):
            moreRows = max([r < len(cascade) for cascade in self._tableau])
            if not moreRows: break

            row = []
            for cascade in self._tableau:
                row.append(formatCard(cascade[r]) if r < len(cascade) else '--')
            result.append(' '.join(row))
            r = r + 1
        result.append('')

        #    Cells at the bottom
        result.append('Cells:')
        row = [formatCard(cell) if cell != noCard else '--' for cell in self._cells]
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

    def moveCard(self, move, validate = True):
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

        return move

    def moveToFoundations(self):
        """Move all cards that can cover aces.
        Return a list of the moves.
        This list should be treated as a single unit."""
        moves = []

        moved = 1
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
                    moves.append(self.moveCard((start, finish, ), False))

            for start, cascade in enumerate(self._tableau):
                while cascade:
                    card = cascade[-1]
                    cardSuit = suit(card)
                    cardPips = pips(card)
                    #   Can we remove it?
                    if self._foundations[cardSuit] != cardPips - 1: break

                    finish = self.indexOfFoundation(cardSuit)
                    moves.append(self.moveCard((start, finish, ), False))

        return moves

    def enumerateFinishCascades(self, start, card):
        """Enumerate all the finish cascades for a card."""
        moves = []
        for finish, cascade in enumerate(self._tableau):
            if start == finish: continue

            if cascade:
                under = cascade[-1]
                #   We can't put a king on an ace because
                #   exposed aces are always removed first
                if under == card + 1:
                    moves.append((start, finish,))
            else:
                moves.append((start, finish,))

        return moves

    def enumerateMoves(self):
        """Enumerate all the legal moves that can be made."""
        moves = []

        #   Build the list in reverse order
        #   because we will pop choices from the back.

        #   3. Move from cascades to the first open cell
        if self._firstFree < len(self._cells):
            finish = self.indexOfCell(self._firstFree)
            for start, cascade in enumerate(self._tableau):
                if not cascade: continue
                moves.append((start, finish,))

        #   2. Move from cascades to cascades
        for start, cascade in enumerate(self._tableau):
            if cascade:
                moves.extend(self.enumerateFinishCascades(start, cascade[-1]))

        #   1. Move from cells to cascades
        for start, card in enumerate(self._cells):
            if card != noCard:
                moves.extend(self.enumerateFinishCascades(self.indexOfCell(start), card))

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

    def backtrack(self, moves):
        """Undoes a sequence of moves by executing them in reverse order."""
        while moves:
            finish, start = moves.pop()
            self.moveCard((start, finish,), False)

    def check(self):
        cards = set()

        for cardSuit, top in enumerate(self._foundations):
            for cardPips in range(top):
                cards.add(makeCard(cardSuit, cardPips))

        for cell, card in enumerate(self._cells):
            assert card not in cards, f"Duplicate card {formatCard(card)} in cell {cell}"
            if card != noCard: cards.add(card)

        for column, cascade in enumerate(self._tableau):
            for row, card in enumerate(cascade):
                assert card not in cards, f"Duplicate card {formatCard(card)} in cascade {column}, row {row}"

                cards.add(card)

        #assert len(cards) == 52, str(self)

    def solve(self):
        """Finds the first solution of the board using a depth first search."""
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
                self.moveCard(move, False)

                moves = [move,]
                moves.extend(self.moveToFoundations())
                history.append(moves)

                #   Are we done?
                if self.solved():
                    #   Keep the shortest
                    if not solution or len(solution) > len(history):
                        # print( len(history), len(visited) )
                        solution = history
                        break

                    #   Nowhere else to go
                    self.backtrack(history.pop())
                    continue

                #   Check whether we have been here before
                memento = self.memento()
                if memento in visited:
                    #   Abort this level if we have been here before
                    self.backtrack(history.pop())

                else:
                    #   Remember this position
                    visited.add(memento)
                    #   Go down one level, if we can
                    level = self.enumerateMoves()
                    if level:
                        stack.append(level)
                    else:
                        self.backtrack(history.pop())


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
