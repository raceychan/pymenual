import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='Print a custom string to the command line.')
    parser.add_argument('string', nargs='?', default='hello', help='The string to print')
    args = parser.parse_args()

    sys.stdout.write(args.string)
    sys.stdout.flush()

if __name__ == '__main__':
    main()
