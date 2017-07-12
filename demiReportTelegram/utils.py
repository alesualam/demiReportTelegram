import datetime
import os
import time

import logging
import pymysql

from reportTelegram import utils as report_utils

from demiReportTelegram import variables

ADMIN_ID = variables.admin_id
GROUP_ID = variables.group_id

DB_HOST = variables.DB_HOST
DB_USER = variables.DB_USER
DB_PASS = variables.DB_PASS
DB_NAME = variables.DB_NAME

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)


def get_user_ids():
    user_ids = []
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    try:
        with con.cursor() as cur:
            cur.execute('SELECT UserId FROM Users')
            rows = cur.fetchall()
            for row in rows:
                user_ids.append(row[0])
    except Exception:
        logger.error('Fatal error in is_from_group', exc_info=True)
    finally:
        if con:
            con.close()
        return user_ids


def get_usernames(bot):
    usernames = {}
    for user_id in get_user_ids():
        username = bot.get_chat_member(GROUP_ID, user_id).user.username
        usernames['@%s' % username.lower()] = user_id
    return usernames


def get_trolls():
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    trolls = []
    try:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM Trolls")
            rows = cur.fetchall()
            for row in rows:
                trolls.append(row[0])
    except Exception as exception:
        print(exception)
    finally:
        if con:
            con.close()
        return trolls


def get_not_mention(mention_type):
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    not_mentions = []
    try:
        with con.cursor() as cur:
            cur.execute("SELECT userId FROM SilentMention WHERE mentionType=%s", (str(mention_type),))
            rows = cur.fetchall()
            for row in rows:
                not_mentions.append(row[0])
    except Exception as exception:
        print(exception)
    finally:
        if con:
            con.close()
        return not_mentions


def get_events():
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    events = []
    try:
        with con.cursor() as cur:
            cur.execute("SELECT eventId FROM Pipas")
            rows = cur.fetchall()
            for row in rows:
                events.append(row[0])
    except Exception as exception:
        print(exception)
    finally:
        if con:
            con.close()
        return events


def get_event_text(event_id):
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    res = ''
    try:
        with con.cursor() as cur:
            cur.execute("SELECT text FROM Pipas WHERE eventId=%s", (str(event_id),))
            res = cur.fetchone()[0]
    except Exception as exception:
        print(exception)
    finally:
        if con:
            con.close()
        return res


def get_event_message_id(event_id):
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    res = ''
    try:
        with con.cursor() as cur:
            cur.execute("SELECT messageId FROM Pipas WHERE eventId=%s", (str(event_id),))
            res = cur.fetchone()[0]
    except Exception as exception:
        print(exception)
    finally:
        if con:
            con.close()
        return res


def get_vote(event_id, user_id):
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    res = ''
    try:
        with con.cursor() as cur:
            cur.execute("SELECT selected FROM PipasVotes WHERE eventId=%s and userId=%s", (str(event_id), str(user_id)))
            query_fetch = cur.fetchone()
            res = query_fetch[0] if query_fetch is not None else res
    except Exception as exception:
        print(exception)
    finally:
        if con:
            con.close()
        return res


def get_participants_event(event_id):
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    user_ids = [[], [], []]
    try:
        with con.cursor() as cur:
            cur.execute("SELECT userId, selected  FROM PipasVotes WHERE eventId = %s", (str(event_id),))
            rows = cur.fetchall()
            for row in rows:
                if row[1] == 0:
                    user_ids[0].append(report_utils.get_name(row[0]))
                if row[1] == 1:
                    user_ids[1].append(report_utils.get_name(row[0]))
    except Exception as exception:
        print(exception)
    finally:
        if con:
            con.close()
        return user_ids


def create_event(event_id, message_id, text):
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    try:
        with con.cursor() as cur:
            cur.execute("INSERT INTO Pipas VALUES(%s, %s, %s)", (str(event_id), str(message_id), str(text)))
    except Exception as exception:
        print(exception)
    finally:
        if con:
            con.commit()
            con.close()


def add_participant_event(event_id, user_id, selected):
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    try:
        with con.cursor() as cur:
            cur.execute('INSERT INTO PipasVotes(eventId, userId, selected) VALUES(%s, %s, %s) '
                        'ON DUPLICATE KEY UPDATE selected = VALUES(selected)',
                        (str(event_id), str(user_id), str(selected)))
    except Exception:
        logger.error('Fatal error in pipas_selected', exc_info=True)
    finally:
        if con:
            con.commit()
            con.close()


def get_who_pipas():
    res = '🌳 Quedadas'
    events = get_events()
    for event in events:
        option_1 = get_participants_event(event)[0]
        option_2 = get_participants_event(event)[1]

        res += '\n\n %s' % get_event_text(event)
        res += '\n✔️ Sí (%i): %s' % (len(option_1), ', '.join(option_1))
        res += '\n❌ No (%i): %s' % (len(option_2), ', '.join(option_2))

    return res


def mention_control(user_id, mention_type, silent):
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    try:
        with con.cursor() as cur:
            if silent:
                cur.execute('INSERT INTO SilentMention VALUES(%s, %s)', (str(user_id), str(mention_type)))
                return '❎ Menciones desactivadas'
            else:
                cur.execute('DELETE FROM SilentMention WHERE userId=%s and mentionType=%s',
                            (str(user_id), str(mention_type)))
                return '✅ Menciones activadas'
    except Exception:
        logger.error('Fatal error in mention_toggle', exc_info=True)
    finally:
        if con:
            con.commit()
            con.close()


def is_silent_user(user_id, mention_type):
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    res = False
    try:
        with con.cursor() as cur:
            cur.execute("SELECT userId FROM SilentMention WHERE userId=%s and mentionType=%s",
                        (str(user_id), str(mention_type)))
            query_fetch = cur.fetchone()
            res = query_fetch is not None
    except Exception as exception:
        print(exception)
    finally:
        if con:
            con.close()
        return res


def change_group_photo():
    os.system("./../tg/bin/telegram-cli -W -e 'channel_set_photo channel#1060426760 photo.jpg'")
    os.system("./../tg/bin/telegram-cli -W -e 'status_offline'")


def set_power(power):
    os.system("./../tg/bin/telegram-cli -W -e 'channel_set_admin channel#1060426760 Selu %i'" % power)
    os.system("./../tg/bin/telegram-cli -W -e 'status_offline'")


def change_group_name(name):
    os.system("./../tg/bin/telegram-cli -W -e 'rename_channel channel#1060426760 %s'" % name)
    os.system("./../tg/bin/telegram-cli -W -e 'status_offline'")


def create_database():
    con = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    try:
        with con.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS `Usos` ( \
                  `UserId` int(11) NOT NULL, \
                  `Veces` int(11) NOT NULL \
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
                CREATE TABLE IF NOT EXISTS `Ranking` ( \
                  `UserId` int(11) NOT NULL, \
                  `Points` int(11) NOT NULL \
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
                CREATE TABLE IF NOT EXISTS `SilentMention` ( \
                  `userId` int(11) NOT NULL, \
                  `mentionType` TEXT NOT NULL \
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
                CREATE TABLE IF NOT EXISTS `Trolls` ( \
                  `UserId` int(11) NOT NULL \
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
                CREATE TABLE IF NOT EXISTS `GroupNames` ( \
                  `groupName` text NOT NULL, \
                  `position` int(11) NOT NULL \
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
                CREATE TABLE IF NOT EXISTS `Pipas` ( \
                  `eventId` BIGINT(30) NOT NULL, \
                  `messageId` BIGINT(30) NOT NULL, \
                  `text` TEXT NOT NULL, \
                  PRIMARY KEY (eventId) \
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
                CREATE TABLE IF NOT EXISTS `PipasVotes` ( \
                  `eventId` BIGINT(30) NOT NULL, \
                  `userId` int(11) NOT NULL, \
                  `selected` int(11) NOT NULL, \
                  UNIQUE KEY (eventId, userId), \
                  FOREIGN KEY (eventId) REFERENCES Pipas(eventId) \
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
                ")
    except Exception as exception:
        print(exception)
    finally:
        if con:
            con.commit()
            con.close()


def pole_counter(bot, job):
    text = time.strftime('%H:%M:*%S*')
    msg = bot.send_message(GROUP_ID, text, parse_mode='Markdown')
    time.sleep(0.5)
    for i in range(10):
        if text != time.strftime('%H:%M:*%S*') and (
                        time.strftime('%S') == '00' or int(time.strftime('%S')) >= 55):
            text = time.strftime('%H:%M:*%S*')
            bot.edit_message_text(text, chat_id=GROUP_ID, message_id=msg.message_id, parse_mode='Markdown')
        time.sleep(0.5)


def pole_timer(job_queue):
    x = datetime.datetime.today()
    y = x.replace(day=x.day, hour=23, minute=59, second=55, microsecond=0)
    y2 = x.replace(day=x.day, hour=1, minute=00, second=00, microsecond=0) + datetime.timedelta(days=1)
    delta_t = y - x
    delta_t2 = y2 - x
    secs = delta_t.seconds + 1
    secs2 = delta_t2.seconds + 1
    job_queue.run_daily(callback=pole_counter, time=secs)
    job_queue.run_daily(callback=variables.clean_poles, time=secs2)


def flooder(user_data, job_queue):
    if 'flood' in user_data and user_data['flood'] > 0:
        user_data['flood'] -= 1
        if user_data['flood'] == 0:
            job_queue.run_once(clear_flooder, 300, context=user_data)
    elif 'flood' not in user_data:
        user_data['flood'] = 5
    return user_data['flood'] == 0


def clear_flooder(bot, job):
    user_data = job.context
    user_data['flood'] = 5