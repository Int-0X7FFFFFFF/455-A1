#!/bin/bash

# Script for running go base unit and basic functional tests

TESTS="test_board.py test_board_util.py test_gtp_connection.py"
 
for unit_test in $TESTS; do
    python3 $unit_test
done
