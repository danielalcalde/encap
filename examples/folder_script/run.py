# Command
# encap run folder_script -f run.py -n test -i 4
import pickle
import os
import time

time.sleep(2)
i = os.environ["ENCAP_INSTANCE"]
save_name = f"test_data_{i}.p"
print(save_name)
print("This is the", os.environ["ENCAP_INSTANCE"], "encap instance")

pickle.dump(["Some", "test", "data"], open(save_name, "wb"))
