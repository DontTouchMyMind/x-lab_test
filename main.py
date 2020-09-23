import xml.etree.ElementTree as XmlElementTree
import httplib2
import uuid
from config import ***

***_HOST = '***'
***_PATH = '/***_xml'
CHUNK_SIZE = 1024 ** 2


def speech_to_text(filename=None, bytes=None, request_id=uuid.uuid4().hex, topic='notes', lang='ru-RU',
                   key=***_KEY):
    """
    Функция осуществляет вызов методов, ответственных за конвертирование и считываение байтов по блокам.
    Конвертирование происходит в формат PCM 16000 Гц 16 бит. Далее функция выполняет формирование запроса
    и чтение ответа.
    :param filename: Имя файла-источника (по умолчанию None).
    :param bytes: Переменная, которая хранит данные преобразованные в байты.
    :param request_id: Идентификатор запроса.
    :param topic: Топик (по умолчанию 'notes').
    :param lang: Язык (по умолчанию русский).
    :param key: Ключ подключения API.
    :return: Текст, преобразованный из голосового сообщения.
    """

    if filename:
        with open(filename, 'br') as file:
            bytes = file.read()
    if not bytes:
        raise Exception('Neither file name nor bytes provided.')

    # Конвертирование в PCM 16000 Гц 16 бит, т.к. формат обеспечивает наилучшее качество распознавания.
    bytes = convert_to_pcm16b16000r(in_bytes=bytes)

    # Формирование тела запроса.
    url = ***_PATH + '?uuid=%s&key=%s&topic=%s&lang=%s' % (
        request_id,
        key,
        topic,
        lang
    )

    # Считывание блока байтов.
    chunks = read_chunks(CHUNK_SIZE, bytes)

    # Установление соединения и формирование запрос.
    connection = httplib2.HTTPConnectionWithTimeout(***_HOST)

    connection.connect()
    connection.putrequest('POST', url)
    connection.putheader('Transfer-Encoding', 'chunked')
    connection.putheader('Content-Type', 'audio/x-pcm;bit=16;rate=16000')
    connection.endheaders()

    # Отправка байтов блоками.
    for chunk in chunks:
        connection.send(('%s\r\n' % hex(len(chunk))[2:]).encode())
        connection.send(chunk)
        connection.send('\r\n'.encode())

    connection.send('0\r\n\r\n'.encode())
    response = connection.getresponse()

    # Обработка ответа сервера.
    if response.code == 200:
        response_text = response.read()
        xml = XmlElementTree.fromstring(response_text)

        if int(xml.attrib['success']) == 1:
            max_confidence = - float("inf")
            text = ''

            for child in xml:
                if float(child.attrib['confidence']) > max_confidence:
                    text = child.text
                    max_confidence = float(child.attrib['confidence'])

            if max_confidence != - float("inf"):
                return text
            else:
                raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))
        else:
            raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))
    else:
        raise SpeechException('Unknown error.\nCode: %s\n\n%s' % (response.code, response.read()))


# Создание своего исключения.
class SpeechException(Exception):
    pass
