import os
import json
import struct

# Constants
HEX_OFFSET_PLAYER_INIT = 0x1d8
HEX_OFFSET_PLAYER_END = 0x383
HEX_OFFSET_HOT_INIT = 0x7C
HEX_OFFSET_HOT_END = 0xef

ENGLISH_JSON = 'english.json'
MAP = 'map'
PLAYER = 'Player.dat'

KEY_TREASURES = 'treasures'
KEY_ID = 'id'
KEY_NAME = 'name'

COMMAND_HELP = """
write   - Write modified buffer to the player file.
reload  - Scan and update the world and player data.
mobile  - Move hotbar slots 6-10 to inventory for mobile transfer.
sort    - Sort inventory and hotbar by ID.
give    - Give the player [id] [amount].
done    - Exit the editor.
"""

# ITEM BYTES
# TOTAL 12 BYTES
# 2 modifier
# 2 unknown
# 2 id
# 2 count
# 2 durability
# 1 renderer
# 1 padding

# Global Variables
itemMap = {}
playerMap = []
hotMap = []

mapData = ""
playerData = ""

def playerSlotToPos(slot):
    return HEX_OFFSET_PLAYER_INIT + (12 * slot)

def hotSlotToPos(slot):
    return HEX_OFFSET_HOT_INIT + (12 * slot)

# Read and return file contents
def readFile(path, mode):
    with open(path, mode) as f:
        data = f.read()

    return data

# Parse data chunk from player data
def parseLittleEndian(data, i):
    _modifier = struct.unpack('<h', data[i : i + 2])[0]
    _unknown = struct.unpack('<h', data[i + 2 : i + 4])[0]
    _id = struct.unpack('<h', data[i + 4 : i + 6])[0]
    _amount = struct.unpack('<h', data[i + 6 : i + 8])[0]
    _durability = struct.unpack('<h', data[i + 8 : i + 10])[0]
    _renderer = struct.unpack('<b', data[i + 10 : i + 11])[0]
    _padding = struct.unpack('<b', data[i + 11 : i + 12])[0]

    # Empty slot check
    if _id is -1:
        _id = 0

    return (_modifier, _unknown, _id, _amount, _durability, _renderer, _padding)

# Check if our item map exists
def verifyEnglishJSON():
    # Check path
    if not os.path.exists(ENGLISH_JSON):
        print('[!] Cannot find english.json file!')
        exit(1)

    # Found
    print('[*] Found english.json.')
    return True

# Check if our player file exists
def setPlayerFile():
    # Scan working directory for a player file
    found = False
    for f in os.listdir():
        ext = f.split('.')
        if ext[-1] == 'dat':
            global PLAYER
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

# Generate item map from english.json
def generateMap():
    # Fetch the JSON
    global mapData
    mapData = readFile(ENGLISH_JSON, 'r')

    # Parse the JSON
    parse = json.loads(mapData)
    treasures = parse[KEY_TREASURES]

    # Create the map
    for item in treasures:
        _id = item[KEY_ID]
        _name = item[KEY_NAME]

        itemMap[_id] = _name

# Map out player data
def generatePlayerMap():
    # Fetch the Player data
    global playerData
    playerData = readFile(PLAYER, 'rb')

    # Loop over hex
    for i in range(HEX_OFFSET_PLAYER_INIT, HEX_OFFSET_PLAYER_END, 12):
        # Parse using little endian
        (_modifier, _unknown, _id, _amount, _durability, _renderer, _padding) = parseLittleEndian(playerData, i)
        playerMap.append([_modifier, _unknown, _id, _amount, _durability, _renderer, _padding])
        print('[*] Appended entry "%s" [%d] : %s' % (itemMap[_id], _id, _amount))

    # Loop over hex
    for i in range(HEX_OFFSET_HOT_INIT, HEX_OFFSET_HOT_END, 12):
        # Parse using little endian
        (_modifier, _unknown, _id, _amount, _durability, _renderer, _padding) = parseLittleEndian(playerData, i)
        hotMap.append([_modifier, _unknown, _id, _amount, _durability, _renderer, _padding])
        print('[*] Appended entry "%s" [%d] : %s' % (itemMap[_id], _id, _amount))

# Write data to player file
def writePlayerFile():
    # Prepare to update player file
    f = open(PLAYER, 'wb')

    # Duplicate player file
    f.write(playerData)

    # Seek to inventory data
    f.seek(HEX_OFFSET_PLAYER_INIT)

    # Write inventory
    mapIndex = 0
    for i in range(HEX_OFFSET_PLAYER_INIT, HEX_OFFSET_PLAYER_END, 12):
        # Loop sequentially
        _modifier = playerMap[mapIndex][0]
        _unknown = playerMap[mapIndex][1]
        _id = playerMap[mapIndex][2]
        _amount = playerMap[mapIndex][3]
        _durability = playerMap[mapIndex][4]
        _renderer = playerMap[mapIndex][5]
        _padding = playerMap[mapIndex][6]
        mapIndex += 1

        # Convert to little endian
        _raw_modifier = struct.pack('<h', _modifier)
        _raw_unknown = struct.pack('<h', _unknown)
        _raw_id = struct.pack('<h', _id)
        _raw_amount = struct.pack('<h', _amount)
        _raw_durability = struct.pack('<h', _durability)
        _raw_renderer = struct.pack('<b', _renderer)
        _raw_padding = struct.pack('<b', _padding)

        # Write to player data
        f.seek(i)
        f.write(_raw_modifier)
        f.seek(i + 2)
        f.write(_raw_unknown)
        f.seek(i + 4)
        f.write(_raw_id)
        f.seek(i + 6)
        f.write(_raw_amount)
        f.seek(i + 8)
        f.write(_raw_durability)
        f.seek(i + 10)
        f.write(_raw_renderer)
        f.seek(i + 11)
        f.write(_raw_padding)

        print('[*] Wrote entry "%s" [%s] : %s' % (itemMap[_id], _raw_id, _raw_amount))

    # Write hotbar
    mapIndex = 0
    for i in range(HEX_OFFSET_HOT_INIT, HEX_OFFSET_HOT_END, 12):
        # Loop sequentially
        _modifier = hotMap[mapIndex][0]
        _unknown = hotMap[mapIndex][1]
        _id = hotMap[mapIndex][2]
        _amount = hotMap[mapIndex][3]
        _durability = hotMap[mapIndex][4]
        _renderer = hotMap[mapIndex][5]
        _padding = hotMap[mapIndex][6]
        mapIndex += 1

        # Convert to little endian
        _raw_modifier = struct.pack('<h', _modifier)
        _raw_unknown = struct.pack('<h', _unknown)
        _raw_id = struct.pack('<h', _id)
        _raw_amount = struct.pack('<h', _amount)
        _raw_durability = struct.pack('<h', _durability)
        _raw_renderer = struct.pack('<b', _renderer)
        _raw_padding = struct.pack('<b', _padding)

        # Write to player data
        f.seek(i)
        f.write(_raw_modifier)
        f.seek(i + 2)
        f.write(_raw_unknown)
        f.seek(i + 4)
        f.write(_raw_id)
        f.seek(i + 6)
        f.write(_raw_amount)
        f.seek(i + 8)
        f.write(_raw_durability)
        f.seek(i + 10)
        f.write(_raw_renderer)
        f.seek(i + 11)
        f.write(_raw_padding)

        print('[*] Wrote entry "%s" [%s] : %s' % (itemMap[_id], _raw_id, _raw_amount))

    f.close()

def findEmptyInventorySlot():
    # Scan for empty slots to utilize
    for i in range(0, len(playerMap)):
        if playerMap[i][0] is 0:
            return i

    # No empty slots. Abort!
    return -1

# Move items from hotbar slots 6-10 to empty player slots
def moveFromHotbarToPlayer(slotsRange):
    for i in slotsRange:
        # Loop sequentially
        _modifier = hotMap[i][0]
        _unknown = hotMap[i][1]
        _id = hotMap[i][2]
        _amount = hotMap[i][3]
        _durability = hotMap[i][4]
        _renderer = hotMap[i][5]
        _padding = hotMap[i][6]

        # No need to move an empty slot
        if _id is 0:
            continue

        # Scan for empty slots to utilize
        nextEmpty = findEmptyInventorySlot()

        # No empty slots. Abort!
        if nextEmpty is -1:
            print('[!] No empty slots left!')
            return

        # Give the items
        playerMap[nextEmpty][0] = _modifier
        playerMap[nextEmpty][1] = _unknown
        playerMap[nextEmpty][2] = _id
        playerMap[nextEmpty][3] = _amount
        playerMap[nextEmpty][4] = _durability
        playerMap[nextEmpty][5] = _renderer
        playerMap[nextEmpty][5] = _padding
        
        # Clear emptied slots
        hotMap[i][0] = 0
        hotMap[i][1] = 0
        hotMap[i][2] = 0
        hotMap[i][3] = 0
        hotMap[i][4] = 0
        hotMap[i][5] = 0
        hotMap[i][6] = 0

        print('[*] Moved "%s" [%s] : %s to inventory.' % (itemMap[_id], _id, _amount))

# Give the player an item
def giveItem(_id, _amount):
    # Int checks and conversions
    _id = int(_id)
    _amount = int(_amount)

    # Scan for empty slots to utilize
    nextEmpty = findEmptyInventorySlot()

    # No empty slots. Abort!
    if nextEmpty is -1:
        print('[!] No empty slots left!')
        return

    # Give the items
    playerMap[nextEmpty][0] = 0
    playerMap[nextEmpty][1] = 0
    playerMap[nextEmpty][2] = _id
    playerMap[nextEmpty][3] = _amount
    playerMap[nextEmpty][4] = 0
    playerMap[nextEmpty][5] = 0
    playerMap[nextEmpty][5] = 0

    print('[*] Gave "%s" [%s] : %s to inventory.' % (itemMap[_id], _id, _amount))

# Sort player and hotbar by ID
def sortAll():
    # Generic list sort
    playerMap.sort()
    hotMap.sort()

    # Move empty player slots to the end
    for i in range(len(playerMap)):
        if playerMap[i][3] is 0:
            temp = playerMap.pop(playerMap.index(playerMap[i]))
            playerMap.append(temp)
    
    # Move empty hotbar slots to the end
    for i in range(len(hotMap)):
        if hotMap[i][3] is 0:
            temp = hotMap.pop(hotMap.index(hotMap[i]))
            hotMap.append(temp)

def preChecks():
    # Clear existing data
    global itemMap
    itemMap = {}
    global playerMap
    playerMap = []
    global hotMap
    hotMap = []

    # Make sure player file exists
    setPlayerFile()

    # Make sure english.json file exists
    verifyEnglishJSON()

    # Create a map of item IDs
    generateMap()
    print('[*] Item map generated.')

    # Generate player map
    generatePlayerMap()
    print('[*] Player map generated.')

# Keep asking the user for commands
def userPick():
    # Print help screen
    print(COMMAND_HELP)

    # Get and parse user input
    userIn = input("Choice: ").split(" ")
    command = userIn[0]
    args = userIn[1::]

    if command == 'write':
        writePlayerFile()
        print("[*] Player file written.")
    elif command == 'reload':
        preChecks()
        print("[*] Did pre-checks and regeneration.")
    elif command == 'mobile':
        moveFromHotbarToPlayer(range(6,10))
        print('[*] Moved hotbar items for mobile compatibility.')
    elif command == 'sort':
        sortAll()
        print('[*] Sorted inventory and hotbar by ID.')
    elif command == 'give':
        giveItem(args[0], args[1])
    elif command == 'done':
        print('[*] Exiting without writing.')
        return
    else:
        print('[!] Bad command format!')
    
    userPick()

# The main function
def main():
    # Check if everything exists and generate the maps
    preChecks()
    print("[*] Did pre-checks and regeneration.")

    #  Begin selection loop
    userPick()

# Start the program
main()