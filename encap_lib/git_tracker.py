from git import Repo
import git
import shutil
import os
import warnings
import random
from encap_lib.machines import run_code_local
from filelock import FileLock

def get_current_commit_hash(path):
    repo = Repo(path)
    return repo.head.commit.hexsha

def get_current_commit_hashes(git_track, force=False, **kwargs):
    
    if isinstance(git_track, str):
        git_track = [git_track]

    elif isinstance(git_track, dict):
        git_track = list(git_track.keys())
    
    elif isinstance(git_track, list):
        pass
    else:
        raise Exception(f"Unexpected type for git-track {type(git_track)}.")

    new_git_track = dict()
    for  i, git_track_folder in enumerate(git_track):
        git_track_folder_expanded = os.path.expanduser(git_track_folder)

        # Check if the git-track folder exists
        assert os.path.isdir(git_track_folder_expanded), f"The git-track folder {git_track_folder} does not exist."

        # Get the git hash
        repo = Repo(git_track_folder)
        if force:
            git_hash = sync_with_encap_branch(repo, **kwargs)
        else:
            git_hash = repo.head.commit.hexsha

        git_track[i] = {git_track_folder : git_hash}
        new_git_track[git_track_folder] = git_hash
    
    return new_git_track


# Functions to support automatic git tracking on the fly on an branch called "encap" which is mounted as a worktree
def sync_with_encap_branch(repo, **kwargs):
    file_lock = os.path.join(repo.git_dir, "encap_worktree_lock")
    with FileLock(file_lock):
        encap_worktree = make_worktree(repo)
        commit = sync_encap_worktree(repo, encap_worktree, **kwargs)
        delete_worktree(repo, encap_worktree)
    
    return commit

def sync_encap_worktree(repo, encap_worktree, commit_message="Automatic commit from encap", verbose=False):
    current_branch = repo.git.branch("--show-current")
    
    merge_message = encap_worktree.git.merge("--no-commit", current_branch, X="theirs")
    checkout_message = encap_worktree.git.checkout("--theirs", current_branch, encap_worktree.working_dir)

    if verbose:
        print(f"Syncing encap worktree with {current_branch} for {repo.working_dir}")
        print("Meging:", merge_message)
        print(checkout_message)

    # Find all files to be synced
    tracked_files_repo = set(repo.git.ls_files("--exclude-standard").split("\n"))
    tracked_files_encap = set(encap_worktree.git.ls_files("--exclude-standard").split("\n"))

    files_tosync = tracked_files_encap.union(tracked_files_repo)
    
    # Add untracked files to set
    untracked_files_repo = set(repo.git.ls_files("--other", "--exclude-standard").split("\n"))
    files_tosync = files_tosync.union(untracked_files_repo)

    untracked_files_encap = set(repo.git.ls_files("--other", "--exclude-standard").split("\n"))
    files_tosync = files_tosync.union(untracked_files_encap)
    
    sync_files(repo, encap_worktree, files_tosync, verbose=verbose)

    # Commit the changes
    encap_worktree.git.add("--all")
    try:
        encap_worktree.git.commit(m=commit_message)
    except git.GitCommandError as e:
        if "nothing to commit" in e.stdout:
            pass
        else:
            raise e

    # Clean up empty directories in encap_worktree
    encap_worktree.git.clean("-df")
    return encap_worktree.head.commit.hexsha


def make_worktree(repo):
    worktree_folder = os.path.join(repo.git_dir, "encap_worktree")
    try:
        repo.git.branch("encap")
        print("encap branch created in git repo", repo.working_dir)
    except git.GitCommandError as e:
        pass

    if "encap_worktree" in repo.git.worktree("list"):
        warnings.warn(f"Worktree {worktree_folder} already exists. This might be due to a previous unexpected termination of encap.")
        worktree_repo = Repo(worktree_folder)
        delete_worktree(repo, worktree_repo)

    try:
        repo.git.worktree("add", worktree_folder, "encap")
    except git.GitCommandError as e:
        warnings.warn(f"Error adding {worktree_folder}. This might be due to a previous unexpected termination of encap. Try removing the worktree manually. The error was:\n {e}")

    worktree_repo = Repo(worktree_folder)
    worktree_repo.git.checkout("encap") # Just in case

    return worktree_repo

def delete_worktree(repo, worktree_repo):
    repo.git.worktree("remove", worktree_repo.working_dir)
    repo.git.worktree("prune")


def get_stash(repo):
    repo.git.stash("save", 'encap_temp_stash', "-u")
    stash = repo.git.stash("show", "-p")
    #stash += "\n" + repo.git.diff("4b825dc642cb6eb9a060e54bf8d69288fbee4904", "stash^3") # Get the stash of untracked files
    repo.git.stash("pop")
    return stash + "\n"

def pop_stash(repo, stash):

    hash = random.getrandbits(128)
    patch_file = f"/tmp/{hash}.patch"

    # Apply patch file
    with open(patch_file, "w") as f:
        f.write(stash)

    repo.git.apply(patch_file)
    os.remove(patch_file)

def sync_files(repo, encap_worktree, files_tosync, verbose=False):
    #rsync -a --files-from=files_tosync main worktree_dir --delete-missing-args
    hash = random.getrandbits(128)
    file = f"/tmp/{hash}.files_tosync"
    
    with open(file, "w") as f:
        f.write("\n".join(files_tosync))
    
    if verbose: print("Syncing:", repo.working_dir, encap_worktree.working_dir)
    code = f"rsync -rlpcv --files-from={file} {repo.working_dir} {encap_worktree.working_dir} --delete-missing-args"
    out = run_code_local(code, verbose=verbose)
    os.remove(file)
    return out


# deprecated
def sync_encap_worktree_using_stash(repo, encap_worktree, commit_message="Automatic commit from encap", verbose=False):
    current_branch = repo.git.branch("--show-current")
    
    merge_message = encap_worktree.git.merge("--no-commit", current_branch)
    checkout_message = encap_worktree.git.checkout("--theirs", current_branch, encap_worktree.working_dir)

    if verbose:
        print(f"Syncing encap worktree with {current_branch}")
        print(merge_message)
        print(checkout_message)

    stash = get_stash(repo)

    # Update the encap branch with the stash
    pop_stash(encap_worktree, stash)

    # Deal with untracked files

    # Find which files exist in encap_worktree but not in master
    tracked_files_repo = set(repo.git.ls_files("--exclude-standard").split("\n"))
    tracked_files_encap = set(encap_worktree.git.ls_files("--exclude-standard").split("\n"))
    files_tosync = tracked_files_encap.difference(tracked_files_repo)
    
    # Add untracked files to set
    untracked_files = repo.git.ls_files("--other", "--exclude-standard").split("\n")
    files_tosync = files_tosync.union(set(untracked_files))
    
    sync_files(repo, encap_worktree, files_tosync)

    # Commit the changes
    encap_worktree.git.add("--all")
    try:
        encap_worktree.git.commit(m=commit_message)
        commited = True
    except git.GitCommandError as e:
        if "nothing to commit" in e.stdout:
            commited = False
            pass
        else:
            raise e

    # Clean up empty directories in encap_worktree
    encap_worktree.git.clean("-df")
    return commited