#-----------------------------------------------------------------------------
# Tests of the simple ko rule for all Go*.py players.
#-----------------------------------------------------------------------------

boardsize 3
play b b2
play w a2
play b c1
play w b1

10 legal_moves b
#? [A1 A3 B3 C2 C3]

play b a1

20 legal_moves w
#? [A3 B3 C2 C3]
# B1 is illegal due to ko rule

play w a3

30 legal_moves b
#? [B1 B3 C2 C3]

play b c2

40 legal_moves w
#? [B1 B3 C3]
# B1 is legal again

