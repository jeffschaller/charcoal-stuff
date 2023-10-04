#!/usr/bin/python3

# inputs:
#       dump_metasmoke_clean-$timestamp.db (arg 1), via wget from MS dump page; and
#       blacklisted_regexes.txt file (arg 2), cloned from from github
# output:
#       CSV to stdout

import sys
import sqlite3
import regex
import csv

# need exactly 2 arguments
if len(sys.argv) != 3:
  print("Usage:", sys.argv[0], "<sqlite-filename> <blacklist-filename>", file=sys.stderr)
  exit(1)

# TODO: error-checking on connect()?
con = sqlite3.connect(sys.argv[1])
cur = con.cursor()

con.create_function('regexp', 2, \
  lambda pattern, str: 1 if pattern and str and regex.search(pattern, str) else 0)

sqlite3.enable_callback_tracebacks(True)
con.set_trace_callback(print)

query = (r"SELECT SUM(is_tp), SUM(is_fp), SUM(is_naa) " +
          "FROM posts WHERE "                           +
          "body     REGEXP ? OR "                       +
          "title    REGEXP ? OR "                       +
          "username REGEXP ?")

csv_writer = csv.writer(sys.stdout)

# extract the DB timestamp; it's a column in the CSV output
dbstamp=regex.findall(r"\d+", sys.argv[1])

with open(sys.argv[2], mode='r') as input_file:
  for blacklist_entry in input_file:

    # the newlines are not a desired part of the regex
    blacklist_entry = blacklist_entry.rstrip('\n')

    # "blacklist_entry" is repeated because there are three parameters expected
    # in the query -- one for each "?"
    query_res = cur.execute(query, (blacklist_entry, blacklist_entry, blacklist_entry))

    # only expecting one result
    result = query_res.fetchone()

    # defaults to 0; TODO - in what situations are these not set?
    tp  = result[0] or 0
    fp  = result[1] or 0
    naa = result[2] or 0
    perc = tp / (tp + fp + naa) if (tp + fp + naa) > 0 else 0
    csv_writer.writerow([ blacklist_entry, tp, fp, naa, perc, "", dbstamp[0] ])
