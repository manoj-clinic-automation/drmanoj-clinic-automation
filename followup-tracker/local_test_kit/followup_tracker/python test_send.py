import http.client
import json

conn = http.client.HTTPSConnection("publicapi.myoperator.co")
payload = json.dumps({
  "phone_number_id": "1090067637530949",
  "customer_country_code": "91",
  "customer_number": "9837114044",
  "data": {
    "type": "template",
    "context": {
      "template_name": "drmanoj_followup_due",
      "language": "en",
      "body": {
        "1": "Test Patient",
        "2": "14 Jun 2026"
      }
    }
  }
})
headers = {
  'Authorization': 'Bearer lHCxj4MRU2KwLqPr8lSI2ZOCN0x3h8SQhu293IwWHn',
  'X-MYOP-COMPANY-ID': '68384350414b9847',
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}
conn.request("POST", "/chat/messages", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
