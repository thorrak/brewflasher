
# Used like: python compile_languages.py /path/to/directory

import os
import argparse
import subprocess
import sys

def compile_po_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".po"):
                po_file_path = os.path.join(root, file)
                mo_file_path = os.path.splitext(po_file_path)[0] + '.mo'
                try:
                    # subprocess.run(["python", "msgfmt.py", "-o", mo_file_path, po_file_path], check=True)
                    subprocess.run(["pybabel", "compile", "-i", po_file_path, "-o", mo_file_path], check=True)
                    # print(f"Compiled {po_file_path} to {mo_file_path}")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to compile {po_file_path} due to error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compile .po files to .mo using msgfmt.py')
    parser.add_argument('directory', type=str, help='The root directory to start the search for .po files')
    args = parser.parse_args()

    if 'directory' not in 'args':
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(
            os.path.dirname(__file__)))  # get the bundle dir if bundled or simply the __file__ dir if not bundled
        localedir = os.path.abspath(os.path.join(bundle_dir, 'locales'))
        args.directory = localedir
        print(f"Defaulting to {args.directory}")
    else:
        print(f"Traversing provided directory {args.directory}")

    compile_po_files(args.directory)
