# Encap (encapsulate)
Encap is a simple tool to keep track of computational experiments.
This program is intended to be used for scientific computing, it makes it easier to run different experiments in different containers and keep track of results.

It currently has support for:
* Rerunning old experiments
* Tracking git repositories
* Starting several experiments in parallel
* Running experiments on Slurm
* Running experiments locally/remotely through ssh

If one wants to execute a script instead of writing:
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
The log file will be tailed afterward. This makes it easy to keep track of different computational experiments. In python an example could be the following:

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

## Help with all the options
```bash
encap -h
```

## Rerunning a previous experiment
To rerun a previous experiment you can use encap in rerun mode:
```bash
encap rerun scripts/my_script.py -n test
```
This will without copying the script again, rerun the experiment. This is useful if you want to rerun an experiment with different parameters. You can for example copy the script, change the parameters and then rerun the modified script.

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

## Choose a script interpreter
There are 3 ways to choose with which interpreter your file will be executed. The first one is to set a custom file extension in the configuration file:
```yml
file_extension:
  go: go run
```
The second option is to make your script executable, this will directly execute it. Lastly, you can define the interpreter directly in the command line:
```sh
encap run my_script.go -n <version> --interpreter "go run"
```

## Configuring Slurm
Example encap invocation that will execute Slurm on 3 nodes and will pass the `ENCAP_PROCID` environment variable to the script as the -i argument. In this example, the `ENCAP_PROCID` will take the values 0, 1, 2 depending on the node.
```
encap run slurm_test.py -n test -sl_nodes 3 -args " -i \$ENCAP_PROCID"
```
Alternatively `ENCAP_PROCID` can be read directly in your script, see for example /examples/slurm_test.py

The configuration file is located at ~/.encap/config.yml.

Example config file that will restart the Slurm job if it did not exit successfully:
```yml
file_extension:
  py: python -u

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

{run.sh} and {run.slurm} will be replaced with the actual script and Slurm file automatically upon execution.

If you want to execute different Slurm instances in parallel you can use the `-sl_i <i>` argument. This will create *i* different Slurm jobs.

## Nesting configuration files
Sometimes you want to have different configuration files for different projects or even different experiments. Encap will recursively search for files called .encap.conf in the directory, the script is located in and in all parent directories. Each .encap.conf file will be merged with the previous one. This allows you to have a global configuration file and then overwrite only parts of it for specific projects or experiments. For example, you could have a global configuration file that sets the default Slurm partition to "gpu" and then overwrite it for a specific project that does not need a GPU. See the examples/slurm_folder_script_extra_configs folder for more examples.

## Folder mode
If you want to run a script that depends on other files in the same folder you can use the folder mode. This will copy the entire folder to the experiment folder and then execute the script. This is useful for example if you have a custom .encap.conf file in the folder that you want to use for the experiment or if your script needs to execute other scripts in the same folder. The folder mode is automatically activated if instead of a script you pass a folder to encap. For example:
```bash
encap run examples/folder_script -n test
```
this will copy the entire folder to the experiment folder and then execute the script called run.* in the folder.
Note that the script name can be different from run.* if it is specified with the -f argument or if the folder contains a .encap.conf file with the field script_name set to the name of the script.

## Follow git
If you want to keep track of the commit in a git repository you can add the following to your .encap.conf file:
```yml
git-track:
  - <repo_dir_1>
  - <repo_dir_2>
```
This will write the commit hash of the current commit in the repository to the .encap_history.conf file in the experiment folder. This can be useful if you want to keep track of the exact commit that was used for a specific experiment in the case that in the future you want to reproduce the results.

## Configuring SSH (untested with newest features)
The script can be also executed on a remote server through ssh. For this, a mirror of the local folder is created on the remote server.

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
### SSH output to be ignored.
ssh_ignore: ["X11 forwarding request failed on channel"]
### Folders to be ignored while rsyncing between local and remote machine
```
rsync_exclude: [".git", "*log*"]
```

## Configuring Google Cloud
TODO
