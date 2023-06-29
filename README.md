# source1import
Set of scripts for importing Source 1 assets such as materials, models, and particle effects into Source 2. Inspired by Valve's own internal utility (written in C++ and Perl), this one is in Python. 

Based off of [source2utils](https://github.com/AlpyneDreams/source2utils).

CS2 Alert: This tool doesn't support touchstone shaders in Counter-Strike 2, so you should most likely use the Valve provided [import scripts](https://github.com/andreaskeller96/cs2-import-scripts) instead.

## Usage
#### Download from here: [Releases](https://github.com/kristiker/source1import/releases)
#### Note:
* Make sure to move the entire s1 `models` folder to `content/` **before importing**.
* Make sure to move the entire s1 `sound` folder to `content/` and rename it to `sounds`. No import necessary.
* Make sure to have `gameinfo.txt` present in Import Game.
* Default settings are the best settings.
* Make sure to read [this guide](https://developer.valvesoftware.com/wiki/Half-Life:_Alyx_Workshop_Tools/Importing_Source_1_Maps) for importing map files.
* Materials won't make use of the PBR renderer. Make sure to tweak them like [here](https://github.com/kristiker/css2-inf-materials#readme), or even better; remake them.
* Materials are mainly converted to Complex and Simple.

## Advanced Usage:
### CLI:
```bash
cd utils
python scripts_import.py   -i "C:/.../Team Fortress 2/tf" -e "D:/Games/steamapps/common/sbox/addons/tf_source2" -b sbox
python particles_import.py -i "C:/.../Portal 2/portal2" -e "C:/.../Half-Life Alyx/game/hlvr_addons/portal2"
python scenes_import.py    -i "C:/.../Half-Life Alyx/game/lostcoast" -e hlvr_addons/lostcoast
python models_import.py    -i "C:/.../Half-Life Alyx/game/l4d2" -e l4d2_source2
python materials_import.py -i "C:/.../Half-Life Alyx/game/ep2" -e hlvr  "materials/skybox"
```
* **-i** *\<dir\>*  This should be an absolute path pointing into a source1 game directory containing gameinfo.txt   
* **-e** *\<dir/modname\>*  Path to source2 mod/addon. \<*modname*\> (e.g. `-e portal2_imported`) instead of an absolute path will only work if the input folder **-i** is placed inside a source2 /game/ environment which also contains \<*modname*\>.
* **-b** *\<branch\>* Switch to a different branch. Default is `hlvr`. Other branches include `steamvr` `adj` `sbox` `cs2` `dota2`, ordered by magnitude of support.
* **[filter]** Optionally a path at the end can be added as a filter.
### Requirements:
* [Python](https://www.python.org/downloads/) >= 3.10  
* `pip install -r requirements.txt`
## Results
### [CS:GO Taser - Streamable](https://streamable.com/eders9)
### [Inferno Source 2 Comparison - YouTube](https://www.youtube.com/watch?v=e-kcE9F_uH0)
<img src="https://i.imgur.com/qxNDhEE.jpeg" width=100%>
<img src="https://i.imgur.com/zhHOMWJ.png" width=100%>
* maps converted via built-in hammer 5 funcionality
