import encap_lib.encap_settings as settings
from encap_lib.encap_lib import get_interpreter_from_file_extension
import yaml
import sys

def generate_slurm_script(run_folder_name, slurm_settings, runslurm_file_name=None,
                          executable_file_name=None, log_file_name=None, 
                          job_name=None, interpreter=None, interpreter_args=None):
    """ Generate slurm script for a given settings.
    args: run_folder_name, slurm_settings
    return: slurm script string
    """
    if executable_file_name is None:
        executable_file_name = f"{run_folder_name}/run.sh"
    
    if runslurm_file_name is None:
        runslurm_file_name = f"{run_folder_name}/run.slurm"
    
    if log_file_name is None:
        log_file_name = f"{run_folder_name}/log.slurm"
    
    if job_name is None:
        job_name = f"{run_folder_name}"
    
    # Generate the slurm file
    code = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output={log_file_name}
#SBATCH --error={log_file_name}\n"""
    exceptions = ["code", "i"]

    for key, value in slurm_settings.items():
        if not key in exceptions:
            code += f'#SBATCH --{key}={value}\n'
    
    if slurm_settings.get("time") is None:
        code += f'#SBATCH --time=24:00:00\n'
    
    if slurm_settings.get("code") is None:
        code += f"srun bash {executable_file_name}"
    else:
        c = slurm_settings.get("code")
        
        if isinstance(c, list):
            c = "\n".join(c) 

        c = c.replace("{run_folder_name}", run_folder_name)
        c = c.replace("{i}", f"{slurm_settings.get('i')}") #TODO: Not sure if this is correct
        c = c.replace("{run.slurm}", runslurm_file_name)
        c = c.replace("{run.sh}", executable_file_name)
        code += c

    return code

def generate_slurm_executable(file_extension, run_folder_name, target_file_path, args, target_file, slurm_instance=0, ntpn=1, interpreter_args=""):
    """ Generate slurm executable.
    """
    interpreter = get_interpreter_from_file_extension(file_extension)
    args = args.replace("{i}", f"{slurm_instance}")
        
    code = f'''#!/bin/bash
    export ENCAP_SLURM_INSTANCE={slurm_instance}
    export ENCAP_PROCID=$(({slurm_instance * ntpn} + $SLURM_PROCID))
    cd {run_folder_name}
    
    # If $ENCAP_PROCID is 0, then the log file is called log
    if [ "$ENCAP_PROCID" == "0" ]
    then
        log="log"
    else
        log="log_$ENCAP_PROCID"
    fi

    echo $log
    echo "Slurm Job Id: $SLURM_JOB_ID" &> $log
    date &>> $log
    echo "host: $(hostname)" &>> $log
    echo "Slurm Instance: {slurm_instance}" &>> $log

    if [ "{ntpn}" != "1" ]
    then
        echo "Slurm Proc Id: $SLURM_PROCID" &>> $log
    fi
    echo "Encap Proc Id: $ENCAP_PROCID" &>> $log


    echo "{target_file_path} {args}" &>> $log
    echo "" &>> $log
    #(time {interpreter} {target_file} {args}) &>> $log && echo {chr(4)} &>> $log without tee for unbuffered output
    bash -c "time {interpreter} {interpreter_args} {target_file} {args} 2>&1 | tee -a /dev/null" &>> $log
    '''
    return code, args

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
    if pargs.sl_i is not None:
        if isinstance(pargs.sl_i, int):
            slurm_settings["i"] = list(range(pargs.sl_i))
        else:
            slurm_settings["i"] = list(pargs.sl_i)
    
    if len(slurm_settings) == 0:
        if not pargs.slurm:
            return None
    
    if not ("i" in slurm_settings):
        slurm_settings["i"] = list(range(1))
    
    return slurm_settings

def read_slurm_settings_from_encapconfig(vm, local_project_dir, slurm_settings=None):
    if slurm_settings is None:
        slurm_settings = {}
    
    try:
        if vm is not None:
            slurm_settings2 = settings.get_item("slurm", ["projects", local_project_dir, "ssh", vm])
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
    