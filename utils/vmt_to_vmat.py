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
# or `python vmt_to_vmat.py input_path output_path`

# This version of vmt_to_vmat has been modified with some configurability in mind
# and is currently suited for CS:GO materials.
#
# This version insists on renaming all of the textures so please be warned.
# That means any texture.tga will be renamed into texture_color.tga and so on.
#
#  Translation table is found at vmt_to_vmat below

import sys
import os
import os.path
from os import path
import shutil
from shutil import copyfile
from difflib import get_close_matches
import re
from PIL import Image
import PIL.ImageOps
from time import sleep
import json

# generic, blend instead of vr_complex, vr_2wayblend etc...
# blend doesn't seem to work though. why...
USE_OLD_SHADERS = False
newshader = not USE_OLD_SHADERS

# File format of the textures. Needs to be lowercase
TEXTURE_FILEEXT = '.tga'

# make sure to remember the final slash!!
PATH_TO_CONTENT_ROOT = ""
#PATH_TO_NEW_CONTENT_ROOT = ""

# Set this to True if you wish to overwrite your old vmat files
OVERWRITE_VMAT = True

REMOVE_VTF_FILES = True
# Set this to True if you wish to do basic renaming of your textures
# texture.tga, texture_color.tga -> texture_color.tga
RENAME_TEXTURES = True
FINE_RENAME = 2

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
        #print("~ ERROR: Cannot recognize shader " + matType + ". Set to VR_BLACK_UNLIT")
        return SH_VR_BLACK_UNLIT

    #TODO: if containts values starting with _rt_ give some empty shader
    
    if USE_OLD_SHADERS:   shaders[SH_GENERIC] += 1
    else:                   shaders[materialTypes[matType]] += 1

    # BUG: sprites/crosshairs sun/overlay are becoiming sky when they shhouldn't
    if matType == "unlitgeneric":

        if '\\skybox\\' in fileName or '/skybox/' in fileName: shaders[SH_SKY] += 4 # 95% correct
        if "$nofog" in vmtKeyValList: shaders[SH_SKY] += 1
        if "$ignorez" in vmtKeyValList: shaders[SH_SKY] += 2
        
        # ofc there will be some sky vmt that has one of these for no damn reason
        if "$receiveflashlight" in vmtKeyValList: shaders[SH_SKY] -= 6
        if "$alphatest" in vmtKeyValList: shaders[SH_SKY] -= 6
        if "$additive" in vmtKeyValList: shaders[SH_SKY] -= 3
        if "$vertexcolor" in vmtKeyValList: shaders[SH_SKY] -= 3
        # translucent
    
    elif matType == "worldvertextransition":
        if vmtKeyValList.get('$basetexture2'): shaders[SH_VR_SIMPLE_2WAY_BLEND] += 69
        else: print("~ ERROR: WTF")

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
    #, #TODO: make this system functional
    #"modulate",
}

ignoreList = [
"vertexlitgeneric_hdr_dx9",
"vertexlitgeneric_dx9",
"vertexlitgeneric_dx8",
"vertexlitgeneric_dx7",
"lightmappedgeneric_hdr_dx9",
"lightmappedgeneric_dx9",
"lightmappedgeneric_dx8",
"lightmappedgeneric_dx7",
"unlitgeneric_dx7",
"unlitgeneric_dx6",
]

surfprop_repl = {
    'stucco':       'world.drywall',
    'tile':         'world.tile_floor',
    'metalpanel':   'world.metal_panel',
    'wood':         'world.wood_solid',
}
surfprop_HLA = ['npc_antlion_abdomen','npc_antlion_armor','npc_antlion_flesh','npc_antlion_worker_abdomen','npc_antlion_worker_flesh','npc_barnacle_flesh','npc_blindzombie_body','npc_boomerplant','npc_combine_grunt_gastank']

QUOTATION = '"'
COMMENT = "// "
debugContent = ''
debugList = []

# and "asphalt_" in fileName
def parseDir(dirName):
    files = []
    skipdirs = ['dev', 'debug', 'tools', 'vgui', 'console', 'correction']
    for root, _, fileNames in os.walk(dirName):
        for skipdir in skipdirs:
            if ('materials\\' + skipdir) in root: continue
        #if not root.endswith(r'materials\skybox'): continue
        for fileName in fileNames:
            if fileName.lower().endswith('.vmt'): # : #
                files.append(os.path.join(root,fileName))

    return files

###
### Main Execution
###

#currentDir = os.getcwd()

#currentDir = r"D:\Users\kristi\Desktop\WORK\MOD\content\hlvr"
#currentDir = r"D:\Users\kristi\Desktop\WORK\test\here"
currentDir =r"D:\Program Files (x86)\Steam\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo"

if not PATH_TO_CONTENT_ROOT:
    if(len(sys.argv) >= 2):
        PATH_TO_CONTENT_ROOT = sys.argv[1]
    else:
        #print("here: " + PATH_TO_CONTENT_ROOT)
        while not PATH_TO_CONTENT_ROOT:
            c = input('Type the root directory of the vmt materials you want to convert (enter to use current directory, q to quit).: ') or currentDir
            if not path.isdir(c):
                if c in ('q', 'quit', 'exit', 'close'):
                    quit()
                print('Could not find directory.')
                continue
            PATH_TO_CONTENT_ROOT = c.lower().strip().strip('"')
            #print(PATH_TO_CONTENT_ROOT)
"""
if not PATH_TO_NEW_CONTENT_ROOT:
    if(len(sys.argv) >= 3):
        PATH_TO_NEW_CONTENT_ROOT = sys.argv[2]
    else:
        while not PATH_TO_NEW_CONTENT_ROOT:
            c = input('Type the directory you wish to output Source 2 materials to (enter to use the same dir): ') or currentDir
            if(c == currentDir):
                PATH_TO_NEW_CONTENT_ROOT = PATH_TO_CONTENT_ROOT # currentDir
            else:
                if not path.isdir(c):
                    if c in ('q', 'quit', 'exit', 'close'):
                        quit()
                    print('Could not find directory.')
                    continue
                PATH_TO_NEW_CONTENT_ROOT = c.lower().strip().strip('"')
"""
PATH_TO_CONTENT_ROOT = os.path.normpath(PATH_TO_CONTENT_ROOT) + '\\'
#PATH_TO_NEW_CONTENT_ROOT =  os.path.normpath(PATH_TO_NEW_CONTENT_ROOT) + '\\'

print('\nSource 2 Material Conveter! By Rectus via Github.')
print('Initially forked by Alpyne, this version by caseytube.\n')
print('+ Reading old materials from: ' + PATH_TO_CONTENT_ROOT)
#print('+ New materials will be created in: ' + PATH_TO_NEW_CONTENT_ROOT)
print('--------------------------------------------------------------------------------------------------------')


# "environment maps/metal_generic_002" -> "materials/environment maps/metal_generic_002(.tga)"
def formatVmtTextureDir(localPath, fileExt = TEXTURE_FILEEXT):
    if localPath.endswith(fileExt): fileExt = ''
    localPath = 'materials/' + localPath.strip().strip('"') + fileExt
    localPath = localPath.replace('\\', '/') # Convert paths to use forward slashes.
    localPath = localPath.replace('.vtf', '')#.replace('.tga', '') # remove any old extensions
    localPath = localPath.lower()

    return localPath

# materials/texture_color.tga -> C:/Users/User/Desktop/stuff/materials/texture_color.tga
def formatFullDir(localPath):
    return os.path.abspath(os.path.join(PATH_TO_CONTENT_ROOT, localPath))

# inverse of formatFullDir()
def formatVmatDir(localPath):
    if not localPath: return None
    localPath = os.path.normpath(localPath)
    return localPath.replace(PATH_TO_CONTENT_ROOT, '')

def vmatContentRecord(path):
    #debugContent += path
    return path

def textureAddSubStr(str1, str2):
    if str1.endswith(str2):
        return str1
    #str1 += str2
    return str1 + str2

# -------------------------------
# Returns correct path, checks if alreay exists, renames with proper extensions, etc...
# -------------------------------
def formatNewTexturePath(vmtPath, textureType = TEXTURE_FILEEXT, noRename = False, forReal = True):

    global debugContent
    global debugList
    newName = ''
    
    subStr = textureType[:-4]#textureType.replace(TEXTURE_FILEEXT, '')
    #breakpoint()
    # BUG: D:\Program Files (x86)\Steam\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo\materials\models\props\de_dust\hr_dust\dust_electric_panel
    # some secndary materials are renamed to _refl.tga when they should be _color.tga -- not necessarily secondary materials
    # dust_electric_panel_cover_color_refl.tga materials\models\props\de_dust\hr_dust\dust_garbage_container\dust_garbage_dumpster_color
    # _color is being used as reflectivity as well as albedo resulting in it being renamed. This should be the root of these all. please FIXME
    # FIXME proposal: if material ends with a DEFAULT_VALUE tag other than the current tag do makeCopy = True
    # this fixes _color_refl.tga -- but theres also those that arent originally color and have had to be renamed.

    # and Error loading resource file "materials/models/props/de_dust/hr_dust/dust_lights/street_lantern_03/street_lantern_03_color.vmat_c" (Error: ERROR_FILEOPEN)
    # same as the _normal problem?
    if vmtPath == '': return 'materials/default/default' + textureType

    vtfTexture = formatFullDir(formatVmtTextureDir(vmtPath + '.vtf', '') + '.vtf')
    if REMOVE_VTF_FILES and os.path.exists(vtfTexture):
        os.remove(vtfTexture)
        print("~ Removed vtf file: " + formatVmatDir(vtfTexture))


    # "newde_cache/nc_corrugated" -> materials/newde_cache/nc_corrugated
    textureLocal = formatVmtTextureDir(vmtPath, '')
    #textureLocal = textureLocal.lower()

    # no rename
    if not RENAME_TEXTURES  or noRename or not subStr or fileName.endswith('_normal.vmt'):
        return textureLocal + TEXTURE_FILEEXT
    # simple rename
    elif not FINE_RENAME: newName = textureLocal + textureType
    # processed rename
    else:
        oldName = os.path.basename(textureLocal)
        newName = textureAddSubStr(oldName, subStr)

        if newName == oldName: return textureLocal + TEXTURE_FILEEXT #return (os.path.normpath(os.path.dirname(textureLocal) + '/' + newName + TEXTURE_FILEEXT)).replace('\\', '/')
        if textureType == "_color.tga" and textureLocal.endswith('_normal'):
            print("@ DBG:", "FIXED NORMAL")
            return textureRename(textureLocal.rstrip(TEXTURE_FILEEXT) + "_color", textureLocal + '.tga', textureType)
        replList = {'refl':'mask', 'normal':'bump'}
        if subStr[1:] in replList and replList[subStr[1:]] in oldName:
            newName = ''.join(oldName.rsplit(replList[subStr[1:]], 1)).rstrip('_') + subStr

        for i in range(1, len(subStr[1:])):
            if textureLocal.endswith(subStr[:-i]) or (textureLocal.endswith(subStr[1:-i]) and i < 3): # i < 3 no underscore needs 3 letters minimum: texturedet
                if i == len(subStr[1:])-1 and FINE_RENAME > 1:
                    newName = ''.join(oldName.rsplit(subStr[1:-i], 1)).rstrip('_') + subStr[1:-i] + subStr
                else:
                    newName = ''.join(oldName.rsplit(subStr[1:-i], 1)).rstrip('_') + subStr

                debugContent += "1 "
                break
            if i < (len(subStr[1:]) - 1): continue
            if oldName[:-1].endswith(subStr[1:]):
                if FINE_RENAME == 2: newName = ''.join(oldName[:-1].rsplit(subStr[1:], 1)).rstrip('_') + subStr
                else: newName = ''.join(oldName[:-1].rsplit(subStr[1:], 1)).rstrip('_') + subStr[-1:] + subStr
                debugContent += "2 "
            elif subStr[1:] in oldName:
                debugContent += "3 "
                if subStr in oldName: newName = ''.join(oldName.rsplit(subStr, 1)).rstrip('_') + subStr
                else: newName = ''.join(oldName.rsplit(subStr[1:], 1)).rstrip('_') + subStr

        newName = (os.path.normpath(os.path.dirname(textureLocal) + '/' + newName + TEXTURE_FILEEXT)).replace('\\', '/')

        if forReal:
            debugContent += os.path.basename(textureLocal) + ' -> ' + newName + '\n'

    if not forReal: return newName
    
    outVmatTexture =  textureRename(textureLocal, newName, textureType) or ('materials/default/default' + textureType)

    if 'materials/default/default' in outVmatTexture:
        print("~ ERROR: Could not find texture: " + formatFullDir(textureLocal))

    return outVmatTexture

#renamedTexturesCache = dict()
def textureRename(localPath, newNamePath, textureType, makeCopy = False):

    if 'skybox' in localPath:
        return localPath

    localPath = formatFullDir(localPath)

    if not localPath.endswith(TEXTURE_FILEEXT):
        localPath += TEXTURE_FILEEXT

    # TODO: this is a temporary fix
    #if(os.path.exists(localPath.rstrip(TEXTURE_FILEEXT))):
    #    if not os.path.exists(localPath):
    #        os.rename(localPath.rstrip(TEXTURE_FILEEXT), localPath)

    newNamePath = formatFullDir(newNamePath)
    
    if(os.path.exists(newNamePath)):
        # don't need this, temporary fix only
        #if os.path.exists(localPath) and not makeCopy:
        #    os.remove(localPath)
        return formatVmatDir(newNamePath)

    # TODO: check if image is used for another map so we don't interfere. if it is we should make a copy/should not rename at all.
    # FUCKKKKK THISSSSS
    
    if not os.path.exists(localPath):
        print("+ Could not find texture " + localPath + " set to be renamed into: " + newNamePath.split('/')[-1])
 
        for key in list(vmt_to_vmat['textures']):
            #if os.path.exists(localPath[:-4] + vmt_to_vmat['textures'][key][VMAT_DEFAULT]):
            tryPath = formatFullDir(formatNewTexturePath(formatVmatDir(localPath[:-4]), vmt_to_vmat['textures'][key][VMAT_DEFAULT], forReal = False))
            print("@ DBG: checking for", tryPath)
            if os.path.exists(tryPath):
                makeCopy = True
                localPath = localPath[:-4] + vmt_to_vmat['textures'][key][VMAT_DEFAULT]
                print("+ Nevermind... found a renamed copy! " + formatVmatDir(localPath))
                print("+ However, we shouldn't have had to search for it. Check if material's using same image for more than one map.")
                break
        
        if not os.path.exists(localPath):
            print("+ Please check!")
            return None
    else:
        if textureType != 'color.tga':
            for key in list(vmt_to_vmat['textures']):
                postFix = vmt_to_vmat['textures'][key][VMAT_DEFAULT]
                if postFix != textureType[:-4] and localPath.endswith(postFix):
                    #localPath = ''.join(localPath.rsplit(postFix, 1)) -- NO, localpath exists and I should not touch it.
                    # output should be texture_color_{postfix} while texture_color remains untouched.
                    print("@ DBG:", "Problematic two map one image detected. Copying", localPath, "->", newNamePath)
                    #sleep(5.0)
                    makeCopy = True
                    break
    try:
        if not makeCopy:
            os.rename(localPath, newNamePath)
            #print("+ Renamed new texture to " + formatVmatDir(localPath))
        else:
            copyfile(localPath, newNamePath)
            #print("+ Copied new texture to " + formatVmatDir(localPath))
        
    
    except FileExistsError:
        print("+ Could not rename " + formatVmatDir(localPath) + ". Renamed copy already exists")
    
    except FileNotFoundError:
        if(not os.path.exists(newNamePath)):
            print("~ ERROR: couldnt find")

    if os.path.exists(localPath) and not makeCopy:
        os.remove(localPath)

    return formatVmatDir(newNamePath)

# -------------------------------
# Returns texture path of given vmtParam, texture which has likely been renamed to be S2 naming compatible
# $basetexture  ->  materials/path/to/texture_color.tga of the TextureColor
# -------------------------------
def getTexture(vmtParam):
    # if we get a list choose from the one that exists
    texturePath = ''
    if isinstance(vmtParam, tuple):
        for actualParam in vmtParam:
            if vmtKeyValList.get(actualParam):
                texturePath = formatNewTexturePath(vmtKeyValList[actualParam], vmt_to_vmat['textures'][actualParam][VMAT_DEFAULT], forReal=False)
                if not os.path.exists(formatFullDir(texturePath)):
                    texturePath = formatVmtTextureDir(vmtKeyValList[actualParam])

    elif vmtKeyValList.get(vmtParam):
        texturePath = formatNewTexturePath(vmtKeyValList[vmtParam], vmt_to_vmat['textures'][vmtParam][VMAT_DEFAULT], forReal=False)
        if not os.path.exists(formatFullDir(texturePath)):
            texturePath = formatVmtTextureDir(vmtKeyValList[vmtParam])

    if not os.path.exists(formatFullDir(texturePath)): texturePath = None # ''

    return texturePath

# Verify file paths
fileList = []
if(PATH_TO_CONTENT_ROOT):
    absFilePath = os.path.abspath(os.path.join(PATH_TO_CONTENT_ROOT, 'materials'))
    
    if os.path.isdir(absFilePath):
        fileList.extend(parseDir(absFilePath))
    
    elif(absFilePath.lower().endswith('.vmt')):
        fileList.append(absFilePath)
    
else:
    input("No directory specified, press any key to quit...")
    quit()

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
            print("@ DBG: Trying using the high-shader parameter.")
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

# TODO: delete original images that are unused at the end of the script
def createMaskFromChannel(vmtTexture, channel = 'A', copySub = '_mask.tga', invert = True):
    if not os.path.exists(vmtTexture):
        vmtTexture = formatFullDir(vmtTexture)

    if invert:  newMaskPath = vmtTexture[:-4] + '_' + channel + '-1' + copySub
    else:       newMaskPath = vmtTexture[:-4] + '_' + channel        + copySub
    
    if os.path.exists(newMaskPath):
        return formatVmatDir(newMaskPath)

    if os.path.exists(vmtTexture):
        image = Image.open(vmtTexture).convert('RGBA')
        imgChannel = image.getchannel(str(channel))

        # Create a new image with an opaque black background
        bg = Image.new("RGBA", image.size, (0,0,0,255))

        # Copy the alpha channel to the new image using itself as the mask
        bg.paste(imgChannel)
        
        if invert:
            r,g,b,_ = bg.split()
            rgb_image = Image.merge('RGB', (r,g,b))
            inverted_image = PIL.ImageOps.invert(rgb_image)

            r2,g2,b2 = inverted_image.split()
            final_transparent_image = Image.merge('RGB', (r2,g2,b2)).convert('RGBA')
            
            final_transparent_image.save(newMaskPath)
            final_transparent_image.close()
        else:
            bg.save(newMaskPath)
            bg.close()
            
    else:
        print("~ ERROR: Couldn't find requested image (" + vmtTexture + "). Please check.")
        #vmatContent += '\t' + COMMENT + 'Missing ' + formatVmatDir(vmtTexture) + '\n'
        return 'materials/default/default' + copySub

    print("+ Saved mask to" + formatVmatDir(newMaskPath))
    return formatVmatDir(vmatContentRecord(newMaskPath))

def flipNormalMap(localPath, tradeFileSizeForProcessing = True):

    image_path = formatFullDir(localPath)

    if tradeFileSizeForProcessing:
        with open(formatFullDir(localPath[:-4] + '.txt'), 'w') as settingsFile:
            settingsFile.write('"settings"\n{\t"legacy_source1_inverted_normal" "1"\n}')

    elif path.exists(image_path):
        # Open the image and convert it to RGBA, just in case it was indexed
        image = Image.open(image_path).convert('RGBA')

        # Extract just the green channel
        r,g,b,a = image.split()

        g = PIL.ImageOps.invert(g)

        final_transparent_image = Image.merge('RGBA', (r,g,b,a))

        final_transparent_image.save(image_path)

    return localPath

skyboxPath = {}
skyboxFaces = ['up', 'dn', 'lf', 'rt', 'bk', 'ft']

def fixIntVector(s, needsAlpha = True, replicateSingle = 0):
    # {255 175 255}
    likelyColorInt = False
    likelySingle = False
    if('{' in s and '}' in s):
        likelyColorInt = True
    elif('[' not in s and ']' not in s):    
        likelySingle = True

    s = s.strip()
    s = s.strip('"' + "'")
    s = s.strip().strip().strip('][}{')

    try: originalValueList = [str(float(i)) for i in s.split(' ') if i != '']
    except: return None 
    # [4] -> [4.000000 4.000000]
    if(replicateSingle and likelySingle and len(originalValueList) <= 1):
        for _ in range(replicateSingle):
            originalValueList.append(originalValueList[0])
    
    # [255 175 255] -> [255 175 255 1.000]
    if(needsAlpha): originalValueList.append(1.0) # alpha
    
    # [255 128 255 1.000] -> [1.000000 0.500000 1.000000 1.000000]
    for strvalue in originalValueList:
        #if(needsAlpha and originalValueList.index(strvalue) > 2): break
        flvalue = float(strvalue)
        if likelyColorInt and originalValueList.index(strvalue) < 3:
            flvalue /= 255
        
        originalValueList[originalValueList.index(strvalue)] = "{:.6f}".format(flvalue)

    #print (originalValueList)
    return '[' + ' '.join(originalValueList) + ']'

def is_convertible_to_float(value):
  try:
    float(value)
    return True
  except:
    return False

MATRIX_ROTATIONCENTER = 0
MATRIX_SCALE = 1
MATRIX_ROTATE = 2
MATRIX_TRANSLATE = 3

def listMatrix(s):
    # [0, 1] center defines the point of rotation. Only useful if rotate is being used.
    # [2, 3] scale fits the texture into the material the given number of times. '2 1' is a 50% scale in the X axis.
    # [4]    rotate rotates the texture counter-clockwise in degrees. Accepts any number, including negatives.
    # [5, 6] translate shifts the texture by the given numbers. '.5' will shift it half-way.

    # Assuming you can't use these individually as "rotate 4" /// TODO: welp you can
    # $detailtexturetransform "center .5 .5 scale 1 1 rotate 0 translate 0 0"
    # -> [0.5, 0.5, 1.0, 1.0, 0.0, 0.0, 0.0]
    s = s.strip('"')
    valueList = [float(str(i)) for i in s.split(' ') if is_convertible_to_float(i)]

    # -> ['[0.5 0.5]', '[1.0 1.0]', '0.0', '[0.0 0.0]']
    return ['[' + "{:.3f}".format(valueList[0]) + ' ' + "{:.3f}".format(valueList[1]) + ']',\
            '[' + "{:.3f}".format(valueList[2]) + ' ' + "{:.3f}".format(valueList[3]) + ']',\
                  "{:.3f}".format(valueList[4]),\
            '[' + "{:.3f}".format(valueList[5]) + ' ' + "{:.3f}".format(valueList[6]) + ']'\
            ]

normalmaps = ('$normal', '$bumpmap', '$bumpmap2')

VMAT_REPLACEMENT = 0
VMAT_DEFAULT = 1
VMAT_EXTRALINES = 2

# TODO: Eliminate hardcoded file extensions throughout the entire code.
vmt_to_vmat = {
    'textures': {

        '$hdrcompressedtexture':('SkyTexture',          '.pfm',             'F_TEXTURE_FORMAT2 6 // BC6H (HDR compressed - recommended)'),
        '$hdrbasetexture':      ('SkyTexture',          '.pfm',             ''),
        
        ## Layer0 
        '$basetexture':         ('TextureColor',        '_color'+TEXTURE_FILEEXT,       ''), # SkyTexture
        '$painttexture':        ('TextureColor',        '_color'+TEXTURE_FILEEXT,       ''),
        '$bumpmap':             ('TextureNormal',       '_normal'+TEXTURE_FILEEXT,      ''),
        '$normalmap':           ('TextureNormal',       '_normal'+TEXTURE_FILEEXT,      ''),
        # 210 is default roughness in s1 [210/255 210/255 210/255 1.000]
        #'$phongexponenttexture':('TextureRoughness',    '_rough'+TEXTURE_FILEEXT,       '') if newshader else ('TextureGlossiness', '_gloss.tga', 'F_ANISOTROPIC_GLOSS 1\n'),
        ## Layer1
        '$basetexture2':        ('TextureColorB',       '_color'+TEXTURE_FILEEXT,       '') if newshader else ('TextureLayer1Color', '_color.tga', ''),
        '$bumpmap2':            ('TextureNormalB',      '_normal'+TEXTURE_FILEEXT,      '') if newshader else ('TextureLayer1Normal', '_normal.tga', 'F_BLEND_NORMALS 1'),
        #'$phongexponent2':      ('TextureRoughnessB',   '_rough'+TEXTURE_FILEEXT,       ''), # $phongmaskcontrastbrightness2, $phongbasetint2, $phongamount2

        ## Layer2-3
        '$basetexture3':        ('TextureLayer2Color',  '_color'+TEXTURE_FILEEXT,       ''),
        '$basetexture4':        ('TextureLayer3Color',  '_color'+TEXTURE_FILEEXT,       ''),

        '$blendmodulatetexture':('TextureMask', '_mask.tga', 'F_BLEND 1') if newshader else ('TextureLayer1RevealMask', '_blend.tga',   'F_BLEND 1'),
        
        #'$texture2':            ('',  '_color.tga',       ''), # UnlitTwoTexture
        '$normalmap2':          ('TextureNormal2',      '_normal.tga',      'F_SECONDARY_NORMAL 1'), # used with refract shader
        '$flowmap':             ('TextureFlow',         TEXTURE_FILEEXT,    'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 1'),
        '$flow_noise_texture':  ('TextureNoise',        '_noise.tga',       'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 2'),
        '$detail':              ('TextureDetail',       '_detail.tga',      'F_DETAIL_TEXTURE 1\n'),
        # BUG: decaltextures seem to be maps from which only parts are applied (seemingly on hammer editor) 
        # see dust2 bombsite A crates
        '$decaltexture':        ('TextureDetail',       '_detail.tga',      'F_DETAIL_TEXTURE 1\n'),
        #'$detail2':            ('TextureDetail',       '_detail.tga',      'F_DETAIL_TEXTURE 1\n'),
        '$tintmasktexture':     ('TextureTintMask',     '_mask.tga',        'F_TINT_MASK 1'), # GREEN CHANNEL ONLY, RED IS FOR $envmapmaskintintmasktexture 1
        '$selfillummask':       ('TextureSelfIllumMask','_selfillummask.tga',''), # $blendtintbybasealpha 1 

        '$envmap':              ('TextureCubeMap',      '_cube.pfm',        'F_SPECULAR 1\n\tF_SPECULAR_CUBE_MAP 1\n\tF_SPECULAR_CUBE_MAP_PROJECTION 1\n\tg_flCubeMapBlurAmount "1.000"\n\tg_flCubeMapScalar "1.000"\n\tg_vReflectanceRange "[0.000 0.600]"\n'),

        #'$envmapmask':          ('TextureReflectance',  '_refl.tga',        ''),  #  selfillum_envmapmask_alpha envmapmaskintintmasktexture 

        #'$phong':               ('TextureReflectance',  '_refl.tga',        '\n\tg_vReflectanceRange "[0.000 0.600]"\n'),
         

        #('TextureTintTexture',)
        
        # These have no separate masks
        '$translucent':         ('TextureTranslucency', '_trans.tga',       'F_TRANSLUCENT 1\n'), # g_flOpacityScale "1.000"
        '$alphatest':           ('TextureTranslucency', '_trans.tga',       'F_ALPHA_TEST 1\n'),
        
        # only the G channel -> R = flCavity, G = flAo, B = cModulation, A = flPaintBlend
        '$ao':                  ('TextureAmbientOcclusion', '_ao.tga',      'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n'),
        '$aotexture':           ('TextureAmbientOcclusion', '_ao.tga',      'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n'),
        #'$ambientoccltexture':  ('TextureAmbientOcclusion', '_ao.tga',      'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n'),
        #'$ambientocclusiontexture':('TextureAmbientOcclusion', '_ao.tga',   'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n')
    },

    # [0, 1] center defines the point of rotation. Only useful if rotate is being used.
    # [2, 3] scale fits the texture into the material the given number of times. '2 1' is a 50% scale in the X axis.
    #    [4] rotate rotates the texture counter-clockwise in degrees. Accepts any number, including negatives.
    # [5, 6] translate shifts the texture by the given numbers. '.5' will shift it half-way.
    # $detailtexturetransform "center .5 .5 scale 1 1 rotate 0 translate 0 0"
    'transform': {
        '$basetexturetransform':     ('g_vTex',          '', 'g_vTexCoordScale "[1.000 1.000]"g_vTexCoordOffset "[0.000 0.000]"'),
        '$basetexturetransform2':    ('', '', ''),
        '$texture2transform':        ('',                '', ''),
        '$detailtexturetransform':   ('g_vDetailTex',    '', 'g_flDetailTexCoordRotation g_vDetailTexCoordOffset g_vDetailTexCoordScale g_vDetailTexCoordXform'),
        '$blendmasktransform':       ('',                '', ''),
        '$bumptransform':            ('g_vNormalTex',    '', ''),
        '$bumptransform2':           ('',                '', ''),
        '$envmapmasktransform':      ('',                '', ''),
        '$envmapmasktransform2':     ('',                '', '')

    },

    'settings': {
        '$detailscale':         ('g_vDetailTexCoordScale',  '[1.000 1.000]',    ''),
        '$detailblendfactor':   ('g_flDetailBlendFactor',   '1.000',            ''),
        #'$detailblendfactor2':  ('g_flDetailBlendFactor',   '1.000',            ''),
        #'$detailblendfactor3':  ('g_flDetailBlendFactor',   '1.000',            ''),
        #'$detailblendfactor4':  ('g_flDetailBlendFactor',   '1.000',            ''),
        '$selfillumscale':      ('g_flSelfIllumScale',      '1.000',            ''),
        '$selfillumtint':       ('g_vSelfIllumTint','[1.000 1.000 1.000 0.000]',''),

        #Probably used artist authored cubemap
        # TODO: if envmapmask, apply tint to the map manually, else just use this below.
        # TODO: I think tints at both phong and envmap need to be applied to the roughness map. But it should be some inverse shit.
        # 1.000 means no change 0.5 means brighten by 0.5??
        # actually not. envmaptint is used to tint the envmap which is usually white so that the reflection matches the albedo of the material
        # example on a red-ish metal you do [.5 .3 0] so that the specular refl does more of a red-ish reflection
        # 
        #'$envmaptint':          ('TextureTODO:',      '[1.000 1.000 1.000 0.000]', ''),
        
        # 210 is default roughness in s1. Also known as default_rough_s1import.tga
        
        '$phongexponent':       ('TextureRoughness',    '[0.823 0.823 0.823 1.000]', ''),
        '$phongexponent2':      ('TextureRoughnessB',   '[0.823 0.823 0.823 1.000]', ''),

        '$color':               ('g_vColorTint',           '[1.000 1.000 1.000 0.000]', ''),
        #'$layertint1':
        #'$color2':              ('g_vColorTint',           '[1.000 1.000 1.000 0.000]', ''),

        '$blendtintcoloroverbase':('g_flModelTintAmount', '1.000', ''),

        '$surfaceprop':         ('SystemAttributes\n\t{\n\t\tPhysicsSurfaceProperties\t', 'default', ''),
        
        '$alpha':               ('g_flOpacityScale', '1.000', ''),
        '$alphatestreference':  ('g_flAlphaTestReference', '0.500', 'g_flAntiAliasedEdgeStrength "1.000"'),
        
        # inverse
        '$nofog':               ('g_bFogEnabled', '0', ''),
        "$notint":              ('g_flModelTintAmount', '1.000', ''),

        '$refractamount':       ('g_flRefractScale',        '0.200', ''),
        '$flow_worlduvscale':   ('g_flWorldUvScale',        '1.000', ''),
        '$flow_noise_scale':    ('g_flNoiseUvScale',        '0.010', ''), # g_flNoiseStrength?
        '$flow_bumpstrength':   ('g_flNormalMapStrength',   '1.000', ''),

        # SH_BLEND and SH_VR_STANDARD(SteamVR) -- $NEWLAYERBLENDING settings used on dust2 etc
        '$blendsoftness':       ('g_flLayer1BlendSoftness', '0.500',    ''),
        '$layerborderstrenth':  ('g_flLayer1BorderStrength','0.500',    ''),
        '$layerborderoffset':   ('g_flLayer1BorderOffset',  '0.000',    ''),
        '$layerbordersoftness': ('g_flLayer1BorderSoftness','0.500',    ''),

        '$layerbordertint':     ('g_vLayer1BorderColor',       '[1.000000 1.000000 1.000000 0.000000]', ''),
        
        #'LAYERBORDERSOFTNESS':  ('g_flLayer1BorderSoftness', '1.0', ''),
        #rimlight
          
    },

    'f_settings': {
        '$selfillum':           ('F_SELF_ILLUM',        '1', ''),
        '$additive':            ('F_ADDITIVE_BLEND',    '1', ''),
        '$nocull':              ('F_RENDER_BACKFACES',  '1', ''),
        '$decal':               ('F_OVERLAY',           '1', ''),
        '$flow_debug':          ('F_FLOW_DEBUG',        '0', ''),
        '$detailblendmode':     ('F_DETAIL_TEXTURE',    '1', ''), # not 1 to 1
        '$decalblendmode':      ('F_DETAIL_TEXTURE',    '1', ''), # not 1 to 1
    },

    'alphamaps': {
        
      # '$vmtKey':  (key for which we provide a map,  key from which we extract a map,  channel to extract)
        # TODO: envmap, phong need processing. They should be added as a key.
        '$normalmapalphaenvmapmask':    ('$envmapmask',     normalmaps,         'A'), 
        '$basealphaenvmapmask':         ('$envmapmask',     '$basetexture',     'A'),
        '$envmapmaskintintmasktexture': ('$envmapmask',     '$tintmasktexture', 'R'),
        
        '$basemapalphaphongmask':       ('$phong',          '$basetexture',     'A'),
        '$basealphaphongmask':          ('$phong',          '$basetexture',     'A'), # rare and stupid
        '$normalmapalphaphongmask':     ('$phong',          normalmaps,         'A'), # rare and stupid
        '$bumpmapalphaphongmask':       ('$phong',          normalmaps,         'A'), # rare and stupid
        
        '$blendtintbybasealpha':        ('$tintmasktexture','$basetexture',     'A'),
        '$selfillum_envmapmask_alpha':  ('$selfillummask',  '$envmap',          'A')
    },

    
    # no direct replacement, etc
    'others2': {
        # ssbump shader is currently broken in HL:A.
        '$ssbump':               ('TextureBentNormal',    '_bentnormal.tga', '\n\tF_ENABLE_NORMAL_SELF_SHADOW 1\n\tF_USE_BENT_NORMALS 1\n'),
        '$newlayerblending':     ('',    '',     ''),

        '$iris': ('',    '',     ''), # paste iris into basetexture

        # fRimMask = vMasks1Params.r;
		# fPhongAlbedoMask = vMasks1Params.g;
		# fMetalnessMask = vMasks1Params.b;
		# fWarpIndex = vMasks1Params.a;
        '$maskstexture':    ('',    '',     ''),
        '$masks':   ('',    '',     ''),
        '$masks1':  ('',    '',     ''),
        '$masks2':  ('',    '',     ''),
        
        # $selfillumfresnelminmaxexp "[1.1 1.7 1.9]"
        #'$selfillum_envmapmask_alpha':     ('',    '',     ''),
        
        
        # TODO: the fake source next to outside area on de_nuke;
        # x = texturescrollrate * cos(texturescrollangle) ?????
        # y = texturescrollrate * sin(texturescrollangle) ?????
        #'TextureScroll':    (('texturescrollvar', 'texturescrollrate', 'texturescrollangle'), 'g_vTexCoordScrollSpeed', '[0.000 0.000]') 
        
        # reflectance maxes at 0.6 for CS:GO
        #'$phong':                ('',    '',     '\n\tg_vReflectanceRange "[0.000 0.600]"\n')   
    }
}

def convertVmtToVmat(vmtKeyValList):

    vmatContent = ''

    for oldKey, oldVal in vmtKeyValList.items():

        #oldKey = oldKey.replace('$', '').lower()
        oldKey = oldKey.lower()
        oldVal = oldVal.strip().strip('"' + "'").strip(' \n\t"')
        outKey = outVal = outAdditionalLines = ''
        #print ( oldKey + " --->" + oldVal)
    
        for keyType in list(vmt_to_vmat):
            #vmtKeyList = vmt_to_vmat[keyType]
            for vmtKey, vmatItems in vmt_to_vmat[keyType].items():     
                
                if ( oldKey != vmtKey ):
                    continue

                vmatReplacement = vmatItems[VMAT_REPLACEMENT]
                vmatDefaultValue = vmatItems[VMAT_DEFAULT]
                vmatExtraLines = vmatItems[VMAT_EXTRALINES]
                if ( vmatReplacement and vmatDefaultValue ):
                    
                    outKey = vmatReplacement
                    
                    if (keyType == 'textures'):
                        outVal = 'materials/default/default' + vmatDefaultValue
                    else:
                        outVal = vmatDefaultValue
                    
                    outAdditionalLines = vmatExtraLines

                # no equivalent key-value for this key, only exists
                # add comment or ignore completely
                elif (vmatExtraLines):
                    if keyType in ('transform'): # exceptions
                        pass
                    else:
                        vmatContent += vmatExtraLines
                        break
                else:
                    #print('No replacement for %s. Skipping', vmtKey)
                    vmatContent += COMMENT + vmtKey
                    break


                if(keyType == 'textures'):
                    
                    if vmtKey in ['$basetexture', '$hdrbasetexture', '$hdrcompressedtexture']:
                        # semi-BUG: how is hr_dust_tile_01,02,03 blending when its shader is LightmappedGeneric??????????
                        if '$newlayerblending' in vmtKeyValList or '$basetexture2' in vmtKeyValList:
                            #if vmatShader in (SH_VR_SIMPLE_2WAY_BLEND, 'xx'): 
                            outKey = vmatReplacement + 'A' # TextureColor -> TextureColorA
                            print("@ DBG: " + outKey + "<--- is noblend ok?")
                        
                        if vmatShader == SH_SKY:
                            outKey = 'SkyTexture'
                            outVal = formatVmtTextureDir(oldVal[:-2].rstrip('_') + '_cube' + vmatDefaultValue.lstrip('_color'), fileExt = '')

                        else:
                            outVal = formatNewTexturePath(oldVal, vmatDefaultValue)

                    elif vmtKey in ['$basetexture3', '$basetexture4']:
                        if not USE_OLD_SHADERS:
                            print('~ WARNING: Found 3/4-WayBlend but it is not supported with the current shader ' + vmatShader + '.')

                    elif vmtKey in  ('$bumpmap', '$bumpmap2', '$normalmap', '$normalmap2'):
                        # all(k not in d for k in ('name', 'amount')) vmtKeyValList.keys() & ('newlayerblending', 'basetexture2', 'bumpmap2'): # >=
                        if (vmtKey != '$bumpmap2') and (vmatShader == SH_VR_SIMPLE_2WAY_BLEND or '$basetexture2' in vmtKeyValList):
                            outKey = vmatReplacement + 'A' # TextureNormal -> TextureNormalA

                        # this is same as default_normal
                        #if oldVal == 'dev/flat_normal':
                        #    pass

                        if str(vmtKeyValList.get('$ssbump')).strip('"') == '1':
                            print('@ DBG: Found SSBUMP' + outVal)
                            outKey = COMMENT + '$SSBUMP' + '\n\t' + outKey
                            pass

                        #    outKey = vmt_to_vmat['others2']['$ssbump'][VMAT_REPLACEMENT]
                        #    outAdditionalLines = vmt_to_vmat['others2']['$ssbump'][VMAT_EXTRALINES]

                        #    outVal = formatNewTexturePath(oldVal, vmt_to_vmat['others2']['$ssbump'][VMAT_DEFAULT], True)
                        outVal = formatNewTexturePath(oldVal, vmatDefaultValue)
                        if not 'default/default' in outVal:
                            flipNormalMap(outVal)

                    elif vmtKey == '$blendmodulatetexture':
                        sourceTexturePath = getTexture(vmtKey)
                        if sourceTexturePath:
                            outVal = createMaskFromChannel(sourceTexturePath, 'G', vmatDefaultValue, False)

                    elif vmtKey == '$envmap':
                        if oldVal == 'env_cubemap':
                            if(vmtKeyValList.get('$envmaptint')):
                                outVal = fixIntVector(vmtKeyValList['$envmaptint'], True) or '[1.000 1.000 1.000 0.000]' #vmt_to_vmat['settings']['$envmaptint'][VMAT_DEFAULT]
                            else:
                                vmatContent += '\t' + outAdditionalLines
                                break ### Skip default content write

                        else:
                            # TODO: maybe make it real cubemap?
                            outAdditionalLines = 'F_SPECULAR 1\n\t'

                    elif vmtKey == '$phong':
                        #if oldVal == '0':
                        break

                        #fixPhongRoughness(paramList = vmtKeyValList)

                        #if not vmtKeyValList.get('$basemapalphaphongmask'):
                            #outVal = createMaskFromChannel(getTexture(('$bumpmap', '$normalmap')), 'A', vmatDefaultValue, False)

                    # TRY: invert for brushes, don't invert for models
                    #elif vmtKey == '$envmapmask':

                        # it's overriden with basealphaenvmapmask, why envmapmask then? 
                        #if vmtKeyValList.get('$basealphaenvmapmask'):
                        #    if vmtKeyValList['$basealphaenvmapmask'] != 0:
                        #        vmatContent += COMMENT + vmtKey
                        #        break

                        # create a non inverted one just in case
                        #createMaskFromChannel(oldVal, 'A', vmatDefaultValue, False)
                        # create inverted and set it
                        #outVal = createMaskFromChannel(oldVal, 'A', vmatDefaultValue, True)

                    elif vmtKey == '$translucent' or vmtKey == '$alphatest':
                        #if is_convertible_to_float(oldVal):
                        #    vmatContent += '\t' + outAdditionalLines

                        if vmtKey == '$alphatest':
                            sourceTexturePath = getTexture('$basetexture')
                            if sourceTexturePath:
                                #if '$model' in vmtKeyValList or 'models' in vmatFileName:
                                outVal = createMaskFromChannel(sourceTexturePath, 'A', vmatDefaultValue, False)
                                #else: #????
                                #    outVal = createMaskFromChannel(sourceTexturePath, 'A', vmatDefaultValue, True)

                        elif vmtKey == '$translucent':
                            if is_convertible_to_float(oldVal):
                                #outVal = fixIntVector(oldVal, True, 2)
                                sourceTexturePath = getTexture('$basetexture')
                                print("@ DBG: IS NUMBER", sourceTexturePath)
                                if sourceTexturePath:
                                    outVal = createMaskFromChannel(sourceTexturePath, 'A', vmatDefaultValue, False)

                    elif vmtKey == '$tintmasktexture':
                        sourceTexturePath = getTexture(vmtKey)
                        if sourceTexturePath:
                            outVal = createMaskFromChannel(getTexture(vmtKey), 'G', vmatDefaultValue, False)

                    elif vmtKey == '$aotexture':
                        sourceTexturePath = getTexture(vmtKey)
                        if sourceTexturePath:
                            outVal = createMaskFromChannel(getTexture(vmtKey), 'G', vmatDefaultValue, False)

                    #### DEFAULT
                    else:
                        if oldVal == 'env_cubemap' or vmatShader == SH_SKY: pass
                        else: outVal = formatNewTexturePath(oldVal, vmatDefaultValue)


                elif(keyType == 'transform'):
                    if not vmatReplacement or vmatShader == SH_SKY:
                        break

                    matrixList = listMatrix(oldVal)

                    ''' doesnt seem like there is rotation
                    if(matrixList[MATRIX_ROTATE] != '0.000'):
                        if(matrixList[MATRIX_ROTATIONCENTER] != '[0.500 0.500]')
                    '''
                    # scale 5 5 -> g_vTexCoordScale "[5.000 5.000]"
                    if(matrixList[MATRIX_SCALE] and matrixList[MATRIX_SCALE] != '[1.000 1.000]'):
                        vmatContent += '\t' + vmatReplacement + 'CoordScale' + '\t\t' + QUOTATION + matrixList[MATRIX_SCALE] + QUOTATION + '\n'

                    # translate .5 2 -> g_vTexCoordScale "[0.500 2.000]"
                    if(matrixList[MATRIX_TRANSLATE] and matrixList[MATRIX_TRANSLATE] != '[0.000 0.000]'):    
                        vmatContent += '\t' + vmatReplacement + 'CoordOffset' + '\t\t' + QUOTATION + matrixList[MATRIX_TRANSLATE] + QUOTATION + '\n'

                    break ### Skip default content write

                elif(keyType == 'settings'):
                    
                    if(vmtKey == '$detailscale'):
                        if '[' in oldVal: # [10 10] -> [10.000000 10.000000]
                            outVal = fixIntVector(oldVal, False)
                        else: # 10 -> [10.000000 10.000000]
                            outVal = fixIntVector(oldVal, False, 1)               

                   # TODO: test if its possible to drop oldVal as it is -raw-
                   # maybe it gets converted?
                    elif (vmtKey == '$surfaceprop'):
                        
                        # bit hardcoded
                        if oldVal in ('default', 'default_silent', 'no_decal', 'player', 'roller', 'weapon'):
                            pass

                        elif oldVal in surfprop_repl:
                            outVal = surfprop_repl[oldVal]

                        else:
                            if("props" in vmatFileName): match = get_close_matches('prop.' + oldVal, surfprop_HLA, 1, 0.4)
                            else: match = get_close_matches('world.' + oldVal, surfprop_HLA, 1, 0.6) or get_close_matches(oldVal, surfprop_HLA, 1, 0.6)

                            outVal = match[0] if match else oldVal

                        print(outVal)
                        vmatContent += '\n\t' + outKey + QUOTATION + outVal + QUOTATION + '\n\t}\n\n'
                        break ### Skip default content write

                    elif vmtKey == '$nofog': outVal = str(int(not int(oldVal)))
                    elif vmtKey == '$notint': outVal = str(float(not int(oldVal)))

                    elif vmtKey == '$selfillum':
                        
                        if oldVal == '0' or '$selfillummask' in vmtKeyValList:
                            break

                        # should use reverse of the basetexture alpha channel as a self iluminating mask
                        # TextureSelfIlumMask "materials/*_selfilummask.tga"
                        sourceTexture = getTexture("$basetexture")
                        outAdditionalLines \
                            = '\n\t' \
                            + vmt_to_vmat['textures']['selfillummask'][VMAT_REPLACEMENT] \
                            + '\t' \
                            + QUOTATION \
                            + createMaskFromChannel(sourceTexture, 'A', vmt_to_vmat['textures']['$selfillummask'][VMAT_DEFAULT], True ) \
                            + QUOTATION
                    
                    elif vmtKey in ("$color", '$color2', "$selfillumtint", '$layerbordertint'):
                        if oldVal:
                            outVal = fixIntVector(oldVal, True)
                    
                    elif vmtKey in ('$phongexponent', '$phongexponent2'): # TODO:
                        if (vmatShader == SH_VR_SIMPLE_2WAY_BLEND) and vmtKey == '$phongexponent':
                            outKey = outKey + 'A'
                        #break
                        #continue
                        pass

                    # The other part are simple floats. Deal with them
                    else:
                        outVal = "{:.6f}".format(float(oldVal.strip(' \t"')))
                

                elif(keyType == 'alphamaps'):
                    outVmtTexture = vmt_to_vmat['alphamaps'][vmtKey][0]

                    if not vmt_to_vmat['textures'].get(outVmtTexture): break

                    sourceTexture       = vmt_to_vmat['alphamaps'][vmtKey][1]
                    sourceChannel       = vmt_to_vmat['alphamaps'][vmtKey][2]
                    outKey              = vmt_to_vmat['textures'][outVmtTexture][VMAT_REPLACEMENT]
                    outAdditionalLines  = vmt_to_vmat['textures'][outVmtTexture][VMAT_EXTRALINES]
                    sourceSubString     = vmt_to_vmat['textures'][outVmtTexture][VMAT_DEFAULT]

                    sourceTexturePath   = getTexture(sourceTexture)

                    if sourceTexturePath:
                        if vmtKeyValList.get(outVmtTexture):
                            print("~ WARNING: Conflicting " + vmtKey + " with " + outVmtTexture + ". Aborting mask creation (using original).")
                            break

                        outVal =  createMaskFromChannel(sourceTexturePath, sourceChannel, sourceSubString, False)

                        # invert for brushes; if it's a model, keep the intact one ^
                        # both versions are provided just in case for 'non models'
                        #if not str(vmtKeyValList.get('$model')).strip('"') != '0':
                        #    outVal = createMaskFromChannel(sourceTexture, 'A', vmt_to_vmat['alphamaps']['$basealphaenvmapmask'][VMAT_DEFAULT], True )
                    else:
                        print("~ WARNING: Couldn't lookup texture from " + str(sourceTexture))
                        break


                # F_RENDER_BACKFACES 1 etc
                elif keyType == 'f_settings':

                    if vmtKey in  ('$detailblendmode', '$decalblendmode'):
                        # https://developer.valvesoftware.com/wiki/$detail#Parameters_and_Effects
                        # materialsystem\stdshaders\BaseVSShader.h#L26

                        # Texture combining modes for combining base and detail/basetexture2
                        # common_ps_fxc.h
                        # define DETAIL_BLEND_MODE_RGB_EQUALS_BASE_x_DETAILx2				
                        # define DETAIL_BLEND_MODE_RGB_ADDITIVE								1	// Base.rgb+detail.rgb*fblend
 
                        # Texture combining modes for combining base and decal texture
                        # define DECAL_BLEND_MODE_DECAL_ALPHA								0	// Original mode ( = decalRGB*decalA + baseRGB*(1-decalA))
                        # define DECAL_BLEND_MODE_RGB_MOD1X									1	// baseRGB * decalRGB
                        # define DECAL_BLEND_MODE_NONE										2	// There is no decal texture

                        if oldVal == '0':       outVal = '1' # Original mode (Mod2x)
                        elif oldVal == '1':     outVal = '2' # Base.rgb+detail.rgb*fblend 
                        #elif oldVal == '7':     outVal = 
                        elif oldVal == '12':    outVal = '0'

                        else: outVal = '1'

                    if outKey in vmatContent:
                        print('@ DBG: ' + outKey + ' is already in.')
                        vmatContent = re.sub(r'%s.+' % outKey, outKey + ' ' + outVal, vmatContent)
                    else:
                        vmatContent += '\t' + outKey + ' ' + outVal + '\n'  
                    break ### Skip default content write

                elif keyType == 'others2':
                    if oldKey == '$ssbump': break
                    vmatContent += '\t' + COMMENT + outKey + '\t\t' + QUOTATION + outVal + QUOTATION + '\n\t' + outAdditionalLines + '\n'
                    break ### Skip default content write
                
                ### Default content write ###
                if(outAdditionalLines): vmatContent += '\n\t' + outAdditionalLines + '\n\t' + outKey + '\t\t' + QUOTATION + outVal + QUOTATION + '\n'
                else: vmatContent += '\t' + outKey + '\t\t' + QUOTATION + outVal + QUOTATION + '\n'

                if(outVal.endswith(TEXTURE_FILEEXT)): outVal = formatFullDir(outVal) # DBG
                ##print("DBG: " + oldKey + ' ' + oldVal + ' (' + vmatReplacement.replace('\t', '').replace('\n', '') + ' ' + vmatDefaultValue.replace('\t', '').replace('\n', '') + ') -------> ' + outKey + ' ' + outVal.replace('\t', '').replace('\n', '') + ' ' + outAdditionalLines.replace('\t', '').replace('\n', ''))
                print("@ DBG: " + oldKey + ' "' + oldVal + '" ---> ' + outKey + ' ' + outVal.replace('\t', '').replace('\n', '') + ' ' + outAdditionalLines.replace('\t', '').replace('\n', ''))
                break ### stop loop now, we replaced the key we needed

    return vmatContent

def convertSpecials(vmtKeyValList):
    # use _ao texture in \weapons\customization\
    if "models\\weapons\\v_models" in fileName:
        weaponDir = os.path.dirname(fileName)
        weaponPathSplit = fileName.split("\\weapons\\v_models\\")
        weaponPathName = os.path.dirname(weaponPathSplit[1])
        print("@ DBG:", weaponPathName + ".vmt")
        if fileName.endswith(weaponPathName + ".vmt") or fileName.endswith(weaponPathName.split('_')[-1] + ".vmt"):
            aoTexturePath = os.path.normpath(weaponPathSplit[0] + "\\weapons\\customization\\" + weaponPathName + '\\' + weaponPathName + "_ao" + TEXTURE_FILEEXT)
            aoNewPath = os.path.normpath(weaponDir + "\\" + weaponPathName + TEXTURE_FILEEXT)
            print("@ DBG:", aoTexturePath)
            if os.path.exists(aoTexturePath):
                print("@ DBG:", aoNewPath)
                if not os.path.exists(aoNewPath):
                    #os.rename(aoTexturePath, aoNewPath)
                    copyfile(aoTexturePath, aoNewPath)
                    print("+ Succesfully moved AO texture for weapon material:", weaponPathName)
                vmtKeyValList["$aotexture"] = formatVmatDir(aoNewPath).replace('materials\\', '')
                print("+ Using ao:", weaponPathName + "_ao" + TEXTURE_FILEEXT)
    
    # Do this so that we use the default value of rougness map -- for now
    #if vmatShader == SH_VR_COMPLEX:
    if not vmtKeyValList.get('$phongexponent'):
        vmtKeyValList['$phongexponent'] = "100"
    if vmatShader == SH_VR_SIMPLE_2WAY_BLEND and not vmtKeyValList.get('$phongexponent2'):
        vmtKeyValList['$phongexponent2'] = "100"

failures = []
listsssss = []

#####################################################################################################################
# Main function, loop through every .vmt
#
#
for fileName in fileList:
    print('--------------------------------------------------------------------------------------------------------')
    print('+ Reading file:  ' + fileName)
    #breakpoint()
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
            
            line = line.strip()
            
            if not line or line.startswith('/'):
                continue
            #rawline = line.lower().replace('"', '').replace("'", "").replace("\n", "").replace("\t", "").replace("{", "").replace("}", "").replace(" ", "")/[^a-zA-Z]/
            if row < 1:
                matType = re.sub(r'[^A-Za-z0-9_-]', '', line).lower()
                #print(matType)
                if any(wd in matType for wd in materialTypes):
                    validMaterial = True
                
            if skipNextLine:
                if "]" in line or "}" in line:
                    skipNextLine = False
            else:
                parseVMTParameter(line, vmtKeyValList)
            
            if any(wd in line.lower() for wd in ignoreList):
                skipNextLine = True
            
            row += 1

    if matType == 'patch':
        includeFile = vmtKeyValList.get("include")
        if includeFile:
            includeFile = includeFile.replace('"', '').replace("'", '').strip()
            if includeFile == 'materials\\models\\weapons\\customization\\paints\\master.vmt':
                continue

            print("+ Patching material details from include: " + includeFile +'\n')
            try:
                with open(formatFullDir(includeFile), 'r') as vmtFile:
                    oldVmtKeyValList = vmtKeyValList.copy()
                    vmtKeyValList.clear()
                    for line in vmtFile.readlines():
                        if any(wd in line.lower() for wd in materialTypes):
                            print('+ Valid patch')
                            validPatch = True
                        
                        line = line.strip()
                        parseVMTParameter(line, vmtKeyValList)
                    
                    vmtKeyValList.update(oldVmtKeyValList)
            
            except FileNotFoundError:
                failures.append(includeFile)
                print("~ WARNING: Couldn't find include file from patch. Skipping!")
                continue
                    
            if not validPatch:
                print("+ Include file is not a recognised material. Shader will be black by default.")
                # matType = 
                #continue
        else:
            print("~ WARNING: No include was provided on material with type 'Patch'. Is it a weapon skin?")
        
    vmatFileName = fileName.replace('.vmt', '') + '.vmat'
    vmatShader = chooseShader(matType, vmtKeyValList, fileName)

    skyboxName = os.path.basename(fileName).replace(".vmt", '')#[-2:]
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
                print("@ DBG:", "Collecting", face, "sky face", skyboxPath[skyboxName][face]['path'])
            transform = vmtKeyValList.get('$basetexturetransform')
            
            if(transform):
                faceTransform = listMatrix(transform) if(transform) else list()
                skyboxPath[skyboxName][face]['rotate'] = int(float(faceTransform[MATRIX_ROTATE]))
                print("@ DBG:", "Collecting", face, "transformation", skyboxPath[skyboxName][face]['rotate'], 'degrees')

            # skip vmat for dn, lf, rt, bk, ft
            # TODO: ok we might need the vmats for all of them because they might be used somewhere else
            vmatShader = SH_SKY
            vmatFileName = vmatFileName.replace(face + '.vmat', '').rstrip('_') + '.vmat'
            if face != 'bk': validMaterial = False


    if validMaterial:
        if os.path.exists(vmatFileName) and not OVERWRITE_VMAT:
            print('+ File already exists. Skipping!')
            continue

        with open(vmatFileName, 'w') as vmatFile:
            vmatFile.write('// Converted with vmt_to_vmat.py\n')
            vmatFile.write('// From: ' + fileName + '\n\n')
            print("@ DBG: " + matType + " => " + vmatShader)
            vmatFile.write('Layer0\n{\n\tshader "' + vmatShader + '.vfx"\n\n')

            convertSpecials(vmtKeyValList)

            vmatFile.write(convertVmtToVmat(vmtKeyValList)) ###############################

            #check if base texture is empty
            #if "metal" in vmatFileName:
            #    vmatFile.write("\tg_flMetalness 1.000\n")

            vmatFile.write('}\n')

        vmatContentRecord(vmatFile)
        #with open(fileName) as f:
        #    with open(vmatFileName, "w") as f1:
        #        for line in f:
        #            f1.write(COMMENT + line)
        print ('+ Converted: ' + fileName)
        print ('+ Saved at:  ' + vmatFileName)
        print ('--------------------------------------------------------------------------------------------------------')
    
    else: print("+ Invalid material. Skipping!")


    if not matType:
        debugContent += "Warning" + fileName + '\n'


########################################################################
# Build skybox cubemap from sky faces
# (blue_sky_up.tga, blue_sky_ft.tga, ...) -> blue_sky_cube.tga
# https://developer.valvesoftware.com/wiki/File:Hdr_skyface_sides.jpg
for skyName in skyboxPath:

    if True: break
    # what is l4d2 skybox/sky_l4d_rural02_ldrbk.pwl
    # TODO: decouple this in a separate script. skyface_to_skymap.py
    # write the sky face contents in a text file. allow manual sky map creation

    # TODO: !!!!! HOW DO I DO HDR FILES !!!!! '_cube.exr'
    # idea: convert to tiff

    faceCount = 0
    facePath = ''
    SkyCubeImage_Path = ''
    for face in skyboxFaces:
        facePath = skyboxPath[skyName][face].get('path')
        if not facePath: continue
        faceHandle = Image.open(formatFullDir(facePath))

        if not faceHandle: continue
        if((not skyboxPath[skyName][face].get('scale') or len(skyboxFaces) == skyboxFaces.index(face)+1) and (not skyboxPath[skyName][face].get('resolution'))):
            skyboxPath[skyName]['resolution'] = faceHandle.size# TODO: find trend
        skyboxPath[skyName][face]['handle'] = faceHandle
        faceCount += 1

    if not faceCount or not skyboxPath[skyName]['resolution']: continue

    face_w = face_h = skyboxPath[skyName]['resolution'][0]
    cube_w = 4 * face_w
    cube_h = 3 * face_h
    SkyCubeImage = Image.new('RGBA', (cube_w, cube_h), color = (0, 0, 0)) # alpha?

    for face in skyboxFaces:
        faceHandle = skyboxPath[skyName][face].get('handle')
        if not faceHandle: continue
        facePath = formatFullDir(skyboxPath[skyName][face]['path'])

        faceScale = skyboxPath[skyName][face].get('scale')
        faceRotate = skyboxPath[skyName][face].get('rotate')

        #print("@ DBG:", "Using image", formatVmatDir(facePath), "for the", face, "face")
        vtfTexture = facePath.replace(TEXTURE_FILEEXT, '') + '.vtf'
        if REMOVE_VTF_FILES and os.path.exists(vtfTexture):
            os.remove(vtfTexture)
            print("~ Removed vtf file: " + formatVmatDir(vtfTexture))

        # TODO: i think top and bottom need to be rotated by 90 + side faces offset by x
        # check if front is below top and above bottom
        # move this inside the dict
        if face == 'up':   facePosition = (cube_w - 3 * face_w, cube_h - 3 * face_h)
        elif face == 'ft': facePosition = (cube_w - 2 * face_w, cube_h - 2 * face_h)
        elif face == 'lf': facePosition = (cube_w - 1 * face_w, cube_h - 2 * face_h)
        elif face == 'bk': facePosition = (cube_w - 4 * face_w, cube_h - 2 * face_h)
        elif face == 'rt': facePosition = (cube_w - 3 * face_w, cube_h - 2 * face_h)
        elif face == 'dn': facePosition = (cube_w - 3 * face_w, cube_h - 1 * face_h)

        if faceHandle.width != face_w:
            faceHandle = faceHandle.resize((face_w, round(faceHandle.height * face_w/faceHandle.width)), Image.BICUBIC)

        if(skyboxPath[skyName][face].get('rotate')):
            print("@ DBG: ROTATING `" + face + "` BY THIS: " + str(skyboxPath[skyName][face]['rotate']))
            faceHandle = faceHandle.rotate(int(skyboxPath[skyName][face]['rotate']))

        
        SkyCubeImage.paste(faceHandle, facePosition)
        faceHandle.close()

    if facePath:
        SkyCubeImage_Path = facePath.replace(TEXTURE_FILEEXT, '')[:-2].rstrip('_') + '_cube' + TEXTURE_FILEEXT
        SkyCubeImage.save(SkyCubeImage_Path)

    if os.path.exists(SkyCubeImage_Path):
        print('+ Successfuly created sky cubemap at: ' + SkyCubeImage_Path)
