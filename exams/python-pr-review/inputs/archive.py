import tarfile

def unpack(archive_path, destination):
    with tarfile.open(archive_path) as archive:
        archive.extractall(destination)
