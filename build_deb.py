#!/usr/bin/env python3
"""Build a .deb package without dpkg-deb (Windows compatible)."""
import os
import sys
import tarfile
import io
import struct

DEBIAN_BINARY = b"2.0\n"


def create_ar_archive(path: str, members: list[tuple[str, bytes]]):
    """Create a BSD ar archive containing named byte blobs.
    Members are (filename, data) pairs in order.
    """
    # Global header
    buf = io.BytesIO()
    buf.write(b"!<arch>\n")

    for name, data in members:
        # Pad odd-length names with newline
        name_bytes = name.encode()
        if len(name_bytes) % 2 == 1:
            name_bytes += b"\n"
        # Build header
        hdr = (
            name_bytes.ljust(16, b" ")
            + f"{int(os.environ.get('SOURCE_DATE_EPOCH', 0))}".rjust(12).encode()
            + b"0     "   # uid
            + b"0     "   # gid
            + b"100644  " # mode
            + f"{len(data)}".rjust(10).encode()
            + b"\x60\x0a"
        )
        assert len(hdr) == 60, f"ar header wrong size: {len(hdr)}"
        buf.write(hdr)
        buf.write(data)
        if len(data) % 2 == 1:
            buf.write(b"\n")  # pad even

    with open(path, "wb") as f:
        f.write(buf.getvalue())


def make_tar_gz_bytes(root: str) -> bytes:
    """Create a .tar.gz from a directory root, return as bytes."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for dirpath, _dirnames, filenames in os.walk(root):
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                arcname = os.path.relpath(full, root).replace("\\", "/")
                tar.add(full, arcname=arcname)
    return buf.getvalue()


def main():
    if len(sys.argv) != 5:
        print("Usage: build_deb.py <package_dir> <output.deb> <name> <version>")
        sys.exit(1)

    pkg_dir = sys.argv[1]
    deb_path = sys.argv[2]
    name = sys.argv[3]
    version = sys.argv[4]

    # control
    control_text = (
        f"Package: {name}\n"
        f"Name: MuMu Piano Theme\n"
        f"Version: {version}\n"
        f"Architecture: iphoneos-arm\n"
        f"Description: 钢琴风格美化主题 for SnowBoard\n"
        f"Maintainer: linmumupro\n"
        f"Author: linmumupro\n"
        f"Section: Themes\n"
        f"Depends: com.spark.snowboard\n"
    )

    # Build control.tar.gz
    control_dir = os.path.join(os.path.dirname(deb_path), ".ctrl_tmp")
    os.makedirs(control_dir, exist_ok=True)
    with open(os.path.join(control_dir, "control"), "w", encoding="utf-8") as fh:
        fh.write(control_text)

    control_gz = make_tar_gz_bytes(control_dir)

    # Clean
    import shutil
    shutil.rmtree(control_dir)

    # Build data.tar.gz from package_dir
    data_gz = make_tar_gz_bytes(pkg_dir)

    # Assemble .deb
    create_ar_archive(
        deb_path,
        [
            ("debian-binary", DEBIAN_BINARY),
            ("control.tar.gz", control_gz),
            ("data.tar.gz", data_gz),
        ],
    )
    print(f"Created: {deb_path}")


if __name__ == "__main__":
    main()
