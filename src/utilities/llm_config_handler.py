import os

def find_llm_config(filename="llm_config.yaml"):
    """Searches for 'llm_config.yaml' from the current directory up to the root directory."""
    current_dir = os.getcwd()
    
    while True:
        potential_path = os.path.join(current_dir, filename)
        if os.path.isfile(potential_path):
            return potential_path
        
        # Move one level up
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            # Reached the filesystem root
            return None
        current_dir = parent_dir
