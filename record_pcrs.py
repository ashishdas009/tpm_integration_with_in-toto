import subprocess
import os

def is_tpm2():
    if os.path.exists("/dev/tpmrm0"):
        return True
    else:
        return False

def read_pcrs():
    if is_tpm2():
        res = subprocess.run(["tpm2_pcrread", "sha256:all"], stdout= subprocess.PIPE)
        res.check_returncode()
        pcrs = res.stdout
        pcrs = str(pcrs, 'utf-8').split('\n')
        return pcrs



