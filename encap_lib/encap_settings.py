import os
import yaml
import sys

config_folder = os.getenv("HOME") + "/.encap"
temp_file = config_folder + "/temp"

config_file_name = config_folder + "/config.yml"

running_processes_file = os.getenv("HOME") + "/.encap/running_processes.yml"
config_items = ["dir", "ip", "sync", "user", "ssh_ignore", "ssh_options", "sync_files",
                "rsync_exclude", "project", "zone", "nfs", "machine_config",
                "GOOGLE_APPLICATION_CREDENTIALS", "machine_config", "slurm"]

# If .encap does not exist
if not os.path.isdir(config_folder):
    os.mkdir(config_folder)

# If .encap/config.yml does not exist
if not os.path.isfile(config_file_name):
    f = {"py": "python -u", "sh": "bash"}
    d = {"file_extension": f}
    with open(config_file_name, 'w') as ymlfile:
        yaml.dump(d, ymlfile, default_flow_style=False)


# Try to find a .encap file in parent directories
path = os.getcwd()
rest = "a"
while rest != "":
    path, rest = os.path.split(path)
    file_path = os.path.join(path, rest, ".encap")
    if os.path.isfile(file_path):
        config_file_name = file_path
        break

# Open config file
with open(config_file_name, 'r') as ymlfile:
    try:
        config = yaml.load(ymlfile, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        print("Error in configuration file")
        sys.exit(exc)




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


def read_settings_from_yml(file_name, settings=None):
    if settings is None:
        settings = {}
    
    try:
        with open(file_name, 'r') as ymlfile:
            config = yaml.load(ymlfile, Loader=yaml.FullLoader)
            if config is not None:
                config.update(settings)
                settings = config
    except FileNotFoundError:
        pass
    
    return settings