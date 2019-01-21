# utils related to ipfs
import tarfile
import glob
import io
import os
import sys

import base58
import multihash

# make tar from protodir/*proto, and publish this tar in ipfs
# return base58 encoded ipfs hash
def publish_proto_in_ipfs(ipfs_client, protodir):
    
    if (not os.path.isdir(protodir)):
        raise Exception("Directory %s doesn't exists"%protodir)

    files = glob.glob(os.path.join(protodir, "*.proto"))

    if (len(files) == 0):
        raise Exception("Cannot find any %s files"%(os.path.join(protodir, "*.proto")) )

    # We are sorting files before we add them to the .tar since an archive containing the same files in a different
    # order will produce a different content hash;
    files.sort()
        
    tarbytes  = io.BytesIO()        
    tar       = tarfile.open(fileobj=tarbytes, mode="w")
    for f in files:
        tar.add(f, os.path.basename(f))
    tar.close()
    return ipfs_client.add_bytes(tarbytes.getvalue())

# get file from ipfs
# We must check the hash becasue we cannot believe that ipfs_client wasn't been compromise
def get_from_ipfs_and_checkhash(ipfs_client, ipfs_hash_base58):
    data  = ipfs_client.cat(ipfs_hash_base58)
    validate = False
    if validate:
        block_data = ipfs_client.block_get(ipfs_hash_base58)
        # multihash is old and has a badly registered base58 codec, overwrite it...
        multihash.CodecReg.register('base58', base58.b58encode, base58.b58decode)
        # create a multihash object
        mh = multihash.decode(ipfs_hash_base58.encode('ascii'), 'base58')
        
        # Debugging
        print(mh.encode('base58')) # Ensure this gives us the same as the input
        # Just see what hash we get from the block_data...
        print(multihash.digest(block_data, 'sha2_256').encode('base58'))
        # Convenience method lets us load a multihash and use it to verify data
        if not mh.verify(block_data):
            raise Exception("IPFS hash mismatch with data")
    return data

# Convert in and from bytes uri format used in Registry contract
# TODO: we should pad string with zeros till closest 32 bytes word because of a bug in processReceipt (in snet_cli.contract.process_receipt)
def hash_to_bytesuri(s):
    s = "ipfs://" + s
    return s.encode("ascii").ljust(32 * (len(s)//32 + 1), b"\0")

def bytesuri_to_hash(s):
    s = s.rstrip(b"\0").decode('ascii')
    if (not s.startswith("ipfs://")):
        raise Exception("We support only ipfs uri in Registry")
    return s[7:]

# tar files might be dangerous (see https://bugs.python.org/issue21109,
# and https://docs.python.org/3/library/tarfile.html, TarFile.extractall warning)
# we extract only simple files
def safe_extract_proto_from_ipfs(ipfs_client, ipfs_hash, protodir):
    spec_tar = get_from_ipfs_and_checkhash(ipfs_client, ipfs_hash)
    with tarfile.open(fileobj=io.BytesIO(spec_tar)) as f:
        for m in f.getmembers():
            if (os.path.dirname(m.name) != ""):
                raise Exception("tarball has directories. We do not support it.")
            if (not m.isfile()):
                raise Exception("tarball contains %s which is not a files"%m.name)
            fullname = os.path.join(protodir, m.name)
            if (os.path.exists(fullname)):
                raise Exception("%s already exists."%fullname)
        # now it is safe to call extractall
        f.extractall(protodir)
