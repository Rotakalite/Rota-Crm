import os

def read_file(filename):
    with open(filename, 'r') as f:
        return f.readlines()

def write_file(filename, lines):
    with open(filename, 'w') as f:
        f.writelines(lines)

# Read the file
filename = '/app/backend/server.py'
lines = read_file(filename)

# The strings to replace
old_str = '        db = mongo_client["rotacrm"]\n'
new_str = '        db = mongo_client[os.environ.get(\'DB_NAME\', \'rotacrm\')]\n'

# Replace all occurrences
modified_lines = [new_str if line == old_str else line for line in lines]

# Write back to file
write_file(filename, modified_lines)
print("Replacement complete")