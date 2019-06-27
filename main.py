import os
import json
import struct

# Constants
HEX_OFFSET_PLAYER_INIT = 0x1dc
HEX_OFFSET_PLAYER_END = 0x383
HEX_OFFSET_HOT_INIT = 0x80
HEX_OFFSET_HOT_END = 0xef
ENGLISH_JSON = 'english.json'
MAP = 'map'
PLAYER = 'Player.dat'

KEY_TREASURES = 'treasures'
KEY_ID = 'id'
KEY_NAME = 'name'

# Global Variables
itemMap = {}
playerMap = {}
hotMap = {}

# Check if our item map exists
def verifyEnglishJSON():
    # Check path
    if not os.path.exists(ENGLISH_JSON):
        print('[!] Missing english.json.')
        return False

    # Found
    print('[*] Found english.json.')
    return True

# Read english.json
def readEnglishJSON():
    # Ensure existence
    if not verifyEnglishJSON():
        # TODO: fetch from game files
        # Temporarily abort
        exit(1)

    # Read into a buffer
    f = open(ENGLISH_JSON, 'r')
    data = f.read()
    f.close()

    # Return our buffer
    return data

# Generate item map from english.json
def generateMap():
    # Fetch the JSON
    english = readEnglishJSON()

    # Parse the JSON
    parse = json.loads(english)
    treasures = parse[KEY_TREASURES]

    # Create the map
    for item in treasures:
        _id = item[KEY_ID]
        _name = item[KEY_NAME]

        itemMap[_id] = _name
        print('[*] Appended entry %d : %s' % (_id, _name))

# Check if our player file exists
def verifyPlayer():
    # Check path
    if not os.path.exists(PLAYER):
        print('[!] Missing Player.dat.')
        return False

    # Found
    print('[*] Found Player.dat.')
    return True

def parseLittleEndian(data, i):
    # Parse item ID with little endian hex (1 byte)
    _id = struct.unpack('<h', data[i : i + 2])[0]

    # An empty slot is ID 0
    if _id is -1:
        _id = 0

    # Parse item ID with little endian hex (2 bytes)
    _amount = struct.unpack('<hh', data[i + 2 : i + 6])[0]

    return (_id, _amount)

def readPlayerFile():
    # Ensure existence
    if not verifyPlayer():
        exit(1)
    
    # Read into a buffer
    f = open(PLAYER, 'rb')
    data = f.read()
    f.close()

    # Return our buffer
    return data

def generatePlayerMap():
    # Fetch the Player data
    data = readPlayerFile()

    # Loop over hex
    for i in range(HEX_OFFSET_PLAYER_INIT, HEX_OFFSET_PLAYER_END, 12):
        # Parse using little endian
        (_id, _amount) = parseLittleEndian(data, i)
        playerMap[_id] = _amount
        print('[*] Appended entry "%s" [%d] : %s' % (itemMap[_id], _id, _amount))

    # Loop over hex
    for i in range(HEX_OFFSET_HOT_INIT, HEX_OFFSET_HOT_END, 12):
        # Parse using little endian
        (_id, _amount) = parseLittleEndian(data, i)
        hotMap[_id] = _amount
        print('[*] Appended entry "%s" [%d] : %s' % (itemMap[_id], _id, _amount))

# The main function
def main():
    # Create a map of item IDs
    generateMap()
    print('[*] Item map generated.')

    generatePlayerMap()
    print('[*] Player map generated.')

# Start the program
main()