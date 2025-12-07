# oplus_super_packer

<p align="left">
	<img src="EXE.ico" alt="oplus_super_packer icon" width="96">
</p>

[![Build](https://github.com/AaronXenos/oplus_super_packer/actions/workflows/build_win.yml/badge.svg)](https://github.com/AaronXenos/oplus_super_packer/actions/workflows/build_win.yml)
[![Latest Release](https://img.shields.io/github/v/release/AaronXenos/oplus_super_packer)](https://github.com/AaronXenos/oplus_super_packer/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)



A small helper to rebuild `super.img` for OPlus/OPPO/OnePlus firmware drops. It wraps `lpmake`/`simg2img`, applies layout from `super_def.json`, and repacks super partitions from domestic or FULL OTA inputs.

## Partition tools origin

The bundled `partition_tools` folder is built from [Rprop’s aosp15_partition_tools patch](https://github.com/Rprop/aosp15_partition_tools). Use `--binpath partition_tools` (default when bundled) to pick up the included `lpmake` and `simg2img`.

## Requirements

- Windows (tested in CI on `windows-latest`) or a shell with `lpmake` and `simg2img` available.
- Python 3.10+ with `colorama` if you run the script directly. The release zip ships a standalone `oplus_super_packer.exe` plus `partition_tools`.
- Input: domestic folder or FULL OTA with matching `super_def.json`/`version_info.txt`.

## Usage

### Prebuilt executable

1) Download the release asset `oplus_super_packer-<tag>.zip` and extract.
2) Run from a terminal inside the extracted folder:

```pwsh
./oplus_super_packer.exe --path .\XXXdomestic_11_15.0.0.850
```

If needed, point to custom tools:

```pwsh
./oplus_super_packer.exe --path .\super_def.json --fullota .\FULL_OTA --binpath .\partition_tools
```

### Run via Python

```pwsh
python oplus_super_packer.py --path ./XXXdomestic_11_15.0.0.850
python oplus_super_packer.py --path ./XXXdomestic_11_15.0.0.850 --fullota ./FULL_OTA
python oplus_super_packer.py --path ./super_def.json --fullota ./FULL_OTA
```

### Common options

- `--path PATH` (required): domestic folder or `super_def.json` file.
- `--fullota PATH`: FULL OTA folder when packing from OTA.
- `--binpath PATH`: directory containing `lpmake` and `simg2img`; defaults to bundled `partition_tools`.
- `--preload PATH`: custom `my_preload` image.
- `--company PATH`: custom `my_company` image.
- `--vab/--no-vab`, `--mslots {2,3}`, `--sparse`, `--abab`: pass-through lpmake behaviors.

Output is written to `super.img` alongside your inputs; when verifying ABAB layout with stock images, metadata is checked automatically.
