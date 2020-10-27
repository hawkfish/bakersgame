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
        self._aces = self._nsuits * [ noCard ]

        #   Cells contains cards
        self._cells = self._nsuits * [ noCard ]
        self._occupied = 0

        #   Columns contains the main board layout
        self._columns = [ [] for c in range(self._nsuits * 2) ]
        for d in range(0, len(deck)):
            self._columns[d % len(self._columns)].append(deck[d])

        #   We use a hash of the sorted columns as a memento
        #   to avoid looping. Resorting is expensive, so we
        #   try to avoid it by setting a flag when the sort
        #   order becomes invalid. Since cards are unique,
        #   the sort order only changes when the first card
        #   in a column changes. We need to rehash whenever
        #   cards move, so that is a separate flag.
        self._memento = None
        self._resort = True
        self._rehash = True
        self._sorted = [column for column in self._columns]

    def __str__(self):
        result = []

        #   Aces stacks across the top
        result.append('Aces:')
        row = []
        for suit in range(len(self._aces)):
            row.append(pipsChars[self._aces[suit] + 1] + suitChars[suit] )
        row.reverse()
        result.append(' '.join(row))
        result.append('')

        #   Columns in the middle
        result.append('Table:')
        r = 0
        while(1):
            moreRows = max([r < len(column) for column in self._columns])
            if not moreRows: break

            row = []
            for column in self._columns:
                row.append(formatCard(column[r]) if r < len(column) else '--')
            result.append(' '.join(row))
            r = r + 1
        result.append('')

        #    Cells at the bottom
        result.append('Cells:')
        row = [formatCard(cell) if r < cell else '--' for cell in self._cells]
        result.append(' '.join(row))
        result.append('')

        return '\n'.join(result)

    def moveCard(self, move):
        """Move a card at the start location to the finish
        location. Negative locations are the aces;
        locations past the number of columns are the
        holding cells.

        moveCard works in both directions so it can
        be used to backtrack."""
        start, finish = move

        card = noCard
        ncols = len(self._columns)

        #   From an ace
        if start < 0:
            cardSuit = -start
            cardPips = self._aces[cardSuit]
            self._aces[cardSuit] = cardPips - 1
            card = makeCard(cardSuit, cardPips)

        #   From a column
        elif start < ncols:
            column = self._columns[start]
            card = column.pop()
            if not column: self._resort = True

        #   From a holding cell
        else:
            cell = start - ncols
            card = self._cells[cell]
            self._cells[cell] = self._cells[self._occupied - 1]
            self._occupied -= 1

        #   To an ace
        if finish < 0:
            self._aces[suit(card)] = pips(card)

        #   To a column
        elif finish < ncols:
            column = self._columns[finish]
            if not column: self._resort = True
            column.append(card)

        #   To a holding cell
        else:
            cell = finish - ncols
            self._cells[cell] = card
            self._occupied += 1

        #   Need to rehash after moving
        self._rehash = True

    def coverAces(self):
        """Move all cards that can cover aces.
        Return a list of the moves.
        This list should be treated as a single unit."""
        moves = []
        ncols = len(self._columns)

        for c in range(0, ncols):
            column = self._columns[c]
            while column:
                card = column[-1]
                cardSuit = suit(card)
                cardPips = pips(card)
                #   Can we remove it?
                if self._aces[cardSuit] != cardPips - 1: break

                self._aces[cardSuit] = cardPips
                column.pop()
                moves.append((c, -cardSuit - 1))
                self._rehash = True
                if not column: self._resort = True

        #   If anything changed, we need to rehash.
        if moves: self._rehash = True

        return moves

    def enumerateFinishColumns(self, start, card):
        """Enumerate all the finish columns for a card."""
        moves = []
        for finish in range(len(self._columns)):
            if start == finish: continue

            column = self._columns[finish]
            if column:
                under = column[-1]
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
        ncols = len(self._columns)

        #   Build the list in reverse order
        #   because we will pop choices from the back.

        #   3. Move from columns to the next open cell
        if self._occupied < len(self._cells):
            finish = ncols + self._occupied
            for start in range(0, ncols):
                if not self._columns[start]: continue
                moves.append((start, finish,))

        #   2. Move from columns to columns
        for start in range(ncols):
            column = self._columns[start]
            if column:
                moves.extend(self.enumerateFinishColumns(start, column[-1]))

        #   1. Move from cells to columns
        for cell in range(0, self._occupied):
            moves.extend(self.enumerateFinishColumns(cell + ncols, self._cells[cell]))

        return moves

    def backtrack(self, moves):
        """Undoes a sequence of moves by executing them in reverse order."""
        while moves:
            finish, start = moves.pop()
            self.moveCard((start, finish,))

    def memento(self):
        """Lazily compute the cached memento."""

        #   If the columns are out of order, then re-sort them
        if self._resort:
            self._sorted.sort()
            self._resort = False
            self._rehash = True

        #   If cards moved, re-hash the sorted columns
        if self._rehash:
            self._memento = hash( (tuple(column) for column in self._sorted) )
            self._rehash = False

        return self._memento

    def solved(self):
        return sum(self._aces) == self._nsuits * 12

    def solve(self):
        """Finds the first solution of the board using a depth first search."""
        history = []

        #   Search state
        visited = set()
        stack = []

        #   Move the aces
        moves = self.coverAces()
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
                self.moveCard(move)

                moves = [move,].extend(self.coverAces())
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
