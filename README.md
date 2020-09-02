# Encapsulate (encap)

This program is intended to be used for scientific computing, it is possible to run different experiments in different containers.
If one want to execute a script instead of writing:
```
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
The log file will be tailed afterwards. This makes it easy to conserve script files and its results for different experiments. In python an example could be the following:

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
and generates three files at container my_scripts/1/.
## Options and details
Encap will also pass an argument -loc with the location of the capsule so that files can be saved there.

## Configuring ssh


## Configuring Google cloud
