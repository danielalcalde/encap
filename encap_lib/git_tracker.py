from git import Repo
import os

def get_current_commit_hash(path):
    repo = Repo(path)
    return repo.head.commit.hexsha

def get_commit_hashes(git_track):
    
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
        git_hash = get_current_commit_hash(git_track_folder_expanded)

        git_track[i] = {git_track_folder : git_hash}
        new_git_track[git_track_folder] = git_hash
    
    return new_git_track