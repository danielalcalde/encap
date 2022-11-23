# Command
# encap run test_script.py -n test
import pickle

save_name = "test_data.p"
print("This is a test script")
print(save_name)

pickle.dump(["Some", "test", "data"], open(save_name, "wb"))
