import encap_lib.encap_settings as settings
import yaml
import sys

def generate_slurm_script(run_folder_name, slurm_settings):
    """ Generate slurm script for a given settings.
    args: run_folder_name, slurm_settings
    return: slurm script string
    """

    # Generate the slurm file
    code = f"""#!/bin/bash
#SBATCH --job-name={run_folder_name}
#SBATCH --output={run_folder_name}/log.slurm
#SBATCH --error={run_folder_name}/log.slurm\n"""
    exceptions = ["code"]

    for key, value in slurm_settings.items():
        if not key in exceptions:
            code += f'#SBATCH --{key}={value}\n'
    
    if slurm_settings.get("time") is None:
        code += f'#SBATCH --time=24:00:00\n'
    
    if slurm_settings.get("code") is None:
        code += f"srun bash {run_folder_name}/run.sh"
    else:
        code += slurm_settings.get("code").replace("{run_folder_name}", f"{run_folder_name}")

    return code

def initialize_slurm_settings(pargs):
    slurm_settings = {}
    if pargs.sl_nodes is not None:
        slurm_settings["nodes"] = pargs.sl_nodes
    if pargs.sl_ntpn is not None:
        slurm_settings["ntasks-per-node"] = pargs.sl_ntpn
    if pargs.sl_time is not None:
        slurm_settings["time"] = pargs.sl_time
    if pargs.sl_partition is not None:
        slurm_settings["partition"] = pargs.sl_partition
    if pargs.sl_account is not None:
        slurm_settings["account"] = pargs.sl_account
    if pargs.sl_cpus is not None:
        slurm_settings["cpus-per-task"] = pargs.sl_cpus
    
    if len(slurm_settings) == 0:
        if not pargs.slurm:
            return None
    
    return slurm_settings

def read_slurm_settings_from_encapconfig(pargs, local_project_dir, slurm_settings=None):
    if slurm_settings is None:
        slurm_settings = {}
    
    try:
        if pargs.vm:
            slurm_settings2 = settings.get_item("slurm", ["projects", local_project_dir, "ssh", pargs.vm])
        else:
            slurm_settings2 = settings.get_item("slurm", ["projects", local_project_dir])
    except KeyError:
        if "slurm" in settings.config:
            slurm_settings2 = settings.config["slurm"]
        else:
            sys.exit("No slurm settings found in ~/.encap/config.yml")
        
    slurm_settings2.update(slurm_settings)
    return slurm_settings2

def read_slurm_settings_from_yml(file_name, slurm_settings=None):
    if slurm_settings is None:
        slurm_settings = {}
    
    try:
        with open(file_name, 'r') as ymlfile:
            config = yaml.load(ymlfile, Loader=yaml.FullLoader)
            if config is not None:
                config.update(slurm_settings)
                slurm_settings = config
    except FileNotFoundError:
        pass
    
    return slurm_settings
    