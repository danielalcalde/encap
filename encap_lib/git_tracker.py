from git import Repo

def get_current_commit_hash(path):
    repo = Repo(path)
    return repo.head.commit.hexsha