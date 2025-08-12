### Content

Required OAuth2 scope: 

api.read

Returns a set of posts created during the specified date range and matched by the requested Listening queries.

#### Parameters

| Name | Description |
| --- | --- |
| date_start, date_end | `string`, the beginning / end of the period you want to get the data for in the format YYYY-MM-DD. Your request is transformed using the time zone assigned to a profile in the Suite settings of your account. The response of the endpoint displays the date/time in UTC time zone. The last day will be also included in the response. |
| listening_queries | `array` of strings, consists of listening query IDs. You can get the listening query IDs from the [List of Listening Queries](https://api.emplifi.io/#list-of-listening-queries) section. |
| fields | `array`, the list of fields that will be returned in the response. Available fields are listed in the table below. |
| limit | `integer`, (optional). The number of results per page. The default and maximum value is 100. |
| sort | (optional), You can sort the results by specifying a field and sorting order in the sort object: `"field": "interactions"` and `"order": "desc"`. See the list of [fields allowed for sorting](https://api.emplifi.io/#listening-posts-sort-fields). |
| filter | (optional), You can filter results by providing the filter parameter with `field` and `value`. See the list of [fields allowed for filtering](https://api.emplifi.io/#listening-posts-filter-fields). |

#### Parameter for Pagination

| after | `string`, value of the next property from previous response. |
| --- | --- |

##### Basic Fields

| Name | Type | Example | Description |
| --- | --- | --- | --- |
| attachments | `array` | ```json<br>{"url": "https://www.instagram.com/p/CdI4TI-xxxx/", "image_url": "https://scontent-lax3-2.cdninstagram.com/…", "type": "photo"}<br>``` | Post attachments. Objects contain fields depending on platform and attachment type: "title", "description", "url", "type", "image_url", "video_url". |
| author | `object` | ```json<br>{"id": "1784142059xxxxxxx", "name": "Emplifi", "url": "https://www.instagram.com/emplifi"}<br>``` | Information about author of the post. Not returned if the author is not in our database. |
| authorId | `string` | ```json<br>1784142059xxxxxxx<br>``` | Id of the author of the post. |
| comments | `integer` | ```json<br>4<br>``` | Comment count of the post. |
| content_type | `string` | ```json<br>post<br>``` | Content type of the post. |
| country | `string` | ```json<br>US<br>``` | Country of origin of the post. |
| created_time | `datetime` | ```json<br>2022-05-17T14:52:32+02:00<br>``` | Date and time the post was created. |
| id  | `string` | ```json<br>17873624615551014<br>``` | Post id. |
| interactions | `integer` | ```json<br>33<br>``` | Number of post interactions. |
| language | `string` | ```json<br>en<br>``` | Language of the post. |
| listening_queries | `array` | ```json<br>["LNQ_302015_60894bf0f78e8dxxxxxxxxxx"]<br>``` | Listening queries associated with this post. |
| media_type | `string` | ```json<br>status<br>``` | Media type of the post. |
| mentions | `array` | ```json<br>["876011587617918977"]<br>``` | Ids of mentioned profiles in the post (Twitter only). |
| message | `string` | ```json<br>Hello from Emplifi!<br>``` | Message of the post. |
| platform | `string` | ```json<br>instagram<br>``` | Platform, where the post was created. |
| post_labels | `array` | ```json<br>[{"id": "785c242afee7418e9877bb885xxxxxxx", "name": "Label B"}, {"id": "fc3fa9ff8df14xxxxxxx", "name": "Label C"}]<br>``` | Content labels assigned to the post. |
| potential_impressions | `integer` | ```json<br>18972<br>``` | Potential impressions of the post. |
| profileId | `string` | ```json<br>1784142059xxxxxxx<br>``` | Id of the profile associated with the post. |
| sentiment | `string` | ```json<br>no_sentiment<br>``` | Users sentiment towards the post. |
| shares | `integer` | ```json<br>14<br>``` | Number of times the post was shared on the platform. |
| site | `string` | ```json<br>example.net<br>``` | Website from which the post was obtained. |
| url | `string` | ```json<br>https://www.instagram.com/p/CUKrCG1rxNi/<br>``` | Link to the post. |

##### Fields that might be used to sort Listening posts:

Basic Fields

- comments
- interactions
- potential_impressions
- shares

##### Fields that might be used to filter Listening posts:

| Field | Allowed values | Description | [Advanced filter support](https://api.emplifi.io/#filter-settings) |
| --- | --- | --- | --- |
| content_type | `post`<br>`comment` | Content type of the post. | ✅ Supported operators:<br><br>- `match_any` |
| country | `*`<br>Pattern: `.+` | Country of origin of the post. | ✅ Supported operators:<br><br>- `match_any` |
| language | `*`<br>Pattern: `.+` | Language of the post. | ✅ Supported operators:<br><br>- `match_any` |
| media_type | `album`<br>`animated_gif`<br>`carousel`<br>`link`<br>`note`<br>`offer`<br>`photo`<br>`poll`<br>`reel`<br>`status`<br>`video` | Media type of the post. | ✅ Supported operators:<br><br>- `match_any` |
| platform | `blogs`<br>`facebook`<br>`forums`<br>`instagram`<br>`news`<br>`twitter`<br>`youtube` | Platform, where the post was created. | ✅ Supported operators:<br><br>- `match_any` |
| post_labels | `*`<br>Pattern: `.+` | Content labels assigned to the post. | ✅ Supported operators:<br><br>- `match_all`<br>- `match_any` |
| sentiment | `positive`<br>`negative`<br>`neutral` | Users sentiment towards the post. | ✅ Supported operators:<br><br>- `match_any` |

#### Response

| Name | Description |
| --- | --- |
| success | Status of the response. Possible values are true or false. |
| data | `object` containing the following properties:<br><br>- posts: `array`, containing post metric data<br>- next: `string`, pagination cursor. Used for pagination over posts data.<br>- remaining: `integer`, number of remaining items, counting from current page, until end of posts data. |

---

#### Example request

```http
POST /3/listening/posts HTTPSHost: api.emplifi.io
Authorization: Basic base64_encoded_auth
Content-Type: application/json; charset=utf-8

{  "listening_queries": [    "LNQ_394957_62a11038bcd2c60422edb994",    "LNQ_394957_6241c597857f917a0529975d"
  ],  "date_start": "2022-06-01",  "date_end": "2022-06-30",  "fields": [    "id",    "created_time",    "author",    "content_type",    "comments",    "interactions"
  ],  "sort": [    {      "field": "comments",      "order": "desc"
    }  ],  "filter": [    {      "field": "platform",      "value": "facebook"
    }  ],  "limit": 5
}
```

#### Example response

```json
{
  "success": true,
  "data": {
    "posts": [
      {
        "id": "164929129743_10155892118379744",
        "created_time": "2022-06-04T16:06:00+00:00",
        "author": {
          "id": "164929129743",
          "name": "Emplifi",
          "url": "https://www.facebook.com/Emplifi"
        },
        "content_type": "post",
        "comments": 153,
        "interactions": 5628
      }
    ],
    "next": "eyJuZXh0IjoiZXlKeGRXVnllU0k2ZXlKbVpXVmtWSGx3WlNJNkluVnpaWEpHWldWa0lpd2labWxsYkdSeklqcGJJbWxrSWl3aVkzSmxZWFJsWkZScGJXVWlMQ0poZFhSb2IzSkpibVp2SWl3aVkyOXVQ==",
    "remaining": 194
  }
}
```