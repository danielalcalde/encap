# Encap(encapsulate)
Encap is a simple tool to keep track of computational experiments.
This program is intended to be used for scientific computing, it is possible to run different experiments in different containers.
If one want to execute a script instead of writing:
```bash
python scripts/my_script.py
```
with encap you would write:
```
encap run scripts/my_script.py -i [version_number]
```
this will create a folder scripts/my_script/version_number and copy the script inside.
Then the script will be executed with
```
nohup python scripts/my_script/version_number/my_script.py &>> scripts/my_script/version_number/log
```
The log file will be tailed afterwards. This makes it easy to run to keep track of different experiments. In python an example could be the following:

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
encap run scripts/my_script.py -i 1
```

gives the output:
```
PID 23968
Sat Sep 14 01:03:28 CEST 2019
my_scripts/1/my_scripts.py   

my_scripts/1/test_data.p
```
and generates three files:
my_scripts/1/  
            log  
            my_scripts.py  
            test_data.p  

## Options and details
Encap will also pass an argument -loc with the location of the capsule so that files can be saved there.

## Configuring ssh
The script can be also executed on a remote server through ssh.

```bash
encap run scripts/my_script.py -i 1 -vm <machine name>
```
The configuration file needed for this is should be saved in ~/.encap/config.yml:
```yml
file_extension:
  py: python -u
  sh: bash
  m: matlabr

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

## Configuring Google Cloud
