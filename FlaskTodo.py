from flask import Flask, jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask_sqlalchemy import SQLAlchemy
import requests
from lxml import etree

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)
token = ''
imdb = ''
what = ''

@app.before_first_request
def setup_app():
    global token
    url = 'http://api.opensubtitles.org/xml-rpc'
    headers = {
        'Content-Type': 'text/xml',
        'User-Agent': 'OSTestUserAgent'
    }
    xml = """<?xml version="1.0"?>
    <methodCall>
        <methodName>LogIn</methodName>
            <params>
                <param>
                    <value><string>yadoxo</string></value>
                </param>
                <param>
                    <value><string>BossaNova203</string></value>
                </param>
                <param>
                    <value><string>en</string></value>
                </param>
                <param>
                    <value><string>OSTestUserAgent</string></value>
                </param>
            </params>
        </methodCall>"""
    resp = requests.post(url, data=xml, headers=headers).text
    e = etree.XML(resp[39:])
    token = e.xpath('//methodResponse/params/param/value/struct/member/value/string/text()')[0]

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, unique=False)
    is_completed = db.Column(db.Boolean)

    def __init__(self, title):
        self.title = title
        self.is_completed = False

@app.route('/')
def index():
    #todos = Todo.query.all()
    return render_template('index.html', imdb=imdb)


@app.route('/add', methods=['POST'])
def add():
    db.session.add(Todo(title=request.form['title']))
    db.session.commit()
    return redirect("/")

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search = request.args.get('q')
    url = 'http://www.omdbapi.com/'
    params = {
        's': str(search),
        'plot': 'short',
        'r': 'json'
    }
    res = requests.get(url, params=params).json()
    # for resp in res['Search']:
    #    results.append(resp['Title'])
    results = [resp['Title'] for resp in res['Search']]
    return jsonify(matching_results=results)

@app.route('/search', methods=['POST'])
def search():
    global imdb
    global what
    what = request.form['autocomplete']
    url = 'http://api.opensubtitles.org/xml-rpc'
    headers = {
        'Content-Type': 'text/xml',
        'User-Agent': 'OSTestUserAgent'
    }
    xml = """<methodCall>
                 <methodName>SearchMoviesOnIMDB</methodName>
                 <params>
                  <param>
                   <value><string>"""+token+"""</string></value>
                  </param>
                  <param>
                   <value><string>"""+what+"""</string></value>
                  </param>
                 </params>
                </methodCall>"""
    resp = requests.post(url, data=xml, headers=headers).text
    e = etree.XML(resp[39:])
    imdb = e.xpath('//methodResponse/params/param/value/struct/member/value/array/data/value/struct/member/value/string/text()')[0]
    return redirect("/")

app.debug = True

if __name__ == '__main__':
    app.run()
