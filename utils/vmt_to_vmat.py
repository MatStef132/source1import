# Converts Source 1 .vmt material files to simple Source 2 .vmat files.
#
# Copyright (c) 2016 Rectus
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Usage Instructions:
# run the script directly
# or `python vmt_to_vmat.py input_path`

#  Translation table is found at vmt_to_vmat below

import re, sys, os
from shutil import copyfile
from time import time, sleep
from difflib import get_close_matches
from random import randint
from PIL import Image, ImageOps
#from s2_helpers import *

# generic, blend instead of vr_complex, vr_2wayblend etc...
# blend doesn't seem to work though. why...
LEGACY_SHADER = False
NEW_SH = not LEGACY_SHADER

# File format of the textures. Needs to be lowercase
TEXTURE_FILEEXT = '.tga'

# Path to content root, before /materials/
PATH_TO_CONTENT_ROOT = r""
#PATH_TO_NEW_CONTENT_ROOT = r""

# Set this to True if you wish to overwrite your old vmat files
OVERWRITE_EXISTING_VMAT = False

REMOVE_VTF_FILES = False

# True for messier files while making the script a bit faster.
FILE_COUNT_OR_PROCESS = True

BASIC_PBR = True

DEBUG = False
def msg(*args, **kwargs):
    if not DEBUG: pass
    else: print("@ DBG:", *args, **kwargs)

Late_Calls = []

# shaders
SH_BLACK = 'black'
SH_VR_BLACK_UNLIT = 'vr_black_unlit'
SH_GENERIC = 'generic'
SH_VR_BASIC = 'vr_basic'
SH_VR_SIMPLE = 'vr_simple'
SH_VR_COMPLEX = 'vr_complex'
SH_VR_STANDARD = 'vr_standard'
SH_BLEND = 'blend'
SH_VR_SIMPLE_2WAY_BLEND = 'vr_simple_2way_blend'
SH_SKY = 'sky'
SH_VR_EYEBALL = 'vr_eyeball'
SH_SIMPLE_WATER = 'simple_water'
SH_REFRACT = 'refract'
SH_CABLES = 'cables'
SH_VR_MONITOR = 'MonitorScreen'
#SH_SPRITECARD = 'spritecard'

# Most shaders have missing/additional properties.
# Need to set an apropriate one that doesn't sacrifice much.
def chooseShader(matType, vmtKeyValList, fileName):

    shaders = {
        SH_BLACK: 0,
        SH_VR_BLACK_UNLIT: 0,
        SH_GENERIC: 0,
        SH_VR_BASIC: 0,
        SH_VR_SIMPLE: 0,
        SH_VR_COMPLEX: 0,
        SH_VR_STANDARD: 0,
        SH_BLEND: 0,
        SH_VR_SIMPLE_2WAY_BLEND: 0,
        SH_SKY: 0,
        SH_VR_EYEBALL: 0,
        SH_SIMPLE_WATER: 0,
        SH_REFRACT: 0,
        SH_CABLES: 0,
        SH_VR_MONITOR: 0
    }
    
    # not recognized, give emtpy shader SH_VR_BLACK_UNLIT
    if matType not in materialTypes:
        return SH_VR_BLACK_UNLIT
    
    if LEGACY_SHADER:   shaders[SH_GENERIC] += 1
    else:                   shaders[materialTypes[matType]] += 1

    if matType == "unlitgeneric":

        if '\\skybox\\' in fileName or '/skybox/' in fileName: shaders[SH_SKY] += 4 # 95% correct
        if "$nofog" in vmtKeyValList: shaders[SH_SKY] += 1
        if "$ignorez" in vmtKeyValList: shaders[SH_SKY] += 2

        if "$receiveflashlight" in vmtKeyValList: shaders[SH_SKY] -= 6
        if "$alphatest" in vmtKeyValList: shaders[SH_SKY] -= 6
        if "$additive" in vmtKeyValList: shaders[SH_SKY] -= 3
        if "$vertexcolor" in vmtKeyValList: shaders[SH_SKY] -= 3
        # translucent
    
    elif matType == "worldvertextransition":
        if vmtKeyValList.get('$basetexture2'): shaders[SH_VR_SIMPLE_2WAY_BLEND] += 69

    elif matType == "lightmappedgeneric":
        if vmtKeyValList.get('$newlayerblending') == '1': shaders[SH_VR_SIMPLE_2WAY_BLEND] += 420

    elif matType == "":
        pass
    
    return max(shaders, key = shaders.get)

# material types need to be lowercase because python is a bit case sensitive
materialTypes = {
    "sky":                  SH_SKY,
    "unlitgeneric":         SH_VR_COMPLEX,
    "vertexlitgeneric":     SH_VR_COMPLEX,
    "decalmodulate":        SH_VR_COMPLEX,
    "lightmappedgeneric":   SH_VR_COMPLEX,
    "lightmappedreflective":SH_VR_COMPLEX,
    "character":            SH_VR_COMPLEX,
    "customcharacter":      SH_VR_COMPLEX,
    "patch":                SH_VR_COMPLEX,
    "teeth":                SH_VR_COMPLEX,
    "eyes":                 SH_VR_EYEBALL,
    "eyeball":              SH_VR_EYEBALL,
    "water":                SH_SIMPLE_WATER,
    "refract":              SH_REFRACT,
    "worldvertextransition":SH_VR_SIMPLE_2WAY_BLEND,
    "lightmapped_4wayblend":SH_VR_SIMPLE_2WAY_BLEND, # no available shader that 4-way-blends
    "cables":               SH_CABLES,
    "lightmappedtwotexture":SH_VR_COMPLEX, # 2 multiblend $texture2 nocull scrolling, model, additive.
    "unlittwotexture":      SH_VR_COMPLEX, # 2 multiblend $texture2 nocull scrolling, model, additive.
    #"spritecard":           SH_SPRITECARD, #"modulate",
    #, #TODO: make this system functional 
    # l4d2
    #"infected":             SH_VR_COMPLEX,
}

ignoreList = [ "dx9", "dx8", "dx7", "dx6", "proxies"]

surfprop_force = {
    'stucco':       'world.drywall',
    'tile':         'world.tile_floor',
    'metalpanel':   'world.metal_panel',
    'wood':         'world.wood_solid',
}
surfprop_HLA = ['metal_panel', 'wood_solid', 'concrete']

INPUT_FILE_EXT = ".vmt"
OUTPUT_FILE_EXT = ".vmat"

VMAT_DEFAULT_PATH = "materials/default/default"
f_KeyVal = '\t{}\t{}\n'
f_KeyValQuoted = '\t{}\t"{}"\n'

def ext(this): return this + TEXTURE_FILEEXT
def default(this): return VMAT_DEFAULT_PATH + this

print('\nSource 2 Material Conveter! By Rectus via Github.')
print('Initially forked by Alpyne, this version by caseytube.\n')
print('--------------------------------------------------------------------------------------------------------')

if DEBUG:
    #currentDir = r"D:\Users\kristi\Desktop\WORK\MOD\content\hlvr"
    currentDir = r"D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo"
    #currentDir = r"D:\Users\kristi\Desktop\WORK\test\there"
    #currentDir = r"D:/Users/kristi/Desktop/WORK/test/materials/2test.vmt"
else:
    currentDir = os.path.dirname(os.path.realpath(__file__)) #os.getcwd()


if not PATH_TO_CONTENT_ROOT:
    if(len(sys.argv) >= 2):
        PATH_TO_CONTENT_ROOT = sys.argv[1]
    else:
        while not PATH_TO_CONTENT_ROOT:
            c = input('Type in the directory of the .vmt file(s) (enter to use current directory, q to quit).: ') or currentDir
            if not os.path.isdir(c) and not os.path.isfile(c):
                if c in ('q', 'quit', 'exit', 'close'): quit()
                print('Could not find directory.')
                continue
            PATH_TO_CONTENT_ROOT = c.lower().strip().strip('"')

# Useful for modname_imported
"""
if not PATH_TO_NEW_CONTENT_ROOT:
    if(len(sys.argv) >= 3):
        PATH_TO_NEW_CONTENT_ROOT = sys.argv[2]
    else:
        while not PATH_TO_NEW_CONTENT_ROOT:
            c = input('Type in the directory you wish to output the converted materials to (enter to use the same dir): ') or currentDir
            if not path.isdir(c):
                    if c in ('q', 'quit', 'exit', 'close'): quit()
                    print('Could not find directory.')
                    continue
                PATH_TO_NEW_CONTENT_ROOT = c.lower().strip().strip('"')
"""

def parseDir(dirName):
    fileCount = 0
    files = []
    for root, _, fileNames in os.walk(dirName):
        #if fileCount > 200: break
        for skipdir in ['console', 'correction', 'dev', 'debug', 'editor', 'tools', 'vgui', ]:
            if ('materials\\' + skipdir) in root: fileNames.clear()

        for fileName in fileNames:
            if fileName.lower().endswith(INPUT_FILE_EXT): # : #
                fileCount += 1
                filePath = os.path.join(root,fileName)
                if len(files) % 17 == 0 or (len(files) == 0):
                    print(f"  Found {len(files)} %sfiles" % ("" if OVERWRITE_EXISTING_VMAT else f"/ {fileCount} "), end="\r")
                if not OVERWRITE_EXISTING_VMAT:
                    if os.path.exists(filePath.replace(INPUT_FILE_EXT, OUTPUT_FILE_EXT)): continue
                files.append(filePath)

    print(f"  Found {len(files)} %sfiles" % ("" if OVERWRITE_EXISTING_VMAT else f"/ {fileCount} "))
    return files

fileList = []

if os.path.isfile(PATH_TO_CONTENT_ROOT): # input is a single file
    if(PATH_TO_CONTENT_ROOT.lower().endswith(INPUT_FILE_EXT)):
        fileList.append(PATH_TO_CONTENT_ROOT)
        PATH_TO_CONTENT_ROOT = PATH_TO_CONTENT_ROOT.split("materials", 1)[0]
    else:
        print("~ Invalid file.")
else:
    folderPath = PATH_TO_CONTENT_ROOT
    if not 'materials' in PATH_TO_CONTENT_ROOT \
    and not PATH_TO_CONTENT_ROOT.endswith(INPUT_FILE_EXT) \
    and not PATH_TO_CONTENT_ROOT.rstrip('\\/').endswith('materials'):
        folderPath = os.path.abspath(os.path.join(PATH_TO_CONTENT_ROOT, 'materials'))
    if os.path.isdir(folderPath):
        print("\n-", folderPath.capitalize())
        print("+ Scanning for .vmt files. This may take a while...")
        fileList.extend(parseDir(folderPath))
    else: print("~ Could not find a /materials/ folder inside this dir.\n")

PATH_TO_CONTENT_ROOT = os.path.normpath(PATH_TO_CONTENT_ROOT) + '\\'
#PATH_TO_NEW_CONTENT_ROOT =  os.path.normpath(PATH_TO_NEW_CONTENT_ROOT) + '\\'


# "environment maps/metal_generic_002" -> "materials/environment maps/metal_generic_002(.tga)"
def formatVmtTextureDir(localPath, fileExt = TEXTURE_FILEEXT):
    if localPath.endswith(fileExt): fileExt = ''
    localPath = 'materials/' + localPath.strip().strip('"') + fileExt
    localPath = localPath.replace('\\', '/') # Convert paths to use forward slashes.
    localPath = localPath.replace('.vtf', '')#.replace('.tga', '') # remove any old extensions
    localPath = os.path.normpath(localPath.lower())

    return localPath

# materials/texture_color.tga -> C:/Users/User/Desktop/stuff/materials/texture_color.tga
def formatFullDir(localPath):
    return os.path.abspath(os.path.join(PATH_TO_CONTENT_ROOT, localPath))

# inverse of formatFullDir()
def formatVmatDir(localPath):
    if not localPath: return None
    localPath = os.path.normpath(localPath)
    return localPath.replace(PATH_TO_CONTENT_ROOT, '')

def textureAddSubStr(str1, str2):
    if str1.endswith(str2):
        return str1
    #str1 += str2
    return (str1 + str2)

# -------------------------------
# Returns correct path, checks if alreay exists, renames with proper extensions, etc...
# -------------------------------
def formatNewTexturePath(vmtPath, textureType = TEXTURE_FILEEXT, noRename = False, forReal = True):
    # and Error loading resource file "materials/models/props/de_dust/hr_dust/dust_lights/street_lantern_03/street_lantern_03_color.vmat_c" (Error: ERROR_FILEOPEN)
    if vmtPath == '': return default(textureType)

    vtfTexture = formatFullDir(formatVmtTextureDir(vmtPath + '.vtf', '') + '.vtf')
    if REMOVE_VTF_FILES and os.path.exists(vtfTexture):
        os.remove(vtfTexture)
        print("~ Removed vtf file: " + formatVmatDir(vtfTexture))

    # "newde_cache/nc_corrugated" -> materials/newde_cache/nc_corrugated
    textureLocal = formatVmtTextureDir(vmtPath, '')

    return ext(textureLocal)

# -------------------------------
# Returns full texture path of given vmt Param, vmt Params, or vmt Path
# $basetexture              -> C:/addon_root/materials/path/to/texture_color.tga
# path/to/texture_color.tga -> C:/addon_root/materials/path/to/texture_color.tga
# -------------------------------
def getTexture(vmtParams):
    #breakpoint()
    texturePath = ''
    bFound = False

    if not isinstance(vmtParams, list):
        vmtParams = [ vmtParams ]

    for vmtParam in vmtParams:

        # were given a full path
        if os.path.exists(vmtParam):
            return vmtParam

        # well it is not a key
        elif not vmtKeyValList.get(vmtParam):
            texturePath = formatFullDir(formatVmtTextureDir(vmtParam))
            if os.path.exists(texturePath):
                bFound = True
                break
            continue
        
        # now it has to be a key...
        texturePath = formatVmtTextureDir(vmtKeyValList[vmtParam])

        #if os.path.exists(texturePath):
        #    texturePath = formatFullDir(texturePath)
        #    if os.path.exists(texturePath):
        #        bFound = True

        #if not RENAME_BY_COPYING or not bFound:
        if not bFound:
            texturePath = formatNewTexturePath(vmtKeyValList[vmtParam], vmt_to_vmat['textures'][vmtParam][VMAT_DEFAULTVAL], forReal=False)
            texturePath = formatFullDir(texturePath)

        if os.path.exists(texturePath):
            bFound = True
            break

    if not bFound: texturePath = '' # ''

    return texturePath

def parseVMTParameter(line, parameters):
    words = []
    nextLine = ''

    # doesn't split inside qotes
    words = re.split(r'\s+(?=(?:[^"]*"[^"]*")*[^"]*$)', line)
    words = list(filter(len, words))

    if not words: return
    elif len(words) == 1:
        Quott = words[0].count('"')
        # fix for: "$key""value""
        if Quott >= 4:
            m = re.match(r'^((?:[^"]*"){1}[^"]*)"(.*)', line)
            if m:
                line = m.group(1)  + '" ' + m.group(2)
                parseVMTParameter(line, vmtKeyValList)
        # fix for: $key"value"
        elif Quott == 2:
            # TODO: sth better that keeps text inside quotes intact.
            #line = line.replace('"', ' " ').rstrip(' " ') + '"'
            line = line.replace('"', '')
            parseVMTParameter(line, vmtKeyValList)
        return # no recursive loops please
    elif len(words) > 2:
        # fix for: "$key""value""$key""value" - we come here after len == 1 has happened
        nextLine = ' '.join(words[2:]) # words[2:3]
        words = words[:2]

    key = words[0].strip('"').lower()

    if key.startswith('/'):
        return

    if not key.startswith('$'):
        if not 'include' in key:
            return

    # "GPU>=2?$detailtexture"
    if '?' in key:
        print("~ WARNING: Might not process well materials that have GPU-setting based parameters. Please manually check.")
        #key = key.split('?')[1].lower()
        key.split('?')
        if key[0] == 'GPU>=2':
            msg("Trying using the high-shader parameter.")
            key = key[2].lower()
        else:
            print("~ WARNING: Might not process well materials that have GPU-setting based parameters. Please manually check.")
            if key[0] == 'GPU<2':
                return
            key = key[2].lower()

    val = words[1].lstrip('\n').lower() # .strip('"')

    # remove comments, HACK
    commentTuple = val.partition('//')
    
    if not commentTuple[0] in parameters:
        parameters[key] = commentTuple[0]

    if nextLine: parseVMTParameter(nextLine, vmtKeyValList)

def createMask(vmtTexture, copySub = '_mask.tga', channel = 'A', invert = False, queue = True):

    imagePath = getTexture(vmtTexture)
    #msg("createMask with", formatVmatDir(vmtTexture), copySub, channel, invert, queue)

    if not imagePath:
        msg("No input for createMask.", imagePath)
        failures.append(fileName + f" - {vmtTexture} not found")
        return default(copySub)

    if invert:  newMaskPath = imagePath[:-4] + '_' + channel[:3].lower() + '-1' + copySub
    else:       newMaskPath = imagePath[:-4] + '_' + channel[:3].lower()        + copySub

    if os.path.exists(newMaskPath) and not DEBUG:
        return formatVmatDir(newMaskPath)

    if not os.path.exists(imagePath):
        failures.append(fileName)
        print("~ ERROR: Couldn't find requested image (" + imagePath + "). Please check.")
        return default(copySub)

    queue = False # QUEUE_INCOMPATIBILITY
    if not queue:
        image = Image.open(imagePath).convert('RGBA')

        if channel == 'L':
            imgChannel = image.convert('L')
        else:
            imgChannel = image.getchannel(str(channel))

        if invert:
            imgChannel = ImageOps.invert(imgChannel)

        # mask with single color
        colors = imgChannel.getcolors()
        if len(colors) == 1:
            if False: # safest method: save space by resizing
                print("~ Warning: Found single color mask wasting space.", imgChannel.size, "resized to ", end = '')
                imgChannel = imgChannel.resize( (4,4), resample = Image.NEAREST)
                print(imgChannel.size)

            # smartest method: use color vector (no space wasted and clutterless) - incompatible with queue :(
            return fixVector(f"{{{colors[0][1]} {colors[0][1]} {colors[0][1]}}}", True)

        #bg = Image.new("RGBA", image.size, (0,0,0,255))
        bg = Image.new("L", image.size)

        # Copy the specified channel to the new image using itself as the mask
        bg.paste(imgChannel)

        bg.convert('L').save(newMaskPath, optimize=True) #.convert('P', palette=Image.ADAPTIVE, colors=8)
        bg.close()
        print("+ Saved mask to " + formatVmatDir(newMaskPath))
    else:
        Late_Calls.append([createMask, (imagePath, copySub, channel, invert, False)])

    return formatVmatDir(newMaskPath)

def flipNormalMap(localPath):

    image_path = formatFullDir(localPath)
    if not os.path.exists(image_path): return

    if FILE_COUNT_OR_PROCESS:
        with open(formatFullDir(localPath[:-4] + '.txt'), 'w') as settingsFile:
            settingsFile.write('"settings"\n{\t"legacy_source1_inverted_normal" "1"\n}')
    else:
        # Open the image and convert it to RGBA, just in case it was indexed
        image = Image.open(image_path).convert('RGB')

        r,g,b,a = image.split()
        g = ImageOps.invert(g)
        final_transparent_image = Image.merge('RGB', (r,g,b,a))
        final_transparent_image.save(image_path)

    return localPath

skyboxPath = {}
skyboxFaces = ['up', 'dn', 'lf', 'rt', 'bk', 'ft']


#BUG: both of these are bugging when unquoted
# 	$color "{127 128 500}"
#	$selfillumtint "[.5 .5 .5 .1]"
def fixVector(s, addAlpha = 1, returnList = False):

    s = str(s)
    if('{' in s or '}' in s): likelyColorInt = True
    else: likelyColorInt = False

    s = s.strip() # TODO: remove letters
    s = s.replace('"', '').replace("'", "")
    s = s.strip().replace(",", "").strip('][}{')

    try: originalValueList = [str(float(i)) for i in s.split(' ') if i != '']
    except: originalValueList =  [1.000000, 1.000000, 1.000000]

    dimension = len(originalValueList)
    if dimension < 3: likelyColorInt = False

    for strvalue in originalValueList:
        flvalue = float(strvalue)
        if likelyColorInt: flvalue /= 255

        originalValueList[originalValueList.index(strvalue)] = "{:.6f}".format(flvalue)

    # todo $detailscale "[8 8 8]" ---> g_vDetailTexCoordScale [8.000000 8.000000 8.000000]
    if(dimension <= 1):
        originalValueList.append(originalValueList[0])  # duplicate for 2D
    elif(addAlpha and (dimension == 3)):
        originalValueList.append("{:.6f}".format(1))    # add alpha

    if returnList:  return originalValueList
    else:           return '[' + ' '.join(originalValueList) + ']'

def fixSurfaceProp(vmtVal):

    if vmtVal in ('default', 'default_silent', 'no_decal', 'player', 'roller', 'weapon'):
        return vmtVal

    elif vmtVal in surfprop_force:
        return surfprop_force[vmtVal]
    else:
        if("props" in vmatFileName): match = get_close_matches('prop.' + vmtVal, surfprop_HLA, 1, 0.4)
        else: match = get_close_matches('world.' + vmtVal, surfprop_HLA, 1, 0.6) or get_close_matches(vmtVal, surfprop_HLA, 1, 0.6)

        return match[0] if match else vmtVal


def int_var(vmtVal, bInvert = False):
    if bInvert:
        return str(int(not int(vmtVal)))
    return str(int(vmtVal))

def float_var(vmtVal): 
    return "{:.6f}".format(float(vmtVal.strip(' \t"')))

def material_A(vmatKey):
    return vmatKey + 'A'

MATRIX_CENTER = 0
MATRIX_SCALE = 1
MATRIX_ROTATE = 2
MATRIX_TRANSLATE = 3

def listMatrix(s):
    # [0, 1] center defines the point of rotation. Only useful if rotate is being used.
    # [2, 3] scale fits the texture into the material the given number of times. '2 1' is a 50% scale in the X axis.
    # 4      rotate rotates the texture counter-clockwise in degrees. Accepts any number, including negatives.
    # [5, 6] translate shifts the texture by the given numbers. '.5' will shift it half-way.

    # "center .5 .5 scale 1 1 rotate 0 translate 0 0" -> [ [0.5 0.5], [1.0, 1.0], 0.0, [0.0, 0.0] ]
    if not s: return

    s = s.strip('"')
    eachTerm = [i for i in s.split(' ')]
    transformList = [None, None, None, None]

    for i in eachTerm:
        try:
            if i == 'rotate':
                nextTerm = int(eachTerm[eachTerm.index(i)+1].strip("'"))
                transformList [ MATRIX_ROTATE ] = nextTerm
                continue

            nextTerm =      float(eachTerm[eachTerm.index(i)+1].strip("'"))
            nextnextTerm =  float(eachTerm[eachTerm.index(i)+2].strip("'"))

            if i == 'center':   transformList [ MATRIX_CENTER ]     = [ nextTerm, nextnextTerm ]
            if i == 'scale':    transformList [ MATRIX_SCALE ]      = [ nextTerm, nextnextTerm ]
            if i == 'translate':transformList [ MATRIX_TRANSLATE ]  = [ nextTerm, nextnextTerm ]
        except:
            pass

    return transformList

def is_convertible_to_float(value):
    try:
        float(value)
        return True
    except: return False

normalmap_list = ['$normal', '$bumpmap', '$bumpmap2']

VMAT_REPLACEMENT = 0
VMAT_DEFAULTVAL = 1
VMAT_TRANSLFUNC = 2
VMAT_EXTRALINES = 3


vmt_to_vmat = {

'f_properties': {
    '$translucent':     ('F_TRANSLUCENT',           '1', None, ''),
    '$alphatest':       ('F_ALPHA_TEST',            '1', None, ''),
    '$envmap':          ('F_SPECULAR',              '1', None, ''),
    '$selfillum':       ('F_SELF_ILLUM',            '1', None, ''),
    '$additive':        ('F_ADDITIVE_BLEND',        '1', None, ''),
    '$ignorez':         ('F_DISABLE_Z_BUFFERING',   '1', None, ''),
    '$nocull':          ('F_RENDER_BACKFACES',      '1', None, ''),
    '$decal':           ('F_OVERLAY',               '1', None, ''),
    '$flow_debug':      ('F_FLOW_DEBUG',            '0', None, ''),
    '$detailblendmode': ('F_DETAIL_TEXTURE',        '1', None, ''), # not 1 to 1
    '$decalblendmode':  ('F_DETAIL_TEXTURE',        '1', None, ''), # not 1 to 1
    '$sequence_blend_mode': ('F_FAST_SEQUENCE_BLEND_MODE', '1', None, '' ), # spritecard///

    '$selfillum_envmapmask_alpha': ('F_SELF_ILLUM', '1', None, ''),
},

'textures': {

    # BUG WITH VERTIGOBLUE: 2 of these lead to 2 SkyTexture 
    '$hdrcompressedtexture':('SkyTexture',  '.pfm', None, 'F_TEXTURE_FORMAT2 6'), # // BC6H (HDR compressed - recommended)
    '$hdrbasetexture':      ('SkyTexture',  '.pfm', None, ''),

    ## Layer0 
    '$basetexture':     ('TextureColor',        ext('_color'),   [formatNewTexturePath],     '' ), # SkyTexture
    '$painttexture':    ('TextureColor',        ext('_color'),   [formatNewTexturePath],     '' ),
    '$bumpmap':         ('TextureNormal',       ext('_normal'),  [formatNewTexturePath],     '' ),
    '$normalmap':       ('TextureNormal',       ext('_normal'),  [formatNewTexturePath],     '' ),

    ## Layer blend mask
    '$blendmodulatetexture':\
                        ('TextureMask',             ext('_mask'),   [createMask, 'G', False], 'F_BLEND 1') if NEW_SH else \
                        ('TextureLayer1RevealMask', ext('_blend'),  [createMask, 'G', False], 'F_BLEND 1'),
    ## Layer1
    '$basetexture2':    ('TextureColorB' if NEW_SH else 'TextureLayer1Color',  ext('_color'),  [formatNewTexturePath], '' ),
    '$texture2':        ('TextureColorB' if NEW_SH else 'TextureLayer1Color',   ext('_color'),  [formatNewTexturePath], '' ), # UnlitTwoTexture
    '$bumpmap2':        ('TextureNormalB' if NEW_SH else 'TextureLayer1Normal', ext('_normal'), [formatNewTexturePath], '' if NEW_SH else 'F_BLEND_NORMALS 1' ),

    ## Layer2-3
    '$basetexture3':    ('TextureLayer2Color',  ext('_color'),  [formatNewTexturePath],     ''), #if LEGACY_SHADER else tuple(),
    '$basetexture4':    ('TextureLayer3Color',  ext('_color'),  [formatNewTexturePath],     ''), #if LEGACY_SHADER else tuple(),

    '$normalmap2':      ('TextureNormal2',      ext('_normal'), [formatNewTexturePath],     'F_SECONDARY_NORMAL 1'), # used with refract shader
    '$flowmap':         ('TextureFlow',         ext(''),        [formatNewTexturePath],     'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 1'),
    '$flow_noise_texture':\
                        ('TextureNoise',        ext('_noise'),  [formatNewTexturePath],     'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 2'),
    '$detail':          ('TextureDetail',       ext('_detail'), [formatNewTexturePath],     'F_DETAIL_TEXTURE 1\n'), # $detail2
    '$decaltexture':    ('TextureDetail',       ext('_detail'), [formatNewTexturePath],     'F_DETAIL_TEXTURE 1\n\tF_SECONDARY_UV 1\n\tg_bUseSecondaryUvForDetailTexture "1"'),

    '$selfillummask':   ('TextureSelfIllumMask',ext('_selfillummask'), [formatNewTexturePath],  ''),
    '$tintmasktexture': ('TextureTintMask',     ext('_mask'),   [createMask, 'G', False],    'F_TINT_MASK 1'), # GREEN CHANNEL ONLY, RED IS FOR $envmapmaskintintmasktexture 1 #('TextureTintTexture',)
    '$_vmat_metalmask': ('TextureMetalness',    ext('_metal'),  [formatNewTexturePath],     'F_METALNESS_TEXTURE 1'), # F_SPECULAR too
    '$_vmat_transmask': ('TextureTranslucency', ext('_trans'),  [formatNewTexturePath],     ''), 

    # in viewmodels, only the G channel -> R = flCavity, G = flAo, B = cModulation, A = flPaintBlend ###'$ambientoccltexture': '$ambientocclusiontexture':
    '$ao':          ('TextureAmbientOcclusion', ext('_ao'),     [createMask, 'G', False],    'F_AMBIENT_OCCLUSION_TEXTURE 1'), # g_flAmbientOcclusionDirectSpecular "1.000"
    '$aotexture':   ('TextureAmbientOcclusion', ext('_ao'),     [createMask, 'G', False],    'F_AMBIENT_OCCLUSION_TEXTURE 1'), # g_flAmbientOcclusionDirectSpecular "1.000"

    #'$phongexponent2' $phongmaskcontrastbrightness2, $phongbasetint2, $phongamount2

    # Next script should take care of these, unless BASIC_PBR
    '$envmapmask':  ('$envmapmask',         ext('_env_mask'),   [formatNewTexturePath], '') if not BASIC_PBR else \
                    ('TextureRoughness',    ext('_rough'),      [formatNewTexturePath], '') if not LEGACY_SHADER else \
                    ('TextureGlossiness',   ext('_gloss'),      [formatNewTexturePath], ''),

    '$phongmask':   ('$phongmask',          ext('_phong_mask'), [formatNewTexturePath], '') if not BASIC_PBR else \
                    ('TextureRoughness',    ext('_rough'),      [formatNewTexturePath], '') if not LEGACY_SHADER else \
                    ('TextureGlossiness',   ext('_gloss'),      [formatNewTexturePath], ''),
},

'transform': {
    '$basetexturetransform':     ('g_vTex',          'x', None, ''), # g_vTexCoordScale "[1.000 1.000]"g_vTexCoordOffset "[0.000 0.000]"
    '$detailtexturetransform':   ('g_vDetailTex',    'x', None, ''), # g_flDetailTexCoordRotation g_vDetailTexCoordOffset g_vDetailTexCoordScale g_vDetailTexCoordXform
    '$bumptransform':            ('g_vNormalTex',    'x', None, ''),
    #'$bumptransform2':           ('',                '', ''),
    #'$basetexturetransform2':    ('',               '', ''),    #
    #'$texture2transform':        ('',                '', ''),   #
    #'$blendmasktransform':       ('',                '', ''),   #
    #'$envmapmasktransform':      ('',                '', ''),   #
    #'$envmapmasktransform2':     ('',                '', '')    #

},

'settings': {

    '$detailblendfactor':   ('g_flDetailBlendFactor',   '1.000',                    [float_var],       ''), #'$detailblendfactor2', '$detailblendfactor3'
    '$detailscale':         ('g_vDetailTexCoordScale',  '[1.000 1.000]',            [fixVector, False], ''),

    '$color':               ('g_vColorTint',            '[1.000 1.000 1.000 0.000]',[fixVector, True],  ''),
    '$color2':              ('g_vColorTint',            '[1.000 1.000 1.000 0.000]',[fixVector, True],  ''),
    '$selfillumtint':       ('g_vSelfIllumTint',        '[1.000 1.000 1.000 0.000]',[fixVector, True],  ''),

    '$selfillumscale':      ('g_flSelfIllumScale',      '1.000',    [float_var],       ''),
    '$blendtintcoloroverbase':('g_flModelTintAmount',   '1.000',    [float_var],       ''),
    '$layertint1':          ('','',''),

    #'$warpindex':           ('g_flDiffuseWrap',         '1.000',    [float_var], ''), # requires F_DIFFUSE_WRAP 1. "? 
    #'$diffuseexp':          ('g_flDiffuseExponent',     '2.000',    [float_var], 'g_vDiffuseWrapColor "[1.000000 1.000000 1.000000 0.000000]'),

    '$metalness':           ('g_flMetalness',           '0.000',    [float_var], ''),
    '$_metalness2':         ('g_flMetalnessB',          '0.000',    [float_var], ''),
    '$alpha':               ('g_flOpacityScale',        '1.000',    [float_var], ''),
    '$alphatestreference':  ('g_flAlphaTestReference',  '0.500',    [float_var], 'g_flAntiAliasedEdgeStrength "1.000"'),
    '$refractamount':       ('g_flRefractScale',        '0.200',    [float_var], ''),
    '$flow_worlduvscale':   ('g_flWorldUvScale',        '1.000',    [float_var], ''),
    '$flow_noise_scale':    ('g_flNoiseUvScale',        '0.010',    [float_var], ''), # g_flNoiseStrength?
    '$flow_bumpstrength':   ('g_flnormalmap_listtrength',   '1.000',    [float_var], ''),

    '$nofog':   ('g_bFogEnabled',       '0',        [int_var, True], ''),
    "$notint":  ('g_flModelTintAmount', '1.000',    [int_var, True], ''),

    # SH_BLEND and SH_VR_STANDARD(SteamVR) -- $NEWLAYERBLENDING settings used on dust2 etc. might as well comment them for steamvr
    #'$blendsoftness':       ('g_flLayer1BlendSoftness', '0.500',    ''),
    #'$layerborderstrenth':  ('g_flLayer1BorderStrength','0.500',    ''),
    #'$layerborderoffset':   ('g_flLayer1BorderOffset',  '0.000',    ''),
    #'$layerbordersoftness': ('g_flLayer1BorderSoftness','0.500',    ''),
    #'$layerbordertint':     ('g_vLayer1BorderColor',       '[1.000000 1.000000 1.000000 0.000000]', [fixIntVector, True], ''),
    #'LAYERBORDERSOFTNESS':  ('g_flLayer1BorderSoftness', '1.0', ''),
    #rimlight
},

'channeled_masks': {
   #'$vmtKey':                      (extract_from,      extract_as,       channel to extract)|
    '$normalmapalphaenvmapmask':    (normalmap_list,    '$envmapmask',      'A'), 
    '$basealphaenvmapmask':         ('$basetexture',    '$envmapmask',      'A'), # 'M_1-A'
    '$envmapmaskintintmasktexture': ('$tintmasktexture','$envmapmask',      'R'),
    '$basemapalphaphongmask':       ('$basetexture',    '$phongmask',       'A'),
    '$basealphaphongmask':          ('$basetexture',    '$phongmask',       'A'),
    '$normalmapalphaphongmask':     (normalmap_list,    '$phongmask',       'A'),
    '$bumpmapalphaphongmask':       (normalmap_list,    '$phongmask',       'A'),
    '$basemapluminancephongmask':   ('$basetexture',    '$phongmask',       'L'),

    '$blendtintbybasealpha':        ('$basetexture',    '$tintmasktexture', 'A'),
    '$selfillum_envmapmask_alpha':  ('$envmapmask',     '$selfillummask',   'A'),

    '$translucent':                 ('$basetexture',    '$_vmat_transmask', 'A'),
    '$alphatest':                   ('$basetexture',    '$_vmat_transmask', 'A'),
    '$selfillum':                   ('$basetexture',    '$selfillummask',   'A'),
    #'$phong':                       (normalmap_list,    '$phongmask',       'A'),

    #'$masks1': ('self', ('$rimmask', '$phongalbedomask', '$_vmat_metalmask', '$warpindex'), 'RGBA')
},

'SystemAttributes': {
    '$surfaceprop':     ('PhysicsSurfaceProperties', 'default', [fixSurfaceProp], '')
},
# no direct replacement, etc
'others2': {
    # ssbump dose not work?
    #'$ssbump':               ('TextureBentNormal',    '_bentnormal.tga', 'F_ENABLE_NORMAL_SELF_SHADOW 1\n\tF_USE_BENT_NORMALS 1\n'),
    #'$newlayerblending':     ('',    '',     ''),

    #'$iris': ('',    '',     ''), # paste iris into basetexture

    # fRimMask = vMasks1Params.r;
    # fPhongAlbedoMask = vMasks1Params.g;
    # fMetalnessMask = vMasks1Params.b;
    # fWarpIndex = vMasks1Params.a;
    # https://developer.valvesoftware.com/wiki/Character_(shader)
    #'$maskstexture':    ('',    '',     ''),
    #'$masks':   ('',    '',     ''),
    #'$masks1':  ('',    '',     ''),
    #'$masks2':  ('',    '',     ''),
    #'$phong':   ('',    '',     ''),

    # $selfillumfresnelminmaxexp "[1.1 1.7 1.9]"
    #'$selfillum_envmapmask_alpha':     ('',    '',     ''),

    # TODO: the fake source next to outside area on de_nuke;
    # x = texturescrollrate * cos(texturescrollangle) ?????
    # y = texturescrollrate * sin(texturescrollangle) ?????
    #'TextureScroll':    (('texturescrollvar', 'texturescrollrate', 'texturescrollangle'), 'g_vTexCoordScrollSpeed', '[0.000 0.000]') 
}
}

def convertVmtToVmat(vmtKeyValList):

    vmatContent = ''
    lines_SysAtributes = []

    # for each key-value in the vmt file ->
    for vmtKey, vmtVal in vmtKeyValList.items():

        outKey = outVal = outAddLines = ''

        vmtKey = vmtKey.lower()
        vmtVal = vmtVal.strip().strip('"' + "'").strip(' \n\t"')

        # search through the dictionary above to find the appropriate replacement.
        for keyType in list(vmt_to_vmat):

            vmatItems = vmt_to_vmat[keyType].get(vmtKey)

            if not vmatItems:
                continue

            vmatReplacement = None
            vmatDefaultVal = None
            vmatTranslFunc = None
            outAddLines = None

            try:
                vmatReplacement = vmatItems [ VMAT_REPLACEMENT  ]
                vmatDefaultVal  = vmatItems [ VMAT_DEFAULTVAL   ]
                vmatTranslFunc  = vmatItems [ VMAT_TRANSLFUNC   ]
                outAddLines     = vmatItems [ VMAT_EXTRALINES   ]
            except: pass

            if ( vmatReplacement and vmatDefaultVal ):
                
                outKey = vmatReplacement
                
                if (keyType == 'textures'):
                    outVal = default(vmatDefaultVal)
                else:
                    outVal = vmatDefaultVal

                if vmatTranslFunc:
                    if hasattr(vmatTranslFunc[0], '__call__'):

                        if (keyType == 'textures'):
                            #msg("//", testt, end = ' ->')
                            #testt.insert(1, vmatDefaultVal)
                            #print(testt)
                            #if testt[0] != createMask:
                            #    assert testt[0](vmtVal, *testt[1:], False, False)

                            if len(vmatTranslFunc) < 2 or vmatTranslFunc[1] != vmatDefaultVal:
                                msg("Adding arg to", vmatTranslFunc, end = ' ->')
                                vmatTranslFunc.insert(1, vmatDefaultVal)
                                print(vmatTranslFunc)

                            #msg("~ For", vmtKey, "calling", vmatTranslFunc[0], "with args: (" + vmtVal, vmatDefaultVal, end=") ---> ")
                            #outVal = vmatTranslFunc[0](vmtVal, vmatDefaultVal)
                        #else:
                        msg(vmtKey, "calls", vmatTranslFunc[0], "args: (" + vmtVal, *vmatTranslFunc[1:], end="). Got -> ")
                        outVal = vmatTranslFunc[0](vmtVal, *vmatTranslFunc[1:])

                        msg(outVal)
                    else:
                        outAddLines = vmatTranslFunc

            # no equivalent key-value for this key, only exists
            # add comment or ignore completely
            elif (outAddLines):
                if keyType in ('transform'): # exceptions
                    pass
                else:
                    vmatContent += outAddLines
                    continue
            else:
                continue

            # F_RENDER_BACKFACES 1 etc
            if keyType == 'f_properties':
                if vmtKey in  ('$detailblendmode', '$decalblendmode'):
                    # https://developer.valvesoftware.com/wiki/$detail#Parameters_and_Effects
                    # materialsystem\stdshaders\BaseVSShader.h#L26

                    if vmtVal == '0':       outVal = '1' # Original mode (Mod2x)
                    elif vmtVal == '1':     outVal = '2' # Base.rgb+detail.rgb*fblend 
                    elif vmtVal == '12':    outVal = '0'
                    else: outVal = '1'

                if outKey in vmatContent: ## Replace keyval if already added
                    msg(outKey + ' is already in.')
                    vmatContent = re.sub(r'%s.+' % outKey, outKey + ' ' + outVal, vmatContent)
                else:
                    vmatContent += '\t' + outKey + ' ' + outVal + '\n'  
                continue ### Skip default content write

            elif(keyType == 'textures'):
                
                if vmtKey in ['$basetexture', '$hdrbasetexture', '$hdrcompressedtexture']:
                    # semi-BUG: how is hr_dust_tile_01,02,03 blending when its shader is LightmappedGeneric??????????
                    if '$newlayerblending' in vmtKeyValList or '$basetexture2' in vmtKeyValList:
                        outKey = vmatReplacement + 'A' # TextureColor -> TextureColorA
                        msg(outKey + "<--- is noblend ok?")
                    
                    if vmatShader == SH_SKY:
                        outKey = 'SkyTexture'
                        outVal = formatVmtTextureDir(vmtVal[:-2].rstrip('_') + '_cube' + vmatDefaultVal.lstrip('_color'), fileExt = '')

                elif vmtKey in ['$basetexture3', '$basetexture4']:
                    if not LEGACY_SHADER: print("~ WARNING: 3/4-WayBlend are limited to 2 layers with the current shader", vmatShader)

                elif vmtKey in  ('$bumpmap', '$bumpmap2', '$normalmap', '$normalmap2'):
                    # all(k not in d for k in ('name', 'amount')) vmtKeyValList.keys() & ('newlayerblending', 'basetexture2', 'bumpmap2'): # >=
                    if (vmtKey != '$bumpmap2') and (vmatShader == SH_VR_SIMPLE_2WAY_BLEND or '$basetexture2' in vmtKeyValList):
                        outKey = vmatReplacement + 'A' # TextureNormal -> TextureNormalA

                    if not 'default/default' in outVal:
                        flipNormalMap(outVal)

                    # this is same as default_normal
                    #if oldVal == 'dev/flat_normal':
                    #    pass

                #elif vmtKey == '$envmapmask':
                #    # do the inverting stuff
                #    pass 

                #### DEFAULT
                #else:
                #    if vmatShader == SH_SKY: pass
                #    else: outVal = formatNewTexturePath(vmtVal, vmatDefaultVal)

            elif(keyType == 'transform'):
                if not vmatReplacement or vmatShader == SH_SKY:
                    break

                matrixList = listMatrix(vmtVal)
                msg( matrixList )
                # doesnt seem like there is rotation
                #if(matrixList[MATRIX_ROTATE] != '0.000'):
                #    if(matrixList[MATRIX_ROTATIONCENTER] != '[0.500 0.500]')

                # scale 5 5 -> g_vTexCoordScale "[5.000 5.000]"

                if matrixList[MATRIX_ROTATE]:
                    msg("HERE IT IS:", int(float(matrixList[MATRIX_ROTATE])))

                if(matrixList[MATRIX_SCALE] and matrixList[MATRIX_SCALE] != [1.000, 1.000]):
                    outKey = vmatReplacement + 'CoordScale'
                    outVal = fixVector(matrixList[MATRIX_SCALE], False)
                    vmatContent += f_KeyValQuoted.format(outKey, outVal)

                # translate .5 2 -> g_vTexCoordOffset "[0.500 2.000]"
                if(matrixList[MATRIX_TRANSLATE] and matrixList[MATRIX_TRANSLATE] != [0.000, 0.000]):
                    outKey = vmatReplacement + 'CoordOffset'
                    outVal = fixVector(matrixList[MATRIX_TRANSLATE], False)
                    vmatContent += f_KeyValQuoted.format(outKey, outVal)

                continue ## Skip default content write

            # should use reverse of the basetexture alpha channel as a self iluminating mask
            # ... why reversE???

            elif(keyType == 'channeled_masks'):
                outVmtTexture = vmt_to_vmat['channeled_masks'][vmtKey][1]

                if not vmt_to_vmat['textures'].get(outVmtTexture): break

                sourceTexture   = vmt_to_vmat['channeled_masks'][vmtKey][0] # extract as
                sourceChannel   = vmt_to_vmat['channeled_masks'][vmtKey][2] # extract from

                outKey          = vmt_to_vmat['textures'][outVmtTexture][VMAT_REPLACEMENT]
                outAddLines     = vmt_to_vmat['textures'][outVmtTexture][VMAT_EXTRALINES]
                sourceSubString = vmt_to_vmat['textures'][outVmtTexture][VMAT_DEFAULTVAL]

                if vmtKeyValList.get(outVmtTexture):
                    print("~", vmtKey, "conflicts with", outVmtTexture + ". Aborting mask extration (using original).")
                    continue

                shouldInvert    = False
                if ('1-' in sourceChannel):
                    if 'M_1-' in sourceChannel:
                        if vmtKeyValList.get('$model'): 
                            shouldInvert = True
                    else:
                        shouldInvert = True

                    sourceChannel = sourceChannel.strip('M_1-')

                # invert for brushes; if it's a model, keep the intact one ^
                # both versions are provided just in case for 'non models'
                #if not str(vmtKeyValList.get('$model')).strip('"') != '0': invert

                outVal =  createMask(sourceTexture, sourceSubString, sourceChannel, shouldInvert)

            elif keyType == 'SystemAttributes':
                lines_SysAtributes.append(f_KeyValQuoted.format(outKey, outVal))
                continue

            elif keyType == 'others2':
                continue ### Skip default content write
            
            if(outAddLines): outAddLines = '\n\t' + outAddLines + '\n'

            #############################
            ### Default content write ###
            vmatContent += outAddLines + f_KeyValQuoted.format(outKey, outVal)

            if DEBUG:
                #if(outVal.endswith(TEXTURE_FILEEXT)): outVal = formatFullDir(outVal)
                msg( vmtKey + ' "' + vmtVal + '" -> ' + outKey + ' ' + outVal.replace('\t', '').replace('\n', '') + ' ' + outAddLines.replace('\t', '').replace('\n', ''))

            # dont break some keys have more than 1 translation (e.g. $selfillum)

    if lines_SysAtributes:
        vmatContent += '\n\tSystemAttributes\n\t{\n'
        
        for line in lines_SysAtributes:
            vmatContent += '\t' + line
        
        vmatContent += '\t}\n'

    return vmatContent

def convertSpecials(vmtKeyValList):

    # fix phongmask logic
    if vmtKeyValList.get("$phong") == '1' and not vmtKeyValList.get("$phongmask"):
        bHasPhongMask = False
        for key, val in vmt_to_vmat['channeled_masks'].items():
            if val[1] == '$phongmask' and vmtKeyValList.get(key):
                bHasPhongMask = True
                break
        if not bHasPhongMask: # normal map Alpha acts as a phong mask by default
            vmtKeyValList.setdefault('$normalmapalphaphongmask', '1')

    # csgo viewmodels
    if "models\\weapons\\v_models" in fileName:
        # use _ao texture in \weapons\customization\
        weaponDir = os.path.dirname(fileName)
        weaponPathSplit = fileName.split("\\weapons\\v_models\\")
        weaponPathName = os.path.dirname(weaponPathSplit[1])
        msg(weaponPathName + INPUT_FILE_EXT)
        if fileName.endswith(weaponPathName + INPUT_FILE_EXT) or fileName.endswith(weaponPathName.split('_')[-1] + INPUT_FILE_EXT):
            aoTexturePath = os.path.normpath(weaponPathSplit[0] + "\\weapons\\customization\\" + weaponPathName + '\\' + weaponPathName + "_ao" + TEXTURE_FILEEXT)
            aoNewPath = os.path.normpath(weaponDir + "\\" + weaponPathName + TEXTURE_FILEEXT)
            msg(aoTexturePath)
            if os.path.exists(aoTexturePath):
                msg(aoNewPath)
                if not os.path.exists(aoNewPath):
                    #os.rename(aoTexturePath, aoNewPath)
                    copyfile(aoTexturePath, aoNewPath)
                    print("+ Succesfully moved AO texture for weapon material:", weaponPathName)
                vmtKeyValList["$aotexture"] = formatVmatDir(aoNewPath).replace('materials\\', '')
                print("+ Using ao:", weaponPathName + "_ao" + TEXTURE_FILEEXT)

        #vmtKeyValList.setdefault("$envmap", "0") # specular looks ugly on viewmodels so disable it. does not affect scope lens

failures = []
invalids = 0
listsssss = []

#######################################################################################
# Main function, loop through every .vmt
##
for fileName in fileList:
    msg("Reading file:", fileName)
    vmtKeyValList = {}
    matType = ''
    vmatShader = ''
    vmatFileName = ''
    validMaterial = False
    validPatch = False
    skipNextLine = False
    
    with open(fileName, 'r') as vmtFile:
        row = 0
        for line in vmtFile:
            
            line = line.strip().split("//", 1)[0]
            
            if not line or line.startswith('/'):
                continue
            #rawline = line.lower().replace('"', '').replace("'", "").replace("\n", "").replace("\t", "").replace("{", "").replace("}", "").replace(" ", "")/[^a-zA-Z]/
            if row < 1:
                matType = re.sub(r'[^A-Za-z0-9_-]', '', line).lower()
                if any(wd in matType for wd in materialTypes):
                    validMaterial = True
                
            if skipNextLine:
                if "]" in line or "}" in line:
                    skipNextLine = False
            else:
                parseVMTParameter(line, vmtKeyValList)
            
            if any(line.lower().endswith(wd) for wd in ignoreList): # split at // take the before part
                msg("Skipping {} block:", line)
                skipNextLine = True
            
            row += 1

    if matType == 'patch':
        includeFile = vmtKeyValList.get("include")
        if includeFile:
            includeFile = includeFile.replace('"', '').replace("'", '').strip()
            if includeFile == 'materials\\models\\weapons\\customization\\paints\\master.vmt':
                continue

            print("+ Patching material details from include:", includeFile, end='')
            try:
                with open(formatFullDir(includeFile), 'r') as vmtFile:
                    oldVmtKeyValList = vmtKeyValList.copy()
                    vmtKeyValList.clear()
                    for line in vmtFile.readlines():
                        if any(wd in line.lower() for wd in materialTypes):
                            print('... Valid patch!!')
                            validPatch = True
                        
                        line = line.strip()
                        parseVMTParameter(line, vmtKeyValList)
                    
                    vmtKeyValList.update(oldVmtKeyValList)
            
            except FileNotFoundError:
                failures.append(includeFile + " - inexistent as an include")
                print("\n~ Skipping patch! Couldn't find include file from patch.")
                continue
                    
            if not validPatch:
                print("... Unsupported shader.")
                # matType = 
                #continue
        else:
            print("~ WARNING: No include was provided on material with type 'Patch'. Is it a weapon skin?")
        
    vmatFileName = fileName.replace(INPUT_FILE_EXT, '') + OUTPUT_FILE_EXT
    vmatShader = chooseShader(matType, vmtKeyValList, fileName)

    skyboxName = os.path.basename(fileName).replace(INPUT_FILE_EXT, '')#[-2:]
    skyboxName, skyboxFace = [skyboxName[:-2], skyboxName[-2:]]
    #skyboxName, skyboxFace = skyboxName.rsplit(skyboxName[-2:-1], 1)
    #skyboxFace = skyboxName[-2:-1] + skyboxFace
    if((('\\skybox\\' in fileName) or ('/skybox/' in fileName)) and (skyboxFace in skyboxFaces)): # and shader
        if skyboxName not in skyboxPath:
            skyboxPath.setdefault(skyboxName, {'up':{}, 'dn':{}, 'lf':{}, 'rt':{}, 'bk':{}, 'ft':{}})
        for face in skyboxFaces:
            if(skyboxFace != face): continue
            
            facePath = vmtKeyValList.get('$hdrbasetexture') or vmtKeyValList.get('$hdrcompressedtexture') or vmtKeyValList.get('$basetexture')
            if(facePath and os.path.exists(formatFullDir(formatNewTexturePath(facePath, noRename= True)))):
                skyboxPath[skyboxName][face]['path'] = formatNewTexturePath(facePath, noRename= True)
                msg("Collecting", face, "sky face", skyboxPath[skyboxName][face]['path'])
            faceTransform = listMatrix(vmtKeyValList.get('$basetexturetransform'))
            
            if(faceTransform and faceTransform[MATRIX_ROTATE]):
                skyboxPath[skyboxName][face]['rotate'] = int(float(faceTransform[MATRIX_ROTATE]))
                msg("Collecting", face, "transformation", skyboxPath[skyboxName][face]['rotate'], 'degrees')

            # skip vmat for dn, lf, rt, bk, ft
            # TODO: ok we might need the vmats for all of them because they might be used somewhere else
            vmatShader = SH_SKY
            vmatFileName = vmatFileName.replace(face + '.vmat', '').rstrip('_') + '.vmat'
            if face != 'bk': validMaterial = False


    if validMaterial:
        if os.path.exists(vmatFileName) and not OVERWRITE_EXISTING_VMAT:
            print('+ File already exists. Skipping!')
            continue

        with open(vmatFileName, 'w') as vmatFile:
            vmatFile.write('// Converted with vmt_to_vmat.py\n')
            vmatFile.write('// From: ' + fileName + '\n\n')
            msg(matType + " => " + vmatShader)
            vmatFile.write('Layer0\n{\n\tshader "' + vmatShader + '.vfx"\n\n')

            convertSpecials(vmtKeyValList)

            vmatFile.write(convertVmtToVmat(vmtKeyValList)) ###############################

            vmatFile.write('}\n')

        if DEBUG: print("+ Saved", vmatFileName)
        else: print("+ Saved", formatVmatDir(vmatFileName))
        #print ('---------------------------------------------------------------------------')
    
    else: invalids += 1


    if not matType:
        if DEBUG: debugContent += "Warning" + fileName + '\n'

print("\nDone with the materials...\nNow onto the images that need processing...")

for Call in Late_Calls:
    DEBUG = True
    Call[0]( *Call[1] )

########################################################################
# Build skybox cubemap from sky faces
# (blue_sky_up.tga, blue_sky_ft.tga, ...) -> blue_sky_cube.tga
# https://developer.valvesoftware.com/wiki/File:Skybox_Template.jpg
# https://learnopengl.com/img/advanced/cubemaps_skybox.png
for skyName in skyboxPath:

    #if True: break
    # what is l4d2 skybox/sky_l4d_rural02_ldrbk.pwl
    # TODO: decouple this in a separate script. face_to_cubemap_sky.py
    # write the sky face contents in a text file. allow manual sky map creation

    # TODO: !!!!! HOW DO I DO HDR FILES !!!!! '_cube.exr'
    # idea: convert to tiff

    faceCount = 0
    facePath = ''
    SkyCubeImage_Path = ''
    for face in skyboxFaces:
        facePath = skyboxPath[skyName][face].get('path')
        if not facePath: continue
        faceImage = Image.open(formatFullDir(facePath))

        if not faceImage: continue
        if((not skyboxPath[skyName][face].get('scale') or len(skyboxFaces) == skyboxFaces.index(face)+1) and (not skyboxPath[skyName][face].get('resolution'))):
            skyboxPath[skyName]['resolution'] = faceImage.size
        skyboxPath[skyName][face]['image'] = faceImage
        faceCount += 1

    if not faceCount or not skyboxPath[skyName]['resolution']:
        failures.append("skybox/" + skyName)
        continue

    face_w = face_h = skyboxPath[skyName]['resolution'][0]
    cube_w = 4 * face_w
    cube_h = 3 * face_h
    SkyCubeImage = Image.new('RGBA', (cube_w, cube_h), color = (0, 0, 0)) # alpha?

    for face in skyboxFaces:
        faceImage = skyboxPath[skyName][face].get('image')
        if not faceImage: continue
        facePath = formatFullDir(skyboxPath[skyName][face]['path'])

        faceScale = skyboxPath[skyName][face].get('scale')
        faceRotate = skyboxPath[skyName][face].get('rotate')

        vtfTexture = facePath.replace(TEXTURE_FILEEXT, '') + '.vtf'
        if REMOVE_VTF_FILES and os.path.exists(vtfTexture):
            os.remove(vtfTexture)
            print("~ Removed vtf file: " + formatVmatDir(vtfTexture))

        # TODO: i think top and bottom need to be rotated by 90 + side faces offset by x
        # -- check if front is below top and above bottom
        # + move this inside the dict
        # Ahhhh https://github.com/TheAlePower/TeamFortress2/blob/1b81dded673d49adebf4d0958e52236ecc28a956/tf2_src/utils/splitskybox/splitskybox.cpp#L172
        if face == 'up':   facePosition = ( cube_w - (face_w * 3) , cube_h - (face_h * 3) )
        elif face == 'ft': facePosition = ( cube_w - (face_w * 2) , cube_h - (face_h * 2) )
        elif face == 'lf': facePosition = ( cube_w - (face_w * 1) , cube_h - (face_h * 2) )
        elif face == 'bk': facePosition = ( cube_w - (face_w * 4) , cube_h - (face_h * 2) )
        elif face == 'rt': facePosition = ( cube_w - (face_w * 3) , cube_h - (face_h * 2) )
        elif face == 'dn': facePosition = ( cube_w - (face_w * 3) , cube_h - (face_h * 1) )

        if faceImage.width != face_w:
            faceImage = faceImage.resize((face_w, round(faceImage.height * face_w/faceImage.width)), Image.BICUBIC)

        if(skyboxPath[skyName][face].get('rotate')):
            msg("ROTATING `" + face + "` BY THIS: " + str(skyboxPath[skyName][face]['rotate']))
            faceImage = faceImage.rotate(int(skyboxPath[skyName][face]['rotate']))

        
        SkyCubeImage.paste(faceImage, facePosition)
        faceImage.close()

    if facePath:
        SkyCubeImage_Path = facePath.replace(TEXTURE_FILEEXT, '')[:-2].rstrip('_') + '_cube' + TEXTURE_FILEEXT
        SkyCubeImage.save(SkyCubeImage_Path)

    if os.path.exists(SkyCubeImage_Path):
        print('+ Successfuly created sky cubemap:' + os.path.basename(SkyCubeImage_Path))

if True: # STATISTICS
    invalids
    print("\n\t<<<< THESE MATERIALS HAVE ERRORS >>>>\n\n")
    for failure in failures:
        print(failure)
    print(f"\n\t^^^^ THESE MATERIALS HAVE ERRORS ^^^^\n\nTotal errors :\t{len(failures)} / {len(fileList)}\t| " + "{:.2f}".format((len(failures)/len(fileList)) * 100) + f" % Error rate (!!)")
    print(f"Total ignores :\t{invalids} / {len(fileList)}\t| " + "{:.2f}".format((invalids/len(fileList)) * 100) + f" % Invalid rate")


print("\nFinished! Your materials are now ready.")
