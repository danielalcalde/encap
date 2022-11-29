from datetime import datetime
from tabulate import tabulate

def get_status(machine):
    # List all the running processes that my user has
    porcesses = machine.run_code("ps -o pid,lstart,cmd -u $USER")
    
    # Convert into a dict with the pid as key
    process_dict = {}
    for process in porcesses[1:]:
        pid = process.split()[0]
        process_dict[pid] = process
    
    # Get all the enviromental variables of the processes
    code = ""
    for pid in process_dict:
        code += f"""cat /proc/{pid}/environ
echo ""
"""

    encap_process_dict = dict()
    envs = machine.run_code(code)[:-1]
    assert len(envs) == len(process_dict), "Something went wrong."
    for env, pid in zip(envs, process_dict):
        if "ENCAP" in env:
            encap_process_dict[pid] = env
    
    # Get the ENCAP variables
    for pid, env in encap_process_dict.items():
        env = env.split("\x00")
        env_dict = dict()
        for env_i in env:
            if "ENCAP" in env_i:
                env_name, env_varaible = env_i.split("=")
                env_dict[env_name] = env_varaible
        encap_process_dict[pid] = env_dict
    
    # Filter out processes that are not the encap processes
    for pid, env in list(encap_process_dict.items()):
        if "tee" in process_dict[pid]:
            del encap_process_dict[pid]

    # Extract how long the process has been running
    for pid in encap_process_dict:
        month, day, time, year = process_dict[pid].split()[2:6]

        # Convert the time into a datetime object
        time = datetime.strptime(f"{month} {day} {year} {time}", "%b %d %Y %H:%M:%S")
        timee_diff = datetime.now() - time
        encap_process_dict[pid]["PID"] = pid
        encap_process_dict[pid]["TIME"] = strfdelta(timee_diff, "{H:02}:{M:02}:{S:02}")

    return encap_process_dict

def print_status(encap_process_dict):
        # Improve table
    for pid in encap_process_dict:
        encap_process_dict[pid]["NAME"] = encap_process_dict[pid]["ENCAP_NAME"]
        if encap_process_dict[pid]["ENCAP_PROCID"] != "0":
            encap_process_dict[pid]["NAME"] += f"_{encap_process_dict[pid]['ENCAP_PROCID']}"
        
        del encap_process_dict[pid]["ENCAP_NAME"]
        del encap_process_dict[pid]["ENCAP_PROCID"]

    # Print the status
    print(tabulate(encap_process_dict.values(), headers="keys"))

from string import Formatter
from datetime import timedelta
# https://stackoverflow.com/questions/538666/format-timedelta-to-string
def strfdelta(tdelta, fmt='{D:02}d {H:02}h {M:02}m {S:02}s', inputtype='timedelta'):
    """Convert a datetime.timedelta object or a regular number to a custom-
    formatted string, just like the stftime() method does for datetime.datetime
    objects.

    The fmt argument allows custom formatting to be specified.  Fields can 
    include seconds, minutes, hours, days, and weeks.  Each field is optional.

    Some examples:
        '{D:02}d {H:02}h {M:02}m {S:02}s' --> '05d 08h 04m 02s' (default)
        '{W}w {D}d {H}:{M:02}:{S:02}'     --> '4w 5d 8:04:02'
        '{D:2}d {H:2}:{M:02}:{S:02}'      --> ' 5d  8:04:02'
        '{H}h {S}s'                       --> '72h 800s'

    The inputtype argument allows tdelta to be a regular number instead of the  
    default, which is a datetime.timedelta object.  Valid inputtype strings: 
        's', 'seconds', 
        'm', 'minutes', 
        'h', 'hours', 
        'd', 'days', 
        'w', 'weeks'
    """

    # Convert tdelta to integer seconds.
    if inputtype == 'timedelta':
        remainder = int(tdelta.total_seconds())
    elif inputtype in ['s', 'seconds']:
        remainder = int(tdelta)
    elif inputtype in ['m', 'minutes']:
        remainder = int(tdelta)*60
    elif inputtype in ['h', 'hours']:
        remainder = int(tdelta)*3600
    elif inputtype in ['d', 'days']:
        remainder = int(tdelta)*86400
    elif inputtype in ['w', 'weeks']:
        remainder = int(tdelta)*604800

    f = Formatter()
    desired_fields = [field_tuple[1] for field_tuple in f.parse(fmt)]
    possible_fields = ('W', 'D', 'H', 'M', 'S')
    constants = {'W': 604800, 'D': 86400, 'H': 3600, 'M': 60, 'S': 1}
    values = {}
    for field in possible_fields:
        if field in desired_fields and field in constants:
            values[field], remainder = divmod(remainder, constants[field])
    return f.format(fmt, **values)