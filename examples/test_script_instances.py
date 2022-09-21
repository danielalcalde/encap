# Command
# encap run test_script_instances.py -n test -i 3
import pickle
import os
import time

time.sleep(2)
i = os.environ["ENCAP_PROCID"]
save_name = f"test_data_{i}.p"
print(save_name)
print("This is the", i, "encap instance")

pickle.dump(["Some", "test", "data"], open(save_name, "wb"))
