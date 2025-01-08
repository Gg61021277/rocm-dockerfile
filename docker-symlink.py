#!/usr/bin/env python3
import os
import re
import argparse
import xml.etree.ElementTree as ET
import shutil
import logging
from ggtoolset.Utils import Logger
global_context={}

# Define a class to match the XML structure
class LinkOperations:
    def __init__(self,  marker_file, 
                        private_host_directory,
                        public_link_directory, 
                        public_files_to_exclude, 
                        private_files_to_exclude):
        self.marker_file = marker_file
        self.private_host_directory = private_host_directory
        self.public_link_directory = public_link_directory
        self.public_files_to_exclude = public_files_to_exclude
        self.private_files_to_exclude = private_files_to_exclude
        self.persist_docker_directory = private_host_directory

    @staticmethod
    def from_xml(file_path:str)->'LinkOperations':
        """!
        @brief Read the XML file and return an instance of the class
        @param file_path Path to the XML file
        @return Instance of the class
        """
        tree = ET.parse(file_path)
        root = tree.getroot()
        marker_file = root.findtext("markerFile")
        #There are directories that have config and other information private to every instance of docker container.
        #They generally start with a dot.  We have kept a copy of these dot files in a provate directory on the host
        #We want to link these directories to the home directory
        private_host_directory = root.findtext("privateHostDirectory")
        private_files_to_exclude = [file.text for file in root.find("privateFilesToExclude").findall("file")]

        # Add public link directory. The ${USER}/home is mounted to this directory
        public_link_directory = root.findtext("publicLinkDirectory")
        #The files that will not be linked from the user home directory ( now called public link directory)
        public_files_to_exclude = [file.text for file in root.find("publicFilesToExclude").findall("file")]
        return LinkOperations(marker_file, 
                              private_host_directory,
                              public_link_directory,
                              public_files_to_exclude, 
                              private_files_to_exclude)

def create_symlinks(host_dir:str, current_dir:str, files_to_exclude:str)->None:
    """!
    @brief Create symlinks for the items in the host directory
    @param host_dir Path to the host directory
    @param current_dir Path to the current directory
    @param files_to_exclude List of files to exclude
    """
    logger=global_context["logger"]
    logger.debug(f"Creating symlinks for directory: {host_dir}")
    linked_files = []
    try:
        items = os.listdir(host_dir)
    except Exception as e:
        logger.error(f"Error reading directory {host_dir}: {e}")
        return
    # Create symlinks for each item
    for item in items:
        host_item_path = os.path.join(host_dir, item)
        symlink_path = os.path.join(current_dir, item)
        # Check if symlink already exists
        if os.path.lexists(symlink_path):
            logger.debug(f"\tSymlink already exists for: {item}")
            continue
        skip_flag = False
        # Check if item is in the list of files to exclude
        logger.debug(f"\tChecking file: {item} for exclusion: {files_to_exclude}")
        for pattern in files_to_exclude or []:
            if pattern is None:
                continue
            logger.debug(f"\tChecking pattern: {pattern}")
            if re.search(pattern, item):
                logger.debug(f"\tExcluding file: {item}")
                skip_flag = True
                break
        if skip_flag is True:
            continue
        # Create the symlink
        try:
            if False==global_context["args"].dummy:
                os.symlink(host_item_path, symlink_path)
            logger.debug(f"\tSymlink created for: {item}")
            linked_files.append(symlink_path)
        except Exception as e:
            logger.error(f"\tError creating symlink for {item}: {e}")
    return

def create_new_files_in_persist(current_dir:str, persist_dir:str,
                                local_dir:str, host_dir:str)->None:
    """!
    @brief Create new files in the persist directory
    @param current_dir Path to the current directory
    @param persist_dir Path to the persist directory
    @param host_dir Path to the host directory
    @param local_dir Path to the local directory
    """
    logger=global_context["logger"]
    logger.debug(f"Creating new files in persist directory: {persist_dir}")
    try:
        os.makedirs(persist_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Error creating persist directory {persist_dir}: {e}")
        return
    # Get the list of items in the current directory
    current_items = os.listdir(current_dir)
    host_items=os.listdir(host_dir)
    # Get the list of items in the host directory
    local_items = os.listdir(local_dir)
    for item in current_items:
        if re.search(host_dir, item):
            logger.debug(f"Skipping file as it is the host directory: {item} is {host_dir}")
            continue
        if item in local_items:
            logger.debug(f"Skipping file as it is present in docker private store: {item}")
            continue
        if item in host_items:
            logger.debug(f"Skipping file as it is present in host store: {item}")
            continue
        #This file is not present in the local or host. We need to copy it to the persist directory
        # Get the path of the item
        item_path = os.path.join(current_dir, item)
        # Get the path of the item in the persist directory
        persist_item_path = os.path.join(persist_dir, item)
        # Copy the file or directory tree to the host directory
        try:
            if os.path.isdir(item_path):
                logger.debug(f"Copying directory: shutil.copytree ({item_path} , {persist_item_path} )")
                if global_context["args"].dummy==False:
                    shutil.copytree(item_path, persist_item_path)
            else:
                logger.debug(f"Copying file: shutil.copy2 ({item_path} , {persist_item_path} )")
                if global_context["args"].dummy==False:
                    shutil.copy2(item_path, persist_item_path)
        except Exception as e:
            logger.debug(f"Error copying {item} to {persist_dir}: {e}")
    return

def entry_main(args:argparse.Namespace)->None:
    """!
    @brief Entry function for the script
    @param args Arguments passed to the script
    """
    if args.debug:
        level=logging.DEBUG
    else:
        level=logging.INFO
    global_context["logger"]=Logger.get_logger("symlink",level=level,log_file="./symlink_entry.log")
    logger=global_context["logger"]
    try:
        current_dir = os.getcwd()
    except Exception as e:
        logger.error(f"Error getting current directory: {e}")
        return
    try:
        link_ops = LinkOperations.from_xml(args.config)
    except Exception as e:
        logger.error(f"Error reading XML file: {e}")
        return
    public_dir = link_ops.public_link_directory
    #private dir is the directory that has the files that are private to the docker 
    #container and located in a directory relative to the home directory
    private_dir = os.path.join(public_dir,link_ops.private_host_directory)
    # Check if private_dir exists, if not create it
    if not os.path.exists(private_dir):
        try:
            os.makedirs(private_dir)
            logger.debug(f"Created private directory: {private_dir}")
        except Exception as e:
            logger.error(f"Error creating private directory {private_dir}: {e}")
            return
    existing_dirs_list = [".local", ".cache", ".config"]  # Directories to create if they do not exist
    #These dirs are created as they can exist on your local host and we are creating symlinks. 
    #The symlink can add a path from your home directory to the docker container which is not
    #what we want. So we create these directories in the private directory
    for dir_name in existing_dirs_list:
        dir_path = os.path.join(private_dir, dir_name)
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
                logger.debug(f"Created directory: {dir_path}")
            except Exception as e:
                logger.error(f"Error creating directory {dir_path}: {e}")
    logger.debug(f"Processing Private Link Directory: {private_dir}")
    create_symlinks(private_dir, current_dir, link_ops.private_files_to_exclude)
    logger.debug(f"Processing Public Link Directory: {public_dir}")
    public_files_to_exclude = link_ops.public_files_to_exclude
    create_symlinks(public_dir, current_dir, public_files_to_exclude)
    # Create marker file
    try:
        with open(link_ops.marker_file, "w",encoding='utf-8') as marker_file:
            marker_file.write("This is a marker file.")
    except Exception as e:
        logger.debug(f"Error creating marker file: {e}")

def exit_main(args:argparse.Namespace)->None:
    """!
    @brief Exit function for the script
    @param args Arguments passed to the script
    """
    if args.debug:
        level=logging.DEBUG
    else:
        level=logging.INFO
    global_context["logger"]=Logger.get_logger("symlink",level=level,log_file="./symlink_exit.log")
    logger=global_context["logger"]
    try:
        current_dir = os.getcwd()
    except Exception as e:
        logger.debug(f"Error getting current directory: {e}")
        return
    try:
        link_ops = LinkOperations.from_xml(args.config)
    except Exception as e:
        logger.debug(f"Error reading XML file: {e}")
        return
    public_dir = link_ops.public_link_directory
    private_dir = os.path.join(public_dir,link_ops.private_host_directory)
    persist_dir = os.path.join(public_dir,link_ops.persist_docker_directory)
    create_new_files_in_persist(current_dir, persist_dir, private_dir, public_dir)
    return

def main()->None:
    """!
    @brief Main function for the script
    """
    parser = argparse.ArgumentParser(description="Create symlinks based on XML configuration.")
    parser.add_argument('--exit', action='store_true', help='Exit the program',default=False)
    parser.add_argument('--dummy', action='store_true', help='Dummy run',default=False)
    parser.add_argument('--debug', action='store_true', help='Debug mode',default=False)
    parser.add_argument('--config', type=str, required=True, help='Path to the XML configuration file',default="config_symlink.xml")
    args = parser.parse_args()
    print(f"{args}")
    global_context["args"]=args
    if args.exit:
        exit_main(args)
    else:
        entry_main(args)
    return

if __name__ == "__main__":
    main()
