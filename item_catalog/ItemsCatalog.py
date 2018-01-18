from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

app = Flask(__name__)

engine = create_engine('sqlite:///itemscatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/items/JSON')
def itemsJSON():
    items = session.query(Item).all()
    return jsonify(items=[r.serialize for r in items])


# Show all items in the catalog
@app.route('/')
@app.route('/item/')
def showItems():
    items = session.query(Item).order_by(asc(Item.name))
    if 'username' not in login_session:
       return render_template('publicCatalog.html', items=items)
    # return "This page will show all items in catalog"
    else:
       return render_template('catalog.html', items=items)


# Create a new item
@app.route('/item/new/', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'], description=request.form['description'], price=request.form['price'], user_id=login_session['user_id'])
        session.add(newItem)
        flash('New Item %s Successfully Created' % newItem.name)
        session.commit()
        return redirect(url_for('showItems'))
    else:
        return render_template('newItem.html')
    # return "This page will be for making a new restaurant"

# Edit item
@app.route('/item/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(item_id):
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if editedItem.user_id == login_session['user_id']:
       if request.method == 'POST':
           if request.form['name']:
               editedItem.name = request.form['name']
           if request.form['description']:
               editedItem.description = request.form['description']
           if request.form['price']:
               editedItem.price = request.form['price']
            
           session.add(editedItem)
           session.commit()
           return redirect(url_for('showItems', item_id=item_id))
       else:
           return render_template(
               'editItem.html', item=editedItem)
    return redirect(url_for('showItems'))

# Delete an item
@app.route('/item/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(item_id):
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if itemToDelete.user_id == login_session['user_id']:
       if request.method == 'POST':
           session.delete(itemToDelete)
           session.commit()
           return redirect(
               url_for('showItems', item_id=item_id))
       else:
           return render_template('deleteItem.html', item=itemToDelete)
    return redirect(url_for('showItems'))
    
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    #state = '111' 100th line
    login_session['state'] = state

    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
       response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
       response.headers['Content-Type'] = 'application/json'
       return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
      response = make_response(json.dumps("Token's client ID does not match app's."), 401)
      print "Token's client ID does not match app's."
      response.headers['Content-Type'] = 'application/json'
      return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
      response = make_response(json.dumps('Current user is already connected.'), 200)
      response.headers['Content-Type'] = 'application/json'
      return response

   # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id
   # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
      user_id = createUser(login_session)
    login_session['user_id'] = user_id


    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

def createUser(login_session):
    newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

@app.route('/gdisconnect')
def gdisconnect():
      # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showItems'))
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response
      

app.secret_key = 'state'

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=80)
