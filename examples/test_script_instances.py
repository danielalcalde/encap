# Command
# encap run test_script_instances.py -n test -i 3
import pickle
import os
import time

time.sleep(2)

save_name = "test_data.p"
print(save_name)
print("This is the", os.environ["ENCAP_INSTANCE"], "encap instance")

pickle.dump(["Some", "test", "data"], open(save_name, "wb"))
