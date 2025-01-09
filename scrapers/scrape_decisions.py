#pip install lxml_html_clean and requests_html boto3 pymysql
#from requests_html import HTMLSession
import requests
import time
#from datetime import datetime, timezone
from bs4 import BeautifulSoup as bs
import json
import os
import boto3
import pymysql

mma_decisions_url = 'https://mmadecisions.com/'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36'}
all_decisions = {}

# RDS settings
proxy_host_name = os.environ['PROXY_HOST_NAME']
port = int(os.environ['PORT'])
db_name = os.environ['DB_NAME']
db_user_name = os.environ['DB_USER_NAME']
aws_region = os.environ['AWS_REGION']
password = os.environ['PASSWORD'].strip()

# def get_auth_token():
#     client = boto3.client('rds')
#     token = client.generate_db_auth_token(
#         DBHostname=proxy_host_name,
#         Port=port,
#         DBUsername=db_user_name,
#         Region=aws_region
#     )
#     return token

def get_events_urls():
    events_list = []
    events_response = requests.get(mma_decisions_url)
    events_bs = bs(events_response.text, 'html.parser')
    events_bs_a = events_bs.select('td.judge > b > a')
    for event in events_bs_a:
        events_list.append(mma_decisions_url + event['href'])
    print(events_list)
    return events_list
    # return [events_list[2]]

def get_bouts_urls(events_urls):
    for url in events_urls:
        events_response = requests.get(url, headers=headers)
#        events_response.raise_for_status()
        events_bs = bs(events_response.text, 'html.parser')
        event_name = events_bs.select('td.decision-top2 > b')[0].text.replace(u'\xa0', u' ')
        bouts_bs = events_bs.select('td.list2 > b > a')
        all_decisions[event_name] = {}
        for bout in bouts_bs:
            bout_name = bout.text.replace(u'\xa0', u' ')
            print('BOUTNAME',bout_name)
            bout_url = mma_decisions_url + bout['href']
            all_decisions[event_name][bout_name] = {}
            all_decisions[event_name][bout_name]['bout_url'] = bout_url.strip()

def get_bouts_results():
    for event_name in all_decisions:
        for bout_name in all_decisions[event_name]:
            try:
                bout_url = all_decisions[event_name][bout_name]['bout_url']
                print(f'Scraping URL {bout_url}')
                bout_response = requests.get(bout_url)
#                bout_response.raise_for_status()
                bout_bs = bs(bout_response.text, 'html.parser')
                main_scores_bs = bout_bs.select('table[style="border: 0px; border-spacing: 0px; width: 100%"]')
                main_scores_bs_select = main_scores_bs[0].select('tr > td > table[style="width: 100%; border: 0"] > tr > td')
                all_decisions[event_name][bout_name]['main_scores'] = {}
                for main_score in main_scores_bs_select:
                    try:
                        judge = main_score.select('tr > td > a')[0].text.replace(u'\xa0', u' ')
                        score1 = main_score.select('tr > td.bottom-cell > b')[0].text
                        score2 = main_score.select('tr > td.bottom-cell > b')[1].text
                        all_decisions[event_name][bout_name]['main_scores'][judge] = {}
                        all_decisions[event_name][bout_name]['main_scores'][judge]["score1"] = score1
                        all_decisions[event_name][bout_name]['main_scores'][judge]["score2"] = score2
                        print('Judge Scores:', judge, score1, score2)
                    except (IndexError, AttributeError) as e:
                        print(f'Error parsing main scores for {bout_url}: {e}')               
                media_scores_bs_select = bout_bs.select('table[style="border-spacing: 0px; width: 100%; border: 0"] > tr > td[width="34%"] > table > tr.decision')
                all_decisions[event_name][bout_name]['media_scores'] = []
                for media_score in media_scores_bs_select:
                    media_one_score = []
                    for td in media_score.select('td'):
                        td_text = td.get_text(separator=" ").strip().replace("\n", " ").replace(u'\xa0', u' ')
                        media_one_score.append(td_text)
                    all_decisions[event_name][bout_name]['media_scores'].append(media_one_score)
            except requests.RequestException as e:
                print(f'Error fetching URL {bout_url}: {e}')
            except Exception as e:
                print(f'Unexpected error processing {bout_name} in {event_name}: {e}')

# TO DO:
# 1. Check if the event / bout / score already exists in the database each time before writing,
# currently working ONLY for new events !!! So not updating the scores later.

# Writing all scraped data to the DB      
def write_to_db(records):
    for event in records:
        print('WRITING event:', event)
        try:
            connection = pymysql.connect(
                host=proxy_host_name,
                user=db_user_name,
                password=password,
                db=db_name,
                port=port,
                # ssl={'ca': 'Amazon RDS', 'verify_identity': False} 
            )
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT IGNORE INTO decision_events (name) 
                    VALUES (%s)""",(event))
                insert_event_result = connection.commit()
                cursor.execute("SELECT LAST_INSERT_ID()")
                inserted_event_id = cursor.fetchone()[0]
                print("Inserted event ID", inserted_event_id)
                if inserted_event_id == 0:  # If the event already exists in the database, check if the bouts count has changed
                    # cursor.execute('SELECT COUNT(*) FROM decision_bouts WHERE decision_event_id = (SELECT id FROM decision_events WHERE name = %s )', (event))
                    # existing_bouts_count = cursor.fetchone()[0]
                    # if existing_bouts_count < len(records[event]):
                    #     print('Bouts count has changed:', existing_bouts_count, len(records[event]))
                    print('Event exists:', event)
                elif inserted_event_id > 0: # New event inserted
                    json_object = json.loads(json.dumps(records[event]))
                    print(json.dumps(json_object, indent=4))
                    try:
                        for bout in records[event]:
                            print('WRITING bout:', bout)
                            cursor.execute("""
                            INSERT INTO decision_bouts (name, bout_url, decision_event_id) 
                            VALUES (%s, %s, %s)""",(bout, records[event][bout]['bout_url'], inserted_event_id))
                            insert_bout_result = connection.commit()
                            cursor.execute("SELECT LAST_INSERT_ID()")
                            inserted_bout_id = cursor.fetchone()[0]
                            print('Inserted bout ID:', inserted_bout_id)
                            if inserted_bout_id == 0:
                                print('Bout exists:', bout)
                            elif inserted_bout_id > 0:
                                for judge in records[event][bout]['main_scores']:
                                    cursor.execute("""
                                    INSERT INTO decision_main_scores (decision_event_id, decision_bout_id, judge, score1, score2) 
                                    VALUES (%s, %s, %s, %s, %s)""",(inserted_event_id, inserted_bout_id, judge, records[event][bout]['main_scores'][judge]['score1'], 
                                            records[event][bout]['main_scores'][judge]['score2']))
                                    insert_main_score_result = connection.commit()
                                for media in records[event][bout]['media_scores']:
                                    cursor.execute("""
                                    INSERT INTO decision_media_scores (decision_event_id, decision_bout_id, judge, score, winner) 
                                    VALUES (%s, %s, %s, %s, %s)""",(inserted_event_id, inserted_bout_id, media[0], media[1], media[2]))
                                    insert_media_score_result = connection.commit()
                    except Exception as e:
                        print('Error', e)
                else:
                    print('Error inserting event:', event)
                    pass
            
        except pymysql.InternalError as e:
            return (f"Error: {str(e)}")  # Return an error message if an internal exception occurs
            pass
        except Exception as e:
            return (f"Error: {str(e)}")

if __name__ == '__main__':
    bouts = get_bouts_urls(get_events_urls())
    get_bouts_results()
    write_to_db(all_decisions)

    # json_object = json.loads(json.dumps(all_decisions))
    # print(json.dumps(json_object, indent=4))