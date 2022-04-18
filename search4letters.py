import sys

letters = sys.argv[1]
phrase = sys.argv[2]

print(set(letters).intersection(set(phrase)))

