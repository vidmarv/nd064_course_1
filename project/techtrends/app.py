import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort




# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post


# Connect to db = `database.db`
db_connects = 0 

def get_db_connection():
    global db_connects
    db_connects = db_connects + 1
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection




def get_article_count(metrics_obj):
    """
    Count the number of articles and increment the number of connections used
    Parameters:
    metrics_obj (dict): Dictionary with basic data for metrics endpoint response
    """
    connection = get_db_connection()
    article_count = connection.execute('SELECT count(*) FROM posts').fetchone()
    connection.close()

    metrics_obj['db_connection_count'] += 1
    metrics_obj['post_count'] = article_count[0]


def valid_db_connection():
    """
    Checks if connecting to database is successful.
    """
    try:
        connection = get_db_connection()
        connection.close()
    except:
        raise Exception("Database connection failure")


def post_table_exists():
    """
    Checks if POST table exists.
    """
    try:
        connection = get_db_connection()
        connection.execute('SELECT 1 FROM posts').fetchone()
        connection.close()
    except:
        raise Exception("Table 'posts' does not exist")





# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      logging.error('Article with id {} does not exists'.format(post_id))
      return render_template('404.html'), 404
    else:
      logging.info('Article "{}" retrieved!'.format(post['title']))
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logging.info('"About Us" page was retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            logging.info('Article "{}" created'.format(title))
            return redirect(url_for('index'))

    return render_template('create.html')





# adding /healthz endpoint
@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )

    app.logger.info('Status request successfull')
    return response

# adding /metrics endpoint
@app.route('/metrics')
def metrics():
    global db_connects

    metrics_obj = {
        'db_connection_count': 0,
        'post_count': None
    }

    get_article_count(metrics_obj)

    response = app.response_class(
        response=json.dumps(metrics_obj),
        status=200,
        mimetype='application/json')

    return response



# start the application on port 3111
if __name__ == "__main__":
   logging.basicConfig(filename='app.log',level=logging.DEBUG)
   root = logging.getLogger()
   root.setLevel(logging.DEBUG)
   
   
   # format output
   format_output = '%(asctime)s:%(levelname)s:%(message)s'
   
   # set logger to handle STDOUT and STDERR 
   # stdout handler 
   stdout_handler =  logging.FileHandler('stdout.log')
   stdout_handler =  logging.StreamHandler(sys.stdout)
   stdout_handler.setLevel(logging.DEBUG)
   stdout_handler.setFormatter(format_output)
   root.addHandler(stdout_handler)
   
   # stderr handler 
   stderr_handler =  logging.FileHandler('stderr.log')
   stderr_handler = logging.StreamHandler(sys.stderr)
   stderr_handler.setLevel(logging.DEBUG)
   stderr_handler.setFormatter(format_output)
   root.addHandler(stderr_handler)
   
   handlers = [stderr_handler, stdout_handler]


   app.run(host='0.0.0.0', port='3111')
