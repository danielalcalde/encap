#!/usr/bin/env -S python -u
# If a file is made executable it will be executed directly, and the interpreter will be ignored.

import pickle

save_name = "test_data.p"
print("This is a test script")
print(save_name)

pickle.dump(["Some", "test", "data"], open(save_name, "wb"))
