import json

from flask import request, Response

from labmanager.application import app

@app.route("/fake_list_courses/gateway4labs/list", methods = ['GET','POST'])
def fake_list_courses():
    # return """{"start":"2","number":3,"per-page":2,"courses":[{"id":"4","name":"example3"}]}"""
    auth = request.authorization
    if auth is None or auth.username not in ('test','labmanager') or auth.password not in ('test','password'):
        return Response('You have to login with proper credentials', 401,
                        {'WWW-Authenticate': 'Basic realm="Login Required"'})

    q         = request.args.get('q','')
    start_str = request.args.get('start','0')

    try:
        start = int(start_str)
    except:
        return "Invalid start"

    fake_data = []
    for pos in xrange(10000):
        if pos % 3 == 0:
            fake_data.append((str(pos), "Fake electronics course %s" % pos))
        elif pos % 3 == 1:
            fake_data.append((str(pos), "Fake physics course %s" % pos))
        else:
            fake_data.append((str(pos), "Fake robotics course %s" % pos))

    fake_return_data = []
    for key, value in fake_data:
        if q in value:
            fake_return_data.append({
                'id'   : key,
                'name' : value,
            })

    N = 10

    view = {
        'start'    : start,
        'number'   : len(fake_return_data),
        'per-page' : N,
        'courses'  : fake_return_data[start:start+N],
    }

    return json.dumps(view, indent = 4)

