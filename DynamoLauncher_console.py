import minecraft_launcher_lib
import subprocess

minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory().replace('minecraft', 'DynamoLauncher')

version = input('Enter Minecraft version: ')
username = input('Enter Username: ')

# Install Minecraft version with all dependencies needed
minecraft_launcher_lib.install.install_minecraft_version(versionid=version, minecraft_directory=minecraft_directory)

# Define launch options
options = {
    'username': username,
    'uuid': '',
    'token': ''
}

# Launch Minecraft
subprocess.call(minecraft_launcher_lib.command.get_minecraft_command(version=version, minecraft_directory=minecraft_directory, options=options))

# MIT License

# Copyright (c) 2023 Sstudiosdev

# this version is for developers to # maker the app work they need the # libraries off

# python
# minecraft-lancher-lib
