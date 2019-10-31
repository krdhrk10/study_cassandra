# Cassandra Tutorial

## CQL Base

### How to run
```
$ docker-compose up -d

... wait until cassandra ready

$ docker exec -ti cassandra_app  cqlsh cassandra --cqlversion=3.4.4
```

### CQL
#### CREATE KEYSPACE
```
cqlsh> CREATE KEYSPACE cs_tutorial_ks WITH REPLICATION = {
   ...   'class': 'SimpleStrategy',
   ...   'replication_factor': 1
   ... };
```

#### CREATE TABLE
```
cqlsh> CREATE TABLE cs_tutorial_ks.members (
   ...   id UUID,
   ...   name text,
   ...   age int,
   ...   PRIMARY KEY(id)
   ... );
```

#### INSERT
```
cqlsh> INSERT INTO cs_tutorial_ks.members (id, name, age)
   ... VALUES (
   ...   UUID(), 'Alice', 5
   ... );
```

#### SELECT
```
cqlsh> SELECT * FROM cs_tutorial_ks.members;

 id                                   | age | name
--------------------------------------+-----+-------
 d9d7a181-e5da-46a4-87b5-71536bb31e12 |  10 |   Bob
 b0029168-e682-477a-bf4b-c76c496cc5c1 |   5 | Alice
 8595b154-4624-4676-83d1-b0230796d5d0 |  18 | Chris

(3 rows)
```

where句はPRIMARY KEYにのみ指定できる  
```
[OK]
cqlsh> SELECT age, name FROM cs_tutorial_ks.members WHERE id=b0029168-e682-477a-bf4b-c76c496cc5c1;

 age | name
-----+-------
   5 | Alice
   
[NG]
cqlsh> SELECT age, name FROM cs_tutorial_ks.members WHERE age=5;
InvalidRequest: Error from server: code=2200 [Invalid query] message="Cannot execute this query as it might involve data filtering and thus may have unpredictable performance. If you want to execute this query despite the performance unpredictability, use ALLOW FILTERING"
```

ALLOW FILTERINGを指定すると一応実行はできるが、フルスキャンしてしまうので実運用では使用すべきでない  
```
cqlsh> SELECT age, name FROM cs_tutorial_ks.members WHERE age=5 ALLOW FILTERING;

 age | name
-----+-------
   5 | Alice

(1 rows)
```

また、INDEXを作成することでも検索キー指定できるようになる。  
が、こちらも分散されたデータ配置を意識して慎重に指定すべき。  
```
cqlsh> CREATE INDEX member_ages ON cs_tutorial_ks.members (age);
cqlsh> SELECT age, name FROM cs_tutorial_ks.members WHERE age=5;

 age | name
-----+-------
   5 | Alice

(1 rows)
```

#### DESC KEYSPACES
```
cqlsh> DESC KEYSPACES;

cs_tutorial_ks  system_auth  system_distributed
system_schema   system       system_traces     
```

#### DESC KEYSPACE ???
```
cqlsh> DESC KEYSPACE cs_tutorial_ks;

CREATE KEYSPACE cs_tutorial_ks WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}  AND durable_writes = true;

CREATE TABLE cs_tutorial_ks.members (
    id uuid PRIMARY KEY,
    age int,
    name text
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy', 'max_threshold': '32', 'min_threshold': '4'}
    AND compression = {'chunk_length_in_kb': '64', 'class': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND crc_check_chance = 1.0
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99PERCENTILE';
```

#### DESC TABLES
```
cqlsh> DESC TABLES;

Keyspace cs_tutorial_ks
-----------------------
members

Keyspace system_schema
----------------------
tables     triggers    views    keyspaces  dropped_columns
functions  aggregates  indexes  types      columns        

Keyspace system_auth
--------------------
resource_role_permissons_index  role_permissions  role_members  roles

Keyspace system
---------------
available_ranges          peers               batchlog        transferred_ranges
batches                   compaction_history  size_estimates  hints             
prepared_statements       sstable_activity    built_views   
"IndexInfo"               peer_events         range_xfers   
views_builds_in_progress  paxos               local         

Keyspace system_distributed
---------------------------
repair_history  view_build_status  parent_repair_history

Keyspace system_traces
----------------------
events  sessions
```
#### DESC TABLE ???
```
cqlsh> DESC TABLE cs_tutorial_ks.members;

CREATE TABLE cs_tutorial_ks.members (
    id uuid PRIMARY KEY,
    age int,
    name text
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy', 'max_threshold': '32', 'min_threshold': '4'}
    AND compression = {'chunk_length_in_kb': '64', 'class': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND crc_check_chance = 1.0
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99PERCENTILE';
```

#### CREATE MATERIALIZED VIEW
MATERIALIZED VIEWを作成することで、特定のカラムをPartition Keyとして検索することができるようになる。  
Secondary Indexと比較した優位性などは不明。。  
しかもこれも「not recommended for production use」。  
なんというか結局使い勝手はRDBと変わらないのではないか（というより、かなり限定的な条件でしか使えないのでは）。
```
cqlsh> CREATE MATERIALIZED VIEW cs_tutorial_ks.age_members
   ... AS SELECT id, age, name
   ... FROM cs_tutorial_ks.members
   ... WHERE age IS NOT NULL AND id IS NOT NULL
   ...  PRIMARY KEY (age, id);
   

Warnings :
Materialized views are experimental and are not recommended for production use.
```

VIEWなので当然、オリジナルのデーブルの更新が自動反映される。（ある程度の遅延は見込む必要がある）  
```
cqlsh> SELECT * FROM cs_tutorial_ks.age_members;

 age | id                                   | name
-----+--------------------------------------+-------
   5 | b0029168-e682-477a-bf4b-c76c496cc5c1 | Alice
  10 | d9d7a181-e5da-46a4-87b5-71536bb31e12 |   Bob
  18 | 8595b154-4624-4676-83d1-b0230796d5d0 | Chris

(3 rows)


// ageで検索できる
cqlsh> SELECT * FROM cs_tutorial_ks.age_members WHERE age = 5;

 age | id                                   | name
-----+--------------------------------------+-------
   5 | b0029168-e682-477a-bf4b-c76c496cc5c1 | Alice


// オリジナルのテーブルにデータ追加
cqlsh> INSERT INTO cs_tutorial_ks.members (id, name, age)
   ... VALUES (UUID(), 'Dave', 18);
cqlsh> SELECT * FROM cs_tutorial_ks.age_members WHERE age = 18;

 age | id                                   | name
-----+--------------------------------------+-------
  18 | 33912f3c-ccbc-43d8-a229-1c9696982610 |  Dave
  18 | 8595b154-4624-4676-83d1-b0230796d5d0 | Chris


// オリジナルのテーブルからデータ削除
cqlsh> DELETE FROM cs_tutorial_ks.memebers WHERE id=33912f3c-ccbc-43d8-a229-1c9696982610;
cqlsh> SELECT * FROM cs_tutorial_ks.age_members WHERE age = 18;

 age | id                                   | name
-----+--------------------------------------+-------
  18 | 8595b154-4624-4676-83d1-b0230796d5d0 | Chris
```

## Python Client Sample
### How to run
```
$ docker-compose up -d

... wait until cassandra ready

$ docker exec -ti cassandra_app  python main.py COMMAND

COMMAND:
 - list
 - get
 - add
 - update
 - delete
```

## note
- cqlshはpython2.7ベースでないと動かない様子
- cassandra-cliはversion2.2からdeprecatedとなり、cqlshが同梱されるようになった模様
- CQLベースではないAPIを使用したければThrift経由で叩く必要がありそう
  - Thrift APIはどうやら導入しずらくなっている模様？cassandra.thriftファイルが同梱されていないように見える。
	CQL v3を推奨しているということか。
- Super Columnも将来的に廃止になる見込みらしく、CQL v3では使用できない
