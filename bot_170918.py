'''
自动聊天默认开启
stop 关闭 start 重新开启
查课+课程名/老师名  捅奶牛查课
听歌+歌名  网易云歌曲链接
校巴 华农校巴
'''
#-*-coding:utf-8-*-
import os
import platform
import itchat
import json,time
import random
import requests
from urllib.parse import quote

# 可变数组
startArray = []
stopArray = []
# 网易云音乐api
from NetEaseMusicApi import api

from queue import Queue
from threading import Thread,Event

MsgQueue = Queue()

userId = None

def sendMsg(response, msg):
    if not type(response) == dict:
        itchat.send(msg=str(response), toUserName=msg['FromUserName'])
    elif 'url' in response.keys():
        itchat.send(msg=str(response['text']), toUserName=msg['FromUserName'])
        itchat.send(msg=str(response['url']), toUserName=msg['FromUserName'])
    elif 'list' in response.keys():
        for i in range(5):
            itchat.send(msg=str(response['list'][i]['article']), toUserName=msg['FromUserName'])
            itchat.send(msg=str(response['list'][i]['detailurl']), toUserName=msg['FromUserName'])
    else:
        itchat.send(msg=str(response['text']), toUserName=msg['FromUserName'])
flag = True

# 通用回复
def commomResponse(msg,event):
    if msg['Type'] == 'Picture':
        itchat.send_image('emoji\\'+ msg['FileName'],itchat.search_mps(name='小冰')[0]['UserName'])
        while not event.is_set():
            event.wait(timeout=10)
    elif msg['Type'] == 'Text':
        if  '听歌' in msg["Text"][:3] and (len(msg['Text']) > 3):
            if '：' in msg["Text"] or ':' in msg["Text"]:
                msg["Text"] = msg["Text"][3:]
            else:
                msg["Text"] = msg["Text"][2 :]
            try:
                sendMsg('http://music.163.com/#/song?id=' + str(api.search.songs(msg['Text'], 1)[0]['id']), msg)
            except:
                itchat.send_image('emoji\\170523-153244.gif', toUserName=msg['FromUserName'])
        elif  'stop' in msg["Text"] :
            stopArray.append(msg['FromUserName'])
        elif (msg["Text"][:2] == '查课') and (len(msg['Text']) > 2):
            if '：' in msg["Text"] or ':' in msg["Text"]:
                msg["Text"] = msg["Text"][3:]
            else:
                msg["Text"] = msg["Text"][2:]
            print(msg["Text"])
            link2 = 'http://hometown.scau.edu.cn/course/index.php?s=/Search/result/'
            sendMsg('亲，我在捅奶牛为你捅到了以下课程，打开链接查看吧'+link2+str(quote(msg['Text']))+'.html', msg)
        elif '校巴' in msg["Text"] :
            link = 'https://hbus.scau.edu.cn/index.php?mod=busmap'
            sendMsg(' 校巴地图：' + link, msg)
        else:
            itchat.send_msg(msg['Text'], itchat.search_mps(name='小冰')[0]['UserName'])
            while not event.is_set():
                event.wait(timeout=10)
    return event

def runQueue(MsgQueue,event):
    global MsgUser
    global userId
    while flag:
        if not MsgQueue.empty():
            msg = MsgQueue.get()
            if itchat.search_friends()["UserName"] != msg['FromUserName'] or msg['ToUserName'] == 'filehelper':
                userId = msg['FromUserName']
                if ( msg['Type'] == 'Picture'and msg['FromUserName'] in startArray ) or msg['ToUserName'] == 'filehelper':
                    if msg['ToUserName'] == 'filehelper':
                        userId = msg['ToUserName']
                    commomResponse(msg, event)
                elif msg['Type'] == 'Text':
                    msg["Text"] = msg["Text"].strip()
                    startArray.append(msg['FromUserName'])
                    if msg['ToUserName'] == 'filehelper':
                        userId = msg['ToUserName']
                        commomResponse(msg, event)
                    elif 'isAt' in msg.keys():
                        commomResponse(msg, event)
                    else:
                        commomResponse(msg, event)
            event.clear()
            MsgQueue.task_done()

def main(MsgQueue,event):
    global flag
    while flag:
        # 小冰公众号消息
        @itchat.msg_register([itchat.content.TEXT,itchat.content.RECORDING, itchat.content.PICTURE], isMpChat=True)
        def map_reply(msg):
            # print(msg['FromUserName'])
            # print(itchat.search_mps(name='小冰')[0]['UserName'])
            if itchat.search_mps(name='小冰')[0]['UserName'] == msg['FromUserName']:
                global userId
                if userId:
                    if msg['Type'] == 'Picture':
                        try:
                            msg['Text']('emoji\\'+msg['FileName'])
                            itchat.send_image('emoji\\' + msg['FileName'], userId)
                        except:
                            itchat.send_image('emoji\\170526-192631.gif', userId)
                    elif msg['Type'] == 'Text':
                        itchat.send_msg(msg["Text"], userId)
                    else:
                        itchat.send_msg('本来想发你语音的，但发现不支持这个功能。', userId)
                userId = None
            event.set()

        @itchat.msg_register([itchat.content.TEXT,itchat.content.PICTURE], isGroupChat=True)
        def text_reply(msg):
            if msg['Type'] == 'Picture':
                try:
                    filePath = 'emoji\\' + msg['FileName']
                    msg['Text'](filePath)
                    fsize = os.path.getsize(filePath)
                    if fsize == 0:
                        os.remove(filePath)
                except:
                    print('fail')
            elif msg['Type'] == 'Text':
                print('qun'+msg['Text'])
                if msg['isAt']:
                    if not msg["User"]["Self"]['DisplayName'] == '':
                        msg["Text"] = msg["Text"].replace('@'+msg["User"]["Self"]["DisplayName"],'')
                    else:
                        msg["Text"] = msg["Text"].replace('@' + msg["User"]["Self"]["NickName"], '')
                    print(msg["Text"])
                    if len(msg["Text"])==0:
                        sendMsg("???",msg)
                    else:
                        MsgQueue.put(msg)

        @itchat.msg_register([itchat.content.TEXT,itchat.content.PICTURE])
        def text_reply(msg):
            if msg['Type'] == 'Picture':
                try:
                    filePath = 'emoji\\' + msg['FileName']
                    msg['Text'](filePath)
                    fsize = os.path.getsize(filePath)
                    if fsize == 0:
                        os.remove(filePath)
                        if msg['FromUserName'] in startArray or msg['ToUserName'] == 'filehelper':
                            itchat.send_image('emoji\\170526-172121.gif',msg['FromUserName'])
                            sendMsg('你发的那个表情是在专辑中的，我收不到。',msg)
                    else:
                        MsgQueue.put(msg)
                except:
                    print('fail')
            elif msg['Type'] == 'Text':
                if msg["Text"] == 'start' and msg['FromUserName'] in stopArray:
                    stopArray.remove(msg['FromUserName'])
                elif not msg['FromUserName'] in stopArray:
                    MsgQueue.put(msg)


        itchat.auto_login()
        itchat.run()

        if itchat.dump_login_status() == None:
            flag = False
            sysstr = platform.system()
            if (sysstr == "Windows"):
                os.system('taskkill /f /im python.exe')
            elif (sysstr == "Linux"):
                os.system('pkill - f bot.py')

#  判断 emoji 文件夹是否存在  存放聊天图片
if not os.path.exists('emoji'):
    os.mkdir('emoji')

event = Event()
replyThread = Thread(target=main, args=(MsgQueue,event,))
replyThread.start()

msgQueueThread = Thread(target=runQueue, args=(MsgQueue,event,))
msgQueueThread.start()

MsgQueue.join()


