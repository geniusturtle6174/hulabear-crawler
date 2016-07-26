# coding=utf-8
# Ref: http://mhwong2007.logdown.com/posts/314403
# Parameters: account, password (optional), board name
# Note:
#   - Assuming no "Announcement"
#   - Assuming input parameters are correct
#   - You may need to install "pyte" or other libs
import telnetlib, pyte, uao_decode, codecs
import sys, time, re, argparse

siteName = 'hulabear.twbbs.org'

parser = argparse.ArgumentParser(description='Hulabear crawler for ONE board')
parser.add_argument('account')
parser.add_argument('board')
parser.add_argument('--password'  , '-p' , default='')
args = parser.parse_args()
account  = args.account
board    = args.board
password = args.password

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

for i in range(1,3):
    tn.write(str(i) + '\r\n'*2)
    #tn.read_very_eager() # used to clear buffer
    #tn.write('\r\n')
    time.sleep(1)
    content = tn.read_very_eager().decode('uao_decode', 'ignore')
    pos = content.find('\x1B[;H\x1B[2J\x1B[47;34m')
    if(pos!=-1): content = content[pos:]
    with codecs.open(str(i) + '.txt', 'w', encoding='utf8') as fout: fout.write(content)
    tn.write('q')
tn.close()
