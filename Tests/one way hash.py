from math import floor
import time

def HashString(string):  
  start_time = time.time()
  bitValueChunk = ""
  bitSum = 0

  for char in string:
    bitSum += ord(char)
    bitValue = format(ord(char), 'b') # Convert char to binary
    bitValueChunk += bitValue # Apend to 'binary chunk'

  n = 9
  bitValues = [bitValueChunk[i:i+n] for i in range(0, len(bitValueChunk), n)] # Split 'binary chunk' into list of 9 bit binary numbers


  moddedBitChunk = ""
  for bitValue in bitValues:
    bitValue = int(bitValue)
    moddedBitValue = bitValue + (bitValue % 37) # Modulo is a one way function, so we modulo by a prime as the core of the hash. This is the step that ensures the hash is unidirectional
    moddedBitValue = moddedBitValue * bitSum # Multiply by sum of the ascii values of the chars to ensure similar input strings look different
    moddedBitChunk += format(moddedBitValue, 'b') # Convert into binary again

  n = 8
  moddedBitValues = [moddedBitChunk[i:i+n] for i in range(0, len(moddedBitChunk), n)] # Split modded 'binary chunk' into list of 8 bit binary numbers    
  
  hashed = ""
  for moddedBitValue in moddedBitValues:
    hashed += chr(int(moddedBitValue, 2)) # Convert binary value into decimal value then into the corresponding character

  hashed = ''.join(hashed.split()) # Strip whitespace, this could cause inconsistencies depending on how the hash is stored/managed
  print("--- Hash completed in approximately " + str((time.time() - start_time)) + " seconds --- ")
  return hashed



while True:
  print(HashString(input("> ")))

