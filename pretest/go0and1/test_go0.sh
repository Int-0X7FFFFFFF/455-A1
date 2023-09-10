#!/bin/bash

# Script for running Go0 unit and basic functional tests

PROGRAM="go0.sh"
OUTPUTDIR="results_test_go0"

gogui-regress $PROGRAM -output $OUTPUTDIR test_go_base.tst
gogui-regress $PROGRAM -output $OUTPUTDIR test_simple_ko.tst
gogui-regress $PROGRAM -output $OUTPUTDIR test_suicide.tst
gogui-regress $PROGRAM -output $OUTPUTDIR test_go0.tst
