from typing import Union, Tuple
import os
import getpass

# Returns (err_msg, ssh_dir, authorized_keys_path) for the current OS
# Returns None if the OS is not supported
def get_os_dependent_vars() -> Union[Tuple[str], None]:
    err_msg = ""
    ssh_dir = ""
    authorized_keys_path = ""
    if os.name == 'posix':
        ssh_dir = os.path.expanduser(f'~{getpass.getuser()}/.ssh')
        authorized_keys_path = os.path.join(ssh_dir, 'authorized_keys')
    elif os.name == 'nt':
        ssh_dir = os.path.expanduser(f'~{getpass.getuser()}\\.ssh')
        authorized_keys_path = os.path.join(ssh_dir, 'authorized_keys')
    else:
        err_msg = "Unsupported OS. Only POSIX and NT are supported."
    return err_msg, ssh_dir, authorized_keys_path