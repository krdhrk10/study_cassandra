# -*- coding:utf-8 -*-
import argparse
import json
import time
import uuid
from cassandra.cluster import Cluster
from cassandra.util import uuid_from_time

HOSTNAME = 'cassandra'
KEYSPACE = 'cs_tutorial_ks'


def cassandra_session(func):
    cluster = Cluster([HOSTNAME])

    def wrapper(*args, **kwargs):
        session = cluster.connect()

        new_args = [session]
        new_args.extend(args)
        resp = func(*new_args, **kwargs)

        cluster.shutdown()
        return resp
    return wrapper


@cassandra_session
def select_members(session):
    items = []
    rows = session.execute(
        """
        SELECT * FROM {keyspace}.members;
        """.format(keyspace=KEYSPACE)
    )
    for row in rows:
        items.append({
            'id': str(row.id),
            'name': row.name,
            'age': row.age,
        })
    return items


@cassandra_session
def select_member(session, id=None):
    rows = session.execute(
        """
        SELECT * FROM {keyspace}.members
        WHERE id=%s
        """.format(keyspace=KEYSPACE),
        (uuid.UUID(id),)
    )
    row = rows.one()
    if not row:
        raise Exception('Not Found')

    return {
        'id': id,
        'name': row.name,
        'age': row.age,
    }


@cassandra_session
def insert_member(session, name=None, age=None):
    id = uuid_from_time(time.time())
    session.execute(
        """
        INSERT INTO {keyspace}.members (id, name, age)
        VALUES (%s, %s, %s);
        """.format(keyspace=KEYSPACE),
        (id, name, age,)
    )
    return {
        'id': str(id),
        'name': name,
        'age': age,
    }


@cassandra_session
def update_member(session, id=None, name=None, age=None):
    target_uuid = uuid.UUID(id)
    rows = session.execute(
        """
        SELECT * FROM {keyspace}.members
        WHERE id=%s
        """.format(keyspace=KEYSPACE),
        (target_uuid,)
    )
    row = rows.one()
    if not row:
        raise Exception('Not Found')

    session.execute(
        """
        INSERT INTO {keyspace}.members (id, name, age)
        VALUES (%s, %s, %s);
        """.format(keyspace=KEYSPACE),
        (target_uuid, name, age,)
    )
    return {
        'id': id,
        'name': name,
        'age': age,
    }


@cassandra_session
def delete_member(session, id=None):
    session.execute(
        """
        DELETE FROM {keyspace}.members
        WHERE id=%s
        """.format(keyspace=KEYSPACE),
        (uuid.UUID(id),)
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cassandra Python Sample')
    parsers = parser.add_subparsers()

    # list
    list_parser = parsers.add_parser('list', help='list sample')
    list_parser.set_defaults(func=select_members)

    # get
    get_parser = parsers.add_parser('get', help='get sample')
    get_parser.add_argument('id', type=str, help='target member id')
    get_parser.set_defaults(func=select_member)

    # add
    add_parser = parsers.add_parser('add', help='add sample')
    add_parser.add_argument('name', type=str, help='target member name')
    add_parser.add_argument('age', type=int, help='target member age')
    add_parser.set_defaults(func=insert_member)

    # update
    upd_parser = parsers.add_parser('update', help='update sample')
    upd_parser.add_argument('id', type=str, help='target member id')
    upd_parser.add_argument('name', type=str, help='target member name')
    upd_parser.add_argument('age', type=int, help='target member age')
    upd_parser.set_defaults(func=update_member)

    # delete
    del_parser = parsers.add_parser('delete', help='delete sample')
    del_parser.add_argument('id', type=str, help='target member id')
    del_parser.set_defaults(func=delete_member)

    args = parser.parse_args()
    func = args.func
    kwargs = vars(args)
    del kwargs['func']
    resp = func(**kwargs)
    if resp:
        print(json.dumps(resp, indent=2))
    print('Result: Success')
