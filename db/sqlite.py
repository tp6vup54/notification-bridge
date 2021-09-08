import hashlib
import sqlite3


class Sqlite:
    def __init__(self, path: str):
        self.con = sqlite3.connect(path)
        self.cursor = self.con.cursor()
        self.table_name = 'history'
        self.cursor.execute(f'select name from sqlite_master where type=\'table\' and name=\'{self.table_name}\';')
        res = self.cursor.fetchall()
        if not res:
            self.cursor.execute(f'create table {self.table_name} (id, name, site)')

    def get_site_history(self, site: str) -> [tuple]:
        self.cursor.execute(f'select * from history where site = \'{site}\'')
        return self.cursor.fetchall()

    def insert_site_history(self, data: [(str, str)]) -> None:
        for d in data:
            md5 = hashlib.md5()
            md5.update(d[0].encode())
            md5.update(d[1].encode())
            hex_id = md5.hexdigest()
            self.cursor.execute(f'insert into history values (\'{hex_id}\', \'{d[0]}\', \'{d[1]}\')')
        self.con.commit()

    def delete_site_history(self, hash_list: [str]):
        for h in hash_list:
            self.cursor.execute(f'delete from history where id = \'{h}\'')
        self.con.commit()

    def close(self):
        self.con.close()
