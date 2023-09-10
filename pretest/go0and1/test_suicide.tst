#-----------------------------------------------------------------------------
# Tests of illegal moves due to suicide for all Go*.py players.
# Example from Fig. 1.9 in book.
#-----------------------------------------------------------------------------

boardsize 4
play b a1
play w a3
play b a2
play w b2
play b b1
play w b3
play b b4
play w c2
play b c1
play w pass
play b c3
play w pass
play b d2

10 legal_moves w
#? [C4 D1 D3 D4]
# A4 is illegal, suicide
# D1 is legal, capture