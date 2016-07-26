# coding=utf-8
# Ref: http://mhwong2007.logdown.com/posts/314403
# Parameters: account, password (optional), board name
# Assumptions:
#   - No "Announcement"
#   - Input parameters are correct
#   - The entered account is currently not login
#   - The entered account can read ALL the article in the specified range
# Notes:
#   - You may need to install "pyte" or other libs
#   - Remember to download uao_decode (https://gist.github.com/andycjw/5617496)
import telnetlib, pyte, uao_decode, codecs
import sys, time, re, argparse

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
    content = tn.read_very_eager().decode('uao_decode', 'ignore')
else: # 沒有
    content = tup[2].decode('uao_decode', 'ignore')

#articleEndStr = '\x1B[34;46m 文章選讀 \x1B[31;47m (y)\x1B[30m回應 \x1B[31m(=\\[]<>-+;\'`jk)\x1B[30m相關主題 \x1B[31m(/?)\x1B[30m搜尋標題 \x1B[31m(aA)\x1B[30m搜尋作者 \x1B[m'.decode('uao_decode', 'ignore');
articleEndStr = '搜尋作者'.decode('uao_decode', 'ignore')
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
        if(counter>=20): break
    with codecs.open(str(i) + '.txt', 'w', encoding='utf8') as fout: fout.write(content)
    tn.write('q')
tn.close()
# python hulaCrawler.py guest 00andychay00 1 5
# python hulaCrawler.py guest 13_family 1 4
