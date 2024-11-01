import requests
import time

URL = 'Your link'  # Замените на свою ссылку
Interval = 60  #Время, по истечению которого бот собирает статьи. По умолчанию 1 минунта

def fetch_lost_animals():
    try:       
        response = requests.get(URL)       
        print(f"Код состояния: {response.status_code}") # если случится ошибка

        # Если код состояния не 200, выводим текст ответа
        if response.status_code != 200:
            print("Ответ API неуспешен:")
            print(response.text)
            return
        
        data = response.json()

        # Проверяем наличие объявлений
        if data and 'results' in data:
            for ad in data['results']:
                # Извлекаем ссылку на объявление
                link = ad.get('link')  # Ключ доступа для сохранения объявлений в формате JSON. Необходимо убедится что ключ присутсвует на сайте.
                if link:
                    print(f'Ссылка на объявление: {link}')
                else:
                    print('Ошибка: ссылка не найдена в объявлении.')
        else:
            print('Объявлений не найдено')

    # Если случилась ошибка при сборе объявлений
    except ValueError as e:
        print(f'Ошибка при разборе JSON: {e}')
        print(f'Ответ API: {response.text}')  # если будет ошибка 200, то будет выводить код сайта
    except Exception as e:
        print(f'Произошла ошибка: {e}')

def main():
    while True:
        fetch_lost_animals()  # Сбор данных
        print(f'Следующий сбор данных через {Interval} секунд...')
        time.sleep(Interval)  # Пауза до следующего запроса

if __name__ == '__main__':
    main()