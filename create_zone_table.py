"""
As of this writing we have 81 zones. That's a lot to scroll through.
Fortunately, the 578 allows you to enter the zone number. So we build
a cheat sheet, showing the number, zone name on screen, and location.
The zone number and name are taken from the zones.csv file. The
repeater_xxx.yaml files have the name and location.
"""
import argparse
import csv
from glob import glob
import os

args = 0


def parse_args():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--AT878', action='store_true',
                        help="Omit any 220 frequencies, save files in ../878")
    parser.add_argument('--AT578', action='store_true',
                        help="Include any 220 frequencies, save files in ../578")
    args = parser.parse_args()
    if args.AT578 and args.AT878:
        parser.error("AT578 and AT878 are mutually exclusive")
    if not (args.AT578 or args.AT878):
        parser.error("One of AT578 or AT878 must be supplied")


def create_name_to_location_dict():
    location_dict = {}
    for repeater_file in glob('data_files/repeaters_*.yaml'):
        with open(repeater_file) as f:
            have_location = False
            location = ''
            while True:
                line = f.readline()
                if not line:
                    break
                if line.startswith('#'):
                    location = line.split('#')[1].strip()
                    have_location = True
                    continue
                if 'Name:' in line:
                    if not have_location:
                        continue
                    name = line.split(':')[1].strip()
                    location_dict[name] = location
                    # We've used this location
                    have_location = False
    return location_dict


def read_zones_file():
    if args.AT578:
        path = '../578'
    else:
        path = '../878'

    with open(os.path.join(path, 'zones.csv')) as f:
        # Get rid of the header row.
        f.readline()
        reader = csv.reader(f)
        # We will be appending the zone names, so zone 1 is at index 0.
        zones = []
        for line in reader:
            zones.append(line[1])
    return zones


def merge_and_print_information(zones, location_dict):
    if args.AT578:
        path = '../578'
    else:
        path = '../878'

    with open(os.path.join(path, 'zone_table.txt'), 'w') as f:
        for i, zone in enumerate(zones):
            zone_num = i + 1
            try:
                location = location_dict[zone]
            except KeyError:
                location = ""
            print(f"{zone_num}\t{zone}\t{location}", file=f)


def main():
    parse_args()
    location_dict = create_name_to_location_dict()
    zones = read_zones_file()
    merge_and_print_information(zones, location_dict)


if __name__ == '__main__':
    main()
