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

# 网易云音乐api
from NetEaseMusicApi import api

from queue import Queue
from threading import Thread,Event

MsgQueue = Queue()

# 获取小冰回复信息后要发人的formUserid
userId = None

# 发送信息模板,url,list 是图灵机器人的。。。
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

# 下载图片
def downloadImageFile(dir,imgUrl,saveUrl):
    try:
        picture = requests.get(imgUrl,timeout=20)
        img = picture.content
    except:
        return None
    pictureSavePath = dir+'\\' + saveUrl
    with open(pictureSavePath, "wb") as jpg:
        jpg.write(img)
    jpg.close()
    return pictureSavePath

# 获取图灵机器人的回复
def getTulingResponse(msg):
    info = msg['Text'].encode("utf-8")
    print(info)
    url = "http://www.tuling123.com/openapi/api"
    data = {
        "key": tulingkey,
        "info": info,
        "userid": msg['FromUserName']
    }
    try:
        apicon = requests.post(url, data).text
        s = json.loads(apicon, encoding="utf-8")
        print("图灵回复", s)
        sendMsg(s, msg)
    except:
        sendMsg('服务器小哥跟吴玲玲跑了！', msg)

#线程启用标志
flag = True
# 通用回复
def commomResponse(msg,event):
    if msg['Type'] == 'Picture':
        itchat.send_image('emoji\\'+ msg['FileName'],itchat.search_mps(name='小冰')[0]['UserName'])
        while not event.is_set():
            event.wait(timeout=10)
    elif msg['Type'] == 'Text':
        if  '听歌' in msg["Text"][:3] and (len(msg['Text']) > 3):
            msg["Text"] = msg["Text"][3:]
            # 网易云音乐 api.search.songs(songName) 获取歌曲信息，然后拼接就是歌的URL
            sendMsg('http://music.163.com/#/song?id=' + str(api.search.songs(msg['Text'], 1)[0]['id']), msg)
        elif '种子'in  msg["Text"][:3] and (len(msg['Text']) > 3):
            msg["Text"] = msg["Text"][3:]
            sendMsg('http://bthub.io/search?key=' + str(quote(msg['Text'])), msg)
        elif '看图' in msg["Text"]:
            msg["Text"] = msg["Text"][2:]
            if '美女' in msg['Text']:
                imgList = json.loads(requests.get('http://www.tngou.net/tnfs/api/news?id='+str(random.randint(1,1000))+'&rows=10').text)
                if len(imgList)  != 0:
                    imgLink = 'http://tnfs.tngou.net/image/' + str(imgList['tngou'][random.randint(0,len(imgList))]['img'])
                    imgFileDir = downloadImageFile('belle',imgLink,str(time.strftime('%Y%m%d-%H%M%S',time.localtime(time.time())))+'.jpg')
                    if imgFileDir != None:
                        itchat.send_image(imgFileDir, toUserName=msg['FromUserName'])
                    else:
                        itchat.send_image('emoji\\170523-153244.gif', toUserName=msg['FromUserName'])
                else:
                    itchat.send_image('emoji\\170523-153244.gif', toUserName=msg['FromUserName'])
            else:
                itchat.send_image('emoji\\170523-153244.gif', toUserName=msg['FromUserName'])
        else:
            if (msg["Text"][:3] == '图灵:' or msg["Text"][:3] == '图灵：') and (len(msg['Text']) > 3):
                msg["Text"] = msg["Text"][3:]
                getTulingResponse(msg)
            else:
                itchat.send_msg(msg['Text'], itchat.search_mps(name='小冰')[0]['UserName'])
                while not event.is_set():
                    event.wait(timeout=10)
    return event

# 监控队列里有没消息
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
                    print(msg['Text'])
                    msg["Text"] = msg["Text"].strip()
                    if  msg['FromUserName'] in startArray or 'start' in str(msg["Text"]):
                        if 'start' in str(msg["Text"]) :
                            if not msg['FromUserName'] in startArray:
                                startArray.append(msg['FromUserName'])
                        elif ('stop' in str(msg["Text"])) and (msg['FromUserName'] in startArray):
                            startArray.remove(msg['FromUserName'])
                        elif msg['ToUserName'] == 'filehelper':
                            userId = msg['ToUserName']
                            commomResponse(msg, event)
                        elif 'isAt' in msg.keys():
                            commomResponse(msg, event)
                        else:
                            commomResponse(msg, event)
            event.clear()
            MsgQueue.task_done()

# 监控有没人发你信息
def main(MsgQueue,event):
    global flag
    while flag:
        # 获取小冰公众号消息
        @itchat.msg_register([itchat.content.TEXT,itchat.content.RECORDING, itchat.content.PICTURE], isMpChat=True)
        def map_reply(msg):
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

        #注册群信息
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

            if msg['isAt']:
                msg["Text"] = msg["Text"].replace('@'+msg["User"]["Self"]["DisplayName"],'')
                print(msg["Text"])
                if len(msg["Text"])==0:
                    sendMsg("???",msg)
                else:
                    MsgQueue.put(msg)
        # 注册信息
        @itchat.msg_register([itchat.content.TEXT,itchat.content.PICTURE])
        def text_reply(msg):
            if msg['Type'] == 'Picture':
                try:
                    filePath = 'emoji\\' + msg['FileName']
                    msg['Text'](filePath)
                    # 专辑中的表情无法下载，文件存在但大小为0，所以我把它删了
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
                print(msg['Text'])
                MsgQueue.put(msg)


		# 根据操作系统是否生成二维码图片
        sysstr = platform.system()
        if (sysstr == "Windows"):
            itchat.auto_login(hotReload=True)
            itchat.run()
        elif (sysstr == "Linux"):
            itchat.auto_login(hotReload=True, enableCmdQR=True)
            itchat.run()

        #  可能是因为多线程的原因，网页中点退出后要干掉进程才行
        if itchat.dump_login_status() == None:
            flag = False
            # 判断 本地操作系统
            sysstr = platform.system()
            if (sysstr == "Windows"):
                os.system('taskkill /f /im python.exe')
            elif (sysstr == "Linux"):
                os.system('pkill - f bot.py')


#  判断 emoji 文件夹是否存在  存放聊天图片
if not os.path.exists('emoji'):
    os.mkdir('emoji')

# 判断 bello 文件夹是否存在  存放美女图片
if not os.path.exists('bello'):
    os.mkdir('bello')

#  线程标志
event = Event()

# 下面两个是进程间通讯
replyThread = Thread(target=main, args=(MsgQueue,event,))
replyThread.start()

msgQueueThread = Thread(target=runQueue, args=(MsgQueue,event,))
msgQueueThread.start()

MsgQueue.join()

