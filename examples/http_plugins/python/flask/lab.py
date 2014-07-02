import json
import uuid
import datetime
from flask import Flask, request, render_template, url_for, redirect

app = Flask(__name__)


# 
# Sessions are reserved in memory in this case
# 
RESERVATIONS = {
    # 'identifier' :  {
    #     'username' : 'john',
    #     'deadline' : datetime(start + 2 minutes)
    #     'back'     : url_to_go_back
    # }
}

SYSTEM_LOGIN = 'myplugin'
SYSTEM_PASSWORD = 'password'
SESSION_SECONDS = 30

#
#  If you go to http://localhost:5001/lab/ it will tell you to log in first.
# 
#  If you go to:
#    http://localhost:5001/lab/reserve/?username=jsmith&system_login=myplugin&system_password=password&back_url=http://www.google.com/
# 
#  You'll be provided with a final URL of the laboratory and a reservation identifier. You can use that URL or one of the 
#  widgets to be logged in with the same reservation.
#  

def _get_reservation():
    reservation_id = request.args.get('reservation_id')
    if reservation_id and reservation_id in RESERVATIONS:
        reservation = RESERVATIONS.get(reservation_id)
        now = datetime.datetime.now()
        if reservation['deadline'] > now:
            return reservation
        else:
            RESERVATIONS.pop(reservation_id)
            if 'back' in reservation:
                return {
                    'must-return' : reservation['back']
                }

@app.route('/lab/')
def lab():
    reservation = _get_reservation()
    if reservation:
        if 'must-return' in reservation:
            return redirect(reservation['must-return'])
        return render_template('lab.html', 
                    reservation = reservation, 
                    remaining = reservation['deadline'] - datetime.datetime.now())
    return render_template('lab_reservation_not_found.html')

@app.route('/lab/camera1/')
def camera1():
    reservation = _get_reservation()
    if reservation:
        if 'must-return' in reservation:
            return redirect(reservation['must-return'])
        return render_template('camera_widget.html', camera = 'left', 
                    reservation = reservation, 
                    remaining = reservation['deadline'] - datetime.datetime.now())
    return render_template('lab_reservation_not_found.html')

@app.route('/lab/camera2/')
def camera2():
    reservation = _get_reservation()
    if reservation:
        if 'must-return' in reservation:
            return redirect(reservation['must-return'])
        return render_template('camera_widget.html', camera = 'right', 
                    reservation = reservation, 
                    remaining = reservation['deadline'] - datetime.datetime.now())
    return render_template('lab_reservation_not_found.html')

@app.route('/lab/reserve/')
def reserve():
    # Insecure but simple for the example
    system_login    = request.args.get('system_login')
    system_password = request.args.get('system_password')
    username        = request.args.get('username', 'username not provided')
    back_url        = request.args.get('back_url', url_for('lab'))
    
    if system_login == SYSTEM_LOGIN and system_password == SYSTEM_PASSWORD:
        now = datetime.datetime.now()
        reservation_id = unicode(uuid.uuid4()) # Random and base64
        RESERVATIONS[reservation_id] = {
            'username' : username,
            'deadline' : datetime.datetime.now() + datetime.timedelta(seconds = SESSION_SECONDS),
            'back'     : back_url,
        }
        return json.dumps({
            'reservation_id' : reservation_id,
            'url'            : url_for('lab', reservation_id = reservation_id, _external = True)
        })

    return json.dumps({
        'error' : 'invalid credentials'
    })

@app.route('/lab/test/')
def test():
    system_login    = request.args.get('system_login')
    system_password = request.args.get('system_password')
    
    if system_login == SYSTEM_LOGIN and system_password == SYSTEM_PASSWORD:
        return 'ok'

    return 'Invalid credentials'

if __name__ == '__main__':
    app.run(port = 5001, debug = True)
