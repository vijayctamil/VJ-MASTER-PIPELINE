import hou
import sys
import json

def extract_filecaches(hip_file):
    """Loads a Houdini .hip file and extracts all File Cache nodes."""
    try:
        hou.hipFile.load(hip_file, suppress_save_prompt=True)
        filecache_nodes = []
        
        for node in hou.node("/obj").allSubChildren():
            if node.type().name() == "filecache" or "filecache" in node.type().name().lower():
                filecache_nodes.append(node.path())
        
        for node in hou.node("/stage").allSubChildren():  # Also check LOPs (Solaris)
            if node.type().name() == "filecache" or "filecache" in node.type().name().lower():
                filecache_nodes.append(node.path())
        
        print(json.dumps(filecache_nodes))  # Output as JSON for UI parsing
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No .hip file provided"}))
        sys.exit(1)
    
    hip_file = sys.argv[1]
    extract_filecaches(hip_file)
