import csv
import yaml


csv_field_names = ['No.', 'Channel Name', 'Receive Frequency',
                   'Transmit Frequency', 'Channel Type', 'Transmit Power',
                   'Band Width', 'CTCSS/DCS Decode', 'CTCSS/DCS Encode',
                   'Contact', 'Contact Call Type', 'Contact TG/DMR ID',
                   'Radio ID', 'Busy Lock/TX Permit', 'Squelch Mode',
                   'Optional Signal', 'DTMF ID', '2Tone ID', '5Tone ID',
                   'PTT ID', 'Color Code', 'Slot', 'Scan List',
                   'Receive Group List', 'PTT Prohibit', 'Reverse',
                   'Simplex TDMA', 'Slot Suit', 'AES Digital Encryption',
                   'Digital Encryption', 'Call Confirmation',
                   'Talk Around(Simplex)', 'Work Alone',
                   'Custom CTCSS', '2TONE Decode', 'Ranging', 'Through Mode',
                   'APRS RX', 'Analog APRS PTT Mode', 'Digital APRS PTT Mode',
                   'APRS Report Type', 'Digital APRS Report Channel',
                   'Correct Frequency[Hz]', 'SMS Confirmation',
                   'Exclude channel from roaming', 'DMR MODE',
                   'DataACK Disable', 'R5toneBot', 'R5ToneEot']


def load_data_from_yaml_files():
    """
    Loads data from
        - repeaters.yaml,
        - talkgroups.yaml,
        - simplex.yaml, and
        - channel_info.yaml,
        - channel_defaults.yaml.
    :return: Dicts:
               repeaters,
               talkgroups,
               simplex,
               channel_info,
               channel_defaults
    """
    with open('repeaters.yaml') as f:
        repeaters = yaml.safe_load(f)
    with open('talkgroups.yaml') as f:
        talkgroups = yaml.safe_load(f)
    with open('simplex.yaml') as f:
        simplex = yaml.safe_load(f)
    with open('channel_info.yaml') as f:
        channel_info = yaml.safe_load(f)
    with open('channel_defaults.yaml') as f:
        channel_defaults = yaml.safe_load(f)
    return repeaters, talkgroups, simplex, channel_info, channel_defaults


def write_csv(channels):
    with open('tyb_channels.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f,
                                fieldnames=csv_field_names,
                                quoting=csv.QUOTE_ALL,
                                quotechar='"')
        writer.writeheader()
        for channel in channels:
            writer.writerow(channel)


def index_channels(channels):
    """
    Once the channels list is completely populated, add the "No." field to
    each entry.
    :param channels: The fully populated list of channels.
    :return: None. Channels is updated.
    """
    for i, channel in enumerate(channels):
        channel["No."] = str(i + 1)


def make_analog_repeater_channel(channels,
                                 repeater,
                                 channel_request,
                                 channel_defaults):
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


def make_analog_simplex_channel(channels,
                                simplex_name,
                                simplex_channel,
                                channel_defaults):
    channel = channel_defaults.copy()
    channel['Channel Name'] = simplex_name
    channel['Transmit Frequency'] = '{:<09}'.format(simplex_channel['Freq'])
    channel['Receive Frequency'] = '{:<09}'.format(simplex_channel['Freq'])
    channel['Channel Type'] = 'A-Analog'
    channel['Band Width'] = '25K'
    channel['Busy Lock/TX Permit'] = 'Busy'
    if 'RO' in simplex_channel.keys() and simplex_channel['RO']:
        channel['PTT Prohibit'] = 'On'
    print(channel)
    channels.append(channel)


def make_digital_repeater_channel(channels,
                                  repeater,
                                  talkgroup,
                                  talkgroup_number,
                                  channel_defaults):
    channel = channel_defaults.copy()
    channel['Channel Name'] = repeater['Name'] + ' ' + talkgroup
    channel['Transmit Frequency'] = '{:<09}'.format(repeater['TX'])
    channel['Receive Frequency'] = '{:<09}'.format(repeater['RX'])
    channel['Channel Type'] = 'D-Digital'
    channel['Band Width'] = '12.5K'
    channel['Color Code'] = repeater['CC']
    channel['Contact'] = talkgroup
    channel['Contact TG/DMR ID'] = talkgroup_number

    # Assume the TG is dynamic.  We'll fix it if it is static
    channel['Slot'] = repeater['DynamicTGs']
    for slot in [1, 2]:
        if talkgroup_number in repeater['StaticTGs'][slot]:
            channel['Slot'] = slot # Choose the right slot for a static TG
    #print(repeater)
    #print(talkgroup)
    channels.append(channel)


def make_digital_repeater_channels(channels,
                                   repeater,
                                   talkgroups,
                                   channel_request,
                                   channel_defaults):
    for talkgroup in channel_request['T']:
        make_digital_repeater_channel(channels,
                                      repeater,
                                      talkgroup,
                                      talkgroups[talkgroup],
                                      channel_defaults)


def make_digital_simplex_channel():
    pass


def make_channels(repeaters,
                  talkgroups,
                  simplex,
                  channel_info,
                  channel_defaults):
    """
    Walks over the desired channels list specified in channel_info, and builds
    the dictionary of all the channels, ready to be written to a CSV file for
    import into the programmer.
    :param repeaters: A dict of repeater info
    :param talkgroups: A dict of talkgroup info
    :param simplex: A dict of simplex channels
    :param channel_info: A dict of desired channels
    :param channel_defaults: A dict with the default values for the channels
        CSV value
    :return: A list of fully populated dicts for writing to a CSV
    """
    channels = []
    for channel_request in channel_info:
        print(channel_request)
        channel = None
        if 'R' in channel_request.keys():
            repeater = repeaters[channel_request['R']]
            if repeater['Mode'] == 'D':
                make_digital_repeater_channels(channels,
                                               repeater,
                                               talkgroups,
                                               channel_request,
                                               channel_defaults)
            elif repeater['Mode'] == 'A':
                make_analog_repeater_channel(channels,
                                             repeater,
                                             channel_request,
                                             channel_defaults)
        elif 'S' in channel_request.keys():
            simplex_name = channel_request['S']
            simplex_channel = simplex[simplex_name]
            if simplex_channel['Mode'] == 'A':
                make_analog_simplex_channel(channels,
                                            simplex_name,
                                            simplex_channel,
                                            channel_defaults)
    return channels


def main():
    repeaters, talkgroups, simplex, channel_info, channel_defaults = \
        load_data_from_yaml_files()
    print("Repeaters", repeaters)
    print("Talkgroups", talkgroups)
    print("Simplex", simplex)
    print("Channel info", channel_info)
    print("Channel defaults", channel_defaults)
    channels = make_channels(repeaters,
                             talkgroups,
                             simplex,
                             channel_info,
                             channel_defaults)
    index_channels(channels)
    for channel in channels:
        print(channel)
    write_csv(channels)

if __name__ == "__main__":
    main()