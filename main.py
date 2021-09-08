from monitor.models import *
from notifier.models import *
from db.sqlite import Sqlite


def generate_class(conf: dict, db: Sqlite) -> list:
    instances = []
    for k, v in conf.items():
        klass = globals()[k]
        if db:
            instances.append(klass(db, *v.values()))
        else:
            instances.append(klass(*v.values()))
    return instances


async def main():
    conf = json.load(open('bridge.json'))
    db = Sqlite(conf['db'])
    notifiers = generate_class(conf['notifiers'], None)
    monitors = generate_class(conf['monitors'], db)
    alert_texts = await asyncio.gather(*(m.get_alert_text() for m in monitors))
    completed_text = '\n'.join(alert_texts)
    await asyncio.gather(*(n.notify(completed_text) for n in notifiers))

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
