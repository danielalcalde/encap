import os
import shutil
import sys
import pytest
import time

def load_encap(tmp_path):
    encap_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "encap"))
    
    encap_py_path = tmp_path / "encap_main.py"
    shutil.copy(encap_path, encap_py_path)
    
    sys.path.insert(0, str(tmp_path))
    
    if "encap_main" in sys.modules:
        del sys.modules["encap_main"]
        
    import encap_main
    from encap_lib import encap_settings
    import importlib
    importlib.reload(encap_settings)
    
    return encap_main

def wait_for_files(files, timeout=5.0):
    start = time.time()
    while time.time() - start < timeout:
        if all(f.exists() for f in files):
            return True
        time.sleep(0.5)
    return False

def test_examples(tmp_path, mocker, monkeypatch):
    encap = load_encap(tmp_path)
    mocker.patch.object(encap, 'tail_pull', return_value=None)
    
    examples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples"))
    tmp_examples_dir = tmp_path / "examples"
    shutil.copytree(examples_dir, tmp_examples_dir)
    
    monkeypatch.chdir(tmp_examples_dir)
    
    # Test 1: test_script.py
    monkeypatch.setattr(sys, "argv", ["encap", "run", "test_script.py", "-n", "test_run_1"])
    encap.main()
    
    run_folder = tmp_examples_dir / "test_script" / "test_run_1"
    assert run_folder.exists(), "Run folder for test_script.py was not created"
    
    wait_for_files([run_folder / "test_data.p"], timeout=5.0)
    
    log_content = (run_folder / "log").read_text() if (run_folder / "log").exists() else "No log file found"
    assert (run_folder / "test_data.p").exists(), f"test_data.p was not created by test_script.py. Log:\n{log_content}"
    assert (run_folder / "log").exists()
    
    # Test 2: test_script_instances.py
    monkeypatch.setattr(sys, "argv", ["encap", "run", "test_script_instances.py", "-n", "test_run_2", "-i", "3"])
    encap.main()
    
    run_folder2 = tmp_examples_dir / "test_script_instances" / "test_run_2"
    assert run_folder2.exists(), "Run folder for test_script_instances.py was not created"
    
    wait_for_files([
        run_folder2 / "test_data_0.p",
        run_folder2 / "test_data_1.p",
        run_folder2 / "test_data_2.p"
    ], timeout=5.0)
    
    # Check that 3 log files were created
    assert (run_folder2 / "log").exists(), "log was not created"
    assert (run_folder2 / "log_1").exists(), "log_1 was not created"
    assert (run_folder2 / "log_2").exists(), "log_2 was not created"
    
    log_content_0 = (run_folder2 / "log").read_text() if (run_folder2 / "log").exists() else ""
    assert (run_folder2 / "test_data_0.p").exists(), f"test_data_0.p was not created. Log:\n{log_content_0}"
    assert (run_folder2 / "test_data_1.p").exists(), "test_data_1.p was not created"
    assert (run_folder2 / "test_data_2.p").exists(), "test_data_2.p was not created"
    
    # Test 3: folder_script
    monkeypatch.setattr(sys, "argv", ["encap", "run", "folder_script", "-sn", "run.py", "-n", "test_run_3", "-i", "4"])
    encap.main()
    
    run_folder3 = tmp_examples_dir / "0encap_folder" / "folder_script" / "test_run_3"
    assert run_folder3.exists(), "Run folder for folder_script was not created"
    
    wait_for_files([
        run_folder3 / "test_data_0.p",
        run_folder3 / "test_data_1.p",
        run_folder3 / "test_data_2.p",
        run_folder3 / "test_data_3.p"
    ], timeout=10.0) # folder_script has time.sleep(2) so it needs more time
    
    assert (run_folder3 / "log").exists(), "log was not created"
    assert (run_folder3 / "log_1").exists(), "log_1 was not created"
    assert (run_folder3 / "log_2").exists(), "log_2 was not created"
    assert (run_folder3 / "log_3").exists(), "log_3 was not created"
    
    log_content_3 = (run_folder3 / "log").read_text() if (run_folder3 / "log").exists() else ""
    assert (run_folder3 / "test_data_0.p").exists(), f"test_data_0.p was not created. Log:\n{log_content_3}"
    assert (run_folder3 / "test_data_1.p").exists(), "test_data_1.p was not created"
    assert (run_folder3 / "test_data_2.p").exists(), "test_data_2.p was not created"
    assert (run_folder3 / "test_data_3.p").exists(), "test_data_3.p was not created"
