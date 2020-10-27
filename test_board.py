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
JD 4H 2C 7C 9H KS 7H 5D
6S AC QS TD JC 9C JH KC
9S 4C QH 2D 4C AH TS 8H
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

        self.assertEqual(suits, len(b._aces))
        for a, ace in enumerate(b._aces):
            self.assertEqual(ace, board.noCard, f"Ace {a} not empty")

        self.assertEqual(suits * 2, len(b._columns))
        for c, column in enumerate(b._columns):
            expected = cards // len(b._columns) + (c < suits)
            self.assertEqual(expected, len(column), f"Column {c} incorrectly sized")
            for r, card in enumerate(column):
                expected = deck[r * suits * 2 + c]
                self.assertEqual(expected, card)

        self.assertIsNone(b._memento, "Pre-initialised memento")
        self.assertTrue(b._resort, "Not initialised to resort")
        self.assertTrue(b._rehash, "Not initialised to rehash")

        self.assertEqual(len(b._columns), len(b._sorted), "Hashing columns not initialised")
        for s, actual in enumerate(b._sorted):
            self.assertEqual(b._columns[s], actual)

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
JD 4H 2C 7C 9H KS 7H 5D
6S AC QS TD JC 9C JH KC
9S 4C QH 2D 4C AH TS 8H
TH 2S JS 6C 9D 3D 8D TC
2C 5H 8C 5S 3H 6H 8S 6D
AH 5C QD AS -- -- -- --

Cells:
-- -- -- --
"""
        self.assert_str(expected, two_aces)

    def test_move_cover_no_aces(self):
        b = board.Board(no_aces)
        actual = b.coverAces()
        expected = []
        self.assertEqual(expected, actual)

    def test_move_cover_two_aces(self):
        b = board.Board(two_aces)
        actual = b.coverAces()
        expected = [(0, -3,), (3, -4),]
        self.assertEqual(expected, actual)

    def test_move_cover_two_aces_two(self):
        b = board.Board(two_aces_two)
        actual = b.coverAces()
        expected = [(0, -1,), (0, -4), (0, -4), ]
        self.assertEqual(expected, actual)

if __name__ == '__main__':
    unittest.main()
