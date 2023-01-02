from argparse import ArgumentParser

parser = ArgumentParser(description="Select options.")
parser.add_argument('-d', action="store_true",
                    help = 'Debug')  
args = parser.parse_args()
