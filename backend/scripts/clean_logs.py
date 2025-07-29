import os
import shutil


def clean():
    """
    Cleans up log and screenshot files in specified directories.
    Reads CLEAN_LOGS_PATHS environment variable, which should be a comma-separated list of directories.
    If not set, no action is taken.
    """
    paths_env = os.getenv("CLEAN_LOGS_PATHS")
    if not paths_env:
        print("No CLEAN_LOGS_PATHS environment variable set. Nothing to clean.")
        return

    paths = [p.strip() for p in paths_env.split(",") if p.strip()]
    for path in paths:
        if not os.path.isdir(path):
            continue
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            try:
                if os.path.isfile(full_path) or os.path.islink(full_path):
                    os.remove(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
            except Exception as e:
                print(f"Failed to remove {full_path}: {e}")
    print("Logs and screenshots cleaned.")


if __name__ == "__main__":
    clean()
