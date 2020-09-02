import os
import yaml
config_folder = os.getenv("HOME") + "/.encap"
temp_file = config_folder + "/temp"

config_file_name = config_folder + "/config.yml"

running_processes_file = os.getenv("HOME") + "/.encap/running_processes.yml"
config_items = ["dir", "ip", "sync", "user", "ssh_ignore", "ssh_options", "sync_files",
                "rsync_exclude", "project", "zone", "nfs", "machine_config",
                "GOOGLE_APPLICATION_CREDENTIALS", "machine_config"]

# If .encap does not exist
if not os.path.isdir(config_folder):
    os.mkdir(config_folder)

# If .encap/config.yml does not exist
if not os.path.isfile(config_file_name):
    f = {"py": "python -u", "sh": "bash"}
    d = {"file_extension": f}
    with open(config_file_name, 'w') as ymlfile:
        yaml.dump(d, ymlfile, default_flow_style=False)

with open(config_file_name, 'r') as ymlfile:
    config = yaml.load(ymlfile)

debug = False
dryrun = False


def get_item(item, config_location):
    cc = config
    out = None
    for loc in config_location:
        if item in cc:
            out = cc[item]
        cc = cc[loc]
    if item in cc:
        out = cc[item]
    return out

def get_all_items(config_location):
    out = dict()
    for item in config_items:
        out[item] = get_item(item, config_location)
    return out
