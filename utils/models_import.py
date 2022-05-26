import shared.base_utils2 as sh
from shared.keyvalues3 import KV3

SHOULD_OVERWRITE = False

def ImportMDLtoVMDL(mdl_path, move_s1_assets = False):
    vmdl_path = mdl_path.with_suffix('.vmdl')
    with open(vmdl_path, 'w') as fp:
        fp.write(
            KV3(
                m_sMDLFilename = mdl_path.local.as_posix()
            ).ToString()
        )
    print('+ Generated', vmdl_path.local)
    return vmdl_path

def main():
    print('Source 2 VMDL Generator!')

    mdl_files = sh.collect('models', '.mdl', '.vmdl', SHOULD_OVERWRITE, searchPath=sh.output('models'))

    for mdl in mdl_files:
        ImportMDLtoVMDL(mdl)

    print("Looks like we are done!")

if __name__ == "__main__":
    sh.parse_argv()
    main()
