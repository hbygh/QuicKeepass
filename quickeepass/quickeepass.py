#!/usr/bin/python3
# Author: @chaignc

from pykeepass import PyKeePass, exceptions as kp_exceptions
from subprocess import Popen, PIPE, check_output
import argparse
import sys
import time
import os

def notify(message, do_print=True):
    """ show a message to the user"""
    if do_print:
        print(message)
    check_output(f'rofi -e "{message}"', shell=True)

def notify_error(message, do_print=True):
    """ show a ERROR message to the user"""
    notify(f"QuicKeepass ERROR: {message}\nAuthor: @chaignc", do_print=do_print)

class Config:
    """ config, Keybindings and advanced config
    """
    version = "0.4"
    key_user_pass = "Return"
    key_pass_only = "Alt+Return"
    rofi_conf = f'-sort -mesg QuicKeepass_By_@chaignc_v{version}'
    rofi_choice = f'{rofi_conf} -kb-accept-entry {key_pass_only} -kb-custom-1 {key_user_pass}'
    rofi_ask_password = f'{rofi_conf}'
    # args sent by the user from cmdline
    rofi_userargs = f''

def sh(cmd, stdin="", sleep=False):
    """ run a command, send stdin and capture stdout and exit status"""
    if sleep:
        time.sleep(0.5)
    # process = Popen(cmd.split(), stdin=PIPE, stdout=PIPE)
    process = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE)
    process.stdin.write(bytes(stdin, "utf-8"))
    stdout = process.communicate()[0].decode('utf-8').strip()
    process.stdin.close()
    returncode = process.returncode
    return returncode, stdout

def rofi(cmd, stdin="", sleep=False):
    returncode, stdout = sh(cmd, stdin, sleep)
    if returncode == 1: # Escape Key
        sys.exit(1)
    return returncode, stdout
    
def ask_password(message):
    """ ask password using rofi """
    return rofi(f'rofi -password -p "{message}" -dmenu {Config.rofi_ask_password} {Config.rofi_userargs}')

def ask_choice(choices):
    """ multiple choice using rofi """
    return rofi(f'rofi -dmenu -p URL {Config.rofi_choice} {Config.rofi_userargs}', stdin='\n'.join(choices))

def autotype(username, password, returncode):
    """ autotype username and password
    Parameters
    ----------
    returncode : str
        user typed key to decide if we autotype password only or username&password
    """
    if returncode == 10: # type username
        sh(f"xdotool type --file /dev/stdin", stdin=username, sleep=True)
        sh(f"xdotool key Tab", sleep=True)
    # type password
    sh(f"xdotool type --file /dev/stdin", stdin=password, sleep=True)
    sh(f"xdotool key Return", sleep=True)

def do_check_dependencies(tool, install_instruction):
    returncode, _ = sh(f"which {tool}")
    if returncode:
        print(f"{tool} not found please => {install_instruction}")
        sys.exit(1)

def check_dependencies():
    do_check_dependencies("rofi", "apt install rofi")
    do_check_dependencies("xdotool", "apt install xdotool")

def opendatabase(database, password, keyfile):
    keepassargs = dict()
    if password:
        keepassargs["password"] = ask_password(f"Enter {os.path.basename(filename)} Password")[1]
    if keyfile:
        keepassargs["keyfile"] = keyfile
    kp = PyKeePass(database, **keepassargs)
    return kp

def quickeeepass(args):
    """ open filename keepass database and autotype password
    Parameters
    ----------
    filename : str
        Keepass database input
    """
    # save active window
    window = sh("xdotool getactivewindow")[1]
    # open keepass database
    kp = opendatabase(args.database, args.password, args.keyfile)
    # prepare rofi selection for user
    choices = [ f"{e.title} {e.url} {e.group}" for e in kp.entries ]
    # ask user to choose a password
    returncode, choice = ask_choice(choices)
    # retriver user choosed password
    entry = kp.entries[choices.index(choice)]
    # restore active window
    sh(f"xdotool windowactivate {window}")
    autotype(entry.username, entry.password, returncode)

class ArgumentParser(argparse.ArgumentParser):    

    def error(self, message):
        notify_error(message, do_print=False)
        super(ArgumentParser, self).error(message)

    @staticmethod
    def parse_sys_argv():
        parser = ArgumentParser(prog='QuicKeepass', description='QuicKeepass')
        parser.add_argument('database', type=argparse.FileType('r'), help='keepass database')
        parser.add_argument('--password', dest='password', default=False, action='store_true')
        parser.add_argument('--keyfile', type=argparse.FileType('r'), dest='keyfile')
        parser.add_argument('--rofiargs', type=str, default="", help='aditional parameters for rofi')

        args = parser.parse_args()

        args.database = args.database.name
        Config.rofi_userargs = args.rofiargs

        if args.keyfile is None:
            args.password = True
        else:
            args.keyfile = args.keyfile.name
        return args

def main():
    check_dependencies()
    args = ArgumentParser.parse_sys_argv()
    try:
        quickeeepass(args)
    except Exception as e:
        notify_error(e)

if __name__ == "__main__":
    main()
