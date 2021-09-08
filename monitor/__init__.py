import hashlib

from db.sqlite import Sqlite


class Monitor:
    def __init__(self, db: Sqlite):
        self.fqdn = ''
        self.db = db

    def get_alert_text(self) -> str:
        pass

    def get_product_id(self, name: str):
        m = hashlib.md5()
        m.update(name.encode())
        m.update(self.fqdn.encode())
        return m.hexdigest()
