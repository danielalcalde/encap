import time
from encap_lib.machines import SSHMachine, LocalMachine, run_code_local
import encap_lib.encap_settings as settings

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

# Minimal memory requirements for 16 August 2019
def get_minimal_memory(cpus):
    if cpus == 1:
        return 1.
    else:
        return int((cpus - 1) // 10 + 1) * 0.25 + 1.75 * cpus / 2

def list_instances(project):
    global instances
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