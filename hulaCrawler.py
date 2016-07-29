# coding=utf-8
# Ref: http://mhwong2007.logdown.com/posts/314403
# Parameters: account, password (optional), board name
# Assumptions:
#   - File for this source is saved in big5 (ANSI)
#   - No "Announcement" in BBS
#   - Input parameters are correct
#   - The entered account is currently not login
#   - The entered account can read **ALL** the article in the specified range
# Notes:
#   - You may need to install "pyte" or other libs
#   - Remember to download uao_decode (https://gist.github.com/andycjw/5617496)
import telnetlib, pyte, uao_decode, codecs
import os, sys, time, re, argparse

siteName = 'hulabear.twbbs.org'

parser = argparse.ArgumentParser(description='Hulabear crawler for ONE board')
parser.add_argument('account')
parser.add_argument('board')
parser.add_argument('startPostId', type=int)
parser.add_argument('endPostId'  , type=int)
parser.add_argument('--password'  , '-p' , default='')
args = parser.parse_args()
account  = args.account
board    = args.board
password = args.password
startId  = args.startPostId
endId    = args.endPostId

def contentPurify(str):
    offset = 4
    # 統整換行格式
    str = str.replace('\r\n', '\n')
    str = str.replace('\n\r', '\n')
    str = str.replace('\r', '\n')
    # 行號，會在下面改成照原始排版
    str = re.sub('(\x1B\[\d+;1H)', r'\n\1', str)
    # 這幾個是啥不知道，可能是代表什麼開頭結尾
    #str = str.replace('\x1B[K\S*', '')
    str = re.sub('\x1B\[23;1H\x1B\[K[\r\n]*', '', str)
    str = re.sub('\x1B\[K', '', str)
    str = str.replace('\x1B[;H\x1B[2J', '') # 刪除最開頭
    # 切分，逐行處理
    strList = str.split('\n')
    # 第一輪刪除
    delIdx = []
    for i in range(len(strList)):
        if(strList[i].startswith('\x1B[0;34;46m 瀏覽'.decode('uao_decode', 'ignore'))): delIdx.append(i)
        elif(strList[i].startswith('\x1B[34;46m 文章選讀'.decode('uao_decode', 'ignore'))): delIdx.append(i)
        elif(strList[i].startswith('\x1B[24;1H\x1B[0;34;46m 瀏覽'.decode('uao_decode', 'ignore'))): strList[i] = ''
    delIdx.reverse()
    for i in delIdx: del strList[i]
    # 第二輪刪除
    delIdx = []
    isCurrEmptyLine = 0
    isPrevEmptyLine = 0
    for i in range(len(strList)):
        isCurrEmptyLine = 1 if(len(strList[i])==0) else 0
        #print i, isCurrEmptyLine, 
        if(isCurrEmptyLine==1 and isPrevEmptyLine==0): delIdx.append(i)
        #print ''
        isPrevEmptyLine = isCurrEmptyLine
    delIdx.reverse()
    for i in delIdx: del strList[i]
    # 處理行號
    for i in range(len(strList)):
        m = re.match('\x1B\[(\d+);1H', strList[i])
        if(m and int(m.group(1))<23):
            strList[i] = re.sub('\x1B\[(\d+);1H', '\n'*(int(m.group(1))-offset-1), strList[i])
            offset = int(m.group(1))
        elif(m):
            strList[i] = re.sub('\x1B\[(\d+);1H', '', strList[i])
    return '\n'.join(strList)

def contentColoring(str):
    str = str.replace('<', '&lt;')
    str = str.replace('>', '&gt;')
    pStart = re.compile('\x1B\[([\d; ]+)m')
    def matchAndRep(m):
        cnStr = m.group(1).replace(';', ' ')
        cnStr = re.sub('(^1|\s1)', ' hl', cnStr)
        cnStr = re.sub('(^3|\s3)', ' f', cnStr)
        cnStr = re.sub('(^4|\s4)', ' b', cnStr)
        return '<span class="' + cnStr + '">'
    str = pStart.sub(matchAndRep, str)
    str = re.sub('\x1B\[m', '</span>', str)
    startIdx = [m.start(0) for m in re.finditer('<span', str)]
    endIdx = [m.start(0) for m in re.finditer('</span', str)]
    #print startIdx, endIdx
    insIdx = []
    for i in range(len(startIdx)-1):
        x = [ value for value in endIdx if value>startIdx[i] and value<startIdx[i+1] ]
        if(x==[]): insIdx.append(startIdx[i+1])
        #print i, startIdx[i], x
    insIdx.reverse()
    for i in insIdx:
        str = str[:i] + '</span>' + str[i:]
    str = '<html><head><link rel="stylesheet" type="text/css" href="../bbs.css"></head><body><div class="bbs-screen bbs-content">' + str + '</div></body></html>'
    return str

screen = pyte.Screen(80, 24)
stream = pyte.Stream()
stream.attach(screen)
tn = telnetlib.Telnet(siteName)

# Login
tn.read_until('請輸入代號：')
if(account=='guest'):
    tn.write(account + '\r\n'*4)
    tn.read_until('【 再別熊窩 】')
else:
    tn.write(account + '\r\n')
    tn.read_until('請輸入密碼：')
    tn.write(password + '\r\n'*2)

# 主選單，按 s 搜尋與進板
tn.write('\r\ns')
tn.read_until('請輸入看板名稱(按空白鍵自動搜尋)：')
tn.read_very_eager() # used to clear buffer
tn.write(board + '\r\n')

# 處理是否有進板畫面
tup = tn.expect(['▏▎▍▌▋▊▉\s\x1B\[1;37m請按任意鍵繼續\s\x1B\[1;33m▉\x1B\[m'], 1)
if(tup[0]!=-1): # 有
    tn.write('\r\n')
    time.sleep(1)
    #content = tn.read_very_eager().decode('uao_decode', 'ignore')
#else: # 沒有
    #content = tup[2].decode('uao_decode', 'ignore')

#articleEndStr = '\x1B[34;46m 文章選讀 \x1B[31;47m (y)\x1B[30m回應 \x1B[31m(=\\[]<>-+;\'`jk)\x1B[30m相關主題 \x1B[31m(/?)\x1B[30m搜尋標題 \x1B[31m(aA)\x1B[30m搜尋作者 \x1B[m'.decode('uao_decode', 'ignore');
articleEndStr = '搜尋作者'.decode('uao_decode', 'ignore')
if not os.path.exists('crawled'): os.mkdir('crawled') # Modified from Bossliaw's code
if not os.path.exists('crawled/'+board): os.mkdir('crawled/'+board) # Modified from Bossliaw's code
for i in range(startId, endId+1):
    print 'Crawling article {}'.format(i)
    tn.write(str(i) + '\r\n'*2)
    time.sleep(1)
    content = tn.read_very_eager().decode('uao_decode', 'ignore')
    # 刪除沒清乾淨的文章列表
    pos = content.find('\x1B[;H\x1B[2J\x1B[47;34m')
    if(pos!=-1): content = content[pos:]
    counter = 0
    while(articleEndStr not in content):
        print '\tdown {}...'.format(counter)
        tn.write('\x1B[B') # down
        time.sleep(0.5)
        content += tn.read_very_eager().decode('uao_decode', 'ignore')
        counter += 1
    content = contentPurify(content)
    with codecs.open('crawled/' + board + '/' + str(i) + '.txt', 'w', encoding='utf8') as fout: fout.write(content)
    content = contentColoring(content)
    with codecs.open('crawled/' + board + '/' + str(i) + '.htm', 'w', encoding='utf8') as fout: fout.write(content)
    tn.write('q')
tn.close()
