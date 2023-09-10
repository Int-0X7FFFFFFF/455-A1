#-----------------------------------------------------------------------------
# Tests of Go base functions for all Go*.py players.
#-----------------------------------------------------------------------------

10 version
#? [1.0]

30 protocol_version
#? [2]

40 komi 0
#? []

50 boardsize 2
#? []

60 legal_moves b
#? [A1 A2 B1 B2]

70 legal_moves w
#? [A1 A2 B1 B2]

80 play b b2
#? []

90 legal_moves w
#? [A1 A2 B1]

play w pass
play b a1

100 legal_moves w
#? []

110 genmove w
#? [PASS]

clear_board

120 legal_moves b
#? [A1 A2 B1 B2]

