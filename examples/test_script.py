# Command
# encap run test_script_instances.py -n test
import pickle


save_name = "test_data.p"
print(save_name)

pickle.dump(["Some", "test", "data"], open(save_name, "wb"))
