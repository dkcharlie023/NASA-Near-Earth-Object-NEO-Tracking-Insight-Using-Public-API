import requests
import pymysql

API_KEY = "pkG3ZUWm26ajcM4kdyIgsLPBonPsqqvVi4L9GgNf"
target = 10000

mydb = pymysql.connect(
    host='localhost',
    user='root',
    password='Mysql@023',
    database='project_nasa_neo',
    autocommit=True
)
mycursor = mydb.cursor()

asteroid_query = """
    INSERT INTO asteroids (
        id,
        name,
        absolute_magnitude_h,
        estimated_diameter_min_km,
        estimated_diameter_max_km,
        is_potentially_hazardous_asteroid
    )
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        absolute_magnitude_h = VALUES(absolute_magnitude_h),
        estimated_diameter_min_km = VALUES(estimated_diameter_min_km),
        estimated_diameter_max_km = VALUES(estimated_diameter_max_km),
        is_potentially_hazardous_asteroid = VALUES(is_potentially_hazardous_asteroid)
"""

approach_query = """
    INSERT INTO close_approach (
        neo_reference_id,
        close_approach_date,
        relative_velocity_kmph,
        astronomical,
        miss_distance_km,
        miss_distance_lunar,
        orbiting_body
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date=2024-01-01&end_date=2024-01-08&api_key={API_KEY}"
count = 0

while count < target and url:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    neo_data = data['near_earth_objects']

    for date, asteroids in neo_data.items():
        for ast in asteroids:
            try:
                asteroid_values = (
                    int(ast['id']),
                    ast['name'],
                    float(ast['absolute_magnitude_h']),
                    float(ast['estimated_diameter']['kilometers']['estimated_diameter_min']),
                    float(ast['estimated_diameter']['kilometers']['estimated_diameter_max']),
                    bool(ast['is_potentially_hazardous_asteroid'])
                )
                mycursor.execute(asteroid_query, asteroid_values)
                for approach in ast.get('close_approach_data', []):
                    try:
                        approach_values = (
                            int(ast['id']),
                            approach['close_approach_date'],
                            float(approach['relative_velocity']['kilometers_per_hour']),
                            float(approach['miss_distance']['astronomical']),
                            float(approach['miss_distance']['kilometers']),
                            float(approach['miss_distance']['lunar']),
                            approach['orbiting_body']
                        )
                        mycursor.execute(approach_query, approach_values)
                    except Exception as e:
                        print(f"⚠️ Skipped close approach insert error: {e}")
                count += 1
                if count >= target:
                    break
            except Exception as e:
                print(f"⚠️ Skipped asteroid insert error: {e}")
        if count >= target:
            break
    url = data.get('links', {}).get('next')

print(f"✅ Inserted {count} asteroids and their close approach data into MySQL.")

mycursor.close()
mydb.close()
