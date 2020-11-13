#!/usr/bin/python3

import unittest

import board

#   Deck fixtures
unshuffled = [*range(0,52)]
reversed = [*range(0,52)]
reversed.reverse()

no_aces = board.parseDeck("""
9H KD 8H JD AC 9S 7C 6D
JH 3H 7S TC AH 2C 6C 4H
KH AD TH 2D 3S QC JS 4S
5D TD 8C TS 6H JC 8S 7D
QS QD 4D 3C AS 5H 7H QH
5C KC 8D 9C 2H 3D KS 6S
9D 5S 2S 4C
""")

two_aces = board.parseDeck("""
KH 2H 4D QC 3S 7D 7S KD
JD 4H 3C 7C 9H KS 7H 5D
6S AC QS TD JC 9C JH KC
9S 4S QH 2D 4C AD TS 8H
TH 2S JS 6C 9D 3D 8D TC
2C 5H 8C 5S 3H 6H 8S 6D
AH 5C QD AS
""")

two_aces_two = board.parseDeck("""
6H AH 3H 2D JC 4D TH QD
TS 7D 9D 2C 7S QS JD 5D
8H 4S 6S 5H 6C KD KC JH
QC TD 8S 7C 4C KS 9H 3S
2S 2H 9S TC 8D 5C AD 4H
AS 5S 8C QH JS 6D KH 7H
AC 3D 9C 3C
""")

class CardUnitTest(unittest.TestCase):

    def test_makeCard(self):
        for card in range(0,52):
            self.assertEqual(card, board.makeCard(card // 13, card % 13))

    def test_suit(self):
        for card in range(0,52):
            self.assertEqual(card // 13, board.suit(card), )

    def test_pips(self):
        for card in range(0,52):
            self.assertEqual(card % 13, board.pips(card))

    def assert_formatCard(self, formatted, suit, pips):
        card = board.makeCard(suit, pips)

        actual = board.formatCard(card)
        self.assertEqual(formatted, actual, f"Card format failed %{pips}; {suit}")

        actual = board.parseCard(formatted)
        self.assertEqual(card, actual, f"Card parse %{pips}; {suit}")

    def test_formatCard(self):
        self.assert_formatCard('AC', 0, 0)
        self.assert_formatCard('2C', 0, 1)
        self.assert_formatCard('9C', 0, 8)
        self.assert_formatCard('TC', 0, 9)
        self.assert_formatCard('JC', 0, 10)
        self.assert_formatCard('QC', 0, 11)
        self.assert_formatCard('KC', 0, 12)

class BoardUnitTest(unittest.TestCase):

    def assert_init(self, deck):
        cards = len(deck)
        self.assertEqual(0, cards % 13, f"Uneven suits: {cards} cards in the deck")

        b = board.Board(deck)

        suits = cards // 13
        self.assertEqual(suits, b._nsuits)

        self.assertEqual(suits, len(b._foundations))
        for a, ace in enumerate(b._foundations):
            self.assertEqual(ace, board.noCard, f"Ace {a} not empty")

        self.assertEqual(suits * 2, len(b._tableau))
        for c, cascade in enumerate(b._tableau):
            expected = cards // len(b._tableau) + (c < suits)
            self.assertEqual(expected, len(cascade), f"Column {c} incorrectly sized")
            for r, card in enumerate(cascade):
                expected = deck[r * suits * 2 + c]
                self.assertEqual(expected, card)

        self.assertIsNone(b._memento, "Pre-initialised memento")
        self.assertTrue(b._resort, "Not initialised to resort")
        self.assertTrue(b._rehash, "Not initialised to rehash")

        self.assertEqual(len(b._tableau), len(b._sorted), "Hashing cascades not initialised")
        for s, actual in enumerate(b._sorted):
            self.assertEqual(b._tableau[s], actual)

    def test_init(self):
        self.assert_init(unshuffled)

    def assert_str(self, expected, deck):
        self.assertEqual(expected, str(board.Board(deck)))

    def test_str_unshuffled(self):
        expected = """Aces:
-S -H -D -C

Table:
AC 2C 3C 4C 5C 6C 7C 8C
9C TC JC QC KC AD 2D 3D
4D 5D 6D 7D 8D 9D TD JD
QD KD AH 2H 3H 4H 5H 6H
7H 8H 9H TH JH QH KH AS
2S 3S 4S 5S 6S 7S 8S 9S
TS JS QS KS -- -- -- --

Cells:
-- -- -- --
"""
        self.assert_str(expected, unshuffled)

    def test_str_reversed(self):
        expected = """Aces:
-S -H -D -C

Table:
KS QS JS TS 9S 8S 7S 6S
5S 4S 3S 2S AS KH QH JH
TH 9H 8H 7H 6H 5H 4H 3H
2H AH KD QD JD TD 9D 8D
7D 6D 5D 4D 3D 2D AD KC
QC JC TC 9C 8C 7C 6C 5C
4C 3C 2C AC -- -- -- --

Cells:
-- -- -- --
"""
        self.assert_str(expected, reversed)

    def test_str_two_aces(self):
        expected = """Aces:
-S -H -D -C

Table:
KH 2H 4D QC 3S 7D 7S KD
JD 4H 3C 7C 9H KS 7H 5D
6S AC QS TD JC 9C JH KC
9S 4S QH 2D 4C AD TS 8H
TH 2S JS 6C 9D 3D 8D TC
2C 5H 8C 5S 3H 6H 8S 6D
AH 5C QD AS -- -- -- --

Cells:
-- -- -- --
"""
        self.assert_str(expected, two_aces)

    def test_move_to_foundations_no_aces(self):
        b = board.Board(no_aces)
        b._rehash = b._resort = False
        actual = b.moveToFoundations()
        expected = []
        self.assertEqual(expected, actual)
        self.assertFalse(b._rehash)
        self.assertFalse(b._resort)

    def test_move_to_foundations_two_aces(self):
        b = board.Board(two_aces)
        b._rehash = b._resort = False
        actual = b.moveToFoundations()
        expected = [(0, -3,), (3, -4),]
        self.assertEqual(expected, actual)
        self.assertTrue(b._rehash)
        self.assertFalse(b._resort)

    def test_move_to_foundations_two_aces_two(self):
        b = board.Board(two_aces_two)
        b._rehash = b._resort = False
        actual = b.moveToFoundations()
        expected = [(0, -1,), (0, -4), (0, -4), ]
        self.assertEqual(expected, actual)
        self.assertTrue(b._rehash)
        self.assertFalse(b._resort)

    def test_move_to_foundations_reversed(self):
        setup = board.Board(reversed)
        setup._rehash = setup._resort = False
        actual = setup.moveToFoundations()
        self.assertTrue(setup._rehash)
        self.assertTrue(setup._resort)

    def test_move_to_foundations_cell(self):
        setup = board.Board(unshuffled)

        # One king in a cell
        for cascade in setup._tableau: cascade.clear()

        king = 12
        queen = king - 1
        clubs = 0
        setup._cells = [ board.noCard, board.makeCard(clubs, king), board.noCard, board.noCard, ]
        setup._foundations = [queen, king, king, king, ]
        expected = [(9, -1,),]
        actual = setup.moveToFoundations()
        self.assertEqual(expected, actual)

    def test_move_between_cascades_and_cells(self):
        b = board.Board(unshuffled)

        #   Move to cell #1
        b.moveCard((0,8,))
        self.assertTrue(b._rehash)
        self.assertEqual(1, b._firstFree)
        self.assertEqual(6, len(b._tableau[0]))

        #   Move to cell #2
        b.moveCard((0,9,))
        self.assertTrue(b._rehash)
        self.assertEqual(2, b._firstFree)
        self.assertEqual(5, len(b._tableau[0]))

        #   Move to cell #3
        b.moveCard((1,10,))
        self.assertTrue(b._rehash)
        self.assertEqual(3, b._firstFree)
        self.assertEqual(6, len(b._tableau[1]))

        #   Move to cell #4
        b.moveCard((2,11,))
        self.assertTrue(b._rehash)
        self.assertEqual(4, b._firstFree)
        self.assertEqual(6, len(b._tableau[2]))

        #   Move to cascade #1
        b.moveCard((11,3,))
        self.assertTrue(b._rehash)
        self.assertEqual(3, b._firstFree)
        self.assertEqual(8, len(b._tableau[3]))

        #   Move to cascade #2
        b.moveCard((10,3,))
        self.assertTrue(b._rehash)
        self.assertEqual(2, b._firstFree)
        self.assertEqual(9, len(b._tableau[3]))

        #   Move to cascade #3
        b.moveCard((8,3,))
        self.assertTrue(b._rehash)
        self.assertEqual(0, b._firstFree)
        self.assertEqual(10, len(b._tableau[3]))

        #   Move to cascade #4
        b.moveCard((9,1,))
        self.assertTrue(b._rehash)
        self.assertEqual(0, b._firstFree)
        self.assertEqual(7, len(b._tableau[1]))

    def test_move_between_cascades_and_foundations(self):
        b = board.Board(two_aces_two)

        #   Move to foundations #1
        b._resort = b._rehash = False
        b.moveCard((0,-1,))
        self.assertTrue(b._rehash)
        self.assertFalse(b._resort)
        self.assertEqual(0, b._firstFree)
        self.assertEqual(6, len(b._tableau[0]))
        self.assertEqual([0, board.noCard, board.noCard, board.noCard,], b._foundations)

        #   Move to foundations #2
        b._resort = b._rehash = False
        b.moveCard((0,-4,))
        self.assertTrue(b._rehash)
        self.assertFalse(b._resort)
        self.assertEqual(0, b._firstFree)
        self.assertEqual(5, len(b._tableau[0]))
        self.assertEqual([0, board.noCard, board.noCard, 0,], b._foundations)

        #   Move to foundations #3
        b._resort = b._rehash = False
        b.moveCard((0,-4,))
        self.assertTrue(b._rehash)
        self.assertFalse(b._resort)
        self.assertEqual(0, b._firstFree)
        self.assertEqual(4, len(b._tableau[0]))
        self.assertEqual([0, board.noCard, board.noCard, 1,], b._foundations)

        #   Move from foundations #1
        b._resort = b._rehash = False
        b.moveCard((-4,0,), False)
        self.assertTrue(b._rehash)
        self.assertFalse(b._resort)
        self.assertEqual(0, b._firstFree)
        self.assertEqual(5, len(b._tableau[0]))
        self.assertEqual([0, board.noCard, board.noCard, 0,], b._foundations)

        #   Move from foundations #2
        b._resort = b._rehash = False
        b.moveCard((-4,0,), False)
        self.assertTrue(b._rehash)
        self.assertFalse(b._resort)
        self.assertEqual(0, b._firstFree)
        self.assertEqual(6, len(b._tableau[0]))
        self.assertEqual([0, board.noCard, board.noCard, board.noCard,], b._foundations)

        #   Move from foundations #2
        b._resort = b._rehash = False
        b.moveCard((-1,0,), False)
        self.assertTrue(b._rehash)
        self.assertFalse(b._resort)
        self.assertEqual(0, b._firstFree)
        self.assertEqual(7, len(b._tableau[0]))
        self.assertEqual([board.noCard, board.noCard, board.noCard, board.noCard,], b._foundations)

    def test_move_to_empty_cascade(self):
        b = board.Board(unshuffled)

        #   Put kings on the foundations
        king = 12
        for f, foundation in enumerate(b._foundations): b._foundations[f] = king

        #   Clear the cascades
        for cascade in b._tableau: cascade.clear()

        #   Move a king to an empty cell
        b.moveCard((-1, 0,))
        self.assertEqual(king, b._tableau[0][-1])
        self.assertTrue(b._resort)
        self.assertTrue(b._rehash)

        #   Move a queen to an empty cell
        queen = king - 1
        b._resort = b._rehash = False
        b.moveCard((-1, 1,))
        self.assertEqual(queen, b._tableau[1][-1])
        self.assertTrue(b._resort)
        self.assertTrue(b._rehash)

    def test_enumerate_finish_to_card(self):
        b = board.Board(no_aces)

        start = 1
        actual = b.enumerateFinishCascades(start, b._tableau[start][-1])
        expected = [(start, 7,),]
        self.assertEqual(expected, actual)

    def test_enumerate_finish_to_empty(self):
        setup = board.Board(unshuffled)

        #   Set up an empty cascade
        setup._foundations = [12 - len(setup._tableau) + 1, 12, 12, 12,]

        #   Clubs in the top row, except the first cascade
        for start, cascade in enumerate(setup._tableau):
            cascade.clear()
            if start: cascade.append(start)

        #   Every card can move to the leftmost or the next cascade
        for start, cascade in enumerate(setup._tableau):
            if cascade:
                actual = setup.enumerateFinishCascades(start, cascade[-1])
                expected = []
                expected.append( (start, 0,) )
                if start + 1 < len(setup._tableau):
                    expected.append( (start, start + 1,) )
                self.assertEqual(expected, actual)

    def test_enumerate_moves_unshuffled(self):
        setup = board.Board(unshuffled)
        width = len(setup._tableau)

        #   3. Move from cascades to the next open width
        expected = [(start, width,) for start in range(width)]

        #   2. Move from cascades to cascades
        for start in range(width):
            if start != 3:
                expected.append((start, (start + 1) % width,))

        #   1. Move from cells to cascades
        #   ...

        actual = setup.enumerateMoves()
        self.assertEqual(expected, actual)

    def test_enumerate_moves_no_aces(self):
        setup = board.Board(no_aces)
        width = len(setup._tableau)

        #   3. Move from cascades to the next open cell
        expected = [(start, width,) for start in range(width)]

        #   2. Move from cascades to cascades
        expected.append( (1, 7,) )

        #   1. Move from cells to cascades

        actual = setup.enumerateMoves()
        self.assertEqual(expected, actual)

    def test_enumerate_moves_two_aces(self):
        setup = board.Board(two_aces)
        width = len(setup._tableau)

        #   3. Move from cascades to the next open cell
        expected = [(start, width,) for start in range(width)]

        #   2. Move from cascades to cascades

        #   1. Move from cells to cascades

        actual = setup.enumerateMoves()
        self.assertEqual(expected, actual)

    def test_enumerate_moves_two_aces_two(self):
        setup = board.Board(two_aces_two)
        width = len(setup._tableau)

        #   Clear the aces
        setup.moveToFoundations()

        #   First move options - cells only
        expected = [(start, width,) for start in range(width)]
        actual = setup.enumerateMoves()
        self.assertEqual( expected, actual )

        #   Uncover QH
        setup.moveCard( (3, width,) )
        expected = [(start, width + 1,) for start in range(width)]
        expected.append( (3, 6,) )
        actual = setup.enumerateMoves()
        self.assertEqual(expected, actual)

    def test_enumerate_moves_keep_sequences(self):
        setup = board.Board(unshuffled)

        setup._foundations = [8, 6, 8, 7, ]
        cascades = ( "TC 9C", "7H 9S 9D KH QH JH TH", "QC", "QD JD TD", "8C KD", "9H 8H", "KS QS JS", "",)
        for t, s in enumerate( cascades ):
            setup._tableau[ t ] = board.parseDeck( s )
        setup._cells = board.parseDeck( "KC TS JC --" )
        setup._firstFree = 3

        #   Validate stacking
        stacked = (0, 1, 3, 5, 6, )
        for c in stacked: self.assertTrue( board.isStacked( setup._tableau[ c ] ) )
        isolate = (2, 4, )
        for c in isolate: self.assertFalse( board.isStacked( setup._tableau[ c ] ) )
        opens = (7, )
        for c in opens: self.assertFalse( board.isStacked( setup._tableau[ c ] ) )

        expected = []

        #   Move stacked cascades to open cell
        expected.extend( [ (start, 11, ) for start in stacked ] )
        expected.pop()

        #   Move isolate cascades to open cell
        expected.extend( [ (start, 11, ) for start in isolate ] )

       #   Move cell 1 to open cascade
        expected.append( ( 8, 7, ) )

        #   Move cell 2 to stack
        expected.append( ( 9, 6, ) )

        #   Move cell 2 to open cascade
        expected.append( ( 9, 7, ) )

        #   Move cell 3 to stack
        expected.append( ( 10, 2, ) )

        #   Move cell 3 to open cascade
        expected.append( ( 10, 7, ) )

        #   Move stacked cascades to open cascade
        expected.extend( [ (start, 7, ) for start in stacked ] )
        expected.pop()

        #   Move isolate cascades to open cascade
        expected.extend( [ (start, 7, ) for start in isolate ] )

        actual = setup.enumerateMoves()
        self.assertEqual(expected, actual)

    def test_memento_values(self):
        visited = set()
        for deck in (unshuffled, reversed, no_aces, two_aces, two_aces_two,):
            setup = board.Board(deck)
            self.assertTrue(setup._resort)
            self.assertTrue(setup._rehash)

            memento = setup.memento()
            self.assertFalse(setup._resort)
            self.assertFalse(setup._rehash)
            self.assertEqual(memento, setup._memento)

            self.assertFalse( memento in visited, f"Duplicate memento #{len(visited)}: {memento}" )
            visited.add(memento)

            #   Check that a new copy gets the same hash
            setup = board.Board(deck)
            self.assertEqual(memento, setup.memento())

    def test_not_solved(self):
        setup = board.Board(unshuffled)
        self.assertFalse( setup.solved() )

    def test_solved(self):
        setup = board.Board(reversed)
        setup.moveToFoundations()
        self.assertTrue( setup.solved() )

    def test_backtrack_foundations(self):
        setup = board.Board(reversed)
        expected = str(setup)

        #   Backtracking should undo everything
        moves = setup.moveToFoundations()
        setup.backtrack( moves )
        actual = str(setup)

        self.assertEqual(expected, actual)

    def assert_backtrack(self, deck):
        setup = board.Board(deck)
        setup.moveToFoundations()
        moves = setup.enumerateMoves()
        for move in moves:
            expected = str(setup)
            setup.moveCard(move)
            setup.backtrack( [move,] )
            actual = str(setup)
            self.assertEqual(expected, actual, move)

    def test_backtrack_no_aces(self):
        self.assert_backtrack(no_aces)

    def test_backtrack_two_aces(self):
        self.assert_backtrack(two_aces)

    def test_backtrack_two_aces_two(self):
        self.assert_backtrack(two_aces_two)

    def assert_solve(self, setup, expected, display = False):
        b = board.Board(setup)
        solution = b.solve()
        actual = len(solution)
        self.assertEqual(expected, actual)
        if display:
            forward = []
            while solution:
                moves = solution.pop()
                forward.append(moves.copy())
                b.backtrack(moves)
            forward.reverse()
            for moves in forward:
                print(moves)
                for move in moves:
                    b.moveCard(move, False)
                print(b)


    def test_solve_unshuffled(self):
        self.assert_solve(unshuffled, 958)

    def test_solve_reversed(self):
        self.assert_solve(reversed, 1)

    def test_solve_no_aces(self):
        self.assert_solve(no_aces, 555, False)

    def test_solve_two_aces(self):
        self.assert_solve(two_aces, 86, False)

    def test_solve_two_aces_two(self):
        self.assert_solve(two_aces_two, 72)

if __name__ == '__main__':
    unittest.main()
