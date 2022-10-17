# Encap (encapsulate)
Encap is a simple tool to keep track of computational experiments.
This program is intended to be used for scientific computing, it is possible to run different experiments in different containers and keep track of the results.

It currently has support for:
* Running experiments locally/remotely thourgh ssh
* Starting several experiments in parallel
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
setsid nohup time python scripts/my_script/<version_name>/my_script.py &>> scripts/my_script/<version_name>/log & disown
```
The log file will be tailed afterwards. This makes it easy to keep track of different computational experiments. In python an example could be the following:

#### my_script.py
```python
import pickle

save_name = "test_data.p"
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

test_data.p
```
and generates three files:
* my_script/test/log
* my_script/test/my_script.py
* my_script/test/test_data.p

## Installation
```bash
pip install git+https://github.com/danielalcalde/encap
```
## Starting several experiments in parallel
#### my_script.py
```python
import pickle
import os

i = os.environ["ENCAP_PROCID"]
save_name = f"test_data_{i}.p"
print(save_name)
print("This is the", i, "encap instance")

pickle.dump(["Some", "test", "data", i], open(save_name, "wb"))
```

```bash
encap run scripts/my_script.py -i 3 -n test
```
will run the script three times in parallel. It will create the files:
* my_script/test/my_script.py
* my_script/test/log
* my_script/test/log_1
* my_script/test/log_2
* my_script/test/test_data_0.p
* my_script/test/test_data_1.p
* my_script/test/test_data_2.p


## More Examples
Several examples can be found in the examples folder.

## Slurm
Example encap invocation that will execute slurm with 3 nodes and will pass the PROC_ID enviroment variable to the script as the -i argument.
```
encap run slurm_test.py -n test -sl_nodes 3 -args " -i \$ENCAP_PROCID"
```
The configuration file is located at ~/.encap/config.yml.

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

{run.sh} and {run.slurm} will be replaced with the actual script and slurm file automatically upon execution.

If you want to execute different slurm instances in parallel you can use the -sl_i argument.

## Configuring SSH (untested with newest features)
The script can be also executed on a remote server through ssh. For this a mirror of the local folder is created on the remote server.

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
```
# SSH output to be ignored.
ssh_ignore: ["X11 forwarding request failed on channel"]
# Folders to be ignored wile rsyncing between local and remote machine
rsync_exclude: [".git", "*log*"]
```
Alternatievly the config file can also be saved in the same folder as the encap script with the name .encap .

## Configuring Google Cloud
TODO
