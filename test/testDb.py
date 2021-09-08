import hashlib
import os
import unittest

from db.sqlite import Sqlite


class TestDb(unittest.TestCase):
    def setUp(self):
        self.path = 'test.db'
        if os.path.exists(self.path):
            os.remove(self.path)
        self.db = Sqlite(self.path)

    def test_init(self):
        self.assertTrue(os.path.exists(self.path))
        self.db.cursor.execute(f'select name from sqlite_master where type=\'table\' and name=\'{self.db.table_name}\';')
        res = self.db.cursor.fetchall()
        self.assertTrue(self.db.table_name in res[0])

    def test_select(self):
        self.db.insert_site_history([('aa', 'bb.com')])
        res = self.db.get_site_history('bb.com')
        md5 = hashlib.md5()
        md5.update(b'aa')
        md5.update(b'bb.com')
        self.assertEqual(res[0][0], md5.hexdigest())
        self.assertEqual(res[0][1], 'aa')
        self.assertEqual(res[0][2], 'bb.com')

    def test_delete(self):
        self.db.insert_site_history([('aa', 'bb.com'), ('cc', 'bb.com')])
        res = self.db.get_site_history('bb.com')
        md5 = hashlib.md5()
        md5.update(b'aa')
        md5.update(b'bb.com')
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0][0], md5.hexdigest())
        self.assertEqual(res[0][1], 'aa')
        self.assertEqual(res[0][2], 'bb.com')
        self.db.delete_site_history([md5.hexdigest()])
        res = self.db.get_site_history('bb.com')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][1], 'cc')
        self.assertEqual(res[0][2], 'bb.com')

    def tearDown(self) -> None:
        self.db.close()
        if os.path.exists(self.path):
            os.remove(self.path)
