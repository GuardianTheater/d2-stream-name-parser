import requests
from PIL import Image
import pytesseract
import cv2 as cv
import os
import shutil
import imutils
import numpy as np
import re
import json
import time
import git
import traceback

if os.path.isdir('d2-stream-name-parser') == False:
    os.mkdir('d2-stream-name-parser')

print('cloning repo...')
repo = git.Repo.clone_from('https://github.com/GuardianTheater/d2-stream-name-parser.git', 'd2-stream-name-parser', branch='gh-pages')

origin = repo.remote('origin')
origin.pull()


def processTwitchQueue():
    for stream in twitch_queue:
        try:
            twitch_id = str(stream['channel']['_id'])
            file_name = twitch_id + '.jpg'
            url = stream['preview']['template']
            url = url.replace('{width}', '1920')
            url = url.replace('{height}', '1080')
            r = requests.get(url)
            with open('forOCR/' + file_name, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=128):
                    fd.write(chunk)

            name = str(stream['channel']['name'])
            if name:
                if os.path.isdir('d2-stream-name-parser/' + name) == False:
                    os.mkdir('d2-stream-name-parser/' + name)
                data = {}
                try:
                    with open('d2-stream-name-parser/' + name + '/twitch.json') as f:
                        for i in f:
                            data = json.loads(i)

                except:
                    pass
                if twitch_id in data:
                    data[twitch_id] += .1
                else:
                    data[twitch_id] = 1
                with open('d2-stream-name-parser/' + name + '/twitch.json', 'w+') as f:
                    f.write(json.dumps(data))

            display_name = str(stream['channel']['display_name'])
            if display_name:
                if os.path.isdir('d2-stream-name-parser/' + display_name) == False:
                    os.mkdir('d2-stream-name-parser/' + display_name)
                data = {}
                try:
                    with open('d2-stream-name-parser/' + display_name + '/twitch.json') as f:
                        for i in f:
                            data = json.loads(i)

                except:
                    pass
                if twitch_id in data:
                    data[twitch_id] += .1
                else:
                    data[twitch_id] = 1
                with open('d2-stream-name-parser/' + display_name + '/twitch.json', 'w+') as f:
                    f.write(json.dumps(data))

        except:
            pass


def processMixerQueue():
    for channel in mixer_queue:
        try:
            channel_id = str(channel['id'])

            username = str(channel['user']['username'])
            if username:
                if os.path.isdir('d2-stream-name-parser/' + username) == False:
                    os.mkdir('d2-stream-name-parser/' + username)
                data = {}
                try:
                    with open('d2-stream-name-parser/' + username + '/mixer.json') as f:
                        for i in f:
                            data = json.loads(i)
                except:
                    pass

                if channel_id in data:
                    data[channel_id] += 1
                else:
                    data[channel_id] = 1
                with open('d2-stream-name-parser/' + username + '/mixer.json', 'w+') as f:
                    f.write(json.dumps(data))

        except:
            pass


def getTwitchStreams(offset=0):
    twitchBaseUrl = 'https://api.twitch.tv/kraken/'
    twitchClientId = 'client_id=o8cuwhl23x5ways7456xhitdm0f4th0'

    if os.path.isdir('forOCR'):
        shutil.rmtree('forOCR')
    os.mkdir('forOCR')

    streamsUrl = twitchBaseUrl + 'streams?' + twitchClientId + \
        '&game=Destiny%202&limit=100&offset=' + str(offset)
    r = requests.get(streamsUrl)
    json = r.json()
    if json['streams']:
        for stream in json['streams']:
            if ('recov' not in stream['channel']['status']):
                twitch_queue.append(stream)
    if json['_total'] > offset + 100:
        getTwitchStreams(offset + 100)
    else:
        processTwitchQueue()


def getMixerStreams(offset=0):
    mixerBaseurl = 'https://mixer.com/api/v1/'
    clientID = '70eaab0506c7699b2c1800b9ce485786273c5db3b65d80c9'
    headers = {'Client-ID': clientID}

    streamsUrl = mixerBaseurl + \
        'channels?limit=100&where=typeId:eq:543113&page=' + str(offset)
    r = requests.get(streamsUrl, headers=headers)
    json = r.json()
    if json:
        for channel in json:
            if ('recov' not in channel['name']):
                mixer_queue.append(channel)
        getMixerStreams(offset + 1)
    else:
        processMixerQueue()


def ocrPlayerScreen(filename):
    filepath = 'forOCR/' + filename
    try:
        im_rgb = cv.imread(filepath)

        im_thresh = cv.cvtColor(im_rgb, cv.COLOR_BGR2GRAY)
        im_thresh = cv.threshold(im_thresh, 150, 255, cv.THRESH_BINARY_INV)[1]

        im_crop1 = im_thresh[13:180, 170:310]
        im_crop2 = im_thresh[191:1080, 384:950]
        im_crop3 = im_thresh[94:1080, 1433:1920]

        lower = np.array([0])
        upper = np.array([15])
        shapeMask1 = cv.inRange(im_crop1, lower, upper)
        shapeMask2 = cv.inRange(im_crop2, lower, upper)
        shapeMask3 = cv.inRange(im_crop3, lower, upper)

        cnts1 = cv.findContours(
            shapeMask1.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts1 = imutils.grab_contours(cnts1)
        cnts1.reverse()

        cnts2 = cv.findContours(
            shapeMask2.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts2 = imutils.grab_contours(cnts2)

        cnts3 = cv.findContours(
            shapeMask3.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts3 = imutils.grab_contours(cnts3)

        for c in cnts1:
            peri = cv.arcLength(c, True)
            approx = cv.approxPolyDP(c, 0.04 * peri, True)

            if len(approx) == 4:
                (x, y, w, h) = cv.boundingRect(approx)
                ar = w / float(h)

                if w > 7 and w < 13 and h <= 3 and ar >= 3.5 and ar <= 6.5:
                    ocr_crop = im_thresh[y + 16:y + 60, x + 168:x+650]
                    text = ''
                    try:
                        text = pytesseract.image_to_string(ocr_crop)
                    except:
                        pass
                    if text:
                        first = text.split('\n')[0]
                        ascii = first.encode(
                            'ascii', 'ignore').strip().split(' ')
                        sans_special = ''
                        for string in ascii:
                            if bool(re.match('[a-zA-Z0-9]+$', string)):
                                sans_special += string + ' '
                        stripped = sans_special.strip()
                        twitch_id = filename.split('.')[0]
                        if stripped:
                            if os.path.isdir('d2-stream-name-parser/' + stripped) == False:
                                os.mkdir('d2-stream-name-parser/' + stripped)
                            data = {}
                            try:
                                with open('d2-stream-name-parser/' + stripped + '/twitch.json') as f:
                                    for i in f:
                                        data = json.loads(i)

                            except:
                                pass
                            if twitch_id in data:
                                data[twitch_id] += 1
                            else:
                                data[twitch_id] = 1
                            with open('d2-stream-name-parser/' + stripped + '/twitch.json', 'w+') as f:
                                f.write(json.dumps(data))
                        break

        for c in cnts2:
            peri = cv.arcLength(c, True)
            approx = cv.approxPolyDP(c, 0.04 * peri, True)

            if len(approx) == 4:
                (x, y, w, h) = cv.boundingRect(approx)
                ar = w / float(h)

                if ar >= .1 and ar <= .3 and h > 40 and h < 50:
                    ocr_crop = im_thresh[approx[2][0][1] + 151: approx[2][0]
                                        [1] + 191, approx[0][0][0] - 31: approx[0][0][0] + 374]
                    text = ''
                    try:
                        text = pytesseract.image_to_string(ocr_crop)
                    except:
                        pass
                    if text:
                        first = text.split('\n')[0]
                        ascii = first.encode(
                            'ascii', 'ignore').strip().split(' ')
                        sans_special = ''
                        for string in ascii:
                            if bool(re.match('[a-zA-Z0-9]+$', string)):
                                sans_special += string + ' '
                        stripped = sans_special.strip()
                        q_check = stripped.split(' ')
                        # Sometimes, the audio icon reads as a 'q' or an 'a', so...
                        if q_check[-1] == 'q' or q_check[-1] == 'a':
                            q_check[-1] = ''
                            stripped = ' '.join(q_check).strip()
                        twitch_id = filename.split('.')[0]
                        if stripped:
                            if os.path.isdir('d2-stream-name-parser/' + stripped) == False:
                                os.mkdir('d2-stream-name-parser/' + stripped)
                            data = {}
                            try:
                                with open('d2-stream-name-parser/' + stripped + '/twitch.json') as f:
                                    for i in f:
                                        data = json.loads(i)

                            except:
                                pass
                            if twitch_id in data:
                                data[twitch_id] += 1
                            else:
                                data[twitch_id] = 1
                            with open('d2-stream-name-parser/' + stripped + '/twitch.json', 'w+') as f:
                                f.write(json.dumps(data))
                        break

        for c in cnts3:
            peri = cv.arcLength(c, True)
            approx = cv.approxPolyDP(c, 0.04 * peri, True)

            if len(approx) == 4:
                (x, y, w, h) = cv.boundingRect(approx)
                ar = w / float(h)

                if ar >= .1 and ar <= .3 and h > 40 and h < 50:
                    ocr_crop = im_thresh[approx[2][0][1] + 54: approx[2][0]
                                        [1] + 94, approx[0][0][0] + 1018: approx[0][0][0] + 1423]
                    text = ''
                    try:
                        text = pytesseract.image_to_string(ocr_crop)
                    except:
                        pass
                    if text:
                        first = text.split('\n')[0]
                        ascii = first.encode(
                            'ascii', 'ignore').strip().split(' ')
                        sans_special = ''
                        for string in ascii:
                            if bool(re.match('[a-zA-Z0-9]+$', string)):
                                sans_special += string + ' '
                        stripped = sans_special.strip()
                        q_check = stripped.split(' ')
                        # Sometimes, the audio icon reads as a 'q' or an 'a', so...
                        if q_check[-1] == 'q' or q_check[-1] == 'a':
                            q_check[-1] = ''
                            stripped = ' '.join(q_check).strip()
                        twitch_id = filename.split('.')[0]
                        if stripped:
                            if os.path.isdir('d2-stream-name-parser/' + stripped) == False:
                                os.mkdir('d2-stream-name-parser/' + stripped)
                            data = {}
                            try:
                                with open('d2-stream-name-parser/' + stripped + '/twitch.json') as f:
                                    for i in f:
                                        data = json.loads(i)

                            except:
                                pass
                            if twitch_id in data:
                                data[twitch_id] += 1
                            else:
                                data[twitch_id] = 1
                            with open('d2-stream-name-parser/' + stripped + '/twitch.json', 'w+') as f:
                                f.write(json.dumps(data))
                        break

        try:
            os.remove(filepath)
        except:
            pass
    except:
        pass


twitch_queue = []
mixer_queue = []

try:
    while True:
        twitch_queue = []
        mixer_queue = []

        print('getting twitch streams...')
        try:
            getTwitchStreams()
        except:
            pass

        print('getting mixer streams...')
        try:
            getMixerStreams()
        except:
            pass

        print('ocr...')
        for filename in os.listdir('forOCR'):
            if not filename.startswith('.'):
                ocrPlayerScreen(filename)

        repo.git.add(A=True)
        repo.index.commit('add mixer and twitch ids')
        origin.push()

        print('sleeping...')
        time.sleep(300)
except KeyboardInterrupt:
    print('Stopped by user')
