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
playerMap = []
hotMap = []

def playerSlotToPos(slot):
    return HEX_OFFSET_PLAYER_INIT + (12 * slot)

def hotSlotToPos(slot):
    return HEX_OFFSET_HOT_INIT + (12 * slot)

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
        print('[!] Please copy english.json from your game files to the working directory.')
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
    # Scan working directory for a player file
    found = False
    for f in os.listdir():
        ext = f.split('.')
        if ext[-1] == 'dat':
            PLAYER = f
            found = True
            break

    # No player file found
    if not found:
        print('[!] Cannot find a player file!')
        exit(1)

    # Found
    print('[*] Found player file "%s".' % PLAYER)
    return True

# Parse data chunk from player data
def parseLittleEndian(data, i):
    # Parse item ID with little endian hex (1 byte)
    _id = struct.unpack('<h', data[i : i + 2])[0]

    # An empty slot is ID 0
    if _id is -1:
        _id = 0

    # Parse item ID with little endian hex (2 bytes)
    _amount = struct.unpack('<hh', data[i + 2 : i + 6])[0]

    return (_id, _amount)

# Read player file
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

# Map out player data
def generatePlayerMap():
    # Fetch the Player data
    data = readPlayerFile()

    # Loop over hex
    for i in range(HEX_OFFSET_PLAYER_INIT, HEX_OFFSET_PLAYER_END, 12):
        # Parse using little endian
        (_id, _amount) = parseLittleEndian(data, i)
        playerMap.append([_id, _amount])
        print('[*] Appended entry "%s" [%d] : %s' % (itemMap[_id], _id, _amount))

    # Loop over hex
    for i in range(HEX_OFFSET_HOT_INIT, HEX_OFFSET_HOT_END, 12):
        # Parse using little endian
        (_id, _amount) = parseLittleEndian(data, i)
        hotMap.append([_id, _amount])
        print('[*] Appended entry "%s" [%d] : %s' % (itemMap[_id], _id, _amount))

# Write data to player file
def writePlayerFile():
    # Backup player data
    player = readPlayerFile()

    # Prepare to update player file
    f = open(PLAYER, 'wb')

    # Duplicate player file
    f.write(player)

    # Seek to inventory data
    f.seek(HEX_OFFSET_PLAYER_INIT)

    # Write inventory
    mapIndex = 0
    for i in range(HEX_OFFSET_PLAYER_INIT, HEX_OFFSET_PLAYER_END, 12):
        # Loop sequentially
        _id = playerMap[mapIndex][0]
        _amount = playerMap[mapIndex][1]
        mapIndex += 1

        # Convert to little endian
        _raw_id = struct.pack('<h', _id)
        _raw_amount = struct.pack('<h', _amount)

        # Write to player data
        f.seek(i)
        f.write(_raw_id)
        f.seek(i + 2)
        f.write(_raw_amount)

        print('[*] Wrote "%s" [%s] : %s' % (itemMap[_id], _raw_id, _raw_amount))

    # Write hotbar
    mapIndex = 0
    for i in range(HEX_OFFSET_HOT_INIT, HEX_OFFSET_HOT_END, 12):
        # Loop sequentially
        _id = hotMap[mapIndex][0]
        _amount = hotMap[mapIndex][1]
        mapIndex += 1

        # Convert to little endian
        _raw_id = struct.pack('<h', _id)
        _raw_amount = struct.pack('<h', _amount)

        # Write to player data
        f.seek(i)
        f.write(_raw_id)
        f.seek(i + 2)
        f.write(_raw_amount)
        print('[*] Wrote entry "%s" [%s] : %s' % (itemMap[_id], _raw_id, _raw_amount))

    f.close()

# Move items from hotbar slots 6-10 to empty player slots
def mobileWork():
    for i in range(6, 10):
        # Loop sequentially
        _id = hotMap[i][0]
        _amount = hotMap[i][1]

        # No need to move an empty slot
        if _id is 0:
            continue

        # Scan for empty slots to utilize
        foundEmpty = False
        for j in range(0, len(playerMap)):
            if playerMap[j][0] is 0:
                playerMap[j][0] = _id
                playerMap[j][1] = _amount
                foundEmpty = True
                break

        # No empty slots. Abort!
        if not foundEmpty:
            print('[!] No empty slots left!')
            return

        # Clear emptied slots
        hotMap[i][0] = 0
        hotMap[i][1] = 0

        print('[*] Moved "%s" [%s] : %s to inventory.' % (itemMap[_id], _id, _amount))

# The main function
def main():
    # Create a map of item IDs
    generateMap()
    print('[*] Item map generated.')

    # Generate player map
    generatePlayerMap()
    print('[*] Player map generated.')

    # Move last 4 hotbar items to inventory
    mobileWork()
    print('[*] Moved hotbar items for mobile compatibility.')

    # Write player map
    writePlayerFile()
    print("[*] Player file written.")

# Start the program
main()