import os, pickle

def get_loc():
    absolute_path = os.path.dirname(os.path.realpath(__file__))
    relative_path = os.path.relpath(absolute_path, os.getcwd())
    return relative_path

save_name = get_loc() + "/test_data.p"
print(save_name)

pickle.dump(["Some", "test", "data"], open(save_name, "wb"))
