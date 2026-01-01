import sys
import os
# Add project root to path
sys.path.append(os.getcwd())

from src.tools import list_files_tree, read_file_cat, get_git_diff, get_git_log, search_code_grep, list_changed_files

def test_tools():
    print("Testing list_files_tree...")
    print(list_files_tree.invoke({"path": "."}))
    print("-" * 20)

    print("Testing read_file_cat...")
    print(read_file_cat.invoke({"file_path": "src/tools.py"})[:200] + "...")
    print("-" * 20)

    print("Testing get_git_log...")
    print(get_git_log.invoke({"limit": 5}))
    print("-" * 20)

    print("Testing search_code_grep...")
    print(search_code_grep.invoke({"pattern": "def list_files_tree"}))
    print("-" * 20)

    # Note: get_git_diff and list_changed_files might return empty or error if not in a proper git context with a main branch
    print("Testing list_changed_files (default branch)...")
    print(list_changed_files.invoke({}))
    print("-" * 20)

if __name__ == "__main__":
    test_tools()
