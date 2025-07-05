import os

def generate_folder_structure(directory, indent=0):
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            print(" " * indent + "> " + item + "/")
            generate_folder_structure(item_path, indent + 2)
        else:
            print(" " * indent + "- " + item)
#Example usage
generate_folder_structure("./wokkahlearn")

