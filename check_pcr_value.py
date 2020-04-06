import hashlib
import os
import subprocess

NUM_PCRS = 24
PCR_SIZE = hashlib.sha1().digest_size


def init_empty_pcrs():
    pcrs = {idx: (b"\xFF" if (17 <= idx <= 22) else b"\x00") * PCR_SIZE
            for idx in range(NUM_PCRS)}
    return pcrs

def is_tpm2():
    if not os.path.exists("/sys/class/tpm/tpm0/caps"):
        # XXX: the sysfs interface is suddenly gone for TPM 2.0, and mjg says it wasn't
        #      actually meant to be there, and I don't know how to check the version in
        #      any other way so just assume it's 2.0 in that case.
        return True
    with open("/sys/class/tpm/tpm0/caps", "r") as fh:
        for line in fh:
            if line.startswith("TCG version: 2."):
                # XXX: untested
                return True
            if line.startswith("TCG version: 1.2"):
                return False
    return True

def in_path(exe):
    for p in os.environ["PATH"].split(":"):
        if p and os.path.exists("%s/%s" % (p, exe)):
            return True
    return False

def read_current_pcr(idx):
    return read_current_pcrs([idx])[idx]

def read_current_pcrs(idxs):
    if is_tpm2():
        if in_path("tpm2_pcrread"):
            # utils 4.0
            res = subprocess.run(["tpm2_pcrread", "sha1:%s" % ",".join(map(str, idxs)),
                                                  "-Q", "-o", "/dev/stdout"],
                                 stdout=subprocess.PIPE)
        elif in_path("tpm2_pcrlist"):
            res = subprocess.run(["tpm2_pcrlist", "-L", "sha1:%s" % ",".join(map(str, idxs)),
                                                  "-Q", "-o", "/dev/stdout"],
                                 stdout=subprocess.PIPE)
        res.check_returncode()
        buf = res.stdout
        return {idx: buf[n*PCR_SIZE:(n+1)*PCR_SIZE] for (n, idx) in enumerate(idxs)}
    else:
        pcrs = {}
        with open("/sys/class/tpm/tpm0/pcrs", "r") as fh:
            for line in fh:
                if line.startswith("PCR-"):
                    idx, buf = line.strip().split(": ")
                    idx = int(idx[4:], 10)
                    buf = bytes.fromhex(buf)
                    pcrs[idx] = buf
        return pcrs
