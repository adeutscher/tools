#!/usr/bin/python

# Setting format title as a variable to make it to
#   to copy content between yaml2json.py and json2yaml.py
# The only thing other than this that should need to be adjusted
#   is the convert() function.
format_name = "YAML"

import json, os, re, sys

def colour_text(colour, text):
    # A useful shorthand for applying a colour to a string.
    return "%s%s%s" % (colour, text, COLOUR_OFF)

def convert(file_handle, title):
    try:
        src_body = yaml.load(file_handle.read())
    except yaml.error.MarkedYAMLError as e:
        # Conveniently, Python's pyyaml module gives a more informative error printout than the JSON module.
        if title == "standard input":
            print_error("Content of standard input is not in readable %s format: %s (line %d, column %d)" % (format_name, e.problem, e.problem_mark.line + 1, e.problem_mark.column + 1))
        else:
            print_error("Content of input (%s) is not in readable %s format: %s (line %d, column %d)" % (colour_text(COLOUR_GREEN, title), format_name, e.problem, e.problem_mark.line + 1, e.problem_mark.column + 1))
        return
    print json.dumps(src_body, sort_keys=True, indent = 4)

def enable_colours(force = False):
    global COLOUR_PURPLE
    global COLOUR_RED
    global COLOUR_GREEN
    global COLOUR_YELLOW
    global COLOUR_BLUE
    global COLOUR_BOLD
    global COLOUR_OFF
    if force or sys.stderr.isatty():
        # Colours for standard output.
        COLOUR_PURPLE = '\033[1;35m'
        COLOUR_RED = '\033[1;91m'
        COLOUR_GREEN = '\033[1;92m'
        COLOUR_YELLOW = '\033[1;93m'
        COLOUR_BLUE = '\033[1;94m'
        COLOUR_BOLD = '\033[1m'
        COLOUR_OFF = '\033[0m'
    else:
        # Set to blank values if not to standard output.
        COLOUR_PURPLE = ''
        COLOUR_RED = ''
        COLOUR_GREEN = ''
        COLOUR_YELLOW = ''
        COLOUR_BLUE = ''
        COLOUR_BOLD = ''
        COLOUR_OFF = ''
enable_colours()

def hexit(code = 0):
    print_usage("%s./%s%s %s-file" % (COLOUR_GREEN, os.path.basename(sys.argv[0]), COLOUR_OFF, format_name.lower()))
    exit(code)

#
# Common Message Functions
###

error_count = 0
def print_error(message):
    global error_count
    error_count += 1
    print >> sys.stderr, "%s[%s]: %s" % (colour_text(COLOUR_RED, "Error"), colour_text(COLOUR_GREEN, os.path.basename(sys.argv[0])), message)

def print_notice(message):
    print >> sys.stderr, "%s[%s]: %s" % (colour_text(COLOUR_BLUE, "Notice"), colour_text(COLOUR_GREEN, os.path.basename(sys.argv[0])), message)

def print_usage(message):
    print >> sys.stderr, "%s[%s]: %s" % (colour_text(COLOUR_PURPLE, "Usage"), colour_text(COLOUR_GREEN, os.path.basename(sys.argv[0])), message)

#
# Script operation
###

try:
    import yaml
except ImportError:
    print_error("YAML module for Python is not installed.")

file_handle = False
if len(sys.argv) >= 2:
    source_file = sys.argv[1]
    if source_file == "-":
        file_handle = sys.stdin
        print_notice("Reading %s content from standard input." % format_name)
    elif not os.path.isfile(source_file):
        print_error("%s file does not exist: %s%s%s" % (format_name, COLOUR_GREEN, source_file, COLOUR_OFF))
    elif not os.access(source_file, os.R_OK):
        print_error("%s file could not be read: %s%s%s" % (format_name, COLOUR_GREEN, source_file, COLOUR_OFF))
else:
    print_error("No %s file path provided." % format_name)

if error_count:
    hexit(1)

if file_handle:
    # File handle was already set (stdin)
    convert(file_handle, "standard input")
else:
    with open(source_file) as file_handle:
        convert(file_handle, source_file)

if error_count:
    exit(1)