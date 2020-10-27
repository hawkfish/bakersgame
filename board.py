#!/usr/bin/python3

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
    return [parseCard(cardStr) for cardStr in deckStr.split()]

class Board:
    def __init__(self, deck):
        #   How many suits were we given?
        self._nsuits = suit(len(deck))

        #   Aces contains the highest pip number for that ace
        self._foundations = self._nsuits * [ noCard ]

        #   Cells contains cards
        self._cells = self._nsuits * [ noCard ]
        self._occupied = 0

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
        row = [formatCard(cell) if r < cell else '--' for cell in self._cells]
        result.append(' '.join(row))
        result.append('')

        return '\n'.join(result)

    def moveCard(self, move, validate = True):
        """Move a card at the start location to the finish
        location. Negative locations are the aces;
        locations past the number of cascades are the
        holding cells.

        moveCard works in both directions so it can
        be used to backtrack."""
        start, finish = move

        card = noCard
        ncols = len(self._tableau)

        #   From a foundation
        if start < 0:
            foundation = -start - 1
            if validate:
                assert foundation < len(self._foundations), f"Move from invalid foundation {foundation}"
            cardPips = self._foundations[foundation]
            self._foundations[foundation] = cardPips - 1
            card = makeCard(foundation, cardPips)

        #   From a cascade
        elif start < ncols:
            cascade = self._tableau[start]
            if validate:
                assert cascade, f"Move from empty cascade {start}"
            card = cascade.pop()
            if not cascade: self._resort = True

        #   From a cell
        else:
            cell = start - ncols
            if validate:
                assert cell < self._occupied, f"Move from empty cell {cell}"
            card = self._cells[cell]
            self._cells[cell] = self._cells[self._occupied - 1]
            self._occupied -= 1

        #   To a foundation
        if finish < 0:
            foundation = suit(card)
            if validate:
                assert foundation < len(self._foundations), f"Move to invalid foundation {foundation}"
            self._foundations[foundation] = pips(card)

        #   To a cascade
        elif finish < ncols:
            cascade = self._tableau[finish]
            if validate and cascade:
                assert cascade[-1] == card + 1, f"Move not onto subsequent card"
            if not cascade: self._resort = True
            cascade.append(card)

        #   To a cell
        else:
            #   Push to the end
            if validate:
                assert self._occupied <= len(self._cells), "Cells full"
            self._cells[self._occupied] = card
            self._occupied += 1

        #   Need to rehash after moving
        self._rehash = True

    def coverFoundations(self):
        """Move all cards that can cover aces.
        Return a list of the moves.
        This list should be treated as a single unit."""
        moves = []
        ncols = len(self._tableau)

        for c in range(0, ncols):
            cascade = self._tableau[c]
            while cascade:
                card = cascade[-1]
                cardSuit = suit(card)
                cardPips = pips(card)
                #   Can we remove it?
                if self._foundations[cardSuit] != cardPips - 1: break

                self._foundations[cardSuit] = cardPips
                cascade.pop()
                moves.append((c, -cardSuit - 1))
                self._rehash = True
                if not cascade: self._resort = True

        #   If anything changed, we need to rehash.
        if moves: self._rehash = True

        return moves

    def enumerateFinishColumns(self, start, card):
        """Enumerate all the finish cascades for a card."""
        moves = []
        for finish in range(len(self._tableau)):
            if start == finish: continue

            cascade = self._tableau[finish]
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
        ncols = len(self._tableau)

        #   Build the list in reverse order
        #   because we will pop choices from the back.

        #   3. Move from cascades to the next open cell
        if self._occupied < len(self._cells):
            finish = ncols + self._occupied
            for start in range(0, ncols):
                if not self._tableau[start]: continue
                moves.append((start, finish,))

        #   2. Move from cascades to cascades
        for start in range(ncols):
            cascade = self._tableau[start]
            if cascade:
                moves.extend(self.enumerateFinishColumns(start, cascade[-1]))

        #   1. Move from cells to cascades
        for cell in range(0, self._occupied):
            moves.extend(self.enumerateFinishColumns(cell + ncols, self._cells[cell]))

        return moves

    def backtrack(self, moves):
        """Undoes a sequence of moves by executing them in reverse order."""
        while moves:
            finish, start = moves.pop()
            self.moveCard((start, finish,), False)

    def memento(self):
        """Lazily compute the cached memento."""

        #   If the cascades are out of order, then re-sort them
        if self._resort:
            self._sorted.sort()
            self._resort = False
            self._rehash = True

        #   If cards moved, re-hash the sorted cascades
        if self._rehash:
            self._memento = hash( (tuple(cascade) for cascade in self._sorted) )
            self._rehash = False

        return self._memento

    def solved(self):
        return sum(self._foundations) == self._nsuits * 12

    def solve(self):
        """Finds the first solution of the board using a depth first search."""
        history = []

        #   Search state
        visited = set()
        stack = []

        #   Move the aces
        moves = self.coverFoundations()
        history.append(moves)

        #   Remember the starting position
        visited.add(self.memento())

        #   Add the first level
        stack.append(self.enumerateMoves())
        while stack:
            #   We always remove from the backs of lists
            #   to avoid copying
            if stack[-1]:
                moves = stack[-1]
                move = moves.pop()
                self.moveCard(move, False)

                moves = [move,].extend(self.coverFoundations())
                history.append(moves)

                #   Are we done?
                if self.solved(): return history

                #   Check whether we have been here before
                memento = self.memento()
                if memento in visited:
                    #   Abort this level if we have been here before
                    self.backtrack(history.pop())

                else:
                    #   Remember this position
                    visited.add(memento)
                    #   Go down one level
                    stack.append(self.enumerateMoves())

            else:
                #   Go up one level
                stack.pop()
                #   Back out the move
                self.backtrack(history.pop())

        #   Empty stack => empty history
        return history

if __name__ == '__main__':
    b = Board(range(0,52))
    print(b)
    print(b.solve())
