from flask import Flask, render_template, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Important for session management
FASTAPI_URL = 'http://127.0.0.1:8001'
INCIDENT_SERVICE_URL = "http://127.0.0.1:8002"

def get_access_token():
    return session.get('access_token')

def set_access_token(token):
    session['access_token'] = token

def clear_access_token():
    session.pop('access_token', None)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        signup_url = f'{FASTAPI_URL}/auth/signup'
        try:
            response = requests.post(signup_url, json={'username': username, 'password': password})
            response.raise_for_status()
            return redirect(url_for('login'))
        except requests.exceptions.RequestException as e:
            error = f"Signup failed: {e}"
            if response is not None and response.status_code == 400:
                error = f"Signup failed: {response.json().get('detail', 'Username already registered')}"
    return render_template('signup.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        token_url = f'{FASTAPI_URL}/token'
        try:
            response = requests.post(token_url, data={'username': username, 'password': password})
            response.raise_for_status()
            token_data = response.json()
            set_access_token(token_data['access_token'])
            return redirect(url_for('list_zones'))
        except requests.exceptions.RequestException as e:
            error = f"Login failed: {e}"
            if response is not None and response.status_code == 401:
                error = f"Login failed: {response.json().get('detail', 'Incorrect username or password')}"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    clear_access_token()
    return redirect(url_for('login'))

def make_api_request(url, method='GET', json=None):
    headers = {}
    access_token = get_access_token()
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=json)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=json)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if response is not None and response.status_code == 401:
            return {'detail': 'Not authenticated'}
        raise

@app.route('/zones')
def list_zones():
    result = make_api_request(f'{FASTAPI_URL}/zones/')
    if isinstance(result, dict) and 'detail' in result and result['detail'] == 'Not authenticated':
        return redirect(url_for('login'))
    return render_template('zones/list.html', zones=result)

@app.route('/zones/create', methods=['GET', 'POST'])
def create_zone():
    if not get_access_token():
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        vehicle_count = request.form['vehicle_count']
        data = {'name': name, 'vehicle_count': int(vehicle_count)}
        try:
            make_api_request(f'{FASTAPI_URL}/zones/', method='POST', json=data)
            return redirect(url_for('list_zones'))
        except requests.exceptions.RequestException as e:
            return f"Error creating zone: {e}"
    return render_template('zones/create.html')

@app.route('/zones/edit/<int:zone_id>', methods=['GET'])
def edit_zone(zone_id):
    if not get_access_token():
        return redirect(url_for('login'))
    zone = make_api_request(f'{FASTAPI_URL}/zones/{zone_id}')
    return render_template('zones/edit.html', zone=zone)

@app.route('/zones/update/<int:zone_id>', methods=['POST'])
def update_zone(zone_id):
    if not get_access_token():
        return redirect(url_for('login'))
    name = request.form['name']
    vehicle_count = request.form['vehicle_count']
    data = {'name': name, 'vehicle_count': int(vehicle_count)}
    try:
        make_api_request(f'{FASTAPI_URL}/zones/{zone_id}', method='PUT', json=data)
        return redirect(url_for('list_zones'))
    except requests.exceptions.RequestException as e:
        return f"Error updating zone {zone_id}: {e}"

@app.route('/zones/delete/<int:zone_id>', methods=['POST'])
def delete_zone(zone_id):
    if not get_access_token():
        return redirect(url_for('login'))
    try:
        make_api_request(f'{FASTAPI_URL}/zones/{zone_id}', method='DELETE')
        return redirect(url_for('list_zones'))
    except requests.exceptions.RequestException as e:
        return f"Error deleting zone {zone_id}: {e}"

@app.route('/incidents')
def incidents():
    incidents_data = make_api_request(f"{INCIDENT_SERVICE_URL}/incidents/")
    return render_template('incidents.html', incident_data=incidents_data)

@app.route('/incidents/edit/<int:incident_id>', methods=['GET'])
def edit_incident(incident_id):
    incident = make_api_request(f'{INCIDENT_SERVICE_URL}/incidents/{incident_id}')
    return render_template('edit_incident.html', incident=incident)

@app.route('/incidents/update/<int:incident_id>', methods=['POST'])
def update_incident(incident_id):
    type = request.form['type']
    location = request.form['location']
    data = {'type': type, 'location': location}
    try:
        make_api_request(f'{INCIDENT_SERVICE_URL}/incidents/{incident_id}', method='PUT', json=data)
        return redirect(url_for('incidents'))
    except requests.exceptions.RequestException as e:
        return f"Error updating incident {incident_id}: {e}"

@app.route('/incidents/delete/<int:incident_id>', methods=['POST'])
def delete_incident(incident_id):
    try:
        make_api_request(f'{INCIDENT_SERVICE_URL}/incidents/{incident_id}', method='DELETE')
        return redirect(url_for('incidents'))
    except requests.exceptions.RequestException as e:
        return f"Error deleting incident {incident_id}: {e}"

@app.route('/report-incident', methods=['GET', 'POST'])
def report_incident():
    if request.method == 'POST':
        type = request.form['type']
        location = request.form['location']
        data = {'type': type, 'location': location}
        try:
            make_api_request(f"{INCIDENT_SERVICE_URL}/report", method='POST', json=data)
            return redirect(url_for('incidents'))
        except requests.exceptions.RequestException as e:
            return f"Error reporting incident: {e}"
    return render_template('report_incident.html')

@app.route('/')
def index():
    return redirect(url_for('list_zones'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)