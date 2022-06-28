import requests
import seaborn as sns
import os.path
import matplotlib.pyplot as plt
import numpy as np
import strings as st
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, AutoMinorLocator, NullFormatter

appid = ''
s_city_name = 'Челябинск'

if os.path.isfile(st.BOT_TOKEN_OWM_FILENAME):
    f = open(st.BOT_TOKEN_OWM_FILENAME, "r")
    appid = f.read() # полученный при регистрации на OpenWeatherMap.org. Что-то вроде такого набора букв и цифр: "6d8e495ca73d5bbc1d6bf8ebd52c4123"
    f.close()
else:
    print("Пожалуйста, создайте в папке проекта файл 'token.txt' и поместите туда токен для работы телеграм бота")

def get_wind_direction(deg):
    l = ['С ','СВ',' В','ЮВ','Ю ','ЮЗ',' З','СЗ']
    for i in range(0,8):
        step = 45.
        min = i*step - 45/2.
        max = i*step + 45/2.
        if i == 0 and deg > 360-45/2.:
            deg = deg - 360
        if deg >= min and deg <= max:
            res = l[i]
            break
    return res

# Проверка наличия в базе информации о нужном населенном пункте
def get_city_id(s_city_name):
    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/find",
                     params={'q': s_city_name, 'type': 'like', 'units': 'metric', 'lang': 'ru', 'APPID': appid})
        data = res.json()
        cities = ["{} ({})".format(d['name'], d['sys']['country'])
                  for d in data['list']]
        city_id = data['list'][0]['id']
    except Exception as e:
        print("Exception (find):", e)
        pass
    assert isinstance(city_id, int)
    return city_id

# Запрос текущей погоды
def request_current_weather(city_id):
    city_id = get_city_id(city_id)
    result = []
    hours = {'1h':'1 час','2h':'2 часа','3h':'3 часа','4h':'4 часа','5h':'5 часов','6h':'6 часов','7h':'7 часов','8h':'8 часов','9h':'9 часов'}
    rain_current = []
    hour = []
    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/weather",
                     params={'id': city_id, 'units': 'metric', 'lang': 'ru', 'APPID': appid})
        data = res.json()
        if 'rain' in data:
            for key, value in data['rain'].items():
                if key in hours:
                    hour.append(hours[key])
                    hour.append(value)
            rain_current = ' '.join(['Обьем осадков за', hour[0], str(hour[1]), 'мм/м2'])
        else:
            rain_current = 'Без осадков'
        result.append('Город: ' + data['name'])
        result.append("Условия: " + data['weather'][0]['description'])
        result.append(rain_current) # получаем обьем осадков
        result.append("Влажность: " + str(data['main']['humidity']))
        result.append("Температура: " + str(data['main']['temp']))
        result.append("Ощущается как: " + str(data['main']['feels_like']))
        result.append("Минимальная температура: " + str(data['main']['temp_min']))
        result.append("Максимальная температура: " + str(data['main']['temp_max']))
        result.append("Давление: " + str(data['main']['pressure']) + ' мм рт.ст.')
        result.append("Ветер: " + str(data['wind']['speed']) + ' м/с')
    except Exception as e:
        print("Exception (weather):", e)
    return ', '. join(result)

# Прогноз
def request_forecast(city_id):
    city_id = get_city_id(city_id)
    result = []
    temp = []
    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                           params={'id': city_id, 'units': 'metric', 'lang': 'ru', 'APPID': appid})
        data = res.json()
        result.append('Город: ' + data['city']['name'])
        for i in data['list']:
            temp = [(i['dt_txt'])[:16],' {0:+3.0f}'.format(i['main']['temp']),' {0:3.0f}'.format(i['main']['humidity']), '{0:2.0f} '.format(i['wind']['speed']),get_wind_direction(i['wind']['deg']),i['weather'][0]['description']]
            result.append(temp)
    except Exception as e:
        return "Exception (forecast):"
    return result

# Визуализация прогноза погоды
def visual(data):
    temp = []
    data_per_dey = []
    wind = []
    humidity = []
    myhex = '#660099'
    myhex_h = '#990000'
    rgb = np.array([204,255,51])/255.
    for i in range(1, len(data)):
        data_per_dey.append(data[i][0][5:]) # добавляем дату [5:-6:]
        temp.append(int(data[i][1]))                # добавляем температуру
        humidity.append(int(data[i][2])/10)  # добавляем влажность в пределах до 10
        wind.append(float(data[i][3]))                 # добавляем ветер
    y = [int(n) for n in range(1,max(temp)+1)]
    x = [int(n) for n in range(0,len(data_per_dey))]
    fig = plt.figure()
    ax = fig.add_subplot(111)
    # повернем надписи по оси х
    xax = ax.xaxis
    xlabels = xax.get_ticklabels()
    for label in xlabels:
        label.set_rotation(90)

    plt.title(data[0])
    # установим диапазон значений по оси у
    plt.yticks(y)

    ax.plot(data_per_dey, wind, color=myhex, label='Ветер, м/с')
    ax.plot(data_per_dey, humidity, color=myhex_h, label='Влажность')
    ax.bar(data_per_dey, temp, color=rgb, alpha=0.75, align='center', label='Температура, град')
    plt.legend(loc='upper center', ncol=2)
    plt.savefig('saved_figure.png', bbox_inches='tight')
    pass

# def visual(data):
#     temp = []
#     data_per_dey = []
#     wind = []
#     myhex = '#660099'
#     rgb = np.array([204,255,51])/255.
#     for i in range(1, len(data)):
#         data_per_dey.append(data[i][0][5:-6:]) # добавляем дату
#         temp.append(int(data[i][1]))                # добавляем температуру
#         wind.append(int(data[i][2]))                 # добавляем ветер
#     y = [int(n) for n in range(1,max(temp))]
#     fig = plt.figure()
#     ax = fig.add_subplot(111)
#     ax.plot(data_per_dey, wind, color=myhex, label='Ветер, м/с')
#     ax.bar(data_per_dey, temp, color=rgb, alpha=0.75, align='center', label='Температура, град')
#     plt.yticks(y)
#     plt.title(data[0])
#     plt.legend(loc='upper center', ncol=2)
#     plt.savefig('saved_figure.png')
#     pass

# print(*request_forecast(city_id), sep='\n')
