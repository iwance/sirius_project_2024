import pandas as pd
from catboost import CatBoostRegressor

from openai import OpenAI
client = OpenAI(api_key='')

#подготовим данные
df = pd.read_csv('data.csv')
districts = pd.read_excel('metro_info.xlsx') # добавим информацию по станции метро
distances = pd.read_excel('metro_distances.xlsx') # добавим расстояния от станции метро до разных мест

#удалим очень редкие станции метро
counts = df.groupby('Metro station')['Metro station'].transform('count')
mask = counts > 2
df = df[mask]

#подготовим датасеты к присоединению (переведем станции метро в нижний регистр, удалим повторения)
df['Metro station'] = df['Metro station'].str.lower()
df['Metro station'] = df['Metro station'].str.replace(' ', '')
districts['Metro station'] = districts['Metro station'].str.lower()
districts['Metro station'] = districts['Metro station'].str.replace(' ', '')
distances['Metro station'] = distances['Metro station'].str.lower()
distances['Metro station'] = distances['Metro station'].str.replace(' ', '')
districts = districts.drop_duplicates(subset=['Metro station'])
distances = distances.drop_duplicates(subset=['Metro station'])

#присоединим
df = pd.merge(df, districts, on='Metro station', how='left')
df = pd.merge(df, distances, on='Metro station', how='left')
df = df.dropna()
df.drop(columns=['Living area', 'Kitchen area'], inplace = True)

#очистим выбросы, готовим выборку (в основном - по боксплотам и распределению)
df = df[df['Number of rooms'] <= 6] #чистим выбросы по количеству комнат
df = df[df['Minutes to metro'] <= 30] #чистим выбросы по минутам до метро
df = df[df['Area'] >= 10] #чистка выбросов по площади 1
df = df[df['Area'] <= 300] #чистка выбросов по площади 2
#по таргету нужно выбрать более конкретный сегмент, поставим границы поуже
df = df[df['Price'] <= 19 * (10 ** 6)] #Один из вариантов границ - 19 млн (верхний ус). В нашем случае можем ставить меньше
df = df[df['Price'] >= 2.5 * (10 ** 6)] #нижняя граница 2.5

#Разбиение на таргет и признаки
X = df.drop(columns=['Price'])  # Признаки 
y = df['Price']  # Таргет

#Обучим модель, используя CatBoost
model = CatBoostRegressor(iterations=1250,  # количество деревьев
                          learning_rate=0.125,  # скорость обучения
                          depth=7,  # глубина деревьев
                          random_state=42,  # для воспроизводимости результатов
                          verbose = 0)  # подробность вывода информации о процессе обучения
# Обучение
model.fit(X, y, cat_features=[0, 1, 3, 10, 11, 8, 9])  # Указываем индексы категориальных признаков

def get_responce(text):
    try:
        completion = client.chat.completions.create(
            model='gpt-4-0125-preview',
            messages=[
                {"role": "system", "content": open("input.txt","r").read()},
                {"role": "user", "content": text}
            ]
        )
        request = completion.choices[0].message.content.split(",")
    except:
        return "Ошибка получения данных от ChatGpt"
    
    try:
        for i in range(len(request)):
            try:
                request[i] = int(request[i])
            except: pass
        print(request)

        columns = ['Apartment type', 'Metro station', 'Minutes to metro', 'Region', 'Number of rooms',
                'Area', 'Floor', 'Number of floors', 'Renovation']

        request_df = pd.DataFrame([request], columns=columns)
        request_df = pd.merge(request_df, districts, on='Metro station', how='left')
        request_df = pd.merge(request_df, distances, on='Metro station', how='left')

        return float(model.predict(request_df)[0])*1.0908 # Инфляция с момента сбора данных
    except: return "Ошибка обработки полученных данных(ChatGpt вернул формат, который не сходится с промптом)"
# ['Secondary', 'окружная', 15, 'Moscow', 2, 50, 15, 25, 'Cosmetic']
