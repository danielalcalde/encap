import os
import re
import socket
import subprocess
import threading
from argparse import ArgumentParser
import secrets

from fabric import Connection
import paramiko

class SSHMachine:
    def __init__(self, host):

        self.host = host
        try:
            self.conn = Connection(self.host)
            self.conn.open()
        except paramiko.ssh_exception.ChannelException as e:
            print("Error:", e, "for host:", self.host)
            self.conn = None
            self.client = None
            return

        self.client = self.conn.client 
    
    def get_host(self):
        if self.username is not None:
            return f"{self.username}@{self.host}"
        else:
            return self.host
    
    def run_code(self, command, verbose=False, wait=True, debug=False, ignore=[]):
        if debug: print(command)

        chan = self.client._transport.open_session()
        chan.set_combine_stderr(True)
        chan.settimeout(None)
        #environment = {"PYTHONUNBUFFERED" : 1}
        #chan.update_environment(environment)
        chan.exec_command(command)
        stdin = chan.makefile_stdin("wb", -1)
        stdout = chan.makefile("r", -1)

        #subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, executable="/bin/bash")
        if wait == False:
            return stdout

        return follow_output(stdout, verbose=verbose)
    
    def open_ssh_tunnel(self, eport, lport):
        #o = machine.conn.forward_local(eport, lport)
        #o.__enter__()
        return run_code_local(f"ssh -N -f -L localhost:{lport}:localhost:{eport} {self.host}", verbose=False, wait=False, debug=True)

def run_code_local(command, verbose=False, wait=True, debug=False, ignore=[]):
    if debug: print(command)
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, executable="/bin/bash")
    if not wait:
        return p.stdout
    
    return follow_output(p.stdout, verbose=verbose)

def follow_output(stdout, verbose=False):
    lines = []
    for line in stdout:
        if hasattr(line, "decode"):
            line = line.decode("utf-8")

        lll = line[:-1]
        if verbose: print(lll)
        lines.append(lll)
    
    return lines