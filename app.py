import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import uuid
import time
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

class Client:
    """
    Main class for managing message and call operations with credential verification.

    Attributes:
        account_sid (str): Unique account identifier for authentication.
        auth_token (str): Authentication token for secure access.
        phone_number (str): Phone number associated with the credentials, or 'default' if unassigned.
        messages (Messages): Namespace for message-related operations.
        calls (Calls): Namespace for call-related operations.
    """
    def __init__(self, account_sid, auth_token, phone_number):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.phone_number = phone_number

        # Load configuration from environment variable
        config_json = os.getenv('APP_CONFIG')
        if not config_json:
            raise ValueError("APP_CONFIG environment variable not set")
        config = json.loads(config_json)
        credentials = config.get('credentials')
        spreadsheet_url = config.get('spreadsheet_url')
        if not (credentials and spreadsheet_url):
            raise ValueError("Missing credentials or spreadsheet_url in APP_CONFIG")

        # Set up Google Sheets API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        if '\\n' in credentials['private_key']:
            credentials['private_key'] = credentials['private_key'].replace('\\n', '\n')
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
        gc = gspread.authorize(creds)
        sh = gc.open_by_url(spreadsheet_url)
        self.worksheet = sh.get_worksheet(0)

        # Verify credentials and phone number
        if not self._has_valid_credentials():
            raise ValueError('Invalid Credentials or Phone Number')

        # Set up messages and calls namespaces
        self.messages = Messages(self)
        self.calls = Calls(self)

    def _has_valid_credentials(self):
        """
        Validate stored credentials and phone number against a data source.
        Returns:
            bool: True if credentials and phone number are valid, False otherwise.
        """
        data = self.worksheet.get_all_values()
        for row in data:
            if (len(row) >= 2 and
                row[0] == self.account_sid and
                row[1] == self.auth_token and
                all(cell == '' for cell in row[2:10])):
                assigned_phone = row[10] if len(row) >= 11 else ''
                if assigned_phone:
                    return assigned_phone == self.phone_number
                else:
                    return self.phone_number == 'default'
        return False

    def _wait_for_update(self, row_index, wait_for_i=False, timeout=900):
        """Poll sheet for updates to J (and I if wait_for_i) or timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            row = self.worksheet.row_values(row_index)
            j_updated = len(row) >= 10 and row[9] != ''
            i_updated = not wait_for_i or (len(row) >= 9 and row[8] != '')
            if j_updated and i_updated:
                return {'i': row[8] if wait_for_i else '', 'j': row[9]}
            time.sleep(5)
        raise TimeoutError("Timed out waiting for sheet update")

    def messages_create(self, body, from_, to):
        """Write send_text data to sheet (leave J empty) and return message object."""
        if not all([body, from_, to]):
            raise ValueError('Missing required fields')
        if not self._has_valid_credentials():
            raise ValueError('Invalid Credentials')

        sid = f'SM_{uuid.uuid4().hex}'
        row_data = [self.account_sid, self.auth_token, from_, to, '', 'send_text', '', body, '', '']
        self.worksheet.append_row(row_data)
        row_index = len(self.worksheet.get_all_values())

        def fetch(self):
            result = self.client._wait_for_update(row_index, wait_for_i=False)
            return {'sid': sid, 'status': result['j'].lower()}

        return type('Message', (), {'fetch': fetch, 'client': self})()

    def calls_create(self, to, from_, auto_hang=True):
        """Write direct_call data to sheet (leave I, J empty) and return call object."""
        if not all([to, from_]):
            raise ValueError('Missing required fields')
        if not self._has_valid_credentials():
            raise ValueError('Invalid Credentials')

        sid = f'CA_{uuid.uuid4().hex}'
        purpose = 'direct_call_auto_hangup_True' if auto_hang else 'direct_call'
        auto_hang_value = 'True' if auto_hang else ''
        row_data = [self.account_sid, self.auth_token, from_, to, '', purpose, auto_hang_value, '', '', '']
        self.worksheet.append_row(row_data)
        row_index = len(self.worksheet.get_all_values())

        def fetch(self):
            result = self.client._wait_for_update(row_index, wait_for_i=True)
            return {'sid': sid, 'duration': result['i'], 'status': result['j'].lower()}

        return type('Call', (), {'fetch': fetch, 'client': self})()

    def calls_merge(self, phone_1, phone_2, from_):
        """Write merge_call data to sheet (leave I, J empty) and return call object."""
        if not all([phone_1, phone_2, from_]):
            raise ValueError('Missing required fields')
        if not self._has_valid_credentials():
            raise ValueError('Invalid Credentials')

        sid = f'CA_{uuid.uuid4().hex}'
        row_data = [self.account_sid, self.auth_token, from_, phone_1, phone_2, 'merge_call', '', '', '', '']
        self.worksheet.append_row(row_data)
        row_index = len(self.worksheet.get_all_values())

        def fetch(self):
            result = self.client._wait_for_update(row_index, wait_for_i=True)
            return {'sid': sid, 'duration': result['i'], 'status': result['j'].lower()}

        return type('Call', (), {'fetch': fetch, 'client': self})()

    def calls_update(self, sid, status, from_=None, to=None):
        """Write hangup_call data to sheet (leave I, J empty) and return call object."""
        if not self._has_valid_credentials():
            raise ValueError('Invalid Credentials')

        row_data = [self.account_sid, self.auth_token, from_ or '', to or '', '', 'direct_call_auto_hangup_True',
                    'True', '', '', '']
        self.worksheet.append_row(row_data)
        row_index = len(self.worksheet.get_all_values())

        def fetch(self):
            result = self.client._wait_for_update(row_index, wait_for_i=True)
            return {'sid': sid, 'duration': result['i'], 'status': result['j'].lower()}

        return type('Call', (), {'fetch': fetch, 'client': self})()

class Messages:
    """Namespace for message-related operations."""
    def __init__(self, client):
        self.client = client

    def create(self, body, from_, to):
        """Delegate to Client.messages_create."""
        return self.client.messages_create(body, from_, to)

class Calls:
    """Namespace for call-related operations."""
    def __init__(self, client):
        self.client = client

    def create(self, to, from_, auto_hang=True):
        """Delegate to Client.calls_create."""
        return self.client.calls_create(to, from_, auto_hang)

    def merge(self, phone_1, phone_2, from_):
        """Delegate to Client.calls_merge."""
        return self.client.calls_merge(phone_1, phone_2, from_)

    def __call__(self, sid):
        """Return CallInstance for updating a call."""
        return CallInstance(self.client, sid)

class CallInstance:
    """Helper class for updating a call."""
    def __init__(self, client, sid):
        self.client = client
        self.sid = sid

    def update(self, status, from_=None, to=None):
        """Delegate to Client.calls_update."""
        return self.client.calls_update(self.sid, status, from_, to)

@app.route('/send-message', methods=['POST'])
def send_message():
    """Endpoint to send a message using the Client class."""
    try:
        data = request.get_json()
        account_sid = data.get('account_sid')
        auth_token = data.get('auth_token')
        phone_number = data.get('phone_number', 'default')
        body = data.get('body')
        from_ = data.get('from')
        to = data.get('to')

        if not all([account_sid, auth_token, body, from_, to]):
            return jsonify({'error': 'Missing required fields'}), 400

        client = Client(account_sid, auth_token, phone_number)
        message = client.messages.create(body, from_, to)
        result = message.fetch()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))