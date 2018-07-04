# SAKURA API Usage - History Module

Leann Mak, leannmak@139.com, (c) 2018.

## Notice
 
Remember to set ```Content-Type: application/json``` when `POST` if using `JSON`.

| Role | Name | Location | Type | Description |
| --- | --- | --- | ----- | ----------- |
| 数据格式 | Content-Type | header | application/json | POST/PUT请求数据格式为JSON |

## API List
* [task（任务执行记录）](#task)
    * [GET: retrieving tasks](#taskget)

### task
#### task.get
##### /api/&lt;api version&gt;/sakura/task
* Description: this api allows to retrieve tasks.
* Normal response code: 200
* Error response code: 400, 500
* Error message:

| Message | Meaning | Code |
| --------------- | --------------- | --- |
| Invalid Access | 请求参数/格式非法 | 400 |

* Request arguments:

| Role | Name | Location | Type | Description | Required |
| --- | ------ | --- | --- | ----------- | --- |
| 分页查询 | page | URL | integer | 访问页码 | no |
| 分页查询 | pp | URL | integer | 每页记录数，指定page后生效，默认为20 | no |
| 信息检索 | 任意非扩展字段名称 | URL | string | 所有非扩展字段可检索 | no |

* Return values:

| Role | Name | Location | Type | Description | Always in |
| --- | --- | --- | --- | ----------- | --- |
| 数据信息 | data | body | dictionary | 查询结果 | yes |
| 分页信息 | totalpage | body | integer | 总页码数，若page未生效，默认为false | yes |

* Examples:  

Request:

```http
GET /api/v1.0/sakura/task
```

Response:

```json
{
    "data": [
        {
            "ack_status": null,
            "begin_time": "Fri, 08 Jun 2018 15:43:50 GMT",
            "delta_time": 3.4856,
            "end_time": "Fri, 08 Jun 2018 15:43:53 GMT",
            "info": "{\"current\": 100, \"message\": \"Configurations files have been checked completely.\", \"total\": 100, \"data\": [{\"greeting.cfg\": {\"127.0.0.1\": {\"content_actual\": \"hello jude, my name is leann.\\nnice to meet you.\\n \\nme too.\", \"content_expected\": \"hello world!\", \"last_modify_time\": \"2018-05-22 10:24:10.637048142 +0800\", \"content\": \"f6ee91aecaa4e412dd75dacff705c9ea != fc3ff98e8c6a0d3087d515c0473f8677\", \"mode\": \"0775 != 0755\", \"owner\": \"OK\"}}}, {\"test.cfg\": {\"127.0.0.1\": {\"content\": \"OK\", \"owner\": \"OK\", \"mode\": \"OK\", \"last_modify_time\": \"2018-06-08 14:35:38.159246182 +0800\"}}}]}",
            "kwargs": "{\"files\": [{\"name\": \"greeting.cfg\", \"items\": {}, \"mode\": \"0755\", \"template\": \"hello world!\", \"owner\": {\"group\": \"apps\", \"name\": \"appa\"}, \"dir\": \"/apps/conf/test\"}, {\"name\": \"test.cfg\", \"items\": {\"what\": \"is playing basketball\", \"who\": \"jay\", \"when\": \"now\", \"whom\": \"kobe\", \"where\": \"on the playground\", \"why\": \"for fun\"}, \"mode\": \"0755\", \"template\": \"{{getv \\\"/who\\\"}} {{getv \\\"/what\\\"}} with {{getv \\\"/whom\\\"}} {{getv \\\"/where\\\"}} {{getv \\\"/when\\\"}} {{getv \\\"/why\\\"}}.\\r\\n\", \"owner\": {\"group\": \"leannmak\", \"name\": \"leannmak\"}, \"dir\": \"/apps/conf/test\"}], \"hosts\": [\"127.0.0.1\"]}",
            "name": "configuration_check",
            "state": "SUCCESS",
            "step": 0,
            "sub_task_id": null,
            "task_id": "d90c3081-3fbf-4058-9545-54d7b69e78bc"
        },
        {
            "ack_status": null,
            "begin_time": "Fri, 08 Jun 2018 15:19:07 GMT",
            "delta_time": 2.38401,
            "end_time": "Fri, 08 Jun 2018 15:19:09 GMT",
            "info": "{\"current\": 100, \"message\": \"Task <7640edbc-d6b2-4fc7-ab37-6f8a3c16bb40> have been acknowledged.\", \"total\": 100, \"data\": null}",
            "kwargs": "{\"main_task_id\": \"7640edbc-d6b2-4fc7-ab37-6f8a3c16bb40\"}",
            "name": "configuration_acknowledge",
            "state": "SUCCESS",
            "step": 0,
            "sub_task_id": null,
            "task_id": "a3ea15d7-ec83-44c6-bb35-5689f94d3887"
        },
        {
            "ack_status": "PASSED",
            "begin_time": "Fri, 08 Jun 2018 14:35:29 GMT",
            "delta_time": 8.84253,
            "end_time": "Fri, 08 Jun 2018 14:35:38 GMT",
            "info": "{\"current\": 100, \"message\": \"Configurations have been updated completely.\", \"total\": 100, \"data\": null}",
            "kwargs": "{\"files\": [{\"name\": \"test.cfg\", \"items\": {\"what\": \"is playing basketball\", \"who\": \"jay\", \"when\": \"now\", \"whom\": \"kobe\", \"where\": \"on the playground\", \"why\": \"for fun\"}, \"mode\": \"0755\", \"template\": \"{{getv \\\"/who\\\"}} {{getv \\\"/what\\\"}} with {{getv \\\"/whom\\\"}} {{getv \\\"/where\\\"}} {{getv \\\"/when\\\"}} {{getv \\\"/why\\\"}}.\\r\\n\", \"owner\": {\"group\": \"leannmak\", \"name\": \"leannmak\"}, \"dir\": \"/apps/conf/test\"}], \"use_disconf\": false, \"service_version\": \"1.0\", \"service_name\": \"test\", \"check_cmd\": \"\", \"hosts\": [\"127.0.0.1\"], \"env_name\": \"qa\", \"reload_cmd\": \"\"}",
            "name": "configuration_update",
            "state": "SUCCESS",
            "step": 4,
            "sub_task_id": "a3ea15d7-ec83-44c6-bb35-5689f94d3887",
            "task_id": "7640edbc-d6b2-4fc7-ab37-6f8a3c16bb40"
        }
    ],
    "totalpage": false
}
```
