#pip install lxml_html_clean and requests_html boto3 pymysql
from requests_html import HTMLSession
import requests
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup as bs
import json
import os
import boto3
import pymysql

tapology_url = str('https://www.tapology.com')
events_url = tapology_url + '/fightcenter?group=major&schedule=upcoming'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36'}
events = []

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

# Getting URLs of upcoming events
def get_upcoming_events():
    events_response = requests.get(events_url)
    events_bs = bs(events_response.text, 'html.parser')
    events_bs_a = events_bs.select('span.hidden > a.border-b')
    events_links = []
    for event in events_bs_a:
        events_links.append(tapology_url + str(event['href']))
    return events_links

def get_event(url):
    print('Starting to get event from:', url)
    session = HTMLSession()
    event_response = session.get(url, headers=headers)
    soup=bs(event_response.text,'html.parser')
    event_record = {}
    try:
        event_record['event_name'] = soup.select('h2.text-center')[0].text
    except Exception as e:
        print(f"Error in clear_display: {e}")
    try:
        raw_datetime = soup.select('li.leading-normal.hidden > span.text-neutral-700')[0].text.split(' ')
    except Exception as e:
        print(f"Error in clear_display: {e}")
    if raw_datetime[5] == 'ET':
        tz_diff = '-0500'
    elif raw_datetime[5] == 'EDT':
        tz_diff = '-0400'
        
    proper_datetime = f'{raw_datetime[1]} {raw_datetime[3]} {raw_datetime[4]} {tz_diff}'
    datetime_format = '%m.%d.%Y %I:%M %p %z'
    event_record['event_datetime'] = datetime.strptime(proper_datetime, datetime_format).astimezone(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    try:
        event_record['logo'] = soup.select('img.border-2.border-white')[0]['src']
    except Exception as e:
        print(f"Error in clear_display: {e}")
        event_record['logo'] = ''
        pass
    try:
        event_record['promotion'] = soup.select('div.div.hidden > ul[data-controller="unordered-list-background"] > li.leading-normal > span.text-neutral-700 > a.link-primary-red')[0].text
    except Exception as e:
        print(f"Error in clear_display: {e}")
        event_record['promotion'] = ''
        pass
    try:
        event_record['location'] = soup.select('div.div.hidden > ul[data-controller="unordered-list-background"] > li.leading-normal.px-1 > span.text-neutral-700 > a:not([class])')[0].text
    except Exception as e:
        print(f"Error in clear_display: {e}")
        event_record['location'] = ''
        pass
    try:
        bouts_bs = soup.select('li.border-b.border-dotted.border-tap_6')
    except Exception as e:
        print(f"Error in clear_display: {e}")
        bouts_bs = []
        pass
    bout_order = 0
    event_record['bouts'] = []

    for bout in bouts_bs:
        bout_order += 1
        figher1 = bout.select('div.div.hidden.order-1 > a.link-primary-red')[0].text
        figher2 = bout.select('div.div.hidden.order-2 > a.link-primary-red')[0].text
        try:
            figher1_url = tapology_url + str(bout.select('div.div.hidden.order-1 > a.link-primary-red')[0]['href'])
        except Exception as e:
            print(f"Error in clear_display: {e}")
            figher1_url = ''
            pass
        try:
            fighter2_url = tapology_url + str(bout.select('div.div.hidden.order-2 > a.link-primary-red')[0]['href'])
        except Exception as e:
            print(f"Error in clear_display: {e}")
            fighter2_url = ''
            pass
        try:
            fighter1_result = bout.select('div.flex > span.order-2')[0].text.replace('\n', '')
        except Exception as e:
            print(f"Error in clear_display: {e}")
            fighter1_result = ''
            pass
        try:
            fighter2_result = bout.select('div.flex > span.order-1')[0].text.replace('\n', '')
        except Exception as e:
            print(f"Error in clear_display: {e}")
            fighter2_result = ''
            pass
        try:
            weight_class = bout.find('span', {'class':'bg-tap_darkgold px-1.5 md:px-1 leading-[23px] text-sm md:text-[13px] text-neutral-50 rounded'}).text.replace('\n', '')
        except Exception as e:
            print(f"Error in clear_display: {e}")
            weight_class = ''
            pass
        try:
            card = bout.select(r'span.uppercase.text-xs11.font-bold > a.hover\:border-neutral-950')[0].text
        except Exception as e:
            print(f"Error in clear_display: {e}")
            card = ''
            pass
        event_record['bouts'].append({
            'fighter1': figher1,
            'fighter2': figher2,
            'fighter1_url': figher1_url,
            'fighter2_url': fighter2_url,
            'fighter1_result': fighter1_result,
            'fighter2_result': fighter2_result,
            'weight_class': weight_class,
            'card': card,
            'bout_order': bout_order
        })
    return event_record


# TO DO:
# 1. Check if the event already exists in the database each time before writing
# Not to do that "deletion" workaround
# 2. Refactor code to avoid partial repetition 

def write_upcoming_events(event_records):
    print('Starting to write events to the database')
    for record in event_records:
        if record['event_name'] == 'UFC Fight Night':
            record['event_name'] = 'UFC Fight Night' + ' ' + record['event_datetime'] 
        print('Writing event:', record['event_name'])
        # token = get_auth_token()
        # print(token)
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
                    INSERT IGNORE INTO mma_events (event_name, event_datetime, logo, promotion, location) 
                    VALUES (%s, %s, %s, %s, %s)""",
                    (record['event_name'], record['event_datetime'], record['logo'], record['promotion'], record['location']))
                insert_event_result = connection.commit()
                cursor.execute("SELECT LAST_INSERT_ID()")
                inserted_event_id = cursor.fetchone()[0]
                print("Inserted ID", inserted_event_id)
                if inserted_event_id == 0:  # If the event already exists in the database, check if the bouts count has changed
                    cursor.execute("SELECT COUNT(*) FROM bouts where event_id = (SELECT id FROM mma_events WHERE event_name = %s)", (record['event_name']))
                    bounts_in_db = cursor.fetchone()[0]
                    print("Bouts in DB", bounts_in_db)
                    print("Bouts to write", len(record['bouts']))
                    if bounts_in_db != len(record['bouts']):
                        cursor.execute("DELETE FROM bouts where event_id = (SELECT id FROM mma_events WHERE event_name = %s)", (record['event_name']))
                        delete_bout_result = connection.commit()
                        cursor.execute("SELECT id FROM mma_events WHERE event_name = %s", (record['event_name']))
                        old_event_id = cursor.fetchone()[0]
                        for bout in record['bouts']:
                            cursor.execute("""
                                INSERT INTO bouts (event_id, fighter1, fighter2, fighter1_url, fighter2_url,
                                    fighter1_result, fighter2_result, weight_class, card, bout_order) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                (old_event_id, bout['fighter1'], bout['fighter2'], bout['fighter1_url'], bout['fighter2_url'], 
                                bout['fighter1_result'], bout['fighter2_result'], bout['weight_class'], bout['card'], bout['bout_order']))
                            insert_bout_result = connection.commit()
                    else:
                        print('No changes in bouts')
                else: # If the event is new, insert all the bouts
                    print("Bouts to write", len(record['bouts']))
                    for bout in record['bouts']:
                        cursor.execute("""
                            INSERT INTO bouts (event_id, fighter1, fighter2, fighter1_url, fighter2_url,
                                fighter1_result, fighter2_result, weight_class, card, bout_order) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (inserted_event_id, bout['fighter1'], bout['fighter2'], bout['fighter1_url'], bout['fighter2_url'], 
                            bout['fighter1_result'], bout['fighter2_result'], bout['weight_class'], bout['card'], bout['bout_order']))
                        insert_bout_result = connection.commit()
            
        except pymysql.InternalError as e:
            return (f"Error: {str(e)}")  # Return an error message if an internal exception occurs
            pass
        except Exception as e:
            return (f"Error: {str(e)}")

if __name__ == "__main__":
    for event_link in get_upcoming_events():
        events.append(get_event(event_link))
        time.sleep(1)
    write_upcoming_events(events)