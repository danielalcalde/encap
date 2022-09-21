# Command to run six instances of the script on two nodes: 
# encap run slurm_test.py -n test -sl_i 2 --slurm_ntasks-per-node 6
import pickle
import os
import time

time.sleep(2)
i = os.environ["ENCAP_SLURM_INSTANCE"] # [0,..., 5]
j = os.environ["SLURM_PROCID"] # [0,1]

save_name = f"test_data_{i}_{j}.p"
print(save_name)
print(f"This is the {j} task on the {i} SLURM_INSTANCE")

pickle.dump(["Some", "test", "data"], open(save_name, "wb"))
