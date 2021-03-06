"""
repeaters_from_repeaterbook.py
Loading analog repeater info from CSV sheets produced by RepeaterBook.
Limits repeaters by lat/long based on user-supplied rectangles in
lat_long.yaml
"""

from csv import DictReader
from glob import glob
import os
import yaml


def get_analog_repeaters_from_repeaterbook(lat_long):
    """
    Entry routine for this module. All the work is in other routines, see them
    for the documentation.
    :param lat_long: a list of lat/long rectangles. Each rectangle is a dict:
        'W': <number>
        'E': <number>
        'N': <number>
        'S': <number>
    :return: A list of repeater dicts in the same form that they would be from
        the YAML files.
    """
    # Get all the open analog repeaters in the desired areas from RepeaterBook
    # CSV exports. The dicts in this list hold all the data in the CSV; they
    # were generated by csv.DictReader().
    analog_repeaters = read_repeaterbook_csvs(lat_long)

    # Convert to the form the rest of the program expects.
    converted_repeaters = convert_from_repeaterbook_to_program_form(
        analog_repeaters)
    return converted_repeaters


def read_repeaterbook_csvs(lat_long):
    """
    Loads repeaters from CSV sheets exported from RepeaterBook
    subject to some constraints:
    - Analog FM only. No digital modes.
    - On-air only, no off-air or unknown
    - Within a bounding box defined by lat_long coordinates.
    - OPEN only, not CLOSED or PRIVATE
    :param lat_long: a list of lat/long rectangles. Each rectangle is a dict:
        'W': <number>
        'E': <number>
        'N': <number>
        'S': <number>
    :return: A dict of lists, keyed by state.
    """
    analog_repeaters = {}
    for filename in glob('data_files/rb_repeaters/*.csv'):
        # We'll put these repeaters as a list of dicts, in a dict keyed
        # by state; actually keyed by the filename minus the extension,
        fn_key = os.path.split(os.path.splitext(filename)[0])[-1].split('_')[0]

        repeater_list = read_repeaterbook_csv(filename, lat_long)
        if not repeater_list:
            continue
        try:
            analog_repeaters[fn_key] += repeater_list
        except KeyError:
            analog_repeaters[fn_key] = []
            analog_repeaters[fn_key] += repeater_list
    sort_analog_repeaters(analog_repeaters)
    return analog_repeaters


def read_repeaterbook_csv(filename, lat_long):
    """
    Reads a single RepeaterBook CSV file, and filters the repeaters
    for inclusion in this code plug build.
    :param filename: The file to process
    :param lat_long: a list of lat/long rectangles. Each rectangle is a dict:
        'W': <number>
        'E': <number>
        'N': <number>
        'S': <number>
    :return: a list of repeaters to include.
    """
    repeater_list = []
    with open(filename) as f:
        reader = DictReader(f)
        for row in reader:
            if not filter_by_lat_long(row, lat_long):
                # Skip it.
                continue
            if not filter_by_criteria(row):
                continue
            repeater_list.append(row)
    return repeater_list


def filter_by_lat_long(repeater, lat_long):
    """
    Determine whether a repeater should be included based on location.
    :param repeater: a repeater dict, with data from the RepeaterBook CSV
    :param lat_long: a list of lat/long rectangles. Each rectangle is a dict:
        'W': <number>
        'E': <number>
        'N': <number>
        'S': <number>
    :return: True if the repeater should be included.
    """
    lat = float(repeater['Lat'])
    long = float(repeater['Long'])
    for box in lat_long:
        if lat > box['N']:
            # Doesn't fit in this box...
            continue
        if lat < box['S']:
            continue
        if long < box['W']:
            continue
        if long > box['E']:
            continue
        return True


def filter_by_criteria(repeater):
    """
    Determine whether a repeater meets the criteria for
    inclusion:
        - Analog (i.e., FM) (no digital, no mixed mode)
        - OPEN
        - On-air
    :param repeater: A repeater dict
    :return: True if the repeater should be included.
    """
    if repeater['Use'] != 'OPEN':
        return False
    if repeater['Op Status'] != 'On-Air':
        return False
    if repeater['Mode'] != 'Analog' and \
            repeater['Mode'] != 'Analog/analog':
        return False
    return True


def sort_analog_repeaters(analog_repeaters):
    """
    Sorts the analog repeaters.  For now, the sort order is increasing
    longitude within each state.  May want to make this more flexible in the
    future, either including a sort command within each lat_long box, or
    command line option, or...
    :param analog_repeaters: A dict of lists of repeaters, keyed by state.
    :return: A dict of lists of repeaters, now sorted.
    """
    for state in analog_repeaters.keys():
        analog_repeaters[state] = sorted(analog_repeaters[state],
                                         key=lambda d: float(d['Long']))


def convert_from_repeaterbook_to_program_form(analog_repeaters):
    """
    Distill the data from RepeaterBook removing unneeded data, and put
    them into dicts of the same form that is created by the routines that
    read the YAML files.
    :param analog_repeaters: A dict keyed by state of list of repeater dicts.
    :return: a list of repeater dicts, transformed into the kind the rest of the
        program espects.
    """
    new_list = []
    for state in analog_repeaters.keys():
        for repeater in analog_repeaters[state]:
            # "nrd" means "New Repeater Dict"  which is too long to type over
            # and over!
            nrd = {}
            # Have to figure out how to handle name better
            nrd['Name'] = repeater['Location']
            nrd['RX'] = repeater['Output Freq']
            nrd['TX'] = repeater['Input Freq']
            # Adding State, not previously used, to automatically build
            # state zones.
            nrd['State'] = state
            nrd['Mode'] = 'A'
            # Handle the CTCSS / DCS tones / codes.  If only Uplink specified,
            # or if both are specified and the same, use "CTCSS" else use
            # "RCTCSS" and "TCTCSS".
            uplink = repeater['Uplink Tone']
            downlink = repeater['Downlink Tone']
            if uplink or downlink:
                if not uplink:
                    # They specified a downlink frequency but not an uplink.
                    # Unusual, but using that for both ways isn't a problem.
                    uplink = downlink
                if (not downlink) or (uplink == downlink):
                    nrd['CTCSS'] = uplink
                else:
                    nrd['RCTCSS'] = downlink
                    nrd['TCTCSS'] = uplink
            new_list.append(nrd)
    return new_list