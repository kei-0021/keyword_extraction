curl 'https://api.notion.com/v1/pages' \
  -H 'Authorization: Bearer ntn_a76908617672J8PK7dPw5GYMuyM2fzXj62lYfUHKNPRa5E' \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2022-06-28" \
  --data '{
	"parent": { "database_id": "14b1478eff9d4658847ce4bdc3da402a" },
  "icon": {
  	"emoji": "🍀"
  },
 "properties": {
    "Name": {
      "title": [
        {
          "text": {
            "content": "Hello Integration!"
          }
        }
      ]
    }
  }
}'
