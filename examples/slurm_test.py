# Command to run six instances of the script on two nodes, would make sense if the processor has 24 cores: 
# encap run slurm_test.py -n test -sl_i 2 --slurm_ntasks-per-node 6 --slurm_cpus-per-task 4
import pickle
import os
import time

time.sleep(2)
i = os.environ["ENCAP_PROCID"]
i2 = os.environ["ENCAP_SLURM_INSTANCE"] # [0,..., 5]
i3 = os.environ["SLURM_PROCID"] # [0,1]

save_name = f"test_data_{i}.p"
print(save_name)
print(f"This is the {i3} task on the {i2} SLURM_INSTANCE")

pickle.dump(["Some", "test", "data"], open(save_name, "wb"))
