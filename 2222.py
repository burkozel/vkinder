import vk_api, requests, json, db
from random import randrange
from vk_api.longpoll import VkLongPoll, VkEventType
from infons import *

vk_session = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk_session)

def get_keyboard(buts):
    nb = []
    for i in range(len(buts)):
        nb.append([])
        for k in range(len(buts[i])):
            nb[i].append(None)
    for i in range(len(buts)):
        for k in range(len(buts[i])):
            text = buts[i][k][0]
            color = {'зеленый': 'positive', 'красный': 'negative', 'синий': 'primary', 'белый': 'secondary'}[buts[i][k][1]]
            nb[i][k] = {"action": {"type": "text", "payload": "{\"button\": \"" + "1" + "\"}", "label": f"{text}"},
                        "color": f"{color}"}
    first_keyboard = {'one_time': False, 'buttons': nb, 'inline': False}
    first_keyboard = json.dumps(first_keyboard, ensure_ascii=False).encode('utf-8')
    first_keyboard = str(first_keyboard.decode('utf-8'))
    return first_keyboard

clear_key = get_keyboard(
    []
)

searching_keyboard = get_keyboard([
    [('Да', 'белый'), ('Нет', 'белый')], [('Стоп', 'красный')]
])

st_keyboard = get_keyboard([
    [('Начать', 'зеленый')]
])

menu_key = get_keyboard([
    [('Избранное', 'белый')], [('Редактировать анкету', 'белый')], [('Продолжить поиск', 'зеленый')], [('Остановить поиск', 'красный')], [('Сохранить пользователей', 'синий')]
])

search_anket = get_keyboard([
    [('Да', 'зеленый'), ('Нет', 'красный')], [('Стоп', 'белый'), ('Меню', 'белый')]
])

family_key = get_keyboard([
    [('В активном поиске', 'белый'), ('Всё сложно', 'белый')], [('Холост', 'белый'), ('В браке', 'белый')]
])

sex_key = get_keyboard([[('1', 'белый')], [('2', 'белый')], [('3', 'белый')]])

def sender(id, text, key):
    vk_session.method('messages.send', {'user_id': id, 'message': text, 'random_id': 0, 'keyboard': key})

def send_to(user_id, message, attachment=''):
    vk_session.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7),
                                        'attachment': attachment})

def get_params(add_params: dict = None):
    params = {
        'access_token': user_token,
        'v': '5.131'
    }
    if add_params:
        params.update(add_params)
        pass
    return params

data = [{'people': [], 'favorite': []}]

class VkBot:

    def __init__(self, user_id):
        self.dict_info = []
        self.user = db.User
        self.user_id = user_id
        self.username = self.user_name()
        self.top_photos = ''
        self.age = 0
        self.searching_user_id = 0
        self.sex = 0
        self.city = 0
        self.sex = 0
        self.settozero = 0

    def user_name(self):
        response = requests.get('https://api.vk.com/method/users.get', get_params({'user_ids': self.user_id}))
        for user_info in response.json()['response']:
            self.username = user_info['first_name'] + ' ' + user_info['last_name']
        return self.username

    def file_writer_all(self, my_dict):
        data[0]['people'].append(my_dict)
        with open('info.json', 'w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, )

    def file_writer_fav(self, my_dict):
        data[0]['favorite'].append(my_dict)
        with open('info.json', 'w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, )

    def show_menu(self):
        sender(self.user_id, "Меню", menu_key)
        while True:
            for new_event in longpoll.listen():
                if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me:
                    if new_event.message.lower() == 'избранное':
                        send_to(self.user_id, 'Понравившиеся:')
                        dating_users = db.view_all(self.user_id)
                        for dating_user in dating_users:
                            send_to(self.user_id, f'@id{dating_user}')
                    elif new_event.message.lower() == 'редактировать анкету':
                        self.settozero = 0
                        self.start()
                    elif new_event.message.lower() == 'продолжить поиск':
                        send_to(self.user_id, 'Ищу...')
                        self.settozero += 1
                        self.find_user()
                        self.get_top_photos()
                        send_to(self.user_id,
                                  f'Имя  и Фамилия: {self.username}\n Ссылка на страницу: @id{self.searching_user_id}',
                                  self.top_photos)
                        info = {'vk_id': self.searching_user_id, 'user_name': self.username, 'age': self.age,
                                'url': 'https://vk.com/id' + str(self.searching_user_id)}
                        self.file_writer_all(info)
                        self.searching()
                    elif new_event.message.lower() == "остановить поиск":
                        sender(self.user_id, 'Обязательно пиши! Подберем тебе кого-нибудь еще!', st_keyboard)
                    elif new_event.message.lower() == 'сохранить пользователей':
                        send_to(self.user_id, 'Сохраняем...')
                        db.write_in_db()
                    else:
                        send_to(self.user_id, f"Попробуй выбрать вариант из кнопок.")
                        self.show_menu()


    def start(self):
        self.user_name()
        sender(self.user_id, 'Заполним анкету для поиска? В каком городе будем искать?', clear_key)
        for new_event in longpoll.listen():
            if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me:
                self.get_user_city(new_event.message)
                self.user_name()
                self.get_user_age()
                self.get_user_sex()
                self.find_user()
                self.get_top_photos()
                people = {'vk_id': self.searching_user_id, 'user_name': self.username, 'age': self.age,
                          'url': 'https://vk.com/id' + str(self.searching_user_id)}
                self.file_writer_all(people)
                send_to(self.user_id,
                          f'Имя  и Фамилия: {self.username}\n \nСсылка на страницу: @id{self.searching_user_id}',
                          self.top_photos)
                return self.searching()

    def searching(self):
        sender(self.user_id, 'Понравился пользователь?', search_anket)
        while True:
            for new_event in longpoll.listen():
                if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me:
                    if new_event.message.lower() == 'стоп':
                        sender(self.user_id, 'Обязательно пиши! Найдем тебе кого-нибудь!', st_keyboard)
                    elif new_event.message.lower() == 'меню':
                        return self.show_menu()
                    elif new_event.message.lower() == 'да':
                        people = {'vk_id': self.searching_user_id, 'user_name': self.username, 'age': self.age,
                                  'url': 'https://vk.com/id' + str(self.searching_user_id)}
                        self.file_writer_fav(people)
                        send_to(self.user_id, 'Пользователь добавлен в базу данных')
                        self.show_menu()
                    else:
                        send_to(self.user_id, 'Идет поиск...')
                        self.settozero += 1
                        self.find_user()
                        self.get_top_photos()
                        send_to(self.user_id,
                                  f'Имя  и Фамилия: {self.username}\n Ссылка на страницу: @id{self.searching_user_id}',
                                  self.top_photos)
                        info = {'vk_id': self.searching_user_id, 'user_name': self.username, 'age': self.age,
                                'url': 'https://vk.com/id' + str(self.searching_user_id)}
                        self.file_writer_all(info)
                        sender(self.user_id, 'Понравился пользователь?', search_anket)

    def get_user_age(self):
        try:
            send_to(self.user_id, 'Введи возраст для поиска')
            for new_event in longpoll.listen():
                if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me:
                    self.age = int(new_event.message)
                    return self.age
        except ValueError:
            send_to(self.user_id, 'Некорректное значение. Попробуй ввести число.')
            return self.get_user_age()

    def get_user_sex(self):
        try:
            sender(self.user_id, "Кого будем искать?\n 1 - Девушку\n 2 - Парня\n 3 - Без разницы", sex_key)
            for new_event in longpoll.listen():
                if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me:
                    self.sex = new_event.message
                    if int(self.sex) in [1, 2, 3]:
                        sender(self.user_id, "Ищу...", clear_key)
                        return self.sex
                    else:
                        send_to(self.user_id, f'Некорректное значение')
                        return self.get_user_sex()
        except ValueError:
            send_to(self.user_id, f'Некорректное значение')
            self.get_user_sex()

    def get_user_city(self, city):
        try:
            response = requests.get('https://api.vk.com/method/database.getCities',
                                    get_params({'country_id': 1, 'count': 1, 'q': city}))
            user_info = response.json()['response']
            self.city = user_info['items'][0]['id']
        except IndexError:
            send_to(self.user_id, f'Некорректное значение')
            self.start()
        return self.city

    def find_user(self):
        try:
            response = requests.get('https://api.vk.com/method/users.search',
                                    get_params({'count': 1,
                                                'offset': self.settozero,
                                                'city': self.city,
                                                'country': 1,
                                                'sex': self.sex,
                                                'age_from': self.age,
                                                'age_to': self.age,
                                                'fields': 'is_closed',
                                                'status': 6,
                                                'has_photo': 1}
                                               )
                                    )
            if response.json()['response']['items']:
                for searching_user_id in response.json()['response']['items']:
                    private = searching_user_id['is_closed']
                    if private:
                        self.settozero += 1
                        self.find_user()
                    else:
                        self.searching_user_id = searching_user_id['id']
                        self.username = searching_user_id['first_name'] + ' ' + searching_user_id['last_name']
            else:
                self.settozero += 1
                self.find_user()
        except KeyError:
            send_to(self.user_id, f'Попробуй перезаполнить анкету. Там было что-то не так.')
            self.start()

    def get_top_photos(self):
        photos = []
        response = requests.get(
            'https://api.vk.com/method/photos.get',
            get_params({'owner_id': self.searching_user_id,
                        'album_id': 'profile',
                        'extended': 1}))
        try:
            sorted_response = sorted(response.json()['response']['items'],
                                     key=lambda x: x['likes']['count'], reverse=True)
            for photo_id in sorted_response:
                photos.append(f'''photo{self.searching_user_id}_{photo_id['id']}''')
            self.top_photos = ','.join(photos[:3])
            return self.top_photos
        except:
            pass

    def react(self, message):
        sender(self.user_id, 'Привет!', st_keyboard)
        if message.lower() == 'начать':
            return self.start()
        elif message.lower() == "стоп":
            return f"Обязательно пиши! Найдем тебе кого-нибудь!"
        else:
            return f"Попробуй выбрать вариант из кнопок."


if __name__ == '__main__':
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            bot = VkBot(event.user_id)
            send_to(event.user_id, bot.react(event.text))