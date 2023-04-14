#!/usr/bin/env python
import os

from flask import Flask, request, abort, render_template
from wechatpy.utils import check_signature
from wechatpy import parse_message, create_reply
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.replies import TextReply

TOKEN = os.getenv("WECHAT_TOKEN", "")
AES_KEY = os.getenv("WECHAT_AES_KEY", "")
APP_ID = os.getenv("WECHAT_APPID", "")
CHATGPT_CONTENT_PATH = ""

app = Flask(__name__, template_folder="template")

@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    timestamp = request.args.get("timestamp")
    nonce = request.args.get("nonce")
    if request.method == 'GET':
        # token, signature, timestamp, nonce
        echostr = request.args.get("echostr")
        signature = request.args.get("signature")
        if echostr:
            try:
                check_signature(TOKEN, signature, timestamp, nonce)
                return echostr
            except InvalidSignatureException:
                app.logger.error("invalid message from request")

    else:
        xml = request.data
        if xml:
            msg_signature = request.args.get("msg_signature")
            crypto = WeChatCrypto(TOKEN, AES_KEY, APP_ID)
            try:
                decrypted_xml = crypto.decrypt_message(
                    xml,
                    msg_signature,
                    timestamp,
                    nonce
                )
                msg = parse_message(decrypted_xml)
                #                      check message type                     #
                if msg.type == "text":
                    app.logger.info("message from wechat %s " % msg)
                    reply = do_reply(msg)
                    xml = reply.render()
                    return xml

            except (InvalidAppIdException, InvalidSignatureException):
                app.logger.error("cannot decrypt message!")
        else:
            app.logger.error("no xml body, invalid request!")
    return ""

def do_reply(msg):
    reply = TextReply()
    reply.source = msg.target
    reply.target = msg.source
    try:
        if msg.content.strip() == '1':
            with open(CHATGPT_CONTENT_PATH, "r") as inFile:
                reply.content = "详情查看： https://yanshuo.site/today_nt/ \n" + inFile.read()
                # reply.content = inFile.read()
                reply.content = (reply.content[:590] + '..') if len(reply.content) > 590 else reply.content
        else:
            reply.content = "发送1，将获取chatGPT解析文献"
    except Exception as e:
        print(e)
    return reply

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
