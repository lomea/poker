# encoding: utf-8

"""
A basic, multiclient 'chat server' using Python's select module
with interrupt handling.

Entering any input at the terminal will exit the server.
"""

import select
import socket
import sys
import signal
import random
from communication import send, receive

BUFSIZ = 4096


#花色
def color(p):
    return p/13
#花色輸出
def strcolor(p):
    if (p==0):
        return '黑桃'
    elif (p==1):
        return '愛心'
    elif (p==2):
        return '梅花'
    elif (p==3):
        return '菱形'
    else:
        return 'error'
#點數
def point(p):
    return p%13
#點數輸出
def strpoint(p):
    if (p==0):
        return 'A'
    elif (p==1):
        return '2'
    elif (p==2):
        return '3'
    elif (p==3):
        return '4'
    elif (p==4):
        return '5'
    elif (p==5):
        return '6'
    elif (p==6):
        return '7'
    elif (p==7):
        return '8'
    elif (p==8):
        return '9'
    elif (p==9):
        return '10'
    elif (p==10):
        return 'J'
    elif (p==11):
        return 'Q'
    elif (p==12):
        return 'K'
    else:
        return 'error'
#同花順
def isStraightFlush(pset):
    if (isFlush(pset)==1 and isStraight(pset)==1):
        return 1
    else:
        return 0
#四條
def isFourofakind(pset):
    point_list=[]
    for i in range(0,13):
        point_list.append(0)
    for i in pset:
        point_list[point(i)]+=1
    for i in range(0,13):
        if (point_list[i]==4):
            return 1
    return 0
#葫蘆
def isFullhouse(pset):
    if (isThreeofakind(pset)==1 and isOnePair(pset)==1):
        return 1
    else:
        return 0
#同花
def isFlush(pset):
    point_list=[]
    for i in range(0,4):
        point_list.append(0)
    for i in pset:
        point_list[color(i)]+=1
    for i in range(0,4):
        if (point_list[i]==5):
            return 1
    return 0
#順子
def isStraight(pset):
    point_list=[]
    for i in pset:
        point_list.append(point(i))
    point_list.sort()
    if (point_list[0]==0 and point_list[1]==9 and point_list[2]==10 and point_list[3]==11 and point_list[4]==12):
        return 1
    else:
        for i in range(0,4):
            if (point_list[i] != (point_list[i+1]-1)):
                return 0
        return 1

#三條
def isThreeofakind(pset):
    point_list=[]
    for i in range(0,13):
        point_list.append(0)
    for i in pset:
        point_list[point(i)]+=1
    for i in range(0,13):
        if (point_list[i]==3):
            return 1
    return 0
#兩對
def isTwoPairs(pset):
    count=0
    point_list=[]
    for i in range(0,13):
        point_list.append(0)
    for i in pset:
        point_list[point(i)]+=1
    for i in range(0,13):
        if (point_list[i]==2):
            count+=1
    if (count==2):
        return 1
    else:
        return 0
#一對
def isOnePair(pset):
    point_list=[]
    for i in range(0,13):
        point_list.append(0)
    for i in pset:
        point_list[point(i)]+=1
    for i in range(0,13):
        if (point_list[i]==2):
            return 1
    return 0
#計分
def scoring(pset):
    if (isStraightFlush(pset)==1):
        return 9
    elif (isFourofakind(pset)==1):
        return 8
    elif (isFullhouse(pset)==1):
        return 7
    elif (isFlush(pset)==1):
        return 6
    elif (isStraight(pset)==1):
        return 5
    elif (isThreeofakind(pset)==1):
        return 4
    elif (isTwoPairs(pset)==1):
        return 3
    elif (isOnePair(pset)==1):
        return 2
    else:
        return 1

#個人計分
def player_scoring(pset):
    best_score=0
    for i in pset:
        pset1=pset-{i}
        for j in pset1:
            pset2=pset1-{j}
            if (scoring(pset2)>best_score):
                best_score=scoring(pset2)
    return best_score


#初始化
ptr=0
maxbetptr=0
betpool=0
giveup=[]
class ChatServer(object):
    """ Simple chat server using select """
    

    def __init__(self, port=3490, backlog=5):
        self.clients = 0
        # Client map
        self.clientmap = {}
        # Output socket list
        self.outputs = []
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('',port))
        print 'Listening to port',port,'...'
        self.server.listen(backlog)
        # Trap keyboard interrupts
        signal.signal(signal.SIGINT, self.sighandler)
        
    def sighandler(self, signum, frame):
        # Close the server
        print 'Shutting down server...'
        # Close existing client sockets
        for o in self.outputs:
            o.close()
            
        self.server.close()

    def getname(self, client):

        # Return the printable name of the
        # client, given its socket...
        info = self.clientmap[client]
        host, name = info[0][0], info[1]
        return '@'.join((name, host))
    

    
    def serve(self):
        
        inputs = [self.server,sys.stdin]
        self.outputs = []
        #手牌
        selfpoker={}
        #戶頭
        selfmoney={}
        #玩家分數
        selfscore={}
        #贏家
        winner=[]
        
        running = 1

        def clntBet():
            #輪流指標
            global ptr
            #最大賭金指標
            global maxbetptr
            #賭池賭金
            global betpool
            #紀錄放棄的玩家
            global giveup
            
            #本迴圈自己下的賭金
            selfbet={}
            for o in self.outputs:
                selfbet[o]=0
            
            #最大賭金
            maxbet=0

            flag=0
            while flag==0:
                msg='\n目前最大賭金='+str(maxbet)+'\n現在戶頭還有：'+str(selfmoney[self.outputs[ptr]])+'\n1.跟, 2:加注, 3.放棄退出'
                send(self.outputs[ptr], msg)
                reMsg=receive(self.outputs[ptr])
                print reMsg
            
                if int(reMsg)==1:
                    if (selfmoney[self.outputs[ptr]]>=maxbet):
                        selfmoney[self.outputs[ptr]]=selfmoney[self.outputs[ptr]]-maxbet
                        betpool=betpool+maxbet
                        ptr=(ptr+1)%len(self.outputs)
                        
                        print selfmoney
                        if (ptr==maxbetptr):
                            flag=1
                    else:
                        msg='錢不夠唷～～～'
                        send(self.outputs[ptr], msg)
        
                elif int(reMsg)==2:
                    msg='輸入你加注的金額：'
                    send(self.outputs[ptr], msg)
                    rebet=receive(self.outputs[ptr])
                    if (selfmoney[self.outputs[ptr]]>=(int(rebet)+maxbet)):
                        maxbet=maxbet+int(rebet)
                        selfmoney[self.outputs[ptr]]=selfmoney[self.outputs[ptr]]-maxbet
                        betpool=betpool+maxbet-selfbet[self.outputs[ptr]]
                        maxbetptr=ptr
                        ptr=(ptr+1)%len(self.outputs)
                        
                        print selfmoney
                    else:
                        msg='錢不夠唷～～～'
                        send(self.outputs[ptr], msg)

                elif int(reMsg)==3:
                    msg='exit～'
                    send(self.outputs[ptr], msg)
                    giveup=giveup+[ptr]
                    ptr=ptr+1
                else:
                    msg='輸入錯誤～～別亂來～～～'
                    send(self.outputs[ptr%len(self.outputs)], msg)


        while running:

            try:
                inputready,outputready,exceptready = select.select(inputs, self.outputs, [])
            except select.error, e:
                break
            except socket.error, e:
                break

            for s in inputready:

                if s == self.server:
                    # handle the server socket
                    client, address = self.server.accept()
                    print 'chatserver: got connection %d from %s' % (client.fileno(), address)
                    # Read the login name
                    cname = receive(client).split('NAME: ')[1]
                    
                    # Compute client name and send back
                    self.clients += 1
                    send(client, 'CLIENT: ' + str(address[0]))
                    inputs.append(client)

                    self.clientmap[client] = (address, cname)
                    # Send joining information to other clients
                    msg = '\n(Connected: New client (%d) from %s)' % (self.clients, self.getname(client))
                    for o in self.outputs:
                        # o.send(msg)
                        send(o, msg)
                    
                    selfmoney[client]=10000
                    msg = '你戶頭有10000元'
                    send(client, msg)
                    self.outputs.append(client)

                elif s == sys.stdin:
                    # handle standard input
                    junk = sys.stdin.readline()
                    running = 0
                else:
                    # handle all other sockets
                    try:
                        # data = s.recv(BUFSIZ)
                        data = receive(s)
                        if data.find('open')!=-1:
                            for o in self.outputs:
                                msg='Game start!'
                                send(o, msg)
                            #遊戲開始
                            
                            #發牌
                            allcard=set(random.sample(range(52),2*len(self.outputs)+5))
                            for i in range( len(self.outputs) ):
                                #手牌設定
                                selfpoker[self.outputs[i]]=set(random.sample(allcard,2))
                                listselfcard=list(selfpoker[self.outputs[i]])
                                msg='/selfcard:'
                                for k in listselfcard:
                                    msg=msg+strcolor(color(k))+strpoint(point(k))+','
                                #發送手牌至每位玩家
                                send(self.outputs[i],msg)
                                allcard=allcard-selfpoker[self.outputs[i]]
                            #公開牌設定
                            communityCard=set(random.sample(allcard,3))
                            allcard=allcard-communityCard
                            #轉牌設定
                            turnCard=set(random.sample(allcard,1))
                            allcard=allcard-turnCard
                            #河牌設定
                            riverCard=allcard
                            #牌組確認

                            print selfpoker
                            print communityCard
                            print turnCard
                            print riverCard
                            #第一次下注
                            clntBet()
                    
                            #發送公開牌
                            msg='/communityCard:'
                            listcommcard=list(communityCard)
                            for k in listcommcard:
                                msg=msg+strcolor(color(k))+strpoint(point(k))+','
                            for o in self.outputs:
                                send(o, msg)
                            
                            #第二次下注
                            clntBet()
                    
                            #公開轉牌
                            msg='/turnCard:'
                            listturncard=list(turnCard)
                            for k in listturncard:
                                msg=msg+strcolor(color(k))+strpoint(point(k))+','
                            for o in self.outputs:
                                send(o, msg)
                
                            #第三次下注
                            clntBet()
                    
                            #公開河牌
                            msg='/riverCard:'
                            listriverCard=list(riverCard)
                            for k in listriverCard:
                                msg=msg+strcolor(color(k))+strpoint(point(k))+','
                            for o in self.outputs:
                                send(o, msg)

                            #第四次下注
                            clntBet()
                            
                            #比牌
                            bestscore=0
                            for o in self.outputs:
                                selfscore[o]=player_scoring(selfpoker[o] | communityCard | turnCard | riverCard)
                                if selfscore[o]>bestscore:
                                    del winner[:]
                                    bestscore=selfscore[o]
                                    winner.append(o)
                                elif selfscore[o]==bestscore:
                                    winner.append(o)
                            
                            print selfscore
                            print winner
                            
                            #分配賭金
                            msg='you win!$  '+str(betpool/len(winner))
                            for o in winner:
                                selfmoney[o]=selfmoney[o]+betpool/len(winner)
                                send(o, msg)
                            print selfmoney
                
                            #遊戲結束
                            msg='Game Over!'
                            for o in self.outputs:
                                send(o, msg)
                        elif data:
                            # Send as new client's message...
                            msg = '\n#[' + self.getname(s) + ']>> ' + data
                            # Send data to all except ourselves
                            for o in self.outputs:
                                if o != s:
                                    # o.send(msg)
                                    send(o, msg)
                        else:
                            print 'chatserver: %d hung up' % s.fileno()
                            self.clients -= 1
                            s.close()
                            inputs.remove(s)
                            self.outputs.remove(s)

                            # Send client leaving information to others
                            msg = '\n(Hung up: Client from %s)' % self.getname(s)
                            for o in self.outputs:
                                # o.send(msg)
                                send(o, msg)
                                
                    except socket.error, e:
                        # Remove
                        inputs.remove(s)
                        self.outputs.remove(s)
                        


        self.server.close()

if __name__ == "__main__":
    ChatServer().serve()
