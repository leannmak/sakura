# SAKURA API Usage - Realtime Module

Leann Mak, leannmak@139.com, (c) 2018.

### Notice
 
Remember to set ```Content-Type: application/json``` when `POST` if using `JSON`.

| Role | Name | Location | Type | Description |
| --- | --- | --- | ----- | ----------- |
| 数据格式 | Content-Type | header | application/json | POST/PUT请求数据格式为JSON |

#### API List
* [configuration update（配置变更）](#configuration-update)
    * [POST: executing a configuration update task](#cfg_updpost)
    * [GET: checking task status](#cfg_updget)
* [configuration acknowledge（配置变更通过）](#configuration-acknowledge)
    * [POST: executing an acknowledge task for a configuration update task](#cfg_ackpost)
    * [GET: checking task status](#cfg_ackget)
* [configuration rollback（配置变更回滚）](#configuration-rollback)
    * [POST: executing a rollback task for a configuration update task](#cfg_rbkpost)
    * [GET: checking task status](#cfg_rbkget)
* [configuration check（配置文件状态检查）](#configuration-check)
    * [POST: executing a configuration check task](#cfg_chkpost)
    * [GET: checking task status](#cfg_chkget)

### configuration update
#### cfg_upd.post
##### /api/&lt;api version&gt;/sakura/cfg_upd
* Description: this api allows to update configuration files in the remote hosts.
* Normal response code: 201
* Error response code: 400, 403, 500
* Error message:

| Message | Meaning | Code |
| --------------- | --------------- | --- |
| Invalid Access | 请求参数/格式非法 | 400 |
| Task Constraint Conflict | 任务冲突 | 403 |
| Pre Task Unconfirmed | 前序任务执行结果未确认 | 403 |

* Request arguments:

| Role | Name | Location | Type | Description | Unique Constraint | Required |
| --- | --- | --- | --------------- | ------------ | -------- | --- |
| 请求参数 | service_name | body | string | 服务名称 | `service_version`、`env_name`相同时存在任务锁，前一任务执行结果确认前不可执行下一任务 | yes |
| 请求参数 | `service_version` | body | string | 服务版本 | 无 | yes |
| 请求参数 | `env_name` | body | string | 环境名称 | 无 | yes |
| 请求参数 | check_cmd | body | string | 配置检查命令 | 无 | no |
| 请求参数 | reload_cmd | body | string | 服务重启/重加载命令 | 无 | no |
| 请求参数 | files | body | list of `dict(name=str, dir=str, mode=str, owner=dict(name=str, group=str), template=str, items=dict)` | 配置文件信息列表 | 无 | yes |
| 请求参数 | hosts | body | list | 服务所在主机IP列表 | 无 | yes if `use_disconf` is false |
| 请求参数 | `use_disconf` | body | boolean | 是否使用Disconf（默认false） | 无 | no |

* Return values:

| Role | Name | Location | Type | Description | Always in |
| --- | --- | --- | --- | ----------- | --- |
| 任务信息 | id | body | string | 任务ID，访问正常时返回 | no |
| 错误信息 | error | body | string | 错误状态描述，访问出错时返回 | no |
| 状态信息 | status | body | integer | 访问状态（0：正常，1：异常） | yes |

* Examples:  

Request:

```http
POST /api/v1.0/sakura/cfg_upd
```

```json
{
  "service_name": "test",
  "service_version": "1.0",
  "env_name": "qa",
  "check_cmd": "",
  "reload_cmd": "",
  "files": [
    {
      "name": "test.cfg",
      "dir": "/apps/conf/test",
      "mode": "0755",
      "owner": {
        "name": "leannmak",
        "group": "leannmak"
      },
      "template": "{{getv \"/who\"}} {{getv \"/what\"}} with {{getv \"/whom\"}} {{getv \"/where\"}} {{getv \"/when\"}} {{getv \"/why\"}}.\r\n",
      "items": {
        "who": "jay",
        "what": "is playing basketball",
        "whom": "kobe",
        "where": "on the playground",
        "when": "now",
        "why": "for fun"
      }
    }],
  "hosts": ["127.0.0.1"]
}
```

Response:

```json
{
    "id": "7640edbc-d6b2-4fc7-ab37-6f8a3c16bb40",
    "status": 0
}
```

#### cfg_upd.get
##### /api/&lt;api version&gt;/sakura/cfg_upd/&lt;id&gt;
* Description: this api allows to retrieve the realtime execution status of a configuration update task according to its id.
* Normal response code: 200
* Error response code: 500
* Return values:

| Role | Name | Location | Type | Description | Always in |
| --- | --- | --- | --- | ----------- | --- |
| 数据信息 | result | body | dictionary | 任务执行结果，访问正常时返回 | no |
| 错误信息 | error | body | string | 错误状态描述，访问出错时返回 | no |
| 状态信息 | status | body | integer | 访问状态（0：正常，1：异常） | yes |

* Examples:  

Request:

```http
GET /api/v1.0/sakura/cfg_upd/7640edbc-d6b2-4fc7-ab37-6f8a3c16bb40
```

Response:

```json
{
    "result": {
        "id": "7640edbc-d6b2-4fc7-ab37-6f8a3c16bb40",
        "info": {
            "current": 100,
            "data": null,
            "message": "Configurations have been updated completely.",
            "total": 100
        },
        "state": "SUCCESS"
    },
    "status": 0
}
```

### configuration acknowledge
#### cfg_ack.post
##### /api/&lt;api version&gt;/sakura/cfg_ack
* Description: this api should be called when a configuration update task is verified to be passed.
* Normal response code: 201
* Error response code: 400, 403, 500
* Error message:

| Message | Meaning | Code |
| --------------- | --------------------- | --- |
| Invalid Access | 请求参数/格式非法 | 400 |
| Failure Main Task Forced to Rollback | 配置变更任务执行过程出错时必须强制回滚 | 400 |
| Task Constraint Conflict | 任务冲突 | 403 |
| Main Task Still Running | 配置变更任务尚在执行 | 403 |
| Main Task Already Confirmed | 配置变更任务已被确认（同一配置变更任务只能执行`1`次确认——[回滚](#configuration-rollback)或[通过](#configuration-acknowledge)） | 403 |

* Request arguments:

| Role | Name | Location | Type | Description | Required |
| --- | --- | --- | --- | ------------------ | --- |
| 请求参数 | [main_task_id](#configuration-update) | body | string | 配置变更任务ID | yes |

* Return values:

| Role | Name | Location | Type | Description | Always in |
| --- | --- | --- | --- | ----------- | --- |
| 任务信息 | id | body | string | 任务ID，访问正常时返回 | no |
| 错误信息 | error | body | string | 错误状态描述，访问出错时返回 | no |
| 状态信息 | status | body | integer | 访问状态（0：正常，1：异常） | yes |

* Examples:  

Request:

```http
POST /api/v1.0/sakura/cfg_ack
```

```json
{
  "main_task_id": "7640edbc-d6b2-4fc7-ab37-6f8a3c16bb40"
}
```

Response:

```json
{
    "id": "a3ea15d7-ec83-44c6-bb35-5689f94d3887",
    "status": 0
}
```

#### cfg_ack.get
##### /api/&lt;api version&gt;/sakura/cfg_ack/&lt;id&gt;
* Description: this api allows to retrieve the realtime execution status of a configuration acknowledge task according to its id.
* Normal response code: 200
* Error response code: 500
* Return values:

| Role | Name | Location | Type | Description | Always in |
| --- | --- | --- | --- | ----------- | --- |
| 数据信息 | result | body | dictionary | 任务执行结果，访问正常时返回 | no |
| 错误信息 | error | body | string | 错误状态描述，访问出错时返回 | no |
| 状态信息 | status | body | integer | 访问状态（0：正常，1：异常） | yes |

* Examples:  

Request:

```http
GET /api/v1.0/sakura/cfg_ack/a3ea15d7-ec83-44c6-bb35-5689f94d3887
```

Response:

```json
{
    "result": {
        "id": "a3ea15d7-ec83-44c6-bb35-5689f94d3887",
        "info": {
            "current": 100,
            "data": null,
            "message": "Task <7640edbc-d6b2-4fc7-ab37-6f8a3c16bb40> have been acknowledged.",
            "total": 100
        },
        "state": "SUCCESS"
    },
    "status": 0
}
```

### configuration rollback
#### cfg_rbk.post
##### /api/&lt;api version&gt;/sakura/cfg_rbk
* Description: this api should be called when the result of a configuration update task is verified to be unexpected.
* Normal response code: 201
* Error response code: 400, 403, 500
* Error message:

| Message | Meaning | Code |
| --------------- | --------------------- | --- |
| Invalid Access | 请求参数/格式非法 | 400 |
| Task Constraint Conflict | 任务冲突 | 403 |
| Main Task Still Running | 配置变更任务尚在执行 | 403 |
| Main Task Already Confirmed | 配置变更任务已被确认（同一配置变更任务只能执行`1`次确认——[回滚](#configuration-rollback)或[通过](#configuration-acknowledge)） | 403 |

* Request arguments:

| Role | Name | Location | Type | Description | Required |
| --- | --- | --- | --- | ------------------ | --- |
| 请求参数 | [main_task_id](#configuration-update) | body | string | 配置变更任务ID | yes |

* Return values:

| Role | Name | Location | Type | Description | Always in |
| --- | --- | --- | --- | ----------- | --- |
| 任务信息 | id | body | string | 任务ID，访问正常时返回 | no |
| 错误信息 | error | body | string | 错误状态描述，访问出错时返回 | no |
| 状态信息 | status | body | integer | 访问状态（0：正常，1：异常） | yes |

* Examples:  

Request:

```http
POST /api/v1.0/sakura/cfg_rbk
```

```json
{
  "main_task_id": "7640edbc-d6b2-4fc7-ab37-6f8a3c16bb40"
}
```

Response:

```json
{
    "id": "55a9a621-55e6-4625-a606-f4defb45c518",
    "status": 0
}
```

#### cfg_rbk.get
##### /api/&lt;api version&gt;/sakura/cfg_rbk/&lt;id&gt;
* Description: this api allows to retrieve the realtime execution status of a configuration rollback task according to its id.
* Normal response code: 200
* Error response code: 500
* Return values:

| Role | Name | Location | Type | Description | Always in |
| --- | --- | --- | --- | ----------- | --- |
| 数据信息 | result | body | dictionary | 任务执行结果，访问正常时返回 | no |
| 错误信息 | error | body | string | 错误状态描述，访问出错时返回 | no |
| 状态信息 | status | body | integer | 访问状态（0：正常，1：异常） | yes |

* Examples:  

Request:

```http
GET /api/v1.0/sakura/cfg_rbk/55a9a621-55e6-4625-a606-f4defb45c518
```

Response:

```json
{
    "result": {
        "id": "55a9a621-55e6-4625-a606-f4defb45c518",
        "info": {
            "current": 100,
            "data": null,
            "message": "Task <7640edbc-d6b2-4fc7-ab37-6f8a3c16bb40> have been rolled back completely.",
            "total": 100
        },
        "state": "SUCCESS"
    },
    "status": 0
}
```

### configuration check
#### cfg_chk.post
##### /api/&lt;api version&gt;/sakura/cfg_chk
* Description: this api allows to check configuration files in the remote hosts.
* Normal response code: 201
* Error response code: 400, 403, 500
* Error message:

| Message | Meaning | Code |
| --------------- | --------------- | --- |
| Invalid Access | 请求参数/格式非法 | 400 |
| Task Constraint Conflict | 任务冲突 | 403 |
| Pre Task Unconfirmed | 前序任务执行结果未确认 | 403 |

* Request arguments:

| Role | Name | Location | Type | Description | Required |
| --- | --- | --- | --------------------- | --------- | --- |
| 请求参数 | files | body | list of `dict(name=str, dir=str, mode=str, owner=dict(name=str, group=str), template=str, items=dict)` | 配置文件信息列表 | yes |
| 请求参数 | hosts | body | list | 服务所在主机IP列表 | 无 | yes |

* Return values:

| Role | Name | Location | Type | Description | Always in |
| --- | --- | --- | --- | ----------- | --- |
| 任务信息 | id | body | string | 任务ID，访问正常时返回 | no |
| 错误信息 | error | body | string | 错误状态描述，访问出错时返回 | no |
| 状态信息 | status | body | integer | 访问状态（0：正常，1：异常） | yes |

* Examples:  

Request:

```http
POST /api/v1.0/sakura/cfg_chk
```

```json
{
  "files": [
    {
      "name": "greeting.cfg",
      "dir": "/apps/conf/test",
      "mode": "0755",
      "owner": {
        "name": "appa",
        "group": "apps"
      },
      "template": "hello world!",
      "items": {}
    },
    {
      "name": "test.cfg",
      "dir": "/apps/conf/test",
      "mode": "0755",
      "owner": {
        "name": "leannmak",
        "group": "leannmak"
      },
      "template": "{{getv \"/who\"}} {{getv \"/what\"}} with {{getv \"/whom\"}} {{getv \"/where\"}} {{getv \"/when\"}} {{getv \"/why\"}}.\r\n",
      "items": {
        "who": "jay",
        "what": "is playing basketball",
        "whom": "kobe",
        "where": "on the playground",
        "when": "now",
        "why": "for fun"
      }
    }],
  "hosts": ["127.0.0.1"]
}
```

Response:

```json
{
    "id": "d90c3081-3fbf-4058-9545-54d7b69e78bc",
    "status": 0
}
```

#### cfg_chk.get
##### /api/&lt;api version&gt;/sakura/cfg_chk/&lt;id&gt;
* Description: this api allows to retrieve the realtime execution status of a configuration check task according to its id.
* Normal response code: 200
* Error response code: 500
* Return values:

| Role | Name | Location | Type | Description | Always in |
| --- | --- | --- | --- | ----------- | --- |
| 数据信息 | result | body | dictionary | 任务执行结果，访问正常时返回 | no |
| 错误信息 | error | body | string | 错误状态描述，访问出错时返回 | no |
| 状态信息 | status | body | integer | 访问状态（0：正常，1：异常） | yes |

* Examples:  

Request:

```http
GET /api/v1.0/sakura/cfg_chk/d90c3081-3fbf-4058-9545-54d7b69e78bc
```

Response:

```json
{
    "result": {
        "id": "d90c3081-3fbf-4058-9545-54d7b69e78bc",
        "info": {
            "current": 100,
            "data": [
                {
                    "greeting.cfg": {
                        "127.0.0.1": {
                            "content": "f6ee91aecaa4e412dd75dacff705c9ea != fc3ff98e8c6a0d3087d515c0473f8677",
                            "content_actual": "hello jude, my name is leann.\nnice to meet you.\n \nme too.",
                            "content_expected": "hello world!",
                            "last_modify_time": "2018-05-22 10:24:10.637048142 +0800",
                            "mode": "0775 != 0755",
                            "owner": "OK"
                        }
                    }
                },
                {
                    "test.cfg": {
                        "127.0.0.1": {
                            "content": "OK",
                            "last_modify_time": "2018-06-08 14:35:38.159246182 +0800",
                            "mode": "OK",
                            "owner": "OK"
                        }
                    }
                }
            ],
            "message": "Configurations files have been checked completely.",
            "total": 100
        },
        "state": "SUCCESS"
    },
    "status": 0
}
```
