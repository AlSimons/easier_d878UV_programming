import csv
import yaml
from glob import glob
from repeaters_from_repeaterbook import get_analog_repeaters_from_repeaterbook


def load_data_from_yaml_files():
    """
    Loads data from
        - radio_ids.yaml,
        - repeaters*.yaml,
        - talkgroups.yaml,
        - simplex.yaml, and
        - channel_requests.yaml,
        - special_zones.yaml,
        - channel_defaults.yaml,
        - field_names.yaml
        - lat_long.yaml
    :return: Dicts:
               radio_ids,
               repeaters,
               talkgroups,
               simplex,
               channel_requests,
               special_zones,
               channel_defaults
               field_names
               lat_long
    """
    with open('data_files/radio_ids.yaml') as f:
        radio_ids = yaml.safe_load(f)
    repeaters = {}
    for fn in glob('data_files/repeaters*'):
        with open(fn) as f:
            repeaters.update(yaml.safe_load(f))
    with open('data_files/talkgroups.yaml') as f:
        talkgroups = yaml.safe_load(f)
    with open('data_files/simplex.yaml') as f:
        simplex = yaml.safe_load(f)
    # Simplex channels are sometimes named with their frequency, e.g., 146.52.
    # Make sure that all keys are strings.
    simplex = {(str(key) if not isinstance(key, str) else key): simplex[key]
               for key in simplex.keys()}
    channel_requests = []
    for fn in glob('data_files/channel_requests*'):
        with open(fn) as f:
            a = yaml.safe_load(f)
            channel_requests += a  # FIXME
    channel_requests = expand_channel_requests(channel_requests)
    with open('data_files/special_zones.yaml') as f:
        special_zones = yaml.safe_load(f)
    with open('data_files/channel_defaults.yaml') as f:
        channel_defaults = yaml.safe_load(f)
    with open('data_files/field_names.yaml') as f:
        field_names = yaml.safe_load(f)
    with open('data_files/lat_long.yaml') as f:
        lat_long = yaml.safe_load(f)
    return radio_ids, repeaters, talkgroups, simplex, channel_requests, \
        special_zones, channel_defaults, field_names, lat_long


def expand_channel_requests(channel_requests):
    # First segregate the group entries from the non-groups.
    groups = {}
    non_groups = []
    for request_dict in channel_requests:
        was_group = False
        for k in request_dict.keys():
            if k.startswith('GROUP_'):
                was_group = True
                groups[k] = request_dict[k]
        if not was_group:
            non_groups.append(request_dict)

    # If there weren't any GROUP_xxx entries, we're done.
    if not groups:
        return channel_requests

    # OK, we have groups.  They may or may not be used,but we have to walk all
    # the talkgroup requests and insert the group contents in place of the
    # group reference.
    expanded_requests = []
    for request_dict in non_groups:
        if 'T' in request_dict.keys():
            # The request has talk groups.  They may be groups of groups, and
            # need expanding.
            # Note that if there are no talk groups in the request (not T key),
            # we don't need to do anything.
            talkgroups = request_dict['T']
            expanded_requests = []
            for talkgroup in talkgroups:
                if talkgroup.startswith('GROUP_'):
                    expanded_requests = expanded_requests + groups[talkgroup]
                else:
                    expanded_requests.append(talkgroup)
            request_dict['T'] = expanded_requests

    return non_groups


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


def make_talkgroup_file(talkgroups):
    """
    The 878 requires duplicate information in multiple tables.  In the
    channels table, it requires the talkgroup name and number, but those are
    ignored if the talkgroup name and number are not also in the talkgroups
    table.

    This routine outputs the talkgroups.csv file, sorted by talkgroup name.
    :param talkgroups: the dict of talkgroups as read from the talkgroups
        YAML file. Most values are scalars, but for Private Call talkgroups,
        the value is itself a dict.
    :return: None
    """
    tg_keys = sorted(talkgroups.keys())
    # Need to turn this into a list of dicts, with the columns that AnyTone CPS
    # wants
    tg_list = []
    for tg_key in tg_keys:
        tg_value = talkgroups[tg_key]
        # Assume Group Call; we'll overwrite if not.
        tg = {'Name': tg_key, 'Call Type': 'Group Call', 'Call Alert': 'None'}
        if type(tg_value) == int:
            tg['Radio ID'] = tg_value
        elif type(tg_value) == dict:
            if tg_value['Private']:
                tg['Call Type'] = 'Private Call'
            tg['Radio ID'] = tg_value['Number']
        tg_list.append(tg)

    # Now write it out.
    field_names = ['No.', "Radio ID", "Name", "Call Type", "Call Alert"]
    write_dict_to_csv(tg_list, 'talkgroups.csv', field_names)


def make_analog_repeater_channel(channels,
                                 channels_by_name,
                                 repeater,
                                 channel_defaults,
                                 zones):
    channel = channel_defaults.copy()
    channel['Repeater Name'] = repeater['Name']
    channel['Channel Name'] = repeater['Name']
    channel['Transmit Frequency'] = '{:<09}'.format(repeater['TX'])
    channel['Receive Frequency'] = '{:<09}'.format(repeater['RX'])
    channel['Channel Type'] = 'A-Analog'
    channel['Band Width'] = '25K'
    channel['Busy Lock/TX Permit'] = 'Off'

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
    try:
        state = repeater['State']
    except KeyError:
        # Use the generic "Ana Rptrs"
        state = 'Ana Rptrs'
    insert_into_zones(channel, zones, state=state)


def make_analog_repeater_from_repeaterbook_channels(repeaters,
                                                    channels,
                                                    channels_by_name,
                                                    channel_defaults,
                                                    zones):
    """
    This is a special channel making routine for repeaters we have mass
    harvested from Repeaterbook based on geography.

    We need this special routine because normal channel generation is based
    on channel_requests.yaml, and we don't want to have to create special
    requests (just a single line, but still) for the scraped repeaters, which
    may number in the hundreds. So...
    :param repeaters: A LIST (not dict) of repeaters
    :param channels: the channels list, already populated from the yaml files.
    :param channels_by_name: The channels_by_name dict.
    :param channel_defaults: The dict of default channel settings.
    :param zones: The zones list
    :return: The channels dict, the channels_by_name dict.
    """
    for repeater in repeaters:
        channel = channel_defaults.copy()
        channel['Repeater Name'] = repeater['Name']
        channel['Channel Name'] = repeater['Name']
        channel['Transmit Frequency'] = '{:<09}'.format(repeater['TX'])
        channel['Receive Frequency'] = '{:<09}'.format(repeater['RX'])
        channel['Channel Type'] = 'A-Analog'
        channel['Band Width'] = '25K'
        channel['Busy Lock/TX Permit'] = 'Off'

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
        try:
            state = repeater['State']
        except KeyError:
            # Use the generic "Ana Rptrs"
            state = 'Ana Rptrs'
        insert_into_zones(channel, zones, state=state)
    return channels, channels_by_name


def make_analog_simplex_channel(channels,
                                channels_by_name,
                                simplex_name,
                                simplex_channel,
                                channel_defaults,
                                zones):
    channel = channel_defaults.copy()
    channel['Channel Name'] = simplex_name
    channel['Transmit Frequency'] = '{:<09}'.format(simplex_channel['Freq'])
    channel['Receive Frequency'] = '{:<09}'.format(simplex_channel['Freq'])
    channel['Channel Type'] = 'A-Analog'
    channel['Band Width'] = '25K'
    channel['Busy Lock/TX Permit'] = 'Off'
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
                                  radio_id,
                                  single_radio_id):
    channel = channel_defaults.copy()
    channel['Repeater Name'] = repeater['Name']
    channel_name = repeater['Name'] + ' ' + talkgroup
    if not single_radio_id:
        channel_name = radio_id['Abbrev'] + ' ' + channel_name
    # Channel names are limited to 16 characters.
    channel_name = channel_name[:16]
    channel['Channel Name'] = channel_name
    channel['Transmit Frequency'] = '{:<09}'.format(repeater['TX'])
    channel['Receive Frequency'] = '{:<09}'.format(repeater['RX'])
    channel['Channel Type'] = 'D-Digital'
    channel['Band Width'] = '12.5K'
    channel['Color Code'] = repeater['CC']
    channel['Contact'] = talkgroup
    if type(talkgroup_number) == dict:
        if talkgroup_number['Private']:
            channel['Contact Call Type'] = 'Private'
        talkgroup_number = talkgroup_number['Number']
    channel['Contact TG/DMR ID'] = talkgroup_number
    channel['Radio ID'] = radio_id['Name']

    # Assume the TG is dynamic.  We'll fix it if it is static
    try:
        channel['Slot'] = repeater['DynamicTGs']
    except KeyError:
        # Didn't find a preferred slot for dynamic TGs. Assume 1, that seems
        # pretty standard.
        channel['Slot'] = 1

    try:
        for slot in [1, 2]:
            if talkgroup_number in repeater['StaticTGs'][slot]:
                channel['Slot'] = slot  # Choose the right slot for a static TG
    except KeyError:
        # No static TGs for this slot (or at all)... Move along
        pass

    channels.append(channel)
    channels_by_name[channel['Channel Name']] = channel
    insert_into_zones(channel, zones, radio_id, single_radio_id)


def make_digital_repeater_channels(channels,
                                   channels_by_name,
                                   repeater,
                                   talkgroups,
                                   channel_request,
                                   channel_defaults,
                                   zones,
                                   radio_id,
                                   single_radio_id):
    for talkgroup in channel_request['T']:
        make_digital_repeater_channel(channels,
                                      channels_by_name,
                                      repeater,
                                      talkgroup,
                                      talkgroups[talkgroup],
                                      channel_defaults,
                                      zones,
                                      radio_id,
                                      single_radio_id)


def make_digital_simplex_channel(channels,
                                 channels_by_name,
                                 simplex_name,
                                 simplex_channel,
                                 channel_defaults,
                                 zones,
                                 radio_id,
                                 single_radio_id):
    if not single_radio_id:
        simplex_name = radio_id['Abbrev'] + ' ' + simplex_name

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
    insert_into_zones(channel, zones, radio_id, single_radio_id)


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
        single_radio_id = len(radio_ids) == 1
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
                                                   radio_id,
                                                   single_radio_id)
                elif repeater['Mode'] == 'A':
                    # Only enter analog channels once, not per-radio_id.
                    if repeater['Name'] in channels_by_name.keys():
                        continue
                    make_analog_repeater_channel(channels,
                                                 channels_by_name,
                                                 repeater,
                                                 channel_defaults,
                                                 zones)
                else:
                    raise ValueError("Repeater mode must be 'A' or 'D'.")
            elif 'S' in channel_request.keys():
                simplex_name = channel_request['S']
                if type(simplex_name) == float:
                    simplex_name = str(simplex_name)
                simplex_channel = simplex[simplex_name]
                if simplex_channel['Mode'] == 'A':
                    # Only enter analog channels once, not per-radio_id.
                    if simplex_name in channels_by_name.keys():
                        continue
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
                                                 radio_id,
                                                 single_radio_id)
    return channels, channels_by_name


def add_special_zone_members(channels_by_name,
                             special_zones,
                             zones,
                             radio_ids,
                             single_radio_id):
    # It is possible that a channel to be added here is already in the zone.
    # We'll filter those out in insert_into_zone().
    for radio_id in radio_ids:
        # First handle the special key "ALL_ZONES":
        chans_for_all_zones = special_zones['ALL_ZONES']
        for zone_key in zones.keys():
            for chan in chans_for_all_zones:
                if type(chan) != str:
                    chan = str(chan)
                insert_into_zone(channels_by_name[chan],
                                 zone_key,
                                 zones,
                                 radio_id,
                                 single_radio_id)
        # Now the channels that only go into certain zones.
        for zone_name in special_zones.keys():
            if zone_name == 'ALL_ZONES':
                continue
            channel_names = special_zones[zone_name]
            if not single_radio_id:
                zone_name = radio_id['Abbrev'] + ' ' + zone_name
            for channel_name in channel_names:
                try:
                    insert_into_zone(channels_by_name[channel_name],
                                     zone_name,
                                     zones,
                                     radio_id,
                                     single_radio_id)
                except KeyError:
                    # If we have a key error, the most likely reason is that
                    # we're having multiple radio IDs, and the channel name
                    # in the special zones dict doesn't have a prefixed
                    # radio ID abbreviation.  Try adding it.  If we still get
                    # a key error, fail.
                    channel_name = radio_id['Abbrev'] + ' ' + channel_name
                    insert_into_zone(channels_by_name[channel_name],
                                     zone_name,
                                     zones,
                                     radio_id,
                                     single_radio_id)


def insert_into_zones(channel, zones, radio_id=None, state='Ana Rptrs',
                      single_radio_id=True):
    """
    Insert each channel into a zone. For digital channels, the radio_id will
    be used to prefix the zone name with an abbreviation indicating it
    contains the channels for that radio_id. For analog channels, the radio_id
    will be none.

    :param channel: A channel
    :param zones: A dict of dicts containing info about the zones.
    :param radio_id: A radio_id dict. All we will use is the Abbrev field.
    :param state: The US State (or other geographic region) in which the
        repeater is located.
    :param single_radio_id:True if this radio has a single DMR ID. If false,
        zone names
    :return: None
    """
    if channel['Transmit Frequency'] == channel['Receive Frequency']:
        # RX == TX: A simplex channel
        insert_into_zone(channel, 'simplex', zones, radio_id, single_radio_id)
    else:
        if channel['Channel Type'] != 'D-Digital':
            # This is an analog repeater. If specified with a state, put into
            # a zone with the state name.  Otherwise, in the generic "Ana Rptrs"
            insert_into_zone(channel, state, zones, radio_id,
                             single_radio_id)
        else:
            zone_name = channel['Repeater Name']
            if not single_radio_id:
                zone_name = radio_id['Abbrev'] + ' ' + zone_name
            insert_into_zone(channel, zone_name, zones, radio_id)


def insert_into_zone(channel, zone_key, zones, radio_id, single_radio_id=True):
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

    channel_name = channel['Channel Name']
    if channel['Channel Type'] == 'D-Digital' and not single_radio_id:
        channel_name = radio_id['Abbrev'] + ' ' + channel_name

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
     field_names,
     lat_long) = load_data_from_yaml_files()

    analog_repeaters = get_analog_repeaters_from_repeaterbook(lat_long)

    make_talkgroup_file(talkgroups)

    channels, channels_by_name = make_channels(repeaters,
                                               talkgroups,
                                               simplex,
                                               channel_requests,
                                               channel_defaults,
                                               zones,
                                               radio_ids)

    channels, channels_by_name = \
        make_analog_repeater_from_repeaterbook_channels(analog_repeaters,
                                                        channels,
                                                        channels_by_name,
                                                        channel_defaults,
                                                        zones)

    add_special_zone_members(channels_by_name,
                             special_zones,
                             zones,
                             radio_ids,
                             len(radio_ids) == 1)
    write_dict_to_csv(channels, 'channels.csv', field_names['channels'])
    write_dict_to_csv(radio_ids, 'radio_ids.csv', field_names['radio_ids'])
    zone_list = change_zone_dict_to_list(zones)
    write_dict_to_csv(zone_list, 'zones.csv', field_names['zones'])


if __name__ == "__main__":
    main()
