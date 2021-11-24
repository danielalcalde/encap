import time
import os
from getpass import getuser
import warnings
import yaml
import encap_lib.encap_settings as settings
from datetime import date
# pip install --upgrade google-api-python-client

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

import subprocess
class Machine:
    def __init__(self):
        pass

    def write_file(self, name, content, *args, **kwargs):
        command = f"""
        echo -e {repr(content)} > "{name}"
        """
        return self.run_code(command, *args, **kwargs)

    def run_code(self, command, *args, **kwargs):
        pass

    def push(self, name_local, name_target, directory=True, *args, **kwargs):
        pass

    def pull(self, name_vm, name_local, directory=False, *args, **kwargs):
        pass

    def sync_files(self):
        pass

class SSHMachine(Machine):

    def __init__(self, ip, username, local_project_dir, remote_project_dir, ssh_options="",
                ssh_ignore=[], sync_files=[], rsync_exclude=[], sync=True, **kwargs):
        super().__init__(**kwargs)
        self.ip = ip
        self.username = username
        self.local_project_dir = local_project_dir
        self.remote_project_dir = remote_project_dir
        self.ssh_options = ssh_options
        self.ssh_ignore = ssh_ignore
        self._sync_files = sync_files
        self.rsync_exclude = rsync_exclude
        self.sync = sync

    @property
    def user(self):
        return self.username

    def run_code(self, command, *args, **kwargs):
        command = f"""
        source /etc/profile
        source ~/.bashrc
        cd {self.remote_project_dir}
        """ + command

        # Write command to txt file
        with open(settings.temp_file, "w") as text_file:
            text_file.write(command)

        if ("debug" in kwargs and kwargs["debug"]) or settings.debug:
            print(command)


        c = f"ssh {self.ssh_options} {self.username}@{self.ip}  'bash -s' < {settings.temp_file}"
        if "ignore" in kwargs:
            ignore = self.ssh_ignore + kwargs["ignore"]
            del kwargs["ignore"]
        else:
            ignore = self.ssh_ignore

        output = run_code_local(c, ignore=ignore, *args, **kwargs)
        return output

    def push(self, name_local, name_target, directory=True, *args, **kwargs):
        # Upload file to VM
        if not self.sync and name_local == name_target:
            return None

        i = name_target[::-1].find("/")
        if i == -1:
            folder = ""
        else:
            i = len(name_target) - i - 1
            folder = name_target[:i]

            code = f"mkdir -p {folder}"
            self.run_code(code, *args, **kwargs)

        if directory:
            recursiv = "-r"
        else:
            recursiv = ""

        code = f"scp {self.ssh_options} {recursiv} {self.local_project_dir}/{name_local} {self.username}@{self.ip}:{self.remote_project_dir}/{folder}"
        return run_code_local(code, *args, **kwargs)

    def pull(self, file_name_vm, file_name_local, directory=False, *args, **kwargs):
        # Download file from VM
        #assert name_local != ""
        if not self.sync and file_name_vm == file_name_local:
            return None

        i = file_name_local[::-1].find("/")
        if i == -1:
            folder = ""

        else:
            i = len(file_name_local) - i - 1
            folder = file_name_local[: i]

            code = f"mkdir -p {folder}"
            run_code_local(code, *args, **kwargs)

        if directory:
            recursiv = "-r"
        else:
            recursiv = ""

        code = f"scp {self.ssh_options} {recursiv} {self.username}@{self.ip}:{self.remote_project_dir}/{file_name_vm} {self.local_project_dir}/{folder}"
        run_code_local(code, *args, **kwargs)

    def rsync_push(self, name_local, name_target, directory=True, dry_run=False, last_timestamp_prevails=True, delete=False, *args, **kwargs):
        # Upload file to VM

        i = name_target[::-1].find("/")
        if i == -1:
            folder = ""
        else:
            i = len(name_target) - i - 1
            folder = name_target[:i]

            code = f"mkdir -p {folder}"
            self.run_code(code, *args, **kwargs)

        if directory:
            options = "-rz"
        else:
            options = "-z"

        if dry_run:
            options = "--dry-run " + options

        if last_timestamp_prevails:
            options = "--update " + options

        if delete:
            options = "--delete " + options

        for exclude in self.rsync_exclude:
            options = f"--exclude '{exclude}' " + options

        code = f"""rsync {options} -v -e "ssh {self.ssh_options}" {self.local_project_dir}/{name_local} {self.username}@{self.ip}:{self.remote_project_dir}/{folder}"""
        return run_code_local(code, *args, **kwargs)

    def sync_files(self):
        for line in self._sync_files:
            self.rsync_push(line, line, last_timestamp_prevails=True, directory=True,
                            verbose=True, ignore=self.ssh_ignore + ["sending incremental", "sent ", "total size"])

    def interactive_ssh(self):
        command = f"ssh {self.ssh_options} {self.username}@{self.ip}"

        if settings.debug:
            print(command)
        os.system(command)

class GCMachine(SSHMachine):
    def __init__(self, vm, username, local_project_dir, remote_project_dir, zone, project, nfs_name=None, machine_config=None, **kwargs):
        # If True will write the timeout variable to ~/.encap/timeout
        write_timeout = False

        self.nfs = None
        if nfs_name is not None:
            self.nfs = GCMachine(nfs_name, username, local_project_dir, remote_project_dir, zone, project, **kwargs)

        self.vm = vm
        self.project = project
        self.vm_info = self.get_info()


        if self.vm_info is None:
            c = input(f"The VM {self.vm} does not exist. Do you whish to create it? y/n : ")
            if c == "y":
                assert machine_config is not None, "The configuration file has no entry for machine_config."
                core_number = 2
                timeout = 10
                memory = get_minimal_memory(core_number)
                flags = ""

                if "core_number" in machine_config:
                    core_number = machine_config["core_number"]
                    memory = get_minimal_memory(core_number)

                if "preemptible" in machine_config:
                    preemptible = machine_config["preemptible"]
                else:
                    preemptible = False

                if "timeout" in machine_config:
                    timeout = machine_config["timeout"]

                if "memory" in machine_config:
                    memory = machine_config["memory"]

                if "flags" in machine_config:
                    flags = machine_config["flags"]


                c = input(f"Input core number={core_number}, preemptible={preemptible*1}, timeout={timeout}m, memory={memory}GB, flags={flags}, seperate by comas, leave empty for default: \n")
                settings = c.replace(" ", "").split(',')
                ls = len(settings)
                if ls > 0:
                    if settings[0].isdigit():
                        core_number = int(settings[0])
                        memory = get_minimal_memory(core_number)

                if ls > 1:
                    if settings[1].isdigit():
                        preemptible = int(settings[1]) == 1

                if ls > 2:
                    if settings[2].isdigit():
                        timeout = int(settings[2])

                if ls > 3:
                    if isfloat(settings[3]):
                        memory = float(settings[3])

                if ls > 4:
                    flags = settings[4]

                c = input(f"Is this correct core number={core_number}, preemptible={preemptible*1}, timeout={timeout}m, memory={memory}GB, flags={flags} ?:")
                if c == "" or c == "y":
                    image = machine_config["image"]

                    create_machine(vm, core_number, memory, image, zone, self.project, flags, preemptible=preemptible)
                    write_timeout = True

                else:
                    quit()
            else:
                quit()

        if zone is None:
            zone = self.vm_info['zone']

        self.zone = zone
        # Starts VM if it is off
        self.start_vm()
        ip = self.vm_info["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
        super().__init__(username=username, ip=ip, local_project_dir=local_project_dir, remote_project_dir=remote_project_dir, **kwargs)
        if write_timeout:
            out = self.run_code(f"echo {timeout} > ~/.encap/timeout", verbose=True)
            if len(out) > 0:
                out = self.run_code(f"echo {timeout} > ~/.encap/timeout", verbose=True)

                if len(out) > 0:
                    out = self.run_code(f"echo {timeout} > ~/.encap/timeout", verbose=True)

                else:
                    print(f"Timeout {timeout} could not be written to ~/.encap/timeout")
                    quit()

    def start_vm(self):
        self.vm_info = self.get_info()
        while self.vm_info['status'] != 'RUNNING':

            if self.vm_info['status'] == "TERMINATED":
                c = input(f"The VM {self.vm} is not running. Status is {self.vm_info['status']}. Do you whish to start it? y/n : ")

                if c == "y" or c == "Y":
                    out = instances.start(project=self.project, zone=self.zone, instance=self.vm).execute()
                    time.sleep(20)
                    self.vm_info = self.get_info()
                else:
                    quit()
            else :
                time.sleep(1)
                print(f"Status is {self.vm_info['status']}.")
            self.vm_info = self.get_info()

    def get_info(self):
        instances_list = list_instances(self.project)

        if self.vm in instances_list:
            return instances_list[self.vm]
        else:
            return None

    def push(self, *args, **kwargs):
        if self.nfs is not None:
            return self.nfs.push(*args, **kwargs)
        else:
            return super().push(*args, **kwargs)

    def pull(self, *args, **kwargs):
        if self.nfs is not None:
            return self.nfs.pull(*args, **kwargs)
        else:
            return super().pull(*args, **kwargs)

    def rsync_push(self, *args, **kwargs):
        if self.nfs is not None:
            return self.nfs.rsync_push(*args, **kwargs)
        else:
            return super().rsync_push(*args, **kwargs)

    def sync_files(self, *args, **kwargs):
        if self.nfs is not None:
            return self.nfs.sync_files(*args, **kwargs)
        else:
            return super().sync_files(*args, **kwargs)

class LocalMachine(Machine):
    def __init__(self, local_project_dir, **kwargs):
        self.local_project_dir = local_project_dir
        self.username = getuser()
        super().__init__(**kwargs)

    def run_code(self, command, *args, **kwargs):

        command = f'''cd {self.local_project_dir}
         ''' + command

        return run_code_local(command, *args, **kwargs)

    def push(self, name_local, name_target, directory=True, copy_full_dir=True, *args, **kwargs):
        if name_local != name_target:
            # Copy file

            i = name_target[::-1].find("/")
            if i == -1:
                folder = ""
            else:
                i = len(name_target) - i - 1
                folder = name_target[:i]

                code = f"mkdir -p {folder}"
                run_code_local(code, *args, **kwargs)

            if directory:
                recursiv = "-r"
                if not copy_full_dir:
                    name_local += "/."
            else:
                recursiv = ""

            code = f"cp {recursiv} {self.local_project_dir}/{name_local} {self.local_project_dir}/{folder}"
            run_code_local(code, *args, **kwargs)

    def pull(self, name_vm, name_local, directory=False, *args, **kwargs):
        pass

    def sync_files(self):
        pass



# Checks if the name of the vm matches the signature in the config file
def is_it_ssh(vm, local_project_dir):
    if "ssh" in settings.config["projects"][local_project_dir]:
        if vm in settings.config["projects"][local_project_dir]["ssh"]:
            return True
    return False


# Checks if the name of the vm matches the signature in the config file
def is_it_gcloud(vm, local_project_dir):
    if "gcloud" in settings.config["projects"][local_project_dir]:
        signature_gcloud = list(settings.config["signature"]["gcloud"].keys())
        is_it = False
        for s in signature_gcloud:
            if s == vm[:len(s)]:
                is_it = True
        return is_it

    return False

def get_machine(vm, local_project_dir):

    if local_project_dir not in settings.config["projects"]:
        raise Exception(f"{local_project_dir} has no configuraion entry in {settings.config_file_name}.")

    ssh_options= ""
    ssh_ignore = []
    sync_files = []
    rsync_exclude = []


    if is_it_ssh(vm, local_project_dir):

        settings_project = settings.get_all_items(["projects", local_project_dir, "ssh", vm])

        ssh_kwargs = {}
        copy_dict_keys = ["ssh_options", "ssh_ignore", "sync_files", "rsync_exclude", "sync"]

        for key in copy_dict_keys:
            if settings_project[key] is not None:
                ssh_kwargs[key] = settings_project[key]

        remote_project_dir = settings_project["dir"]
        ip = settings_project["ip"]
        username = settings_project["user"]

        machine = SSHMachine(ip=ip, username=username, local_project_dir=local_project_dir,
                            remote_project_dir=remote_project_dir, **ssh_kwargs)

    elif is_it_gcloud(vm, local_project_dir):

        settings_project = settings.get_all_items(["projects", local_project_dir, "gcloud"])

        if settings_project['GOOGLE_APPLICATION_CREDENTIALS'] is not None:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings_project['GOOGLE_APPLICATION_CREDENTIALS']

        with warnings.catch_warnings():
            global instances, compute
            # pip install --upgrade google-api-python-client
            warnings.simplefilter("ignore")
            import apiclient.discovery
            compute = apiclient.discovery.build('compute', 'v1')
            instances = compute.instances()

        if settings_project["ssh_options"] is not None:
            ssh_options = settings_project["ssh_options"]

        if settings_project["ssh_ignore"] is not None:
            ssh_ignore = settings_project["ssh_ignore"]

        if settings_project["sync_files"] is not None:
            sync_files = settings_project["sync_files"]

        if settings_project["rsync_exclude"] is not None:
            rsync_exclude = settings_project["rsync_exclude"]


        remote_project_dir = settings_project["dir"]
        username = settings_project["user"]
        zone = settings_project["zone"]
        machine_config = settings_project["machine_config"]
        project = settings_project["project"]
        nfs = settings_project["nfs"]

        machine = GCMachine(vm=vm, username=username, local_project_dir=local_project_dir,
                            remote_project_dir=remote_project_dir, ssh_options=ssh_options,
                            ssh_ignore=ssh_ignore, sync_files=sync_files, rsync_exclude=rsync_exclude,
                            zone=zone, project=project, machine_config=machine_config, nfs_name=nfs)


    else:
        raise Exception(f"The VM name '{vm}' does not match any of the ssh instances nor the gcloud signature.")

    machine.settings = settings_project
    
    return machine

def should_it_be_ignored(string, ignore):
    l = len(string)
    for i, si in enumerate(ignore):
        ls = len(si)
        #print(si == string[:min(ls,l)])
        #print(si, string[:min(ls,l)])
        if l >= ls and si == string[:ls]:
            return True
    return False


def run_code_local(command, output=True, verbose=False, wait=True, debug=False, ignore=[]):
    if settings.debug:
        debug = True

    if debug: print(command)
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, executable="/bin/bash")
    if wait == False:
        return p.pid

    if output:
        lines = []
        #for line in p.stdout.readlines():
        for line in p.stdout:
            lll = line.decode("utf-8")[:-1]
            if not should_it_be_ignored(lll, ignore):
                if verbose: print(lll)
                lines.append(lll)
        retval = p.wait()
        return lines

    else:
        return p.pid

def preempted():
    command = 'gcloud compute operations list --filter="operationType=compute.instances.preempted"'
    output = run_code(command, output=True)

# Minimal memory requirements for 16 August 2019
def get_minimal_memory(cpus):
    if cpus == 1:
        return 1.
    else:
        return int((cpus - 1) // 10 + 1) * 0.25 + 1.75 * cpus / 2

def list_instances(project):
    result = instances.aggregatedList(project=project).execute()
    if "items" in result:
        instances_list = {}
        for key, item in result['items'].items():
             if 'instances' in item:
                 for i in item['instances']:
                     i['zone'] = key[6:]
                     instances_list[i['name']] = i
        return instances_list
    else:
        return None

def create_machine(vm, core_number, memory, image, zone, project, flags, preemptible=True):

    command = f"gcloud beta compute --project={project} instances create {vm} --custom-cpu {core_number} --custom-memory {int(memory * 1024)}MB --zone {zone} --image={image} {flags}"

    if preemptible:
        command = command + " --preemptible"

    output = run_code_local(command, verbose=True)
    assert not output[0][:5] == "ERROR"
    #print(command)

def get_interpreter_from_file_extension(f):
    if f == "":
        return ""
    return settings.config["file_extension"][f]

def filename_and_file_extension(a):
    a_split = a.split(".")
    # If there is no .
    if len(a_split) == 1:
        return a, ""
    else:
        file_extension = a_split[-1]
        file_without_extension = a[:-len(file_extension) - 1]
        return file_without_extension, file_extension

def extract_folder_name(a):
    a_split = a.split("/")
    return a_split[-1]

def record_process(vm, name, i):
    remove_process_from_database(name, i)

    with open(settings.running_processes_file, 'r') as ymlfile:
        running = yaml.load(ymlfile, Loader=yaml.FullLoader)

    running["running"] += [[vm, name, i, date.today()]]
    with open(settings.running_processes_file, 'w') as yml_file:
        yaml.dump(running, yml_file, default_flow_style=False)

def remove_process_from_database(name, i):
    """
    Remove a process from the running processes file.
    args: name: name of the process
            i: index of the process
    """
    try:
        with open(settings.running_processes_file, 'r') as ymlfile:
            running = yaml.load(ymlfile, Loader=yaml.FullLoader)
    except FileNotFoundError:
        running = {"running": []}

    # Go backwards so that the deleteion does not mess with the indices
    for j in range(len(running["running"]))[::-1]:
        item = running["running"][j]
        if item[1] == name and item[2] == i:
            del running["running"][j]

    with open(settings.running_processes_file, 'w') as yml_file:
        yaml.dump(running, yml_file, default_flow_style=False)

def get_all_processes():
    try:
        with open(settings.running_processes_file, 'r') as ymlfile:
            running = yaml.load(ymlfile)
    except FileNotFoundError:
        running = {"running": []}

    return running["running"]

def changedir(s):
    os.chdir(os.path.dirname(os.path.realpath(s)))
