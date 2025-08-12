### Metrics

Required OAuth2 scope: 

api.read

Returns metrics for requested listening queries.

#### Request

##### Parameters

| Name | Description |
| --- | --- |
| date_start, date_end | `string`, the beginning / end of the period you want to get the data for in the ISO date-time format without timezone. |
| listening_queries | `array` of strings, consists of listening query IDs. You can get the listening query IDs from the [List of Listening Queries](https://api.emplifi.io/#list-of-listening-queries) section. |
| metrics | `array` of objects. See parameters of the object in [table below](https://api.emplifi.io/#listening-metrics-metrics). |
| dimensions (optional) | `array` of objects. The data of the metric can be split by a specific dimension. See the [metrics table](https://api.emplifi.io/#listening-metrics-metrics) below for list of available dimensions. |
| filter (optional) | `array` of objects. You can filter the results using simple or [advanced post filters](https://api.emplifi.io/#filter-settings). See the table of [fields allowed for filtering](https://api.emplifi.io/#listening-metrics-filter-fields). |

##### Metrics

###### Parameters

| Name | Description |
| --- | --- |
| metric | `string`, table of available metrics is displayed below. |

###### Available metrics

| Name | Dimensions | Aggregation | Metric Description |
| --- | --- | --- | --- |
| authors | `content_type`,<br>`country`,<br>`hashtag`,<br>`keyword`,<br>`language`,<br>`location`,<br>`media_type`,<br>`organization`,<br>`person`,<br>`platform`,<br>`post_label`,<br>`profession`,<br>`sentiment`,<br>`topic`,<br>`url` | sum | The number of users who produced content. |
| comments | `content_type`,<br>`country`,<br>`hashtag`,<br>`keyword`,<br>`language`,<br>`location`,<br>`media_type`,<br>`organization`,<br>`person`,<br>`platform`,<br>`post_label`,<br>`profession`,<br>`sentiment`,<br>`topic`,<br>`url` | sum | The number of comments. |
| content_count | `content_type`,<br>`country`,<br>`hashtag`,<br>`keyword`,<br>`language`,<br>`location`,<br>`media_type`,<br>`organization`,<br>`person`,<br>`platform`,<br>`post_label`,<br>`profession`,<br>`sentiment`,<br>`topic`,<br>`url` | sum | The number of total available content. |
| interactions | `content_type`,<br>`country`,<br>`hashtag`,<br>`keyword`,<br>`language`,<br>`location`,<br>`media_type`,<br>`organization`,<br>`person`,<br>`platform`,<br>`post_label`,<br>`profession`,<br>`sentiment`,<br>`topic`,<br>`url` | sum | The number of interactions. |
| potential_impressions | `content_type`,<br>`country`,<br>`hashtag`,<br>`keyword`,<br>`language`,<br>`location`,<br>`media_type`,<br>`organization`,<br>`person`,<br>`platform`,<br>`post_label`,<br>`profession`,<br>`sentiment`,<br>`topic`,<br>`url` | sum | The number of potential impressions. |
| shares | `content_type`,<br>`country`,<br>`hashtag`,<br>`keyword`,<br>`language`,<br>`location`,<br>`media_type`,<br>`organization`,<br>`person`,<br>`platform`,<br>`post_label`,<br>`profession`,<br>`sentiment`,<br>`topic`,<br>`url` | sum | The number of shares. |

##### Dimensions

###### Parameters

| Name | Description |
| --- | --- |
| type | `string`, table of available dimension types is displayed below. |
| group (optional) | `object`, can be used to limit and sort the result buckets. See parameters of the object in table below. |

###### Group parameters

| Name | Description |
| --- | --- |
| sort | `object`, can be used to define sorting logic. Consists of parameters `key` and `order`. |
| sort.key | `string`, possible values are `value` or `name`. |
| sort.order (optional) | `string`, possible values are `desc` (default) or `asc`. |
| limit | `integer`, limits number of result buckets in response. Default is `10`. |

##### Filter

| Field | Allowed values | Description | [Advanced filter support](https://api.emplifi.io/#filter-settings) |
| --- | --- | --- | --- |
| author | `[platform]-[profile_id]`<br><br>Example:<br>`facebook-1649291xxxxx` |     | ✅ Supported operators:<br><br>- `match_any` |
| content_type | `post`<br>`comment`<br>`share` |     | ✅ Supported operators:<br><br>- `match_any` |
| country | `GB`<br>`FR`<br>`CA`<br>`NE`<br>... | List of codes from ISO 3166-1 alpha-2 | ✅ Supported operators:<br><br>- `match_any` |
| language | `en`<br>`fr`<br>`de`<br>`es`<br>... | List of codes from ISO 639-1 (or ISO 639-2 if missing in ISO 639-1) | ✅ Supported operators:<br><br>- `match_any` |
| media_type | `album`<br>`animated_gif`<br>`carousel`<br>`link`<br>`note`<br>`offer`<br>`photo`<br>`poll`<br>`reel`<br>`status`<br>`video` |     | ✅ Supported operators:<br><br>- `match_any` |
| platform | `facebook`<br>`instagram`<br>`linkedin`<br>`pinterest`<br>`tiktok`<br>`twitter`<br>`youtube`<br>`blogs`<br>`forums`<br>`news` |     | ✅ Supported operators:<br><br>- `match_any` |
| post_labels | `*`<br>Pattern: `.+` | See [List of Content Labels](https://api.emplifi.io/#list-of-post-labels) | ✅ Supported operators:<br><br>- `match_all`<br>- `match_any` |
| sentiment | `positive`<br>`negative`<br>`neutral`<br>`no_sentiment` |     | ✅ Supported operators:<br><br>- `match_any` |

#### Response

##### Parameters

| Name | Description |
| --- | --- |
| success | `boolean`, status of the response. Possible values are `true` or `false`. |
| header | `array` of objects. Result format depends on request parameters. |
| data | `array` of arrays. Result format depends on request parameters. |

---

#### Example request

```http
POST /3/listening/metrics HTTPSHost: api.emplifi.io
Authorization: Basic base64_encoded_auth
Content-Type: application/json; charset=utf-8

{  "date_start": "2022-01-01T00:30:00",  "date_end": "2022-12-31",  "listening_queries": [    "LNQ_394xxx_6241c636857f917a0xxxxxxx",    "LNQ_394xxx_62a11038bcd2c6042xxxxxxx"
  ],  "metrics": [    {      "metric": "comments"
    }  ],  "dimensions": [    {      "type": "platform",      "group": {        "sort": {          "key": "value",          "order": "asc"
        },        "limit": 3
      }    },    {      "type": "content_type"
    }  ],  "filter": [    {      "field": "sentiment",      "value": "positive"
    }  ]}
```

#### Example response

```json
{
  "success": true,
  "header": [
    {
      "type": "platform",
      "rows": [
        "blogs",
        "forums",
        {
          "other": {
            "length": 3
          }
        }
      ]
    },
    {
      "type": "content_type",
      "rows": [
        "comment",
        "post"
      ]
    },
    {
      "type": "metric",
      "rows": [
        "comments"
      ]
    }
  ],
  "data": [
    [
      [
        21
      ],
      [
        3
      ]
    ],
    [
      [
        0
      ],
      [
        null
      ]
    ],
    [
      [
        4
      ],
      [
        51
      ]
    ]
  ]
}
```