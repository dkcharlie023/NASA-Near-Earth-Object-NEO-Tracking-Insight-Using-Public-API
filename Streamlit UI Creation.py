import streamlit as st
import pymysql
from io import StringIO
import csv

st.set_page_config(layout="wide")
st.title("🚀 NASA NEO Dashboard")

db = {"host": "localhost","user": "root","password": "Mysql@023","database": "project_nasa_neo"}

@st.cache_data
def get_orbiting_bodies():
    try:
        con = pymysql.connect(**db); cur = con.cursor()
        cur.execute("SELECT DISTINCT orbiting_body FROM close_approach")
        rows = [r[0] for r in cur.fetchall()]
        con.close(); return rows
    except: return []

@st.cache_data
def get_filter_ranges():
    try:
        con = pymysql.connect(**db); cur = con.cursor()
        cur.execute("""
            SELECT MIN(ca.close_approach_date), MAX(ca.close_approach_date),
                   MIN(ca.relative_velocity_kmph), MAX(ca.relative_velocity_kmph),
                   MIN(ca.miss_distance_km), MAX(ca.miss_distance_km),
                   MIN(ca.miss_distance_lunar), MAX(ca.miss_distance_lunar),
                   MIN(a.absolute_magnitude_h), MAX(a.absolute_magnitude_h),
                   MIN(a.estimated_diameter_max_km), MAX(a.estimated_diameter_max_km)
            FROM close_approach ca JOIN asteroids a ON ca.neo_reference_id = a.id
        """)
        row = cur.fetchone(); con.close()
        return {
            "date_min": str(row[0]), "date_max": str(row[1]),
            "velocity_min": int(row[2] or 0), "velocity_max": int(row[3] or 100000),
            "distance_min": int(row[4] or 0), "distance_max": int(row[5] or 1000000),
            "lunar_min": float(row[6] or 0.0), "lunar_max": float(row[7] or 100.0),
            "magnitude_min": float(row[8] or 0.0), "magnitude_max": float(row[9] or 35.0),
            "diameter_min": float(row[10] or 0.0), "diameter_max": float(row[11] or 15.0),
        }
    except:
        return {
            "date_min": "2024-01-01","date_max": "2024-12-31",
            "velocity_min": 0,"velocity_max": 100000,
            "distance_min": 0,"distance_max": 1000000,
            "lunar_min": 0.0,"lunar_max": 100.0,
            "magnitude_min": 0.0,"magnitude_max": 35.0,
            "diameter_min": 0.0,"diameter_max": 15.0,
        }

bodies, ranges = get_orbiting_bodies(), get_filter_ranges()
if "filters" not in st.session_state:
    st.session_state.filters = {
        "start_date": ranges["date_min"], "end_date": ranges["date_max"],
        "velocity_range": (ranges["velocity_min"], ranges["velocity_max"]),
        "distance_range": (ranges["distance_min"], ranges["distance_max"]),
        "lunar_range": (ranges["lunar_min"], ranges["lunar_max"]),
        "magnitude_range": (ranges["magnitude_min"], ranges["magnitude_max"]),
        "diameter_range": (ranges["diameter_min"], ranges["diameter_max"]),
        "hazard_only": False,"orbiting_body": "All"
    }

f = st.session_state.filters
tab1, tab2 = st.tabs(["🧪 Filters","📊 Queries"])

with tab1:
    f["start_date"] = st.text_input("Start Date (YYYY-MM-DD)", f["start_date"])
    f["end_date"] = st.text_input("End Date (YYYY-MM-DD)", f["end_date"])
    f["velocity_range"] = st.slider("Velocity Range (km/h)", ranges["velocity_min"], ranges["velocity_max"], f["velocity_range"])
    f["distance_range"] = st.slider("Miss Distance Range (km)", ranges["distance_min"], ranges["distance_max"], f["distance_range"])
    f["lunar_range"] = st.slider("Lunar Distance Range", ranges["lunar_min"], ranges["lunar_max"], f["lunar_range"])
    f["magnitude_range"] = st.slider("Magnitude Range", ranges["magnitude_min"], ranges["magnitude_max"], f["magnitude_range"])
    f["diameter_range"] = st.slider("Diameter Range (km)", ranges["diameter_min"], ranges["diameter_max"], f["diameter_range"])
    f["hazard_only"] = st.checkbox("Hazardous Only", value=f["hazard_only"])
    f["orbiting_body"] = st.selectbox("Orbiting Body", ["All"]+bodies, index=0)
    if st.button("Run Filters"):
        try:
            query = """SELECT a.name, ca.neo_reference_id, ca.close_approach_date,
                              ca.relative_velocity_kmph, ca.miss_distance_km, ca.miss_distance_lunar,
                              a.absolute_magnitude_h, a.estimated_diameter_max_km, ca.orbiting_body,
                              a.is_potentially_hazardous_asteroid
                       FROM close_approach ca JOIN asteroids a ON ca.neo_reference_id = a.id
                       WHERE ca.close_approach_date BETWEEN %s AND %s
                         AND ca.relative_velocity_kmph BETWEEN %s AND %s
                         AND ca.miss_distance_km BETWEEN %s AND %s
                         AND ca.miss_distance_lunar BETWEEN %s AND %s
                         AND a.absolute_magnitude_h BETWEEN %s AND %s
                         AND a.estimated_diameter_max_km BETWEEN %s AND %s"""
            params = [f["start_date"],f["end_date"],f["velocity_range"][0],f["velocity_range"][1],
                      f["distance_range"][0],f["distance_range"][1],f["lunar_range"][0],f["lunar_range"][1],
                      f["magnitude_range"][0],f["magnitude_range"][1],f["diameter_range"][0],f["diameter_range"][1]]
            if f["hazard_only"]: query += " AND a.is_potentially_hazardous_asteroid = 1"
            if f["orbiting_body"]!="All": query+=" AND ca.orbiting_body=%s"; params.append(f["orbiting_body"])
            con = pymysql.connect(**db); cur = con.cursor(); cur.execute(query,params)
            rows, cols = cur.fetchall(), [d[0] for d in cur.description]; con.close()
            st.markdown(f"**Total Results:** {len(rows)}")
            output = StringIO(); csv.writer(output).writerows([cols]+list(rows))
            st.download_button("📥 Download CSV", output.getvalue(), "filter_results.csv","text/csv")
            if rows:
                table="<table><thead><tr>"+"".join(f"<th>{c}</th>" for c in cols)+"</tr></thead><tbody>"
                for r in rows: table+="<tr>"+"".join(f"<td>{v}</td>" for v in r)+"</tr>"
                st.markdown(table+"</tbody></table>", unsafe_allow_html=True)
            else: st.info("No data found.")
        except Exception as e: st.error(f"Error: {e}")

with tab2:
    queries={
        "1.Count how many times each asteroid has approached Earth":"SELECT a.name,COUNT(*) FROM close_approach ca JOIN asteroids a ON a.id=ca.neo_reference_id GROUP BY a.name ORDER BY COUNT(*) DESC",
        "2.List all Near-Earth Objects (NEOs) and their hazard status":"SELECT a.name,a.is_potentially_hazardous_asteroid FROM asteroids a",
        "3.Show the top 10 fastest NEOs":"SELECT a.name,MAX(ca.relative_velocity_kmph) FROM close_approach ca JOIN asteroids a ON a.id=ca.neo_reference_id GROUP BY a.name ORDER BY MAX(ca.relative_velocity_kmph) DESC LIMIT 10",
        "4.Find the NEOs that passed closest to Earth":"SELECT a.name,MIN(ca.miss_distance_km) FROM close_approach ca JOIN asteroids a ON a.id=ca.neo_reference_id GROUP BY a.name ORDER BY MIN(ca.miss_distance_km) ASC",
        "5.Determine the largest asteroid by diameter":"SELECT a.name,a.estimated_diameter_max_km FROM asteroids a ORDER BY a.estimated_diameter_max_km DESC LIMIT 1",
        "6.Monthly trend of NEO approaches":"SELECT MONTH(ca.close_approach_date),COUNT(*) FROM close_approach ca GROUP BY MONTH(ca.close_approach_date) ORDER BY MONTH(ca.close_approach_date)",
        "7.Hazardous vs non-hazardous asteroid count":"SELECT a.is_potentially_hazardous_asteroid,COUNT(*) FROM asteroids a GROUP BY a.is_potentially_hazardous_asteroid",
        "8.Orbiting body distribution":"SELECT ca.orbiting_body,COUNT(*) FROM close_approach ca GROUP BY ca.orbiting_body ORDER BY COUNT(*) DESC",
        "9.Average velocity per orbiting body":"SELECT ca.orbiting_body,AVG(ca.relative_velocity_kmph) FROM close_approach ca GROUP BY ca.orbiting_body",
        "10.List NEOs with absolute magnitude above 25":"SELECT a.name,a.absolute_magnitude_h FROM asteroids a WHERE a.absolute_magnitude_h>25 ORDER BY a.absolute_magnitude_h DESC",
        "11.Yearly approach count":"SELECT YEAR(ca.close_approach_date),COUNT(*) FROM close_approach ca GROUP BY YEAR(ca.close_approach_date)",
        "12.Approaches on Earth only":"SELECT * FROM close_approach ca WHERE ca.orbiting_body='Earth'",
        "13.NEOs with minimum diameter greater than 1 km":"SELECT a.name,a.estimated_diameter_max_km FROM asteroids a WHERE a.estimated_diameter_max_km>1",
        "14.Most approaches by a single NEO":"SELECT ca.neo_reference_id,COUNT(*) FROM close_approach ca GROUP BY ca.neo_reference_id ORDER BY COUNT(*) DESC LIMIT 1",
        "15.Fastest approach per year":"SELECT YEAR(ca.close_approach_date),MAX(ca.relative_velocity_kmph) FROM close_approach ca GROUP BY YEAR(ca.close_approach_date)",
        "16.Average miss distance":"SELECT AVG(ca.miss_distance_km) FROM close_approach ca",
        "17.Distinct orbiting bodies":"SELECT DISTINCT ca.orbiting_body FROM close_approach ca",
        "18.Most distant approaches":"SELECT a.name,MAX(ca.miss_distance_km) FROM close_approach ca JOIN asteroids a ON a.id=ca.neo_reference_id GROUP BY a.name ORDER BY MAX(ca.miss_distance_km) DESC",
        "19.NEOs with '2024' in name":"SELECT * FROM asteroids a WHERE a.name LIKE '%2024%'",
        "20.NEOs without any approaches":"SELECT * FROM asteroids a WHERE a.id NOT IN (SELECT DISTINCT ca.neo_reference_id FROM close_approach ca)",
        "21.Most active orbiting body":"SELECT ca.orbiting_body,COUNT(*) FROM close_approach ca GROUP BY ca.orbiting_body ORDER BY COUNT(*) DESC LIMIT 1"
    }
    selected_query=st.selectbox("Select a query",list(queries.keys()))
    if st.button("Run Query"):
        try:
            con=pymysql.connect(**db); cur=con.cursor(); cur.execute(queries[selected_query])
            rows,cols=cur.fetchall(),[d[0] for d in cur.description]; con.close()
            st.markdown(f"**Total Results:** {len(rows)}")
            output=StringIO(); csv.writer(output).writerows([cols]+list(rows))
            st.download_button("📥 Download CSV",output.getvalue(),"query_results.csv","text/csv")
            if rows:
                table="<table><thead><tr>"+"".join(f"<th>{c}</th>" for c in cols)+"</tr></thead><tbody>"
                for r in rows: table+="<tr>"+"".join(f"<td>{v}</td>" for v in r)+"</tr>"
                st.markdown(table+"</tbody></table>",unsafe_allow_html=True)
            else: st.info("No data found.")
        except Exception as e: st.error(f"Error: {e}")
