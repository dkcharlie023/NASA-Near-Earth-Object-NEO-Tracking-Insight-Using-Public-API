import streamlit as st
import pymysql
from io import StringIO
import csv

st.set_page_config(layout="wide")
st.title("🚀 NASA NEO Dashboard")

db = {
    "host": "localhost",
    "user": "root",
    "password": "Mysql@023",
    "database": "project_nasa_neo"
}

@st.cache_data
def get_orbiting_bodies():
    try:
        con = pymysql.connect(**db)
        cur = con.cursor()
        cur.execute("SELECT DISTINCT orbiting_body FROM close_approach")
        rows = [r[0] for r in cur.fetchall()]
        con.close()
        return rows
    except:
        return []

bodies = get_orbiting_bodies()

# ✅ Removed neo_reference_id, name_contains, min_approaches
if "filters" not in st.session_state:
    st.session_state.filters = {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "min_velocity": 0,
        "max_velocity": 100000,
        "max_distance": 1000000,
        "hazard_only": False,
        "orbiting_body": "All",
        "orbiting_body_contains": "",
        "magnitude_range": (5.0, 30.0),
        "diameter_range": (0.0, 10.0),
        "lunar_range": (0.0, 100.0)
    }

f = st.session_state.filters
tab1, tab2 = st.tabs(["🧪 Filters", "📊 Queries"])

with tab1:
    f["start_date"] = st.text_input("Start Date (YYYY-MM-DD)", f["start_date"])
    f["end_date"] = st.text_input("End Date (YYYY-MM-DD)", f["end_date"])
    f["min_velocity"] = st.number_input("Min Velocity (km/h)", 0, value=f["min_velocity"])
    f["max_velocity"] = st.number_input("Max Velocity (km/h)", 0, value=f["max_velocity"])
    f["max_distance"] = st.number_input("Max Miss Distance (km)", 0, value=f["max_distance"])
    f["lunar_range"] = st.slider("Lunar Distance Range", 0.0, 100.0, f["lunar_range"])
    f["hazard_only"] = st.checkbox("Hazardous Only", value=f["hazard_only"])
    f["orbiting_body"] = st.selectbox("Orbiting Body", ["All"] + bodies, index=0)
    f["orbiting_body_contains"] = st.text_input("Orbiting Body Contains", f["orbiting_body_contains"])
    f["magnitude_range"] = st.slider("Magnitude Range", 5.0, 35.0, f["magnitude_range"])
    f["diameter_range"] = st.slider("Diameter Max (km)", 0.0, 15.0, f["diameter_range"])

with tab2:
    st.subheader("Select and Run Query")

    def filtered_query():
        query = (
            "SELECT a.name, ca.neo_reference_id, ca.close_approach_date, "
            "ca.relative_velocity_kmph, ca.miss_distance_km, ca.miss_distance_lunar, "
            "a.absolute_magnitude_h, a.estimated_diameter_max_km, ca.orbiting_body, "
            "a.is_potentially_hazardous_asteroid "
            "FROM close_approach ca "
            "JOIN asteroids a ON ca.neo_reference_id = a.id "
            "WHERE ca.close_approach_date BETWEEN '{0}' AND '{1}' "
            "AND ca.relative_velocity_kmph BETWEEN {2} AND {3} "
            "AND ca.miss_distance_km <= {4} "
            "AND ca.miss_distance_lunar BETWEEN {5} AND {6} "
            "AND a.absolute_magnitude_h BETWEEN {7} AND {8} "
            "AND a.estimated_diameter_max_km BETWEEN {9} AND {10} ".format(
                f["start_date"], f["end_date"], f["min_velocity"], f["max_velocity"],
                f["max_distance"], f["lunar_range"][0], f["lunar_range"][1],
                f["magnitude_range"][0], f["magnitude_range"][1],
                f["diameter_range"][0], f["diameter_range"][1]
            )
        )

        if f["hazard_only"]:
            query += "AND a.is_potentially_hazardous_asteroid = TRUE "
        if f["orbiting_body"] != "All":
            query += "AND ca.orbiting_body = '" + f["orbiting_body"] + "' "
        if f["orbiting_body_contains"]:
            query += "AND ca.orbiting_body LIKE '%" + f["orbiting_body_contains"] + "%' "

        query += "ORDER BY ca.close_approach_date DESC LIMIT 100"
        return query

    queries = {
        "1. Filtered NEO Summary": filtered_query,
        "2. All Asteroids": "SELECT * FROM asteroids LIMIT 100",
        "3. All Close Approaches": "SELECT * FROM close_approach LIMIT 100",
        "4. Monthly Approach Trends": "SELECT MONTH(close_approach_date) AS month, COUNT(*) AS count FROM close_approach GROUP BY month ORDER BY month",
        "5. Top 10 Fastest NEOs": "SELECT name, MAX(relative_velocity_kmph) AS velocity FROM close_approach JOIN asteroids ON id = neo_reference_id GROUP BY name ORDER BY velocity DESC LIMIT 10",
        "6. Hazardous vs Non-Hazardous": "SELECT is_potentially_hazardous_asteroid, COUNT(*) FROM asteroids GROUP BY is_potentially_hazardous_asteroid",
        "7. Orbiting Body Distribution": "SELECT orbiting_body, COUNT(*) FROM close_approach GROUP BY orbiting_body ORDER BY COUNT(*) DESC",
        "8. Largest Asteroids": "SELECT name, estimated_diameter_max_km FROM asteroids ORDER BY estimated_diameter_max_km DESC LIMIT 10",
        "9. Closest Approaches": "SELECT name, miss_distance_km FROM close_approach JOIN asteroids ON id = neo_reference_id ORDER BY miss_distance_km ASC LIMIT 10",
        "10. Most Frequent NEOs": "SELECT neo_reference_id, COUNT(*) as approaches FROM close_approach GROUP BY neo_reference_id ORDER BY approaches DESC LIMIT 10",
        "11. Average Velocity per Orbiting Body": "SELECT orbiting_body, AVG(relative_velocity_kmph) as avg_velocity FROM close_approach GROUP BY orbiting_body",
        "12. High Magnitude NEOs": "SELECT name, absolute_magnitude_h FROM asteroids WHERE absolute_magnitude_h > 25 ORDER BY absolute_magnitude_h DESC",
        "13. Yearly Approach Count": "SELECT YEAR(close_approach_date), COUNT(*) FROM close_approach GROUP BY YEAR(close_approach_date)",
        "14. Approaches on Earth Only": "SELECT * FROM close_approach WHERE orbiting_body = 'Earth'",
        "15. NEOs with Min Diameter > 1km": "SELECT name, estimated_diameter_max_km FROM asteroids WHERE estimated_diameter_max_km > 1",
        "16. Most Approaches by Single NEO": "SELECT neo_reference_id, COUNT(*) FROM close_approach GROUP BY neo_reference_id ORDER BY COUNT(*) DESC LIMIT 1",
        "17. Fastest Per Year": "SELECT YEAR(close_approach_date) as yr, MAX(relative_velocity_kmph) FROM close_approach GROUP BY yr",
        "18. Average Miss Distance": "SELECT AVG(miss_distance_km) FROM close_approach",
        "19. Distinct Orbiting Bodies": "SELECT DISTINCT orbiting_body FROM close_approach",
        "20. Most Distant Approaches": "SELECT name, miss_distance_km FROM close_approach JOIN asteroids ON id = neo_reference_id ORDER BY miss_distance_km DESC LIMIT 10",
        "21. NEOs with Specific Term in Name ('2024')": "SELECT * FROM asteroids WHERE name LIKE '%2024%'",
        "22. NEOs Without Approaches": "SELECT * FROM asteroids WHERE id NOT IN (SELECT DISTINCT neo_reference_id FROM close_approach)",
        "23. Most Active Orbiting Body": "SELECT orbiting_body, COUNT(*) FROM close_approach GROUP BY orbiting_body ORDER BY COUNT(*) DESC LIMIT 1"
    }

    query = st.selectbox("Select a query", list(queries.keys()))

    if st.button("Run Query"):
        try:
            con = pymysql.connect(**db)
            cur = con.cursor()
            sql = queries[query]() if callable(queries[query]) else queries[query]
            cur.execute(sql)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

            if rows:
                table = "<table><thead><tr>" + "".join("<th>" + c + "</th>" for c in cols) + "</tr></thead><tbody>"
                for r in rows:
                    table += "<tr>" + "".join("<td>" + str(v) + "</td>" for v in r) + "</tr>"
                table += "</tbody></table>"
                st.markdown(table, unsafe_allow_html=True)

                output = StringIO()
                writer = csv.writer(output)
                writer.writerow(cols)
                writer.writerows(rows)
                st.download_button("📥 Download CSV", output.getvalue(), "results.csv", "text/csv")
            else:
                st.info("No data found.")
            con.close()
        except Exception as e:
            st.error("Error: " + str(e))
