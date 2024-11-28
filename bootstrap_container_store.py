#!/usr/bin/env python3
import os
import shutil
import argparse


def get_blacklist(blacklist_file:str)->set:
    """
    Reads the blacklist file and returns a set of filenames to exclude.
    """
    if not os.path.exists(blacklist_file):
        return set()
    try:
        with open(blacklist_file, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except Exception as e:
        print(f"Error reading blacklist file: {e}")
        return set()    

def copy_dotfiles(args:argparse.Namespace)->None:
    """
    Copies dotfiles and dot directories from the user's home directory
    to the destination directory, excluding those in the blacklist.
    """
    destdir = args.destdir
    blacklist_file = args.blacklist
    docker_dirs_on_host = args.docker_dirs_on_host
    dummy_flag = args.dummy

    destdir=os.path.join(docker_dirs_on_host,destdir)
    homedir = os.path.expanduser("~")
    blacklist = get_blacklist(blacklist_file)
    if not os.path.exists(destdir):
        try:
            os.makedirs(destdir)
        except Exception as e:
            print(f"Error creating destination directory: {e}")
            return
    print(f"Copying dotfiles to {homedir}->{destdir}")
    for item in os.listdir(homedir):
        if item.startswith('.') and item not in ('.', '..', blacklist):
            src_path = os.path.join(homedir, item)
            dest_path = os.path.join(destdir, item)
            try:
                if os.path.isdir(src_path):
                    print(f"copytree: {src_path} -> {dest_path}")
                    if False is dummy_flag:
                        shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                else:
                    print(f"copy2: {src_path} -> {dest_path}")
                    if False is dummy_flag:
                        shutil.copy2(src_path, dest_path)
            except Exception as e:
                print(f"Error copying {src_path}: {e}")

                

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy dotfiles and dot directories to a destination directory.",formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--destdir", help="Destination directory (default=%(default)s)",default="private-rocm-torch")
    parser.add_argument("--docker-dirs-on-host", default="~/DOCKER-DIRS-ON-HOST", help="Destination directory (default: %(default)s)")
    parser.add_argument("--blacklist", default="blacklist.txt", help="Blacklist file containing names to exclude (default:%(default)s)")
    parser.add_argument("--dummy", action="store_true", help="Dry run (don't copy)")
    args = parser.parse_args()
    copy_dotfiles(args)
