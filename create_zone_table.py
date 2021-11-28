"""
As of this writing we have 81 zones. That's a lot to scroll through.
Fortunately, the 578 allows you to enter the zone number. So we build
a cheat sheet, showing the number, zone name on screen, and location.
The zone number and name are taken from the zones.csv file. The
repeater_xxx.yaml files have the name and location.
"""
import csv
from glob import glob


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
    with open('../578/zones.csv') as f:
        # Get rid of the header row.
        f.readline()
        reader = csv.reader(f)
        # We will be appending the zone names, so zone 1 is at index 0.
        zones = []
        for line in reader:
            zones.append(line[1])
    return zones


def merge_and_print_information(zones, location_dict):
    with open('zone_table.txt', 'w') as f:
        for i, zone in enumerate(zones):
            zone_num = i + 1
            try:
                location = location_dict[zone]
            except KeyError:
                location = ""
            print(f"{zone_num}\t{zone}\t{location}", file=f)


def main():
    location_dict = create_name_to_location_dict()
    zones = read_zones_file()
    merge_and_print_information(zones, location_dict)
    pass


if __name__ == '__main__':
    main()
