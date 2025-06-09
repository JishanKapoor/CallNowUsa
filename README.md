# CallNowUSA
A Python client for the CallNowUSA API to send messages and manage calls. Please visit CallNowUsa.com for more information.

## Installation
```bash
pip install callnowusa
```

## Usage
```python
from callnowusa import Client

# Initialize CallNowUSA client
account_sid = 'YOUR_ACCOUNT_SID'  # e.g., 'SID_xxx...'
auth_token = 'YOUR_AUTH_TOKEN'   # e.g., 'AUTH_xxx...'
callnowusa_number = 'default'    # or your assigned CallNowUSA number

client = Client(account_sid, auth_token, callnowusa_number)

# Numbers to interact with
to_number = '+19876543210'
to_number2 = '+10987654321'

# 1. Send SMS
try:
    message = client.messages.create(
        body="Test message from CallNowUSA.",
        from_=callnowusa_number,
        to=to_number
    )
    print(f"Message SID: {message.sid}")
    print(f"Message Response: {message.fetch()}")
except Exception as e:
    print(f"Error sending message: {e}")

# 2. Direct Call
try:
    call = client.calls.create(
        to=to_number,
        from_=callnowusa_number,
        auto_hang=False  # False keeps call active; True hangs up after connect
    )
    print(f"Direct Call SID: {call.sid}")
    print(f"Direct Call Response: {call.fetch()}")
except Exception as e:
    print(f"Error initiating direct call: {e}")

# 3. Merge Call
try:
    merge_call = client.calls.merge(
        phone_1=to_number,
        phone_2=to_number2,
        from_=callnowusa_number
    )
    print(f"Merge Call SID: {merge_call.sid}")
    print(f"Merge Call Response: {merge_call.fetch()}")
except Exception as e:
    print(f"Error initiating merge call: {e}")
```

## Requirements
- Python 3.7+
- `requests` (installed automatically via `pip`)

## Setup
1. Get `account_sid`, `auth_token`, and `callnowusa_number` from the CallNowUSA dashboard.
2. Install the package using the command above.
3. Replace placeholders in the usage examples with your credentials.

## License
MIT
