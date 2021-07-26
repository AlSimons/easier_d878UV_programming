import csv
import yaml


def load_data_from_yaml_files():
    """
    Loads data from
        - radio_ids.yaml,
        - repeaters.yaml,
        - talkgroups.yaml,
        - simplex.yaml, and
        - channel_requests.yaml,
        - special_zones.yaml,
        - channel_defaults.yaml,
        - field_names.yaml
    :return: Dicts:
               radio_ids,
               repeaters,
               talkgroups,
               simplex,
               channel_requests,
               special_zones,
               channel_defaults
               field_names
    """
    with open('radio_ids.yaml') as f:
        radio_ids = yaml.safe_load(f)
    with open('repeaters.yaml') as f:
        repeaters = yaml.safe_load(f)
    with open('talkgroups.yaml') as f:
        talkgroups = yaml.safe_load(f)
    with open('simplex.yaml') as f:
        simplex = yaml.safe_load(f)
    with open('channel_requests.yaml') as f:
        channel_requests = yaml.safe_load(f)
    with open('special_zones.yaml') as f:
        special_zones = yaml.safe_load(f)
    with open('channel_defaults.yaml') as f:
        channel_defaults = yaml.safe_load(f)
    with open('field_names.yaml') as f:
        field_names = yaml.safe_load(f)
    return radio_ids, repeaters, talkgroups, simplex, channel_requests, \
        special_zones, channel_defaults, field_names


def fix_list_members(dict_list):
    """
    dict_list is a list of dicts.  Some elements of each dict may be a list.
    Since we are writing a csv we have to flatten those lists into a scalar
    element.  The CPS software expects the list elements to be a pipe-separated
    single string.
    :param dict_list: a list of dicts.
    :return: a list of dicts, with dict members that were lists now single
        strings with the former list elements separated by pipe.
    """
    for this_dict in dict_list:
        for dict_key in this_dict.keys():
            dict_element = this_dict[dict_key]
            if type(dict_element) == list:
                this_dict[dict_key] = '|'.join(dict_element)
    return dict_list


def write_dict_to_csv(dict_list_to_write, file_name, field_names):
    index_dict_list(dict_list_to_write)
    fix_list_members(dict_list_to_write)
    with open(file_name, 'w', newline='') as f:
        writer = csv.DictWriter(f,
                                fieldnames=field_names,
                                extrasaction='ignore',
                                quoting=csv.QUOTE_ALL,
                                quotechar='"')
        writer.writeheader()
        for row in dict_list_to_write:
            writer.writerow(row)


def index_dict_list(dictionary_list):
    """
    Once the channels list is completely populated, add the "No." field to
    each entry.
    :param dictionary_list: The fully populated dictionary.
    :return: None. The dictionary is updated.
    """
    for i, row in enumerate(dictionary_list):
        row["No."] = str(i + 1)


def make_analog_repeater_channel(channels,
                                 channels_by_name,
                                 repeater,
                                 channel_defaults,
                                 zones):
    channel = channel_defaults.copy()
    channel['Channel Name'] = repeater['Name']
    channel['Transmit Frequency'] = '{:<09}'.format(repeater['TX'])
    channel['Receive Frequency'] = '{:<09}'.format(repeater['RX'])
    channel['Channel Type'] = 'A-Analog'
    channel['Band Width'] = '25K'
    channel['Busy Lock/TX Permit'] = 'Busy'

    keys = repeater.keys()
    # Can't specify both CTCSS (both dirs) and either RCTCSS or TCTCSS
    if 'CTCSS' in keys and ('RCTCSS' in keys or 'TCTCSS' in keys):
        raise KeyError
    if 'CTCSS' in keys:
        channel["CTCSS/DCS Decode"] = repeater['CTCSS']
        channel["CTCSS/DCS Encode"] = repeater['CTCSS']
    if 'RCTCSS' in keys:
        channel["CTCSS/DCS Encode"] = repeater['RCTCSS']
    if 'TCTCSS' in keys:
        channel["CTCSS/DCS Decode"] = repeater['TCTCSS']
    if 'RO' in keys and repeater['RO']:
        channel['PTT Prohibit'] = 'True'

    channels.append(channel)
    channels_by_name[channel['Channel Name']] = channel
    insert_into_zones(channel, zones)


def make_analog_simplex_channel(channels,
                                channels_by_name,
                                simplex_name,
                                simplex_channel,
                                channel_defaults,
                                zones):
    # Make sure the simplex name is a string, in case someone used a
    # frequency as the name, e.g., 146.52.
    simplex_name = str(simplex_name)
    channel = channel_defaults.copy()
    channel['Channel Name'] = simplex_name
    channel['Transmit Frequency'] = '{:<09}'.format(simplex_channel['Freq'])
    channel['Receive Frequency'] = '{:<09}'.format(simplex_channel['Freq'])
    channel['Channel Type'] = 'A-Analog'
    channel['Band Width'] = '25K'
    channel['Busy Lock/TX Permit'] = 'Busy'
    if 'RO' in simplex_channel.keys() and simplex_channel['RO']:
        channel['PTT Prohibit'] = 'On'
    channels.append(channel)
    channels_by_name[simplex_name] = channel
    insert_into_zones(channel, zones)


def make_digital_repeater_channel(channels,
                                  channels_by_name,
                                  repeater,
                                  talkgroup,
                                  talkgroup_number,
                                  channel_defaults,
                                  zones,
                                  radio_id):
    channel = channel_defaults.copy()
    channel['Repeater Name'] = repeater['Name']
    channel['Channel Name'] = repeater['Name'] + ' ' + talkgroup
    channel['Transmit Frequency'] = '{:<09}'.format(repeater['TX'])
    channel['Receive Frequency'] = '{:<09}'.format(repeater['RX'])
    channel['Channel Type'] = 'D-Digital'
    channel['Band Width'] = '12.5K'
    channel['Color Code'] = repeater['CC']
    channel['Contact'] = talkgroup
    channel['Contact TG/DMR ID'] = talkgroup_number
    channel['Radio ID'] = radio_id['Name']
    # Assume the TG is dynamic.  We'll fix it if it is static
    channel['Slot'] = repeater['DynamicTGs']
    for slot in [1, 2]:
        if talkgroup_number in repeater['StaticTGs'][slot]:
            channel['Slot'] = slot  # Choose the right slot for a static TG
    channels.append(channel)
    channels_by_name[channel['Channel Name']] = channel
    insert_into_zones(channel, zones, radio_id)


def make_digital_repeater_channels(channels,
                                   channels_by_name,
                                   repeater,
                                   talkgroups,
                                   channel_request,
                                   channel_defaults,
                                   zones,
                                   radio_id):
    for talkgroup in channel_request['T']:
        make_digital_repeater_channel(channels,
                                      channels_by_name,
                                      repeater,
                                      talkgroup,
                                      talkgroups[talkgroup],
                                      channel_defaults,
                                      zones,
                                      radio_id)


def make_digital_simplex_channel(channels,
                                 channels_by_name,
                                 simplex_name,
                                 simplex_channel,
                                 channel_defaults,
                                 zones,
                                 radio_id):
    # Make sure the simplex name is a string, in case someone used a
    # frequency as the name, e.g., 146.52.
    simplex_name = str(simplex_name)

    channel = channel_defaults.copy()
    channel['Channel Name'] = simplex_name
    channel['Transmit Frequency'] = '{:<09}'.format(simplex_channel['Freq'])
    channel['Receive Frequency'] = '{:<09}'.format(simplex_channel['Freq'])
    channel['Channel Type'] = 'D-Digital'
    channel['Band Width'] = '12.5K'
    channel['Color Code'] = 1
    channel['Contact TG/DMR ID'] = 99
    channel['Slot'] = 1
    channel['Radio ID'] = radio_id['Name']
    if 'RO' in simplex_channel.keys() and simplex_channel['RO']:
        channel['PTT Prohibit'] = 'On'
    channels.append(channel)
    channels_by_name[channel['Channel Name']] = channel
    insert_into_zones(channel, zones, radio_id)


def make_channels(repeaters,
                  talkgroups,
                  simplex,
                  channel_requests,
                  channel_defaults,
                  zones,
                  radio_ids):
    """
    Walks over the desired channels list specified in channel_info, and builds
    the dictionary of all the channels, ready to be written to a CSV file for
    import into the programmer.
    :param repeaters: A dict of repeater info
    :param talkgroups: A dict of talkgroup info
    :param simplex: A dict of simplex channels
    :param channel_requests: A dict of desired channels
    :param channel_defaults: A dict with the default values for the channels
        CSV value
    :param zones: A dict into which zone info will be entered.
    :param radio_ids: a list of dicts (possibly of length one), containing
        information about the radio IDs to be programmed into the radio.
    :return: A list of fully populated dicts for writing to a CSV
    """
    channels = []
    channels_by_name = {}
    for radio_id in radio_ids:
        for channel_request in channel_requests:
            if 'R' in channel_request.keys():
                repeater = repeaters[channel_request['R']]
                if repeater['Mode'] == 'D':
                    make_digital_repeater_channels(channels,
                                                   channels_by_name,
                                                   repeater,
                                                   talkgroups,
                                                   channel_request,
                                                   channel_defaults,
                                                   zones,
                                                   radio_id)
                elif repeater['Mode'] == 'A':
                    make_analog_repeater_channel(channels,
                                                 channels_by_name,
                                                 repeater,
                                                 channel_defaults,
                                                 zones)
            elif 'S' in channel_request.keys():
                simplex_name = channel_request['S']
                simplex_channel = simplex[simplex_name]
                if simplex_channel['Mode'] == 'A':
                    make_analog_simplex_channel(channels,
                                                channels_by_name,
                                                simplex_name,
                                                simplex_channel,
                                                channel_defaults,
                                                zones)
                else:
                    make_digital_simplex_channel(channels,
                                                 channels_by_name,
                                                 simplex_name,
                                                 simplex_channel,
                                                 channel_defaults,
                                                 zones,
                                                 radio_id)
    return channels, channels_by_name


def add_special_zone_members(channels_by_name, special_zones, zones, radio_ids):
    # It is possible that a channel to be added here is already in the zone.
    # We'll filter those out in insert_into_zone().
    for radio_id in radio_ids:
        # First handle the special key "ALL_ZONES":
        chans_for_all_zones = special_zones['ALL_ZONES']
        for zone_key in zones.keys():
            for chan in chans_for_all_zones:
                if type(chan) == float:
                    chan = str(chan)
                insert_into_zone(channels_by_name[chan], zone_key, zones)


def insert_into_zones(channel, zones, radio_id=None):
    """
    Insert each channel into a zone. For digital channels, the radio_id will
    be used to prefix the zone name with an abbreviation indicating it
    contains the channels for that radio_id. For analog channels, the radio_id
    will be none.

    :param channel: A channel
    :param zones: A dict of dicts containing info about the zones.
    :param radio_id: A radio_id dict. All we will use is the Abbrev field.
    :return: None
    """
    if channel['Transmit Frequency'] == channel['Receive Frequency']:
        # RX == TX: A simplex channel
        insert_into_zone(channel, 'simplex', zones)
    else:
        # All repeaters go into a zone named for the repeater.
        # Fixme: This isn't terribly useful for analog repeaters.
        if channel['Channel Type'] == 'D-Digital':
            zone_name = radio_id['Abbrev'] + ' ' + channel['Repeater Name']
        else:
            zone_name = channel['Channel Name']
        insert_into_zone(channel, zone_name, zones)


def insert_into_zone(channel, zone_key, zones):
    try:
        this_zone = zones[zone_key]
    except KeyError:
        this_zone = {
            'Zone Name': zone_key,
            'Zone Channel Member': [],
            'Zone Channel Member RX Frequency': [],
            'Zone Channel Member TX Frequency': []
        }
        zones[zone_key] = this_zone

    # Don't enter a channel already in the zone.
    if channel['Channel Name'] in this_zone['Zone Channel Member']:
        return

    this_zone['Zone Channel Member'].append(channel['Channel Name'])
    this_zone['Zone Channel Member RX Frequency'].append(
        channel['Receive Frequency'])
    this_zone['Zone Channel Member TX Frequency'].append(
        channel['Transmit Frequency'])
    if len(this_zone['Zone Channel Member']) == 1:
        this_zone['A Channel'] = channel['Channel Name']
        this_zone['A Channel RX Frequency'] = channel['Receive Frequency']
        this_zone['A Channel TX Frequency'] = channel['Transmit Frequency']
    if len(this_zone['Zone Channel Member']) == 2:
        this_zone['B Channel'] = channel['Channel Name']
        this_zone['B Channel RX Frequency'] = channel['Receive Frequency']
        this_zone['B Channel TX Frequency'] = channel['Transmit Frequency']


def change_zone_dict_to_list(zone_dict):
    """
    Because we had to add channels to zones based on zone name, the zone
    data are currently stored in a dict, with the keys being the zone name.
    The elements of this dict are also dicts, containing all the information
    for the zone--including the zone name.

    In order to write this information to a csv, we have to convert from a
    dict of dicts to a list of dicts, dropping the redundant outer key.
    :param zone_dict: A dict of dicts containing zone information.
    :return: A list of dicts containing zone information.
    """
    zone_list = []
    for zone in zone_dict.keys():
        zone_list.append(zone_dict[zone])
    return zone_list


def main():
    zones = {}
    (radio_ids,
     repeaters,
     talkgroups,
     simplex,
     channel_requests,
     special_zones,
     channel_defaults,
     field_names) = load_data_from_yaml_files()

    channels, channels_by_name = make_channels(repeaters,
                                               talkgroups,
                                               simplex,
                                               channel_requests,
                                               channel_defaults,
                                               zones,
                                               radio_ids)
    add_special_zone_members(channels_by_name, special_zones, zones, radio_ids)
    write_dict_to_csv(channels, 'channels.csv', field_names['channels'])
    write_dict_to_csv(radio_ids, 'radio_ids.csv', field_names['radio_ids'])
    zone_list = change_zone_dict_to_list(zones)
    write_dict_to_csv(zone_list, 'zones.csv', field_names['zones'])


if __name__ == "__main__":
    main()
