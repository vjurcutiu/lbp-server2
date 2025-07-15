import sys
import os

# Get the directory of this script (so it works on both host and in container)
script_dir = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(script_dir, "..", "latest_version.txt")

if len(sys.argv) != 2:
    print("Usage: python set_version.py <new_version>")
    sys.exit(1)

new_version = sys.argv[1]
with open(VERSION_FILE, "w") as f:
    f.write(new_version + "\n")

print(f"Updated version to {new_version}")
