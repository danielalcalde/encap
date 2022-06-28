# Encap (encapsulate)
Encap is a simple tool to keep track of computational experiments.
This program is intended to be used for scientific computing, it is possible to run different experiments in different containers and keep track of the results.

It currently has support for:
* Running experiments locally/remotely thourgh ssh
* Running experiments through SLURM

If one want to execute a script instead of writing:
```bash
python scripts/my_script.py
```
with encap you would write:
```
encap run scripts/my_script.py -n <version_name>
```
this will create a folder scripts/my_script/<version_name> and copy the script inside.
Then the script will be executed with
```
nohup time python scripts/my_script/<version_name>/my_script.py &>> scripts/my_script/<version_name>/log & disown
```
The log file will be tailed afterwards. This makes it easy to keep track of different computational experiments. In python an example could be the following:

#### my_script.py
```python
import os, pickle

def get_loc():
    absolute_path = os.path.dirname(os.path.realpath(__file__))
    relative_path = os.path.relpath(absolute_path, os.getcwd())
    return relative_path

save_name = get_loc() + "/test_data.p"
print(save_name)

pickle.dump(["Some", "test", "data"], open(save_name, "wb"))
```
Running:
```
encap run scripts/my_script.py -n test
```

gives the output:
```
PID 23968
Sat Sep 14 01:03:28 CEST 2019
scripts/test/my_script.py   

my_script/test/test_data.p
```
and generates three files:
* my_script/test/log
* my_script/test/my_script.py
* my_script/test/test_data.p

## Installation
```bash
pip install git+https://github.com/danielalcalde/encap
```

## Configuring ssh
The script can be also executed on a remote server through ssh.

```bash
encap run scripts/my_script.py -name <version_name> -vm <machine name>
```
The configuration file is located at ~/.encap/config.yml:
```yml
file_extension:
  py: python -u
  sh: bash

projects:
   <dir in local machine>:
    dir: <dir in remote machine>
    ssh:
      user: <username>
      <machine name>:
        ip: <ip>

# SSH output to be ignored.
ssh_ignore: ["X11 forwarding request failed on channel"]
# Folders to be ignored wile rsyncing between local and remote machine
rsync_exclude: [".git", "*log*"]
```
Alternatievly the config file can also be saved in the same folder as the encap script with the name .encap .

## Slurm
Example encap invocation that will execute slurm with 3 nodes and will pass the PROC_ID enviroment variable to the script as the -i argument.
```
encap run slurm_test.py -n test -sln 3 -args " -i \$SLURM_PROCID"
```

Example config file that will restart the slurm job if it did not exit sucessfully.
```yml
slurm:
  account: <account>
  partition: <partition>
  cpus-per-task: 256
  ntasks-per-node: 1
  time: "24:00:00"
  code:
    - timeout 23h srun bash {run.sh}
    - if [[ $? -eq 124 ]]; then
    - sbatch {run.slurm}
    - fi
```

{run.sh} and {run.slurm} will be replaced with the actual script and slurm file upon execution.

## Configuring Google Cloud
TODO
