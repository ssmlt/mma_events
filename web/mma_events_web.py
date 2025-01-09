# install pymysql, flask, mysqk
from flask import Flask, render_template, jsonify#, request
import pymysql
#import mysql.connector
import os

app = Flask(__name__)

def get_db_connection():
    return pymysql.connect(
        host=os.environ['PROXY_HOST_NAME'],
        user=os.environ['DB_USER_NAME'],
        password=os.environ['PASSWORD'].strip(),
        db=os.environ['DB_NAME'],
        port=int(os.environ['PORT'])
    )

# def get_db_connection_mysql_connector():
#     return mysql.connector.connect(
#         host=os.environ['PROXY_HOST_NAME'],
#         user=os.environ['DB_USER_NAME'],
#         password=os.environ['PASSWORD'].strip(),
#         database=os.environ['DB_NAME'],
#         port=int(os.environ['PORT'])
#     )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return "<h1>Welcome to the MMA Event page</h1> <p><h4>We have here 1) Upcoming Events 2) MMA Decisions</h4></p><p>Data was scraped from great MMA portals <a href='https://mmadecisions.com/'>MMA Decisions</a> and <a href='https://www.tapology.com'>Tapology</a>. Thanks! </p>"

@app.route('/raw_mma_events')
def mma_events():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM mma_events')
        events = cursor.fetchall()
    conn.close()
    return render_template('raw_mma_events.html', events=events)

@app.route('/raw_bouts')
def bouts():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM bouts')
        bouts = cursor.fetchall()
    conn.close()
    return render_template('raw_bouts.html', bouts=bouts)

@app.route('/raw_decision_events')
def decision_events():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM decision_events')
        events = cursor.fetchall()
    conn.close()
    return render_template('raw_decision_events.html', events=events)

@app.route('/raw_decision_bouts')
def decision_bouts():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM decision_bouts')
        bouts = cursor.fetchall()
    conn.close()
    return render_template('raw_decision_bouts.html', bouts=bouts)

@app.route('/raw_decision_main_scores')
def decision_main_scores():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM decision_main_scores')
        scores = cursor.fetchall()
    conn.close()
    return render_template('raw_decision_main_scores.html', scores=scores)

@app.route('/raw_decision_media_scores')
def decision_media_scores():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM decision_media_scores')
        scores = cursor.fetchall()
    conn.close()
    return render_template('raw_decision_media_scores.html', scores=scores)

@app.route('/upcoming_events')
def upcoming_events():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM mma_events ORDER BY event_datetime ASC')
        events = cursor.fetchall()
    conn.close()
    return render_template('upcoming_events.html', events=events)

@app.route('/events/<int:event_id>')
def event_details(event_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT bout_order,fighter1,fighter2,fighter1_url,fighter2_url,fighter1_result,fighter2_result,weight_class,card FROM bouts WHERE event_id = %s ORDER BY bout_order', (event_id))
        bouts = cursor.fetchall()
        cursor.execute('SELECT event_name FROM mma_events WHERE id = %s', (event_id))
        name = cursor.fetchone()[0]       
    conn.close()
    if bouts:
        return render_template('upcoming_event_details.html', bouts=bouts, name=name)
    else:
        return "Event not found", 404

@app.route('/decisions', methods=['GET'])
def decisions():
    # conn = get_db_connection_mysql_connector()
    # cursor = conn.cursor(dictionary=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch all events
    cursor.execute("SELECT * FROM decision_events")
    events = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('decisions.html', events=events)

@app.route('/decisions/<int:event_id>', methods=['GET'])
def decisions_one_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    selected_event = None
    bouts = []
    main_scores = []
    media_scores = []
    if event_id:
        cursor.execute("""
            SELECT name
            FROM decision_events
            WHERE id = %s
        """, (event_id,))
        event_name = cursor.fetchone()[0]

        cursor.execute("""
            SELECT 
                decision_bouts.name AS bout_name,
                decision_main_scores.judge AS main_judge,
                decision_main_scores.score1 AS main_score1,
                decision_main_scores.score2 AS main_score2
            FROM decision_bouts
            LEFT JOIN decision_main_scores ON decision_bouts.id = decision_main_scores.decision_bout_id
            WHERE decision_bouts.decision_event_id = %s
            ORDER BY decision_bouts.name
        """, (event_id,))
        main_scores = cursor.fetchall()

        cursor.execute("""
            SELECT 
                decision_bouts.name AS bout_name,
                decision_media_scores.judge AS media_judge,
                decision_media_scores.score AS media_score,
                decision_media_scores.winner AS media_winner
            FROM decision_bouts
            LEFT JOIN decision_media_scores ON decision_bouts.id = decision_media_scores.decision_bout_id
            WHERE decision_bouts.decision_event_id = %s
            ORDER BY decision_bouts.name
        """, (event_id,))
        media_scores = cursor.fetchall()
        conn.close()

        bouts_data = {}
        for row in main_scores:
            bout_name = row[0]
            if bout_name not in bouts_data:
                bouts_data[bout_name] = {'main_scores': [], 'media_scores': []}
            bouts_data[bout_name]['main_scores'].append({
                'judge': row[1],
                'score1': row[2],
                'score2': row[3]
            })

        for row in media_scores:
            bout_name = row[0]
            if bout_name not in bouts_data:
                bouts_data[bout_name] = {'main_scores': [], 'media_scores': []}
            bouts_data[bout_name]['media_scores'].append({
                'judge': row[1],
                'score': row[2],
                'winner': row[3]
            })

    return render_template('decisions_one_event.html', bouts_data=bouts_data, event_name=event_name)

if __name__ == '__main__':
    app.run(debug=True)
