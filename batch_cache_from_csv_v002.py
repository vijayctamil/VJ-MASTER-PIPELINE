import hou
import sys
import csv
import threading
import os
import time
from tqdm import tqdm

# # Set Houdini environment
# houdini_path = r"C:\Program Files\Side Effects Software\Houdini 19.5.303\bin"
# os.environ["PATH"] = houdini_path + ";" + os.environ["PATH"]

# Check if running in the correct environment
if "hython.exe" not in sys.executable:
    print("Error: Please run this script using Houdini's Python (hython.exe)")
    sys.exit(1)

def read_csv(csv_file):
    """ Reads HIP file paths, execution types, and File Cache node paths from a CSV file. """
    hip_cache_map = {}

    try:
        with open(csv_file, newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 3:
                    print(f"Skipping invalid row: {row}")
                    continue

                hip_file = row[0].strip()
                execution_type = row[1].strip().lower()  # 'sequential' or 'parallel'
                filecache_paths = [path.strip() for path in row[2:] if path.strip()]

                if hip_file not in hip_cache_map:
                    hip_cache_map[hip_file] = []

                hip_cache_map[hip_file].append((execution_type, filecache_paths))

        return hip_cache_map

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

def cache_file_nodes_sequential(filecache_paths):
    """ Caches File Cache nodes one after another (sequential execution). """
    for cache_path in filecache_paths:
        cache_node = hou.node(cache_path)
        if not cache_node:
            print(f"Error: File Cache node not found - {cache_path}")
            continue

        save_button = cache_node.parm("execute")
        if save_button:
            print(f"Caching Sequentially: {cache_path}")
            save_button.pressButton()

            # Wait until node is done cooking
            wait_for_cache_completion(cache_node)
        else:
            print(f"Error: 'Save to Disk' button not found on {cache_path}")


def wait_for_cache_completion(cache_node):
    """ Wait until the File Cache node finishes caching by checking if output files exist. """
    file_path_parm = cache_node.parm("sopoutput")  # Get file path parameter
    if not file_path_parm:
        print(f"Error: 'file' parameter not found on {cache_node.path()}")
        return

    file_path = file_path_parm.eval()  # Evaluate file path
    file_extn_type = cache_node.parm("filetype").eval()
    if(file_extn_type == 0):
        file_extn = ".bgeo.sc"
        file_path = file_path[:-12]
    else:
        file_extn = ".vdb"
        file_path = file_path[:-8]
    
    start_frame = int(cache_node.parm("f1").eval())
    end_frame = int(cache_node.parm("f2").eval())
    total_frames = end_frame-start_frame

    padded_start_frame = f'{start_frame:04}'
    padded_end_frame = f'{end_frame:04}'

    first_frame_file = file_path + padded_start_frame + file_extn
    # last_frame_file = file_path + padded_end_frame + file_extn

    # print(f"Waiting for cache: {cache_node.path()}")
    # print(f"Checking existence of: {last_frame_file}")
    print(f"Waiting for cache: {cache_node.path()} ({start_frame} → {end_frame})")

    # Force tqdm to print immediately
    sys.stderr.flush()

    # Live Progress bar

    with tqdm(total=total_frames, desc=f"Caching {cache_node.name()}", unit="frame", leave=True) as pbar:
        cached_frames = 0
        previous_cached_frames = -1  # Track changes to avoid unnecessary updates

        while cached_frames < total_frames:
            # Count valid cached frames (existing and non-zero size)
            cached_frames = sum(
                os.path.exists(file_path + f'{f:04}' + file_extn) and
                os.path.getsize(file_path + f'{f:04}' + file_extn) > 0 
                for f in range(start_frame, end_frame + 1)
            )
            
            if cached_frames != previous_cached_frames:  # Update progress only if there's a change
                pbar.n = cached_frames
                pbar.refresh()
                sys.stderr.flush()  # Flush output to show updates in real-time
                previous_cached_frames = cached_frames

            time.sleep(0.5)  # Check every half second for faster updates


def cache_file_nodes_parallel(filecache_paths):
    """ Caches File Cache nodes simultaneously (parallel execution). """
    threads = []

    for cache_path in filecache_paths:
        cache_node = hou.node(cache_path)
        if not cache_node:
            print(f"Error: File Cache node not found - {cache_path}")
            continue

        save_button = cache_node.parm("execute")
        if save_button:
            print(f"Caching in Parallel: {cache_path}")
            thread = threading.Thread(target=lambda: save_button.pressButton())
            threads.append(thread)
            thread.start()
        else:
            print(f"Error: 'Save to Disk' button not found on {cache_path}")

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

def process_hip_file(hip_file, execution_batches):
    """ Loads a HIP file and processes caching in both sequential and parallel modes. """
    try:
        hou.hipFile.load(hip_file, suppress_save_prompt=True)
        print(f"\nLoaded HIP file: {hip_file}")

        for execution_type, filecache_paths in execution_batches:
            if execution_type == "sequential":
                cache_file_nodes_sequential(filecache_paths)
            elif execution_type == "parallel":
                cache_file_nodes_parallel(filecache_paths)
            else:
                print(f"Error: Invalid execution type '{execution_type}' for {hip_file}")

        print(f"Completed caching for {hip_file}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: hython batch_cache_mixed.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    hip_cache_map = read_csv(csv_file)

    for hip_file, execution_batches in hip_cache_map.items():
        process_hip_file(hip_file, execution_batches)
