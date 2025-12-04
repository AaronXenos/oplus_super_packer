import os
import json
import sys
import shutil
import argparse
import subprocess

import colorama
colorama.init(autoreset=True)

VERSION_STRING = 'v1.0.0'
DEBUG_ENABLED = False


def bright_text(text: str) -> str:
    return f"{colorama.Style.BRIGHT}{text:8}{colorama.Style.NORMAL}"


def path_exists(path: str) -> bool:
    if os.path.exists(path):
        msg_debug(f'Path found {bright_text(path)}')
        return True
    else:
        msg_error(f'Path not found {bright_text(path)}')
        sys.exit(-1)


def msg_debug(msg: str) -> None:
    if DEBUG_ENABLED:
        print(f"[-] {msg}")


def msg_info(msg: str) -> None:
    print(f"{colorama.Fore.CYAN}[*] {msg}{colorama.Style.RESET_ALL}")


def msg_warn(msg: str) -> None:
    print(f"{colorama.Fore.YELLOW}[!] {msg}{colorama.Style.RESET_ALL}")


def msg_error(msg: str, rtn=False) -> str:
    out = f"{colorama.Fore.RED}[x] {msg}{colorama.Style.RESET_ALL}"
    if rtn:
        return out
    else:
        print(out)
        return ''


def align_up(n: int, align_size: int = 4096) -> int:
    return (n + align_size - 1) & ~(align_size - 1)


def exe_cmd(cmd: str) -> None:
    try:
        msg_info(f'EXEC CMD: {cmd}')
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            msg_error(f'EXEC stderr: \n{result.stderr}')
            sys.exit(-1)
        else:
            msg_info(f'EXEC stdout: {result.stdout}')
    except Exception as e:
        msg_error(f'EXEC EXCEPTION: {str(e)}')
        sys.exit(-1)


def clean_temp_folder(folder_path: str = ".temp") -> None:
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        msg_info(f"Create {folder_path}")
        return
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            msg_error(f'Failed to delete {file_path}. Reason: {e}')

    msg_info(f"Clean {folder_path}")


def is_sparse_image(part_path: str) -> bool:
    with open(part_path, 'rb') as f:
        magic = f.read(4)
    return magic == b'\x3A\xFF\x26\xED'


def super_packer(args: argparse.Namespace) -> None:
    if DEBUG_ENABLED:
        print(args)
    temp_dir = ".temp"
    clean_temp_folder(temp_dir)
    # =========================== preparation ===========================
    # check args
    arg_path = args.path
    arg_binpath = args.binpath
    arg_preload = args.preload
    arg_company = args.company
    arg_vab = args.vab
    arg_mslots = args.mslots
    arg_sparse = args.sparse
    arg_abab = args.abab
    arg_fullota = args.fullota

    # ========================== pack mode set ===========================
    path_exists(arg_path)
    # 0: domestic
    # 1: fullota whit domestic
    # 2: fullota whit json
    if os.path.isdir(arg_path) and arg_fullota is None:
        pack_mode = 0
        msg_info('Pack mode: domestic')
    elif os.path.isdir(arg_path) and arg_fullota is not None:
        pack_mode = 1
        msg_info('Pack mode: full ota whit domestic')
    elif os.path.isfile(arg_path) and arg_fullota is not None:
        pack_mode = 2
        msg_info('Pack mode: full ota whit super_def.json')
    else:
        msg_error('Invalid pack mode!')
        sys.exit(-1)

    # =========================== path check ===========================
    if arg_preload is not None:
        path_exists(arg_preload)
    if arg_company is not None:
        path_exists(arg_company)
    if arg_fullota is not None:
        path_exists(arg_fullota)
    if arg_binpath is not None and path_exists(arg_binpath):
        os.environ['PATH'] = f"{arg_binpath}{os.pathsep}{os.environ['PATH']}"
    

    # =========================== check necessary tools ===========================
    necessary_tools = ('lpmake', 'simg2img')
    contains_all_tools = True
    for tool in necessary_tools:
        if shutil.which(tool) is None:
            msg_error(f'Tool not found {bright_text(tool)}')
            contains_all_tools = False
        else:
            msg_info(
                f'Tool found {bright_text(tool)} : {shutil.which(tool)}')
    if not contains_all_tools:
        msg_warn('Some necessary tools are missing, exiting...')
        sys.exit(-1)

    # =========================== get super def config ===========================
    if pack_mode == 0 or pack_mode == 1:
        nvid = 0
        version_info_path = os.path.join(arg_path, 'version_info.txt')
        if path_exists(version_info_path):
            with open(version_info_path, 'r', encoding='utf-8') as f:
                temp = f.read()
            json_version_info = json.loads(temp)
            nvid = json_version_info[0]['nv_id']
            msg_info(f'nv_id : {nvid}')
        super_def_path = os.path.join(
            arg_path, 'META', f'super_def.{nvid:08}.json')
        path_exists(super_def_path)
        with open(super_def_path, 'r') as f:
            sd = json.load(f)
        msg_info(f'Pack mode: {pack_mode}  use {super_def_path}')
    elif pack_mode == 2:
        super_def_path = arg_path
        with open(super_def_path, 'r') as f:
            sd = json.load(f)
        msg_info(f'Pack mode: {pack_mode}  use {super_def_path}')

    # =====================================================================
    # ========================== lpmake command ===========================
    # =====================================================================
    lpmake_cmd = ['lpmake']
    if arg_vab:
        lpmake_cmd.append('--virtual-ab')
    if arg_sparse:
        lpmake_cmd.append('--sparse')

    super_meta_path = sd['super_meta']['path']
    metadata_size = sd['super_meta']['size']
    metadata_slots = arg_mslots
    lpmake_cmd.append(f'--metadata-size {metadata_size}')
    lpmake_cmd.append(f'--metadata-slots {metadata_slots}')

    # ========================== set block device ==========================
    block_size = int(sd['block_devices'][0]['block_size'])
    lpmake_cmd.append(f'--block-size {block_size}')
    device_size = sd['block_devices'][0]['size']
    device_aligment = sd["block_devices"][0]["alignment"]
    lpmake_cmd.append(f'--device super:{device_size}:{device_aligment}')

    # ============================ add groups ==============================
    groups = set()
    for group in sd['groups']:
        group_name = group['name']
        if group_name != 'default':
            maximum_size = group['maximum_size']
            lpmake_cmd.append(f'--group {group_name}:{maximum_size}')
            groups.add(group_name)
    groups = list(groups)

    # ============================ add partitions ==========================
    for partition in sd['partitions']:
        group_name = partition['group_name']
        if group_name.endswith('_a'):
            if DEBUG_ENABLED:
                print()

            # ====================== get partition info ====================
            part_name = partition['name']
            part_size = partition.get('size', 0)
            # get partition path
            if pack_mode == 0:
                # get path from super_def.json
                path_in_def = str(partition['path'])
                path_in_def = os.path.join(*path_in_def.split('/'))
                part_path = os.path.join(arg_path, path_in_def)
            else:
                # get path from full ota dir with name
                part_path = os.path.join(arg_fullota, f'{part_name[:-2]}.img')

            if part_name.startswith('my_preload') and arg_preload is not None:
                raw_image_path = arg_preload
                msg_info(f'Using {arg_preload} for {part_name}')
            else:
                raw_image_path = os.path.join(
                    temp_dir, f'raw_{part_name[:-2]}')

            # ============= convert sparse to raw if needed ================
            if path_exists(part_path) and is_sparse_image(part_path):
                if not DEBUG_ENABLED:
                    print()
                exe_cmd(f'simg2img {part_path} {raw_image_path}')
            else:
                raw_image_path = part_path

            if part_name.startswith('my_company'):
                pass
            # =================== get and verify size ======================
            real_size = os.path.getsize(raw_image_path)
            if pack_mode == 1 or pack_mode == 2:
                # get size from file
                msg_debug(f'{part_name} origin  size: {real_size}')
                align_size = align_up(real_size, block_size)
                msg_debug(f'{part_name} aligned size: {real_size}')
                final_size = align_size
            elif part_name.startswith('my_preload') and arg_preload is not None:
                # get preload size from file
                msg_debug(f'my_preload origin  size: {real_size}')
                align_size = align_up(real_size, block_size)
                msg_debug(f'my_preload aligned size: {align_size}')
                final_size = align_size
            else:
                # get size from super_def.json
                real_size = os.path.getsize(raw_image_path)
                msg_debug(f'{part_name} def     size: {part_size}')
                msg_debug(f'{part_name} origin  size: {real_size}')
                align_size = align_up(real_size, block_size)
                msg_debug(f'{part_name} aligned size: {align_size}')
                if int(part_size) == int(align_size):
                    final_size = align_size
                else:
                    msg_error('{part_name} size mismatch!')
                    sys.exit(-1)

            # ==================== append lpmake cmd =======================
            cmd_a = f'--partition {part_name}:readonly:{final_size}:{group_name} --image {part_name}={raw_image_path}'
            lpmake_cmd.append(cmd_a)
            # add b partition if abab layout as super_meta.raw
            if arg_abab:
                cmd_b = f'--partition {part_name[:-1]}b:readonly:0:qti_dynamic_partitions_b'
                lpmake_cmd.append(cmd_b)
    # generate super.img path
    if pack_mode == 0:
        super_img_path = os.path.join(arg_path, 'IMAGES', 'super.img')
    else:
        super_img_path = os.path.join(arg_fullota, 'super.img')
    lpmake_cmd.append(f'--output {super_img_path}')
    msg_warn(' \\\n\t'.join(lpmake_cmd))

    final_lpmake_cmd = ' '.join(lpmake_cmd)
    exe_cmd(final_lpmake_cmd)

    # ========================== verify handling ===========================
    print()
    if (arg_abab) and ((arg_fullota is None) and (arg_preload is None) and (arg_company is None)):
        super_meta_raw = os.path.join(
            arg_path, os.path.join(*super_meta_path.split('/')))
        path_exists(bright_text(super_meta_raw))
        msg_info(f"{bright_text(super_meta_raw)} verify start...")
        with open(super_meta_raw, 'rb') as f:
            original_meta = f.read()
        with open('super.img', 'rb') as f:
            f.seek(8192)
            meta_raw = f.read(len(original_meta))
        if meta_raw == original_meta:
            msg_info(f"{bright_text(super_meta_raw)} MATCH")
        else:
            msg_error(f"{bright_text(super_meta_raw)} NOT MATCH !!!")
    else:
        msg_warn('Skip verify due to custom images used!')

    # END
    msg_info('Super packing completed!')


class MyArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        if len(sys.argv) == 1:
            self.print_help(sys.stderr)
            sys.exit(2)
        sys.stderr.write(
            msg_error(f'error: {message}\n\n')
        )
        self.print_help(sys.stderr)
        sys.exit(2)


class SmartFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass


def parse_args():
    logo = f'''
╔═╗╔═╗╦  ╦ ╦╔═╗  ╔═╗╦ ╦╔═╗╔═╗╦═╗  ╔═╗╔═╗╔═╗╦╔═╔═╗╦═╗
║ ║╠═╝║  ║ ║╚═╗  ╚═╗║ ║╠═╝║╣ ╠╦╝  ╠═╝╠═╣║  ╠╩╗║╣ ╠╦╝
╚═╝╩  ╩═╝╚═╝╚═╝  ╚═╝╚═╝╩  ╚═╝╩╚═  ╩  ╩ ╩╚═╝╩ ╩╚═╝╩╚═ {VERSION_STRING}
A super packer for oplus zip
by AaronXenos (https://github.com/AaronXenos)
'''
    print(logo[1:], end='')

    example_text = '''Examples:
    1. Pack super from domestic folder:
        
        oplus_super_packer --path ./XXXdomestic_11_15.0.0.850

    2. Pack super from full ota with domestic folder:
        
        oplus_super_packer --path ./XXXdomestic_11_15.0.0.850 --fullota ./FULL_OTA 

    3. Pack super from full ota with super_def.json:
        
        oplus_super_packer --path ./super_def.json --fullota ./FULL_OTA
'''
    parser = MyArgumentParser(
        description='A super packer for oplus zip',
        epilog=example_text,
        usage='oplus_super_packer [options]',
        formatter_class=SmartFormatter
    )

    # path options
    parser.add_argument('--path', type=str, required=True, metavar='PATH',
                        help='Working folder/file path.')
    parser.add_argument('-b', '--binpath', type=str, default=None, metavar='PATH',
                        help='path to partition tools')
    parser.add_argument('--preload', type=str, default=None, metavar='PATH',
                        help='path to my_preload image')
    parser.add_argument('--company', type=str, default=None, metavar='PATH',
                        help='path to my_company image')
    # lpmake options
    parser.add_argument('--vab', action='store_true', default=True,
                        help='lpmake option: --virtual-ab')
    parser.add_argument('--mslots', type=int, choices=[2, 3], default=3,
                        help='lpmake option: --metadata-slots')
    parser.add_argument('--sparse', action='store_true',
                        help='lpmake option: --sparse')
    # other options
    parser.add_argument('--abab', action='store_true',
                        help='make layout as super_meta.raw')
    parser.add_argument('--fullota', type=str, default=None, metavar='PATH',
                        help='pack super from FULL_OTA')
    parser.add_argument('-vv', '--verbose', action='store_true',
                        help='enable verbose output')
    parser.add_argument('-v', '--version', action='version',
                        version=f'oplus_super_packer {VERSION_STRING}')
    args = parser.parse_args()
    if args.verbose:
        global DEBUG_ENABLED
        DEBUG_ENABLED = True
    return args


if __name__ == "__main__":
    try:
        args = parse_args()
        super_packer(args)
    except Exception as e:
        msg_error(f'EXCEPTION: {str(e)}')
        sys.exit(-1)
