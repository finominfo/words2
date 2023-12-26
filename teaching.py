import random
import time
import sqlite3
import requests
import json
from datetime import datetime
from datetime import datetime, timedelta
import pytz

budapest_timezone = pytz.timezone('Europe/Budapest')
db_path = 'words.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
table_name = 'translations'
success_table = 'success'
unsuccess_table = 'unsuccess'
cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {success_table} (
        word TEXT,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {unsuccess_table} (
        word TEXT,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
cursor.execute(f'SELECT * FROM {table_name}')
rows = cursor.fetchall()
words = {row[0]: row[1] for row in rows}

cursor.execute(f'SELECT * FROM {success_table}')
rows = cursor.fetchall()
success_translations = {row[0]: row[1] for row in rows}

cursor.execute(f'SELECT * FROM {unsuccess_table}')
rows = cursor.fetchall()
unsuccess_translations = {row[0]: row[1] for row in rows}
unsuccess_translations = {key: value for key, value in unsuccess_translations.items() if key not in success_translations}



def print_statistics():
    print("Statistics:")
    cursor.execute(f'''
        SELECT DATE(created) as day, COUNT(*) as count
        FROM {success_table}
        GROUP BY day
    ''')
    rows = cursor.fetchall()
    for row in rows:
        print(f"Day: {row[0]}, Successful Answers: {row[1]}")
    cursor.execute(f'''
        SELECT DATE(created) as day, COUNT(*) as count
        FROM {unsuccess_table}
        GROUP BY day
    ''')
    rows = cursor.fetchall()
    for row in rows:
        print(f"Day: {row[0]}, Unsuccessful Answers: {row[1]}")

def print_number_of_failed_translations():
    if len(unsuccess_translations) > 10:
        print('Number of failed tarnslation: ' + str(len(unsuccess_translations)))

def get_oldest_word(translations):
    diff = 0
    oldest_word = None
    if len(translations) > 0:
        oldest_word = min(translations, key=lambda x: translations[x])
        oldest_word_age = datetime.strptime(translations[oldest_word], '%Y-%m-%d %H:%M:%S')
        oldest_word_age = oldest_word_age.replace(tzinfo=pytz.timezone('UTC')) 
        current_time = datetime.now(pytz.timezone('Europe/Budapest')) 
        diff = (current_time - oldest_word_age).total_seconds()
    return oldest_word, diff


def main():
    print_statistics()
    cycle_num = 0
    while True:
        print_number_of_failed_translations()
        cycle_num += 1
        word = None
        question_from = ''
        while word is None:
            success_word, success_diff = get_oldest_word(success_translations)
            unsuccess_word, unsuccess_diff = get_oldest_word(unsuccess_translations)
            if success_diff > 86_400:  # 1 day
                print(f"success word: {success_word}, success diff: {success_diff}, unsuccess word: {unsuccess_word}, unsuccess diff: {unsuccess_diff}")
            elif unsuccess_diff > 600 and (cycle_num & 1) == 1:
                print(f"unsuccess word: {unsuccess_word}, unsuccess diff: {unsuccess_diff}")    
            if success_diff > 86_400 and (cycle_num & 15) == 15:
                word = success_word
                question_from = 'Successfully answered, but long time ago. '
            elif unsuccess_diff > 180 and (cycle_num & 1) == 1:
                word = unsuccess_word
                question_from = 'Failed more than 3 minutes ago. '
            elif len(unsuccess_translations) > 5 and (cycle_num & 1) == 1:
                word = random.choice(list(unsuccess_translations.keys()))
                question_from = 'Failed, randomly selected. '
            else:    
                word = random.choice(list(words.keys()))
                question_from = 'Not asked until now. '
                if word in success_translations.keys() or word in unsuccess_translations.keys():
                    word = None


        good_and_bad_translations = words.get(word, [])
        translations = good_and_bad_translations.split()

        good_translations = [translate[1:] for translate in translations if translate.startswith('+')]
        good_translations = [translation.lower() for translation in good_translations]

        bad_translations = [translate[1:] for translate in translations if translate.startswith('-')]
        bad_translations = [translation.lower() for translation in bad_translations]

        user_answer = input(f"{question_from}What is the meaning of '{word}'? ").strip()
        user_answer = user_answer.lower()
        if user_answer == 'exit' or user_answer == 'quit' or user_answer == 'q':
            print_statistics()
            print_number_of_failed_translations()
            print("Bye!")
            break
        if user_answer.startswith('correct '):
            myword = user_answer.split(' ', 1)[1]
            mytranslation = words.get(myword, None)
            if mytranslation is not None:
                myanswer = input(f"{myword} current translation is: \"{mytranslation}\" What is the good one? ").strip()
                # Check if the myanswer consist of good and bad translations. This means space separated words which starts with + or -
                if '+' in myanswer and len(myanswer.strip()) > 3 and all([translation.startswith('+') or translation.startswith('-') for translation in myanswer.split()]):
                    words[myword] = myanswer
                    cursor.execute(f'UPDATE {table_name} SET translation = ? WHERE original = ?', (myanswer, myword))
                    conn.commit()                    
                    print(f"{myword} new translation is: \"{myanswer}\"")
                else:
                    print("Invalid answer. Dismissed.")
            else:
                print(f"\"{myword}\" is not in the database.")        
            continue
        if not user_answer or len(user_answer) > 30:
            print("Invalid answer. Try again.")
            continue
        if user_answer in good_translations:
            print("Correct! Well done.")
            utc_now = time.gmtime()
            utc_timezone = pytz.timezone('UTC')
            utc_datetime = datetime.fromtimestamp(time.mktime(utc_now), tz=utc_timezone)
            budapest_datetime = utc_datetime.astimezone(budapest_timezone)
            success_translations[word] = budapest_datetime.strftime('%Y-%m-%d %H:%M:%S')
            #success_translations[word] = time.strftime('%Y-%m-%d %H:%M:%S')
            if word in unsuccess_translations:
                del unsuccess_translations[word]
            cursor.execute(f'INSERT INTO {success_table} (word) VALUES (?)', (word,))
            conn.commit()
            continue

        if user_answer in bad_translations:
            print(f"Sorry, the correct translations for '{word}' are: {', '.join(good_translations)}")
            utc_now = time.gmtime()
            utc_timezone = pytz.timezone('UTC')
            utc_datetime = datetime.fromtimestamp(time.mktime(utc_now), tz=utc_timezone)
            budapest_datetime = utc_datetime.astimezone(budapest_timezone)
            unsuccess_translations[word] = budapest_datetime.strftime('%Y-%m-%d %H:%M:%S')
            #unsuccess_translations[word] = time.strftime('%Y-%m-%d %H:%M:%S')
            if word in success_translations:
                del success_translations[word]
            cursor.execute(f'INSERT INTO {unsuccess_table} (word) VALUES (?)', (word,))
            conn.commit()
            continue    

        text = f'''
            '{word}' The translation of the above english word to hungarian is: '{user_answer}' Answer yes, if it is true, and no, if it is false. 
            '''
        url = "https://api.deepai.org/api/text-generator"
        headers = {
            "api-key" : "0ee0754a-acb5-4bcc-8e38-d9110b4ffda4",
        }
        data = {
            "text": text,
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            json_response = json.loads(response.text)
            deepai_answer = json_response.get("output", "")
            print(deepai_answer)
            if deepai_answer.lower().startswith('yes'):
                good_and_bad_translations += ' +' + user_answer
                print(good_and_bad_translations)
                cursor.execute(f'UPDATE {table_name} SET translation = ? WHERE original = ?', (good_and_bad_translations, word))
                words[word] = good_and_bad_translations
                utc_now = time.gmtime()
                utc_timezone = pytz.timezone('UTC')
                utc_datetime = datetime.fromtimestamp(time.mktime(utc_now), tz=utc_timezone)
                budapest_datetime = utc_datetime.astimezone(budapest_timezone)
                success_translations[word] = budapest_datetime.strftime('%Y-%m-%d %H:%M:%S')
                if word in unsuccess_translations:
                    del unsuccess_translations[word]
                cursor.execute(f'INSERT INTO {success_table} (word) VALUES (?)', (word,))
                conn.commit()
            else:
                good_and_bad_translations += ' -' + user_answer
                print(good_and_bad_translations)
                cursor.execute(f'UPDATE {table_name} SET translation = ? WHERE original = ?', (good_and_bad_translations, word))
                words[word] = good_and_bad_translations
                utc_now = time.gmtime()
                utc_timezone = pytz.timezone('UTC')
                utc_datetime = datetime.fromtimestamp(time.mktime(utc_now), tz=utc_timezone)
                budapest_datetime = utc_datetime.astimezone(budapest_timezone)
                unsuccess_translations[word] = budapest_datetime.strftime('%Y-%m-%d %H:%M:%S')
                if word in success_translations:
                    del success_translations[word]
                cursor.execute(f'INSERT INTO {unsuccess_table} (word) VALUES (?)', (word,))
                conn.commit()
        else:
            print(f"Request failed with status code {response.status_code}")


if __name__ == "__main__":
    main()
