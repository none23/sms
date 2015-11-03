#!/usr/bin/env python
# -*- coding: utf8 -*-

# This is a slightly changed version of smssend by Denis Khabarov
# Originally from https://github.com/dkhabarov/smssend


import sys, argparse
from os import getenv

if sys.version_info[0] == 2:
    from urllib2 import urlopen, URLError
    from urllib import quote
if sys.version_info[0] == 3:
    from urllib.request import urlopen
    from urllib.error import URLError
    from urllib.parse import quote

parser = argparse.ArgumentParser(
    epilog="""
    Return codes:
        0 - Message send successful
        1 - Service has retured error message
        2 - HTTP Error
        3 - Error for usage this tool
    Default API ID are read from the files:
        Linux: $HOME/.smssendrc
        Windows: %USERPROFILE%/.smssendrc
    Example usage:
        echo "Hello world" | smssend --api-id=youapiid --to=target_phone_number
    """,
    description="""
    smssend is a program to send SMS messages from the commandline.
    Using API service http://sms.ru
    """,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    prog="smssend",
    usage="%(prog)s --help"
            )
parser.add_argument("--api-id", dest="api_id", metavar="VALUE", help="API ID (optional)")
parser.add_argument("--to", metavar="PHONENUMBER", required=True, help="Telephone number to send the message to (required)")
parser.add_argument("--message", metavar="MESSAGE", help="Read the message from a file (optional)")
parser.add_argument("--from", dest="sendername", metavar="VALUE", help="Sender name (optional)")
parser.add_argument("--time", metavar="VALUE", help="Send time using UNIX TIME format (optional)")
parser.add_argument("--http_timeout", metavar="VALUE", default=10, help="Timeout for http connection (default is 10)")
parser.add_argument("--translit", action="store_true", help="Convert non-latin characters to translit")
parser.add_argument("--debug", action="store_true", help="Print debug messages")
cliargs = parser.parse_args()

servicecodes = {
    100: "Сообщение принято к отправке. На следующих строчках  вы найдете \
          идентификаторы отправленных сообщений в том же порядке, в котором вы \
          указали номера, на которых совершалась отправка.",
    200: "Неправильный api_id",
    201: "Не хватает средств на лицевом счету",
    202: "Неправильно указан получатель",
    203: "Нет текста сообщения",
    204: "Имя отправителя не согласовано с администрацией",
    205: "Сообщение слишком длинное (превышает 8 СМС)",
    206: "Будет превышен или уже превышен дневной лимит на отправку сообщений",
    207: "На этот номер (или один из номеров) нельзя отправлять сообщения, \
          либо указано более 100 номеров в списке получателей",
    208: "Параметр time указан неправильно",
    209: "Вы добавили этот номер (или один из номеров) в стоп-лист",
    210: "Используется GET, где необходимо использовать POST",
    211: "Метод не найден",
    220: "Сервис временно недоступен, попробуйте чуть позже.",
    300: "Неправильный token (возможно истек срок действия, \
          либо ваш IP изменился)",
    301: "Неправильный пароль, либо пользователь не найден",
    302: "Пользователь авторизован, но аккаунт не подтвержден (пользователь \
          не ввел код, присланный в регистрационной смс)",
    }

def show_debug_messages(msg):
    if cliargs.debug == True:
        print(msg)

def get_home_path():
    if sys.platform.startswith('freebsd') or sys.platform.startswith('linux'):
        home = getenv('HOME')
    elif sys.platform.startswith('win'):
        home = getenv('USERPROFILE')
    if home:
        return home
    else:
        print("Unable to get home path.")
        sys.exit(3)

def get_api_id():
    if cliargs.api_id:
        api_id = cliargs.api_id
    else:
        try:
            with open("%s/.smssendrc" % (get_home_path())) as fp:
                data = fp.read()
        except IOError as errstr:
            print(errstr)
            sys.exit(3)
        if len(data) >= 10:
            api_id = data.replace("\r\n", "")
            api_id = api_id.replace("\n", "")
    return api_id

def get_msg():
    if cliargs.message:
        message = cliargs.message
    else:
        message = sys.stdin.read()
    return message

def main():
    api_id = get_api_id()
    if api_id is None:
        print("Error for get api-id. Check" +
              get_home_path() + "/.smssendrc or see --help")
        sys.exit(3)

    url = ("http://sms.ru/sms/send?api_id=" + str(api_id) + "&to=" +
           str(cliargs.to) +"&text=" + quote(get_msg()) + "&partner_id=3805")
    if cliargs.debug:
        url = url + "&test=1"
    if cliargs.sendername:
        url = url + "&from=" + cliargs.sendername
    if cliargs.time:
        url = url + "&time=" + str(int(cliargs.time))
    if cliargs.translit:
        url = url + "&translit=1"

    try:
        res = urlopen(url, timeout=cliargs.http_timeout)
        show_debug_messages("GET: " + res.geturl() + str(res.msg) +
                            "\nReply:\n" + str(res.info()))
    except URLError as errstr:
        show_debug_messages("smssend[debug]: " + errstr)
        sys.exit(2)

    service_result = res.read().splitlines()
    if service_result:
        if int(service_result[0]) == 100:
            show_debug_messages("smssend[debug]: Message send ok. ID: " +
                                str(service_result[1]))
            sys.exit(0)
        else:
            show_debug_messages("smssend[debug]: Unable send sms message to" +
                                cliargs.to + " Service has returned code: " +
                                servicecodes[int(service_result[0])])
            sys.exit(1)

if __name__ == "__main__":
    main()
