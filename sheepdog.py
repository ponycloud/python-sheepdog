__author__ = 'ondrej'
__all__ = ['SheepdogStorage', 'SheepdogStorageException']

import subprocess
import re

RE_LINE = re.compile('(?:(?:\\\\.|[^\\ \t\v\r\n])+[ \t\v\r\n]){8}', re.S)
RE_COLS = re.compile('(?:\\\\.|[^\\ \t\v\r\n])+', re.S)
RE_WORD = re.compile('\\\\(.)', re.S)

def wrap_popen(*args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise SheepdogStorageException(err)
    return out
    
class SheepdogStorage(object):
    """
    Wrapper for managing Sheepdog VDIs and snapshots
    """

    def create_vdi(self, name, size):
        """
        Creates VDI of given name and size

        name is arbitrary string
        size can be int or string in format "10G"
        """
        wrap_popen('qemu-img', 'create', 'sheepdog:%s' % name, size)

    def list_vdi(self):
        """
        Returns list of VDIs the same way collie vdi list does

        example:
        {'Alice': {
           'clone': False,
           'creation_time': '1344950085',
           'id': '2',
           'name': 'Alice',
           'shared': '0',
           'size': '21474836480',
           'snapshot': False,
           'used': '0',
           'vdi_id': '15d168'},
        {'Hello kitty': {
           'clone': False,
           'creation_time': '1344951085',
           'id': '1',
           'name': 'Hello kitty',
           'shared': '0',
           'size': '2199023255552',
           'snapshot': False,
           'used': '0',
           'vdi_id': 'ea5044'}
        """
        vdi_list_raw = wrap_popen('collie', 'vdi', 'list', '-r')
        lines = RE_LINE.findall(vdi_list_raw)
        vdis = {}
        for line in lines:
            cols = [RE_WORD.sub('\\1', x) for x in RE_COLS.findall(line)]
            vdis[cols[1]] = {     'snapshot': cols[0] == 's',
                                     'clone': cols[0] == 'c',
                                      'name': cols[1],
                                        'id': cols[2],
                                      'size': cols[3],
                                      'used': cols[4],
                                    'shared': cols[5],
                             'creation_time': cols[6],
                                    'vdi_id': cols[7]}
        return vdis

    def vdi_exists(self, name):
        """
        Checks if VDI of given name exists
        """
        return name in self.list_vdi()


    def resize_vdi(self, name, size):
        """
        Resizes VDI of given name to given size

        name must be existing VDI's name
        size can be int or string in format "10G"
        """
        wrap_popen('collie', 'vdi', 'resize', name, size)

    def create_snapshot(self, name, snapshot_id=None):
        """
        Creates snapshot of VDI of given name

        name must be existing VDI's name
        snapshot is arbitrary string
        """
        if snapshot_id is None:
            wrap_popen('collie', 'vdi', 'snapshot', name)
        else:
            wrap_popen(
                'collie', 'vdi', 'snapshot', '-s', snapshot_id, name)

    def delete(self, vdi_name, snapshot_id=None):
        """
        Deletes a snapshot of a VDI (defined by name) of given snapshot_id

        snapshot_id must be an if of a snapshot
        name is arbitrary string
        """
        if snapshot_id is None:
            wrap_popen('collie', 'vdi', 'delete', name)
        else:
            wrap_popen(
            'collie', 'vdi', 'delete', '-s', snapshot_id, vdi_name)

    def clone(self, source_name, snapshot_id, dest_name):
        """
        Clones a VDI snapshot

        source_name and snapshot_id identifes the source
        dest_name is name of newly created VDI
        """
        wrap_popen(
            'collie', 'vdi', 'clone', '-s', snapshot_id, source_name,
             dest_name)

class SheepdogStorageException(Exception): pass

if __name__ == "__main__":
    c = SheepdogStorage()
    c.resize_vdi("Mooo", "10G")
