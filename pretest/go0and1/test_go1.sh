#!/bin/bash

# Script for running Go1 unit and basic functional tests

PROGRAM="go1.sh"
OUTPUTDIR="results_test_go1"

gogui-regress $PROGRAM -output $OUTPUTDIR test_go_base.tst
gogui-regress $PROGRAM -output $OUTPUTDIR test_simple_ko.tst
gogui-regress $PROGRAM -output $OUTPUTDIR test_suicide.tst
gogui-regress $PROGRAM -output $OUTPUTDIR test_go1.tst
