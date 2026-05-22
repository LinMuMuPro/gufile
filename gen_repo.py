#!/usr/bin/env python3
"""Generate Cydia repo index (Packages, Packages.bz2, Release)."""
import os
import sys
import hashlib

DEBS_DIR = "debs"
OUTPUT = "Packages"


def parse_control(deb_path: str) -> dict:
    """Extract control fields from .deb filename and size."""
    info = {}
    base = os.path.basename(deb_path)
    # Parse: package_version_arch.deb
    parts = base.rsplit("_", 2)
    info["Package"] = parts[0]
    info["Version"] = parts[1].rsplit("_", 1)[0] if "_" in parts[1] else parts[1]
    info["Architecture"] = parts[2].replace(".deb", "") if len(parts) > 2 else "iphoneos-arm"

    stat = os.stat(deb_path)
    info["Filename"] = f"./debs/{base}"
    info["Size"] = str(stat.st_size)

    with open(deb_path, "rb") as f:
        info["MD5sum"] = hashlib.md5(f.read()).hexdigest()
        f.seek(0)
        info["SHA256"] = hashlib.sha256(f.read()).hexdigest()

    # Default fields for themes
    info["Name"] = "MuMu Piano Theme"
    info["Description"] = "钢琴风格美化主题 for SnowBoard"
    info["Section"] = "Themes"
    info["Author"] = "linmumupro"
    info["Maintainer"] = "linmumupro"
    info["Depends"] = "com.spark.snowboard"
    return info


def generate_packages():
    entries = []
    for fn in sorted(os.listdir(DEBS_DIR)):
        if fn.endswith(".deb"):
            info = parse_control(os.path.join(DEBS_DIR, fn))
            lines = []
            for k, v in info.items():
                lines.append(f"{k}: {v}")
            entries.append("\n".join(lines))

    packages = "\n\n".join(entries) + "\n"
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(packages)

    # bzip2 compress
    import bz2
    with open(OUTPUT, "rb") as f:
        with bz2.open(OUTPUT + ".bz2", "wb") as bz:
            bz.write(f.read())

    print(f"Generated {OUTPUT} ({len(entries)} packages)")
    print(f"Generated {OUTPUT}.bz2")

    # Generate Release
    import gzip
    release = (
        "Origin: MuMu Repo\n"
        "Label: MuMu Repo\n"
        "Suite: stable\n"
        "Version: 1.0\n"
        "Codename: ios\n"
        "Architectures: iphoneos-arm\n"
        "Components: main\n"
        "Description: 个人美化主题源 - MuMu Piano Theme\n"
    )
    with open("Release", "w", encoding="utf-8") as f:
        f.write(release)
    print("Generated Release")


if __name__ == "__main__":
    generate_packages()
