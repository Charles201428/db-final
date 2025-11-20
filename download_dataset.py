import kagglehub
import os
import shutil
import glob

# Get the current directory
current_dir = os.getcwd()

# Download dataset (will download to cache first)
print("Downloading dataset...")
path = kagglehub.dataset_download("saketk511/2019-2024-us-stock-market-data")
print(f"Downloaded to: {path}")

# Move all files from the download path to current directory
if os.path.exists(path):
    print(f"Moving files to current directory: {current_dir}")
    for file_path in glob.glob(os.path.join(path, "*")):
        if os.path.isfile(file_path):
            filename = os.path.basename(file_path)
            dest_path = os.path.join(current_dir, filename)
            shutil.move(file_path, dest_path)
            print(f"  Moved: {filename}")
    
    # Delete the cached directory after moving files
    try:
        shutil.rmtree(path)
        print(f"Deleted cached files from: {path}")
    except Exception as e:
        print(f"Error deleting cache: {e}")

print(f"\nFiles are now in: {current_dir}")

