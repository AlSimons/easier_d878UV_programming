#Design for a code plug builder for the AnyTone D878UV Plus II.

Programming the 878 is complex and tedious, particularly for channels.

The channels list needs an entry for every repeater and talkgroup combination 
you want to use. As a result all the repeater information needs to be entered 
multiple times.  I want to enter the repeater information once (actually, I 
want to simply download it from RepeaterBook as a starting point),
and enter the talkgroup information once, and have the program create the
channels CSV file ready for import into the AnyTone software.

Perhaps an excel sheet?  Hmmm. Have to think about that.

Probably will record this information in YAML.

## Repeater Information
(Have to figure out how to represent simplex channels. Is digital simplex 
used?)
* Label: a short name for use in referencing this repeater. May be used to 
  form part of the channel name.
* Name: The "real" name, e.g., what is listed in Repeaterbook
* Mode: (Analog (="A") or Digital (="D"))
* User's TX Freq
* User's RX Freq

### Digital mode
* Color code (if omitted, default CC1)
* Static talk groups and time slots
* Time slot for all other talk groups (if omitted, default TS1)
* IPSC (if omitted, default Brandmeister)

### Analog mode
* CTCSS or DCS, or
* RCTCSS, TCTCSS, RDCS, TDCS if repeater uses different tx, rx codes.
* If none supplied, no tones used.

## Talkgroup Information
* Label: a short name for use in referencing this repeater. May be used to 
  form part of the channel name.
* Name: The "real" name, e.g., what is listed in the Brandmeister TG list.
* IPSC: The IPSC for this talkgroup.  If omitted, default Brandmeister.
* Number: The TG number in the numbering system used by a repeater's IPSC, 
  e.g., Brandmeister or DRM-MARC.
  
## Channel Information
This is the core reason for this program. We need a convenient way to create
pairings of repeaters and talkgroups to form channels.  I want an easy / 
succinct way to specify this. 

* R: (repeater) the repeater label.
* T: (talkgroup) the talkgroup label.
* S: Simplex channel label.

Exactly one of  R or S must be specified.  T is required if the mode of the 
repeater or simplex channel is digital.

This doesn't currently handle "special" channels, such as 
APRS channels, or receive-only channels such as weather channels and GMRS 
channels.
  
## Zones Design
Don't know how I want to do Zones yet. These are just my current thoughts of
possible schemes.
* By location (like nearby town) A&D together
* By repeater
* Zones for non-Brandmeister IPSC
* Simplex zone?
  * Or at least Simplex 1 (both bands?) in every zone?
* APRS zone?

## Need to figure out
* Simplex channels
* APRS
* Should zone population (have repeater info include area) be partially
  automated? (Future)
  