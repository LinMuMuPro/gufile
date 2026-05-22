#!/usr/bin/env python3
"""Generate Cydia repo index - flat format for iOS 6 compatibility."""
import os
import hashlib
import bz2
import gzip

DEBS_DIR = "debs"


def parse_control(deb_path: str) -> dict:
    base = os.path.basename(deb_path)
    parts = base.rsplit("_", 2)
    info = {}
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

    info["Name"] = "MuMu Piano Theme"
    info["Description"] = "A beautiful piano-themed UI theme for SnowBoard"
    info["Section"] = "Themes"
    info["Author"] = "linmumupro"
    info["Maintainer"] = "linmumupro"
    info["Depends"] = "com.spark.snowboard"
    return info


def generate():
    # Build Packages content
    entries = []
    for fn in sorted(os.listdir(DEBS_DIR)):
        if fn.endswith(".deb"):
            info = parse_control(os.path.join(DEBS_DIR, fn))
            # Fixed field order for consistency
            order = [
                "Package", "Version", "Architecture", "Filename", "Size",
                "MD5sum", "SHA256", "Name", "Description", "Section",
                "Author", "Maintainer", "Depends",
            ]
            lines = [f"{k}: {info[k]}" for k in order]
            entries.append("\n".join(lines))

    packages = "\n\n".join(entries) + "\n"

    # Write Packages with LF line endings
    with open("Packages", "w", encoding="utf-8", newline="\n") as f:
        f.write(packages)

    # bzip2 (primary format Cydia reads)
    data = packages.encode("utf-8")
    with bz2.open("Packages.bz2", "wb") as bz:
        bz.write(data)

    # gzip (fallback)
    with gzip.open("Packages.gz", "wb") as gz:
        gz.write(data)

    print(f"Generated Packages ({len(entries)} packages)")
    print("Generated Packages.bz2, Packages.gz")

    # Simple Release file - NO Debian fields
    # Including Codename/Components makes Cydia look for Packages
    # in dists/{codename}/{components}/... instead of the root
    release = (
        "Origin: MuMu Repo\n"
        "Label: MuMu Repo\n"
        "Description: Personal theme repo - MuMu Piano Theme\n"
    )
    with open("Release", "w", encoding="utf-8", newline="\n") as f:
        f.write(release)
    print("Generated Release")


if __name__ == "__main__":
    generate()
