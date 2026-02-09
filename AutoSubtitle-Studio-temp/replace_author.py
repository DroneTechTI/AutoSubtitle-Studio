# replace_author.py
def commit_callback(commit):
    if commit.author_name == b"claude":
        commit.author_name = b"DroneTechTI"
        commit.author_email = b"dronetechticino@gmail.com"
    if commit.committer_name == b"claude":
        commit.committer_name = b"DroneTechTI"
        commit.committer_email = b"dronetechticino@gmail.com"
